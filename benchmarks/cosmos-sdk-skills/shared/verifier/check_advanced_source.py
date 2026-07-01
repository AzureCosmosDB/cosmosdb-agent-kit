"""Advanced source-code best-practice checks.

These extend check_source.py with rules that are harder to verify via API
behavior alone. Like the other verifier suites, they scan comment-stripped
source via the shared `source_text` fixture and gate SDK-specific checks with
`_need(...)`.
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


_CREATE_PATTERNS = {
    "python": r"\bcreate_item\s*\(",
    "dotnet": r"\bCreateItem\w*Async\s*\(",
    "java": r"\bcreateItem\s*\(",
    "nodejs": r"\.items?\.create\s*\(",
    "go": r"\bCreateItem\w*\s*\(",
}

_CONDITIONAL_CREATE_PATTERNS = {
    "python": (
        r"if_none_match(?:_etag)?\s*=\s*['\"]\*['\"]|"
        r"MatchConditions\.IfMissing|"
        r"etag\s*=\s*['\"]\*['\"][^\n\r)]{0,160}match_condition\s*=\s*MatchConditions\.IfMissing"
    ),
    "dotnet": r"IfNoneMatchEtag\s*[:=]\s*['\"]\*['\"]",
    "java": r"setIfNoneMatchETag\s*\(\s*['\"]\*['\"]\s*\)",
    "nodejs": (
        r"IfNoneMatch|ifNoneMatch|ifNoneMatchEtag|"
        r"accessCondition\s*[:=]\s*\{[^}]*type\s*:\s*['\"]IfNoneMatch['\"][^}]*condition\s*:\s*['\"]\*['\"]"
    ),
    "go": r"IfNoneMatch|IfNoneMatchEtag|WithIfNoneMatch",
}

_UPDATE_PATTERNS = {
    "python": r"\b(?:replace_item|upsert_item|patch_item)\s*\(",
    "dotnet": r"\b(?:ReplaceItem|UpsertItem|PatchItem)\w*Async\s*\(",
    "java": r"\b(?:replaceItem|upsertItem|patchItem)\s*\(",
    "nodejs": r"\b(?:replace|upsert|patch)\s*\(",
    "go": r"\b(?:ReplaceItem|UpsertItem|PatchItem)\w*\s*\(",
}

_ETAG_PATTERNS = {
    "python": r"_etag|MatchConditions\.IfNotModified|if_match|etag\s*=",
    "dotnet": r"IfMatchEtag|\.ETag\b|ETag\s*=",
    "java": r"setIfMatchETag\s*\(|getETag\s*\(",
    "nodejs": r"_etag|IfMatch|ifMatch|ifMatchEtag|accessCondition",
    "go": r"etag|if_match|IfMatch|IfMatchEtag|with_if_match",
}

_COUNTER_PATTERNS = {
    "python": r"\+=\s*\d+|-=\s*\d+|=\s*\w+(?:\[['\"][^\]]+['\"]\])?\s*[+-]\s*\d+|\bincrement\b|\bcounter\b",
    "dotnet": r"\+\+|--|\+=\s*\d+|-=\s*\d+|=\s*[\w\.]+\s*[+-]\s*\d+|\bIncrement\b|\bcounter\b",
    "java": r"\+\+|--|\+=\s*\d+|-=\s*\d+|=\s*[\w\.()]+\s*[+-]\s*\d+|\.increment\s*\(|\bcounter\b",
    "nodejs": r'\+\+|--|\+=\s*\d+|-=\s*\d+|=\s*[\w\.\[\]"\']+\s*[+-]\s*\d+|\bincr\b|\bincrement\b|\bcounter\b',
    "go": r"\+\+|--|\+=\s*\d+|-=\s*\d+|=\s*[\w\.]+\s*[+-]\s*\d+|\bIncrement\b|\bcounter\b",
}

_PATCH_PATTERNS = {
    "python": r"\bpatch_item\s*\(|['\"]op['\"]\s*:\s*['\"]incr['\"]|\boperations\s*=\s*\[",
    "dotnet": r"\bPatchItem\w*Async\s*\(|PatchOperation\.Increment\s*\(",
    "java": r"\bpatchItem\s*\(|CosmosPatchOperations|\.increment\s*\(",
    "nodejs": r"\.patch\s*\(|['\"]op['\"]\s*:\s*['\"]incr['\"]",
    "go": r"\bPatchItem\w*\s*\(|\bPatchOperations\b|\bIncrement\b",
}


# ---------------------------------------------------------------------
# Async API usage
# ---------------------------------------------------------------------

class TestAsyncApi:
    def test_python_uses_async_cosmos_client_and_handlers(self, sdk, source_text):
        _need(sdk, "python")
        assert "azure.cosmos.aio" in source_text, (
            "Rule sdk-async-api: Python FastAPI handlers should use the async Cosmos SDK "
            "(`from azure.cosmos.aio import CosmosClient`) instead of the synchronous client."
        )
        assert re.search(r"\basync\s+def\b", source_text), (
            "Rule sdk-async-api: FastAPI route and service handlers should be declared with "
            "`async def` so Cosmos operations can be awaited without blocking the server."
        )
        assert re.search(r"\bawait\b", source_text), (
            "Rule sdk-async-api: async Cosmos code should `await` SDK operations rather than "
            "calling them synchronously."
        )

    def test_dotnet_uses_async_without_blocking(self, sdk, source_text):
        _need(sdk, "dotnet")
        assert re.search(r"\bawait\b", source_text) and re.search(r"\w+Async\s*\(", source_text), (
            "Rule sdk-async-api: .NET Cosmos operations should use async/await all the way "
            "up the call stack (`await container.ReadItemAsync(...)`, etc.)."
        )
        assert not re.search(r"\.Result\b|\.Wait\s*\(|\.GetAwaiter\s*\(\s*\)\.GetResult\s*\(", source_text), (
            "Rule sdk-async-api: do not block on Cosmos async calls with `.Result`, `.Wait()`, "
            "or `.GetAwaiter().GetResult()`; these patterns exhaust threads and can deadlock."
        )

    def test_java_uses_async_without_blocking(self, sdk, source_text):
        _need(sdk, "java")
        assert re.search(r"CosmosAsyncClient|buildAsyncClient\s*\(", source_text), (
            "Rule sdk-async-api: Java should use the reactive async SDK (`CosmosAsyncClient` / "
            "`buildAsyncClient()`) for Cosmos operations."
        )
        assert not re.search(r"\.block\s*\(", source_text), (
            "Rule sdk-async-api: do not call `.block()` on Cosmos reactive operations; compose "
            "the returned Mono/Flux instead so request threads are not blocked."
        )


# ---------------------------------------------------------------------
# Availability strategy / hedging (.NET)
# ---------------------------------------------------------------------

class TestAvailabilityStrategyDotnet:
    def test_configures_availability_strategy(self, sdk, source_text):
        _need(sdk, "dotnet")
        assert re.search(
            r"AvailabilityStrategy\b|WithAvailabilityStrategy\s*\(|"
            r"ThresholdBasedAvailabilityStrategy\b|"
            r"CrossRegion(?:Parallel)?HedgingAvailabilityStrategy\b|"
            r"CrossRegionHedgingStrategy\s*\(",
            source_text,
        ), (
            "Rule sdk-availability-strategy: configure Cosmos hedging / availability strategy "
            "in .NET via `AvailabilityStrategy`, `WithAvailabilityStrategy(...)`, or a "
            "threshold-based / cross-region hedging strategy."
        )


# ---------------------------------------------------------------------
# Partition-level circuit breaker (.NET)
# ---------------------------------------------------------------------

class TestCircuitBreakerDotnet:
    def test_configures_partition_level_circuit_breaker(self, sdk, source_text):
        _need(sdk, "dotnet")
        assert re.search(
            r"PartitionLevelCircuitBreakerOptions\b|"
            r"EnablePartitionLevelCircuitBreaker\b|"
            r"AZURE_COSMOS_CIRCUIT_BREAKER_ENABLED|"
            r"AZURE_COSMOS_PPCB_",
            source_text,
        ), (
            "Rule sdk-circuit-breaker: enable the .NET partition-level circuit breaker with "
            "`PartitionLevelCircuitBreakerOptions`, `EnablePartitionLevelCircuitBreaker`, or "
            "the documented PPCB environment variables before creating the client."
        )


# ---------------------------------------------------------------------
# Conditional creates with If-None-Match
# ---------------------------------------------------------------------

class TestConditionalCreateEtag:
    def test_uses_conditional_create_etag(self, sdk, source_text):
        create_pat = _CREATE_PATTERNS.get(sdk)
        cond_pat = _CONDITIONAL_CREATE_PATTERNS.get(sdk)
        if not create_pat or not cond_pat:
            pytest.skip(f"No conditional-create pattern registered for {sdk}")
        assert re.search(create_pat, source_text), (
            f"No create operation detected for {sdk}. Rule sdk-conditional-create-etag expects "
            "create-style writes so duplicates can be prevented atomically with If-None-Match."
        )
        assert re.search(cond_pat, source_text, re.IGNORECASE | re.DOTALL), (
            "Rule sdk-conditional-create-etag: create operations that must be unique should use "
            "If-None-Match semantics (for example `IfNoneMatchEtag = \"*\"`, "
            "`setIfNoneMatchETag(\"*\")`, or the SDK-equivalent conditional create options) "
            "to reject duplicates without a prior read."
        )


# ---------------------------------------------------------------------
# Optimistic concurrency with ETags
# ---------------------------------------------------------------------

class TestEtagConcurrency:
    def test_uses_etag_for_update_replace_paths(self, sdk, source_text):
        update_pat = _UPDATE_PATTERNS.get(sdk)
        etag_pat = _ETAG_PATTERNS.get(sdk)
        if not update_pat or not etag_pat:
            pytest.skip(f"No ETag-concurrency pattern registered for {sdk}")
        if not re.search(update_pat, source_text):
            pytest.skip("No update/replace/upsert/patch operations detected; optimistic concurrency check is not applicable.")
        assert re.search(etag_pat, source_text, re.IGNORECASE | re.DOTALL), (
            "Rule sdk-etag-concurrency: update, replace, or read-modify-write paths should use "
            "ETag-based optimistic concurrency (`IfMatchEtag`, `setIfMatchETag(...)`, "
            "`MatchConditions.IfNotModified`, or the SDK-equivalent If-Match option) to "
            "prevent lost updates."
        )


# ---------------------------------------------------------------------
# Excluded regions (.NET)
# ---------------------------------------------------------------------

class TestExcludedRegionsDotnet:
    def test_configures_excluded_regions(self, sdk, source_text):
        _need(sdk, "dotnet")
        assert re.search(r"ExcludedRegions\b|ExcludeRegions\b", source_text), (
            "Rule sdk-excluded-regions: .NET code should expose request-level or client-level "
            "excluded-region routing (`ExcludeRegions` / `ExcludedRegions`) so traffic can be "
            "steered away from unhealthy regions without a redeploy."
        )


# ---------------------------------------------------------------------
# Patch API for counter increments
# ---------------------------------------------------------------------

class TestPatchCounterIncrement:
    def test_uses_patch_for_counter_increments(self, sdk, source_text):
        counter_pat = _COUNTER_PATTERNS.get(sdk)
        patch_pat = _PATCH_PATTERNS.get(sdk)
        if not counter_pat or not patch_pat:
            pytest.skip(f"No patch-counter pattern registered for {sdk}")
        if not re.search(counter_pat, source_text, re.IGNORECASE | re.DOTALL):
            pytest.skip("No counter-style increment/decrement logic detected; Patch increment check is not applicable.")
        assert re.search(patch_pat, source_text, re.IGNORECASE | re.DOTALL), (
            "Rule sdk-patch-counter-increment: when incrementing counters or totals, prefer the "
            "Cosmos Patch API (`PatchOperation.Increment`, `CosmosPatchOperations.increment`, "
            "`patch_item`, or the SDK-equivalent patch/incr operation) instead of read-modify-write updates."
        )


# ---------------------------------------------------------------------
# Python async dependency hygiene
# ---------------------------------------------------------------------

class TestPythonAsyncDeps:
    def test_python_async_sdk_declares_aiohttp(self, sdk, source_text):
        _need(sdk, "python")
        if "azure.cosmos.aio" not in source_text:
            pytest.skip("Async Cosmos SDK not detected; aiohttp dependency rule is not applicable.")
        assert re.search(r"\baiohttp\b", source_text), (
            "Rule sdk-python-async-deps: when using `azure.cosmos.aio`, declare `aiohttp` in "
            "requirements.txt or pyproject.toml so the async transport is available at runtime."
        )


# ---------------------------------------------------------------------
# Enum serialization consistency (.NET)
# ---------------------------------------------------------------------

class TestSerializationEnumsDotnet:
    def test_dotnet_configures_string_enum_serialization(self, sdk, source_text):
        _need(sdk, "dotnet")
        if not re.search(r"\benum\s+\w+", source_text):
            pytest.skip("No enum declarations detected; enum-serialization check is not applicable.")
        assert re.search(r"JsonStringEnumConverter\b|StringEnumConverter\b", source_text), (
            "Rule sdk-serialization-enums: .NET applications with enums should configure string "
            "enum serialization (for example `JsonStringEnumConverter` or `StringEnumConverter`) "
            "so Cosmos documents and application queries use the same representation."
        )


# ---------------------------------------------------------------------
# Java request options must not be shared across createItem calls
# ---------------------------------------------------------------------

class TestRequestOptionsPerCallJava:
    def test_java_does_not_share_request_options_across_create_calls(self, sdk, source_text):
        _need(sdk, "java")
        create_calls = _find(source_text, r"\bcreateItem\s*\(", re.IGNORECASE)
        if len(create_calls) < 2:
            pytest.skip("Fewer than two createItem calls detected; shared-request-options check is not applicable.")

        option_vars = set(_find(
            source_text,
            r"\bCosmosItemRequestOptions\s+(\w+)\s*=\s*new\s+CosmosItemRequestOptions\b",
            re.IGNORECASE,
        ))
        shared: list[str] = []
        for var in option_vars:
            uses = _find(
                source_text,
                rf"\bcreateItem\s*\([^;{{}}]{{0,400}}\b{re.escape(var)}\b",
                re.IGNORECASE | re.DOTALL,
            )
            if len(uses) > 1:
                shared.append(f"{var} ({len(uses)} createItem calls)")

        assert not shared, (
            "Rule sdk-request-options-per-call: do not reuse one mutable `CosmosItemRequestOptions` "
            "instance across multiple `createItem` calls. Each create should get a fresh options "
            "object (inline or per-request). Reused option variables detected: "
            f"{', '.join(shared)}"
        )
