"""Source-code best-practice checks — STATIC (client-config) signals.

IMPORTANT: these are regex/keyword scans over the agent's source (comments
stripped — see _strip_comments in conftest.py). They are deliberately the
*weaker* half of the grader. Per the MSBench lessons doc (§15/§16), the
rules asserted here — singleton client, preferred regions, Direct mode,
429 retry, diagnostics, client lifecycle, end-to-end timeouts, provision-
once — are **client-side configuration that a single-node local emulator
cannot prove behaviorally**. They change nothing about what gets persisted
or what the API returns; they only matter against real multi-region Azure
Cosmos DB. So we keep them as source signals (to retain skill coverage for
the A/B comparison) but do NOT pretend they are behavioral.

The concrete, hard-to-game behavioral grading lives in check_behavior.py
(and check_cosmos.py / check_api.py): build the app, drive its HTTP API,
and independently read the emulator. Prefer adding new rules there whenever
the behavior is observable; only fall back to a static check here when it
genuinely is not.

The rules asserted here come from cosmosdb-agent-kit/skills/cosmosdb-best-practices.

Each check is language-gated by the `sdk` fixture; tests for other SDKs
are skipped with a clear reason. This keeps one file per category
rather than five parallel suites.
"""
from __future__ import annotations

import re

import pytest

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _need(sdk: str, *want: str):
    if sdk not in want:
        pytest.skip(f"Test does not apply to {sdk} (only runs for: {', '.join(want)})")


def _find(text: str, pat: str, flags: int = 0) -> list[str]:
    return re.findall(pat, text, flags)


# ---------------------------------------------------------------------
# Latest SDK package / version hygiene
# ---------------------------------------------------------------------

class TestLatestSdk:
    def test_python_uses_azure_cosmos(self, sdk, source_text):
        _need(sdk, "python")
        assert re.search(r"\bazure[._-]cosmos\b", source_text), (
            "Python SDK is missing. Rule sdk-python-async-deps: declare `azure-cosmos` "
            "(or `azure-cosmos-aio` for async). Found no import or dependency reference."
        )
        assert not re.search(r"\bpydocumentdb\b", source_text), (
            "Legacy `pydocumentdb` package is forbidden — it is deprecated and predates "
            "the partitioned account model. Use `azure-cosmos` instead."
        )

    def test_dotnet_uses_microsoft_azure_cosmos(self, sdk, source_text):
        _need(sdk, "dotnet")
        assert re.search(r"Microsoft\.Azure\.Cosmos", source_text), (
            "Microsoft.Azure.Cosmos package is missing. Rule sdk-dotnet-cosmos-package-id: "
            "use the GA package id `Microsoft.Azure.Cosmos`, not the abandoned `Azure.Cosmos` "
            "preview."
        )
        # Negative is enforced in check_skills.py::TestDotnetForbiddenPackage too,
        # but assert here as well for a single-place readable failure mode.
        # The negative lookbehind keeps the GA id `Microsoft.Azure.Cosmos` from
        # matching (the '.' before 'Azure' is a word boundary, so a bare
        # \bAzure\.Cosmos\b would otherwise fire on the correct package id).
        assert not re.search(r"(?<!Microsoft\.)\bAzure\.Cosmos\b", source_text), (
            "Found `Azure.Cosmos` reference. That is the abandoned preview package; the "
            "GA package is `Microsoft.Azure.Cosmos`. Rule sdk-dotnet-cosmos-package-id."
        )

    def test_java_uses_azure_cosmos_v4(self, sdk, source_text):
        _need(sdk, "java")
        # com.azure:azure-cosmos is the v4 GA artifact. Reject the v2 com.microsoft.azure:azure-documentdb.
        assert re.search(r"com\.azure[:.]azure-cosmos", source_text) or "azure-cosmos" in source_text, (
            "Java azure-cosmos v4 artifact is missing. Use `com.azure:azure-cosmos`."
        )
        assert not re.search(r"com\.microsoft\.azure[:.]azure-documentdb", source_text), (
            "Legacy `com.microsoft.azure:azure-documentdb` (v2) is forbidden. Use the v4 "
            "`com.azure:azure-cosmos` artifact."
        )

    def test_nodejs_uses_at_azure_cosmos(self, sdk, source_text):
        _need(sdk, "nodejs")
        assert "@azure/cosmos" in source_text, (
            "`@azure/cosmos` package is missing. Rule sdk-nodejs-package: use "
            "`@azure/cosmos`, not the deprecated `documentdb` npm package."
        )
        assert not re.search(r"\bdocumentdb\b", source_text), (
            "Legacy `documentdb` npm package is forbidden. Use `@azure/cosmos`."
        )

    def test_go_uses_azcosmos(self, sdk, source_text):
        _need(sdk, "go")
        assert "azcosmos" in source_text, (
            "Go SDK is missing. Use `github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos` "
            "(the only first-party Go Cosmos SDK)."
        )


# ---------------------------------------------------------------------
# Singleton client / client reuse
# ---------------------------------------------------------------------

class TestSingletonClient:
    """At most one CosmosClient construction per process. Rule sdk-singleton-client."""

    def test_python_constructs_once(self, sdk, source_text):
        _need(sdk, "python")
        # Both sync and async constructors count.
        constructors = re.findall(r"\bCosmosClient\s*\(", source_text)
        assert 0 < len(constructors) <= 2, (
            f"Found {len(constructors)} CosmosClient constructor calls. "
            "Rule sdk-singleton-client: construct exactly once and share. "
            "(At most 2 allowed to permit a single sync + single async client if needed.)"
        )

    def test_dotnet_singleton_registration(self, sdk, source_text):
        _need(sdk, "dotnet")
        # Acceptable patterns: AddSingleton<CosmosClient>, static readonly field,
        # or registering an instance via AddSingleton(new CosmosClient(...)).
        patterns = [
            r"AddSingleton\s*<\s*CosmosClient\s*>",
            r"AddSingleton\s*\(\s*new\s+CosmosClient",
            r"\bstatic\s+(readonly\s+)?CosmosClient\b",
        ]
        ok = any(re.search(p, source_text) for p in patterns)
        assert ok, (
            "No singleton CosmosClient registration detected. "
            "Rule sdk-singleton-client: register CosmosClient as a singleton with DI "
            "(`services.AddSingleton<CosmosClient>(...)`) or hold a static instance."
        )

    def test_java_singleton(self, sdk, source_text):
        _need(sdk, "java")
        # Acceptable: @Bean CosmosClient, @Singleton, static final CosmosClient, etc.
        patterns = [
            r"@Bean[\s\S]{0,200}CosmosClient",
            r"@Singleton[\s\S]{0,200}CosmosClient",
            r"static\s+final\s+CosmosClient",
            r"static\s+CosmosClient\b",
            r"static\s+CosmosAsyncClient\b",
        ]
        ok = any(re.search(p, source_text) for p in patterns)
        assert ok, (
            "No singleton CosmosClient pattern detected. "
            "Rule sdk-singleton-client: expose CosmosClient as a Spring @Bean, a Jakarta "
            "@Singleton, or a static final field."
        )

    def test_nodejs_constructs_once(self, sdk, source_text):
        _need(sdk, "nodejs")
        constructors = re.findall(r"new\s+CosmosClient\s*\(", source_text)
        assert 0 < len(constructors) <= 1, (
            f"Found {len(constructors)} `new CosmosClient(...)` calls. "
            "Rule sdk-singleton-client: construct exactly once and reuse the instance."
        )

    def test_go_constructs_once(self, sdk, source_text):
        _need(sdk, "go")
        constructors = re.findall(r"azcosmos\.NewClient\w*\s*\(", source_text)
        assert 0 < len(constructors) <= 1, (
            f"Found {len(constructors)} azcosmos.NewClient* calls. "
            "Construct the Go Cosmos client once and reuse it."
        )


# ---------------------------------------------------------------------
# Preferred regions / preferred locations
# ---------------------------------------------------------------------

class TestPreferredRegions:
    def test_python_sets_preferred_locations(self, sdk, source_text):
        _need(sdk, "python")
        assert "preferred_locations" in source_text, (
            "Rule sdk-preferred-regions: pass `preferred_locations=[...]` to CosmosClient."
        )

    def test_dotnet_sets_application_preferred_regions(self, sdk, source_text):
        _need(sdk, "dotnet")
        assert re.search(
            r"ApplicationPreferredRegions?|ApplicationRegion\b|WithApplicationPreferredRegions",
            source_text,
        ), (
            "Rule sdk-preferred-regions: set CosmosClientOptions.ApplicationPreferredRegions "
            "(or ApplicationRegion / WithApplicationPreferredRegions on the builder)."
        )

    def test_java_sets_preferred_regions(self, sdk, source_text):
        _need(sdk, "java")
        assert re.search(r"preferredRegions|preferredLocations|setPreferredRegions", source_text), (
            "Rule sdk-preferred-regions: call .preferredRegions(...) on CosmosClientBuilder."
        )

    def test_nodejs_sets_preferred_locations(self, sdk, source_text):
        _need(sdk, "nodejs")
        assert re.search(r"preferredLocations|connectionPolicy\s*[:=]", source_text), (
            "Rule sdk-preferred-regions: set connectionPolicy.preferredLocations on the "
            "CosmosClient options."
        )


# ---------------------------------------------------------------------
# Direct connection mode (.NET and Java only, per spec)
# ---------------------------------------------------------------------

class TestDirectModeDotnet:
    def test_uses_connection_mode_direct(self, sdk, source_text):
        _need(sdk, "dotnet")
        assert re.search(
            r"ConnectionMode\.Direct|WithConnectionModeDirect\s*\(",
            source_text,
        ), (
            "Rule sdk-connection-mode: .NET production default is Direct mode. Set "
            "CosmosClientOptions.ConnectionMode = ConnectionMode.Direct or use "
            "CosmosClientBuilder.WithConnectionModeDirect()."
        )


class TestDirectModeJava:
    def test_uses_direct_mode_builder(self, sdk, source_text):
        _need(sdk, "java")
        assert re.search(
            r"\.directMode\s*\(|DirectConnectionConfig\b",
            source_text,
        ), (
            "Rule sdk-connection-mode: Java production default is Direct mode. Use "
            "CosmosClientBuilder.directMode(DirectConnectionConfig.getDefaultConfig())."
        )


# ---------------------------------------------------------------------
# Retry / 429 resilience
# ---------------------------------------------------------------------

class TestRetry:
    def test_python_configures_retry(self, sdk, source_text):
        _need(sdk, "python")
        assert re.search(
            r"retry_total|retry_throttle|RetryOptions|RetryPolicy",
            source_text,
        ), (
            "No retry configuration detected. Rule sdk-retry-throttled: configure "
            "azure-core retry settings (retry_total / retry_throttle) on the client."
        )

    def test_dotnet_configures_retry(self, sdk, source_text):
        _need(sdk, "dotnet")
        assert re.search(
            r"MaxRetryAttemptsOnRateLimitedRequests|MaxRetryWaitTimeOnRateLimitedRequests|RetryOptions",
            source_text,
        ), (
            "No retry configuration. Set CosmosClientOptions.MaxRetryAttemptsOnRateLimitedRequests "
            "and MaxRetryWaitTimeOnRateLimitedRequests. Rule sdk-retry-throttled."
        )

    def test_java_configures_retry(self, sdk, source_text):
        _need(sdk, "java")
        assert re.search(
            r"throttlingRetryOptions|ThrottlingRetryOptions|setMaxRetryAttemptsOnThrottledRequests",
            source_text,
        ), (
            "No throttling retry options. Use CosmosClientBuilder.throttlingRetryOptions(...). "
            "Rule sdk-retry-throttled."
        )

    def test_nodejs_configures_retry(self, sdk, source_text):
        _need(sdk, "nodejs")
        assert re.search(
            r"retryOptions|maxRetryAttemptCount|maxWaitTimeInSeconds",
            source_text,
        ), (
            "No retry options configured. Set connectionPolicy.retryOptions on the client. "
            "Rule sdk-retry-throttled."
        )


# ---------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------

class TestDiagnostics:
    def test_python_diagnostics(self, sdk, source_text):
        _need(sdk, "python")
        assert re.search(
            r"logging_enable\s*=\s*True|CosmosHttpLoggingPolicy|enable_diagnostics_logging",
            source_text,
        ), (
            "Diagnostics are off. Rule sdk-diagnostics: pass `logging_enable=True` to "
            "operations or attach CosmosHttpLoggingPolicy."
        )

    def test_dotnet_diagnostics(self, sdk, source_text):
        _need(sdk, "dotnet")
        assert re.search(
            r"CosmosDiagnostics\b|RequestDiagnostics|DiagnosticsThresholds|"
            r"ApplicationName\s*=|EnableContentResponseOnWrite",
            source_text,
        ), (
            "No diagnostics or ApplicationName tag detected. Rule sdk-diagnostics: enable "
            "request diagnostics or at least set CosmosClientOptions.ApplicationName."
        )

    def test_java_diagnostics(self, sdk, source_text):
        _need(sdk, "java")
        assert re.search(
            r"CosmosDiagnostics|diagnosticsThresholds|clientTelemetryConfig|userAgentSuffix",
            source_text,
        ), (
            "No diagnostics enabled. Rule sdk-diagnostics: configure "
            "CosmosClientBuilder.clientTelemetryConfig or userAgentSuffix and log diagnostics."
        )

    def test_nodejs_diagnostics(self, sdk, source_text):
        _need(sdk, "nodejs")
        assert re.search(
            r"diagnostic|userAgentSuffix|logger\s*[:=]|console\.log\b",
            source_text,
            re.IGNORECASE,
        ), (
            "No diagnostics or user-agent tagging. Rule sdk-diagnostics: set userAgentSuffix "
            "and log diagnosticNode information."
        )


# ---------------------------------------------------------------------
# Lifecycle / disposal
# ---------------------------------------------------------------------

class TestLifecycle:
    def test_python_async_uses_close_or_context(self, sdk, source_text):
        _need(sdk, "python")
        # Sync CosmosClient does not require explicit close, but async does.
        if "azure.cosmos.aio" in source_text or "CosmosClient.from_connection_string" in source_text:
            assert re.search(r"\basync\s+with\b|await\s+client\.close\s*\(|\.close\s*\(\s*\)", source_text), (
                "Async CosmosClient not closed. Rule sdk-python-async-deps: use "
                "`async with CosmosClient(...) as client:` or await client.close()."
            )

    def test_dotnet_disposes_client(self, sdk, source_text):
        _need(sdk, "dotnet")
        assert re.search(
            r"AddSingleton\s*<\s*CosmosClient\s*>|using\s+\w*Cosmos|Dispose\s*\(\s*\)",
            source_text,
        ), (
            "CosmosClient lifecycle unclear. Singleton DI registration disposes for you; "
            "otherwise use `using` or call Dispose() in shutdown."
        )

    def test_java_closes_client(self, sdk, source_text):
        _need(sdk, "java")
        assert re.search(
            r"@PreDestroy|\.close\s*\(\s*\)|try\s*\(\s*CosmosClient",
            source_text,
        ), (
            "CosmosClient close() not detected. Use @PreDestroy in Spring, try-with-resources, "
            "or call .close() explicitly on shutdown."
        )


# ---------------------------------------------------------------------
# End-to-end timeouts (.NET and Java)
# ---------------------------------------------------------------------

class TestEndToEndTimeout:
    """Rule sdk-end-to-end-timeouts: SDK retries + backoff can make
    total latency exceed any per-attempt RequestTimeout by an order of
    magnitude. Caller-bounded operations need an end-to-end cap."""

    def test_dotnet_propagates_cancellation_token(self, sdk, source_text):
        _need(sdk, "dotnet")
        # Two acceptable shapes:
        #   1. RequestTimeout set on CosmosClientOptions AND at least one
        #      SDK call passes cancellationToken / ct
        #   2. CancellationTokenSource.CreateLinkedTokenSource + CancelAfter
        has_request_timeout = bool(re.search(r"\bRequestTimeout\s*=", source_text))
        passes_token = bool(re.search(
            r"(?:Read|Create|Upsert|Replace|Delete|Query|Execute|Patch)Item\w*Async\s*\([^;{}]{0,400}cancellationToken\s*[:=]",
            source_text,
            re.DOTALL,
        ))
        has_linked_cts = bool(re.search(
            r"CreateLinkedTokenSource|CancelAfter\s*\(",
            source_text,
        ))
        ok = (has_request_timeout and passes_token) or has_linked_cts
        assert ok, (
            "No end-to-end timeout pattern detected. Rule sdk-end-to-end-timeouts: "
            "either (a) set CosmosClientOptions.RequestTimeout AND pass a "
            "CancellationToken (typically HttpContext.RequestAborted) to every "
            "Cosmos call, or (b) wrap calls in a linked CancellationTokenSource "
            "with CancelAfter(...) to enforce a hard deadline across retries."
        )

    def test_java_sets_end_to_end_policy(self, sdk, source_text):
        _need(sdk, "java")
        assert re.search(
            r"endToEndOperationLatencyPolicyConfig|"
            r"setCosmosEndToEndOperationLatencyPolicyConfig|"
            r"CosmosEndToEndOperationLatencyPolicyConfig",
            source_text,
        ), (
            "No end-to-end timeout policy detected. Rule sdk-end-to-end-timeouts: "
            "build a `CosmosEndToEndOperationLatencyPolicyConfig` and attach it on "
            "the `CosmosClientBuilder` via `endToEndOperationLatencyPolicyConfig(...)`, "
            "or attach per-call via "
            "`CosmosItemRequestOptions.setCosmosEndToEndOperationLatencyPolicyConfig(...)`. "
            "ThrottlingRetryOptions alone is per-attempt, not end-to-end."
        )


# ---------------------------------------------------------------------
# Cache database/container handles — provision once, reuse forever
# ---------------------------------------------------------------------

# Patterns for "did the agent provision the database / container?".
# Per-language, case-insensitive against the comment-stripped source.
_PROVISION_PATTERNS = {
    "python":  r"create_database_if_not_exists|create_container_if_not_exists",
    "dotnet":  r"CreateDatabaseIfNotExistsAsync|CreateContainerIfNotExistsAsync",
    "java":    r"createDatabaseIfNotExists|createContainerIfNotExists",
    "nodejs":  r"databases\.createIfNotExists|containers\.createIfNotExists",
    "go":      r"\.CreateDatabase\s*\(|\.CreateContainer\s*\(",
}


class TestCacheMetadata:
    """Rule sdk-cache-metadata: createDatabaseIfNotExists /
    createContainerIfNotExists are startup-only. Each should appear
    at most once in the entire source — never per-request."""

    def test_provision_only_once(self, sdk, source_text):
        pat = _PROVISION_PATTERNS.get(sdk)
        if not pat:
            pytest.skip(f"No provision pattern registered for {sdk}")
        hits = re.findall(pat, source_text)
        # We allow up to 2 hits to accommodate one CreateDatabase + one
        # CreateContainer call. >2 means the agent is almost certainly
        # re-provisioning per request.
        assert len(hits) <= 2, (
            f"Found {len(hits)} calls to create*IfNotExists in source. "
            "Rule sdk-cache-metadata: provision the database and container exactly "
            "once at startup (FastAPI lifespan / Spring @PostConstruct / .NET startup "
            "/ Node top-level await / Go init) and cache the handle. Re-calling "
            "createIfNotExists per request consumes from the system-reserved RU "
            "budget on every call and adds gateway latency."
        )
