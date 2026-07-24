"""Source anti-pattern checks.

These are negative / anti-pattern checks on the submitted source. They
are deliberately separated from check_source.py so the failure log makes
the category clear.
"""
from __future__ import annotations

import re

import pytest

# The well-known emulator key is the only literal key string we allow
# in source. Any other key-shaped base64 string is a hardcoded
# credential and fails.
EMULATOR_KEY = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="


def _need(sdk: str, *want: str):
    if sdk not in want:
        pytest.skip(f"Not applicable to {sdk}")


class TestNoHardcodedKey:
    # Lock files and SBOM-style manifests contain legitimate base64
    # integrity hashes (e.g. npm package-lock.json's "integrity": "sha512-...")
    # that match the cosmos-key shape. Skip those when looking for
    # hardcoded credentials.
    _LOCK_FILE_NAMES = {
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
        "poetry.lock", "Pipfile.lock", "go.sum",
        "Gemfile.lock", "Cargo.lock", "composer.lock",
    }

    def test_no_real_account_key_literal(self, sdk, source_files):
        # The shape of a Cosmos account key: 88-char base64 ending in '=='.
        # The emulator key is the only allowed literal. Scan code-only files;
        # lock files / SBOMs have legitimate integrity hashes.
        from pathlib import Path
        for p in source_files:
            if Path(p).name in self._LOCK_FILE_NAMES:
                continue
            try:
                text = Path(p).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for c in re.findall(r"[A-Za-z0-9+/]{86}==", text):
                assert c == EMULATOR_KEY, (
                    f"Found a hardcoded Cosmos account-key-shaped literal in {p}: "
                    f"{c[:20]}...{c[-8:]}. Rule sdk-secrets-from-env: load the "
                    f"key from an environment variable or a secret store, never "
                    f"from source."
                )

    def test_endpoint_read_from_env(self, sdk, source_text):
        # The agent's source must reference COSMOS_ENDPOINT (or a related
        # configuration mechanism). Hardcoded https://localhost:8081 in
        # a non-test file is the failure mode.
        patterns_env = [
            r"COSMOS_ENDPOINT",
            r"COSMOS_URI",
            r"COSMOSDB_ENDPOINT",
            r"AZURE_COSMOS_ENDPOINT",
            r"CosmosDb:Endpoint",
            r'"Cosmos":\s*\{',
        ]
        assert any(re.search(p, source_text, re.IGNORECASE) for p in patterns_env), (
            "Source does not appear to read the Cosmos endpoint from configuration. "
            "Rule sdk-secrets-from-env: load endpoint + key from env or appsettings."
        )


class TestPythonForbiddenConnectionPolicy:
    def test_no_legacy_connection_policy_mutation(self, sdk, source_text):
        _need(sdk, "python")
        # ConnectionPolicy mutation (e.g., policy.RequestTimeout = ...) is
        # the legacy pydocumentdb style. azure-cosmos doesn't expose
        # ConnectionPolicy as a mutable object the same way.
        assert not re.search(r"ConnectionPolicy\s*\(\s*\)\s*\n", source_text), (
            "Detected legacy `ConnectionPolicy()` mutation pattern (pydocumentdb-era). "
            "azure-cosmos passes settings as constructor kwargs or via "
            "ConnectionConfig — do not mutate a ConnectionPolicy instance."
        )


class TestDotnetForbiddenPackage:
    def test_no_azure_cosmos_preview_package(self, sdk, source_text):
        _need(sdk, "dotnet")
        # Already asserted in check_source as well; second occurrence here
        # makes the failure clearly attributable to the skills category.
        assert not re.search(r'"Azure\.Cosmos"', source_text), (
            "PackageReference Include=\"Azure.Cosmos\" found. Rule sdk-dotnet-cosmos-package-id: "
            "that is the abandoned preview package. Use Microsoft.Azure.Cosmos."
        )


# ---------------------------------------------------------------------
# Python: async client required inside async web frameworks
# ---------------------------------------------------------------------

class TestPythonAsyncClient:
    """Rule sdk-python-async-deps: keep async Cosmos usage consistent.
    These checks are gated on the async Cosmos client (azure.cosmos.aio)
    actually being used -- an app that pairs an async web framework with
    the sync client and plain `def` handlers is acceptable (the handlers
    run in a threadpool), so framework presence alone is never flagged.
    When the aio client is used, at least one route handler must be
    `async def`, and `aiohttp` must be pinned as a dependency."""

    def test_at_least_one_async_handler(self, sdk, source_text):
        _need(sdk, "python")
        if "azure.cosmos.aio" not in source_text:
            pytest.skip("Async Cosmos client not in use; sync client with `def` handlers is acceptable.")
        assert re.search(r"async\s+def\s+\w+\s*\(", source_text), (
            "The async Cosmos client (azure.cosmos.aio) is in use but no `async def` "
            "handler was found. Every handler that awaits a Cosmos call must be "
            "`async def`; calling the aio client from plain `def` handlers means the "
            "coroutines are never awaited on the event loop. Rule sdk-python-async-deps."
        )

    def test_aiohttp_dependency_pinned(self, sdk, source_text):
        _need(sdk, "python")
        if "azure.cosmos.aio" not in source_text:
            pytest.skip("Sync client in use; aiohttp not required.")
        assert "aiohttp" in source_text, (
            "Using azure.cosmos.aio but no aiohttp dependency declared. "
            "`azure-cosmos` does NOT install aiohttp automatically — add `aiohttp` "
            "to requirements.txt / pyproject.toml. Rule sdk-python-async-deps."
        )


# ---------------------------------------------------------------------
# .NET / Java: no sync-over-async blocking calls
# ---------------------------------------------------------------------

class TestNoBlockingInAsync:
    """Rule sdk-async-api: do not block on async Cosmos calls with
    .Result / .Wait() / .GetAwaiter().GetResult() (.NET) or .block()
    (Java reactive). Async-over-sync blocking causes thread-pool
    exhaustion and, in ASP.NET, deadlocks."""

    def test_dotnet_no_result_or_wait(self, sdk, source_text):
        _need(sdk, "dotnet")
        offenders = []
        # .Result on a Task return from a Cosmos call.
        for m in re.finditer(r"\b(?:Read|Create|Upsert|Replace|Delete|Query|Execute|Patch)Item\w*Async\s*\([^;{}]{0,400}\)\s*\.\s*(?:Result|GetAwaiter\s*\(\s*\)\s*\.\s*GetResult\s*\(\s*\))",
                             source_text, re.DOTALL):
            offenders.append(m.group(0)[:120] + "...")
        # .Wait() chained off a Cosmos call.
        for m in re.finditer(r"\b(?:Read|Create|Upsert|Replace|Delete|Query|Execute|Patch)Item\w*Async\s*\([^;{}]{0,400}\)\s*\.\s*Wait\s*\(\s*\)",
                             source_text, re.DOTALL):
            offenders.append(m.group(0)[:120] + "...")
        assert not offenders, (
            "Found sync-over-async blocking on Cosmos calls:\n  - " +
            "\n  - ".join(offenders) + "\n\n"
            "Rule sdk-async-api: await the call (and propagate async up the stack). "
            "`.Result` / `.Wait()` / `.GetAwaiter().GetResult()` cause thread-pool "
            "exhaustion under load and can deadlock in ASP.NET."
        )

    def test_java_no_bare_block(self, sdk, source_text):
        _need(sdk, "java")
        # `.block()` with no qualifier — anti-pattern when using
        # CosmosAsyncClient inside a reactive pipeline. The sync wrapper
        # CosmosClient is itself implemented in terms of .block(), so
        # user code calling .block() directly on an async result is the
        # specific anti-pattern. We look for `.block()` only in source
        # where CosmosAsyncClient appears.
        if "CosmosAsyncClient" not in source_text and "Mono<" not in source_text and "Flux<" not in source_text:
            pytest.skip("No async/reactive Cosmos usage; .block() check not applicable.")
        bare_blocks = re.findall(r"\.\s*block\s*\(\s*\)", source_text)
        assert not bare_blocks, (
            f"Found {len(bare_blocks)} call(s) to `.block()` in a reactive code path. "
            "Rule sdk-async-api: do not collapse Mono/Flux back to blocking. Stay in "
            "the reactive pipeline (use Spring WebFlux) or use the sync `CosmosClient` "
            "wrapper, which internally manages the blocking boundary correctly."
        )
