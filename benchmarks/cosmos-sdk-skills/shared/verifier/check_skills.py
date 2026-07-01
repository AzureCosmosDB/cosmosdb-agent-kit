"""Skills-compliance checks.

These are the negative / anti-pattern checks plus the missing-guidance
transparency rubric for the Go SDK. They are deliberately separated
from check_source.py so the failure log makes the category clear.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache

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

# Frameworks whose presence implies an asyncio event loop is running.
_PY_ASYNC_FRAMEWORKS = [
    "fastapi", "FastAPI",
    "from quart", "import quart",
    "from sanic", "import sanic",
    "starlette.applications",
    "azure.functions.AsyncApp",
    "langgraph.",
]


class TestPythonAsyncClient:
    """Rule sdk-python-async-deps: don't run the sync Cosmos client
    inside an asyncio event loop. If the source imports an async web
    framework, the Cosmos client must come from azure.cosmos.aio and
    at least one route handler must be `async def`."""

    def test_async_client_when_async_framework_present(self, sdk, source_text):
        _need(sdk, "python")
        is_async_app = any(marker in source_text for marker in _PY_ASYNC_FRAMEWORKS)
        if not is_async_app:
            pytest.skip("No async web framework detected; sync client is acceptable.")
        assert "azure.cosmos.aio" in source_text, (
            "Detected an async web framework (FastAPI / Quart / Sanic / Starlette / "
            "Azure Functions async / LangGraph) but the Cosmos client is the sync "
            "`azure.cosmos.CosmosClient`. Rule sdk-python-async-deps: switch to "
            "`from azure.cosmos.aio import CosmosClient` (and pin `aiohttp` in "
            "requirements.txt). The sync client blocks the event loop and can deadlock."
        )

    def test_at_least_one_async_handler(self, sdk, source_text):
        _need(sdk, "python")
        is_async_app = any(marker in source_text for marker in _PY_ASYNC_FRAMEWORKS)
        if not is_async_app:
            pytest.skip("No async web framework detected.")
        assert re.search(r"async\s+def\s+\w+\s*\(", source_text), (
            "No `async def` handler found. With the async Cosmos client, every "
            "handler that touches Cosmos must be `async def` and `await` the call. "
            "Plain `def` handlers force FastAPI to run them in a threadpool, which "
            "negates the point of the async client."
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


# ---------------------------------------------------------------------
# Node.js missing-canonical-guidance transparency rubric
# ---------------------------------------------------------------------
# Microsoft Learn has no `best-practice-nodejs` page; the canonical
# guidance is the GitHub README and quickstart. We apply the same
# transparency rubric as Go (no fabricated certainty; document what
# you borrowed) but only when the agent claims a Node.js-specific
# best practice. The check is intentionally weaker than Go's — Node
# at least has SDK-level docs — so we only fail on fabricated phrasing.

NODEJS_FABRICATED_PHRASES = [
    "official node.js sdk best practice",
    "@azure/cosmos best practice",
    "node cosmos sdk recommends",
    "microsoft recommends for the node sdk",
]


class TestNodejsNoOverstatedCertainty:
    def test_nodejs_no_fabricated_certainty(self, sdk, docs_text, source_text_with_comments):
        _need(sdk, "nodejs")
        haystack = _normalize(docs_text + "\n" + source_text_with_comments)
        offenders = [p for p in NODEJS_FABRICATED_PHRASES if p in haystack]
        if offenders:
            transparent = any(p in haystack for p in TRANSPARENCY_PHRASES)
            assert transparent, (
                "Found phrases that imply official Node.js-specific Cosmos best-practice "
                "guidance without any transparency marker. "
                f"Offenders: {offenders}. Microsoft Learn does not publish a "
                "best-practice-nodejs page; SDK-level guidance comes from the GitHub "
                "README and quickstart. Don't claim 'official' recommendations that "
                "don't exist."
            )


# ---------------------------------------------------------------------
# Go missing-guidance transparency rubric
# ---------------------------------------------------------------------

# Phrases that satisfy the transparency requirement. Matched
# case-insensitively against the README + comments + docs.
TRANSPARENCY_PHRASES = [
    "borrowed from",
    "adapted from",
    "inferred from",
    "based on the .net",
    "based on the dotnet",
    "based on the java",
    "based on the python",
    "based on the node",
    "no sdk-specific guidance",
    "no go-specific",
    "no local guidance",
    "asked for clarification",
    "needs clarification",
    "general retry guidance",
    "general resilience guidance",
    "cross-sdk guidance",
]

# Phrases that — if present without a transparency marker — represent
# fabricated certainty (claiming official guidance that doesn't exist).
FABRICATED_PHRASES = [
    "official go sdk best practice",
    "azure-sdk-for-go best practice",
    "azcosmos best practice",
    "go cosmos sdk recommends",
    "microsoft recommends for the go sdk",
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


class TestGoMissingGuidanceTransparency:
    def test_go_iteration_documents_borrowed_or_asked(self, sdk, docs_text, source_text_with_comments):
        _need(sdk, "go")
        haystack = _normalize(docs_text + "\n" + source_text_with_comments)
        hits = [p for p in TRANSPARENCY_PHRASES if p in haystack]
        assert hits, (
            "Go transparency rubric failed.\n\n"
            "The local Cosmos best-practices skill set contains no SDK-specific guidance "
            "for the Go SDK (preferred regions, retries, diagnostics, Direct mode all lack "
            "Go entries). The agent therefore must either ask for clarification or "
            "explicitly state that it borrowed guidance from another SDK / general "
            "guidance, and name the source.\n\n"
            f"Expected at least one of:\n  - " + "\n  - ".join(TRANSPARENCY_PHRASES) +
            "\n\nNone of these phrases were found in the README, markdown docs, or Go "
            "source comments. Silent guessing is not acceptable for this benchmark."
        )


class TestNoOverstatedCertainty:
    def test_go_no_fabricated_certainty(self, sdk, docs_text, source_text_with_comments):
        _need(sdk, "go")
        haystack = _normalize(docs_text + "\n" + source_text_with_comments)
        offenders = [p for p in FABRICATED_PHRASES if p in haystack]
        # Fabricated phrasing is only OK if paired with a transparency marker.
        if offenders:
            transparent = any(p in haystack for p in TRANSPARENCY_PHRASES)
            assert transparent, (
                "Found phrases that imply official Go-specific Cosmos guidance without any "
                f"transparency marker. Offenders: {offenders}. The benchmark penalises "
                "fabricated certainty — there is no official Go-specific best-practice "
                "guidance for the topics covered by this skill set."
            )


# ---------------------------------------------------------------------
# skills_read gate — did the agent actually READ the skill files?
# ---------------------------------------------------------------------
# The compliance checks above prove the agent's *output* follows best
# practices, but they cannot prove the agent *consulted* the bundled
# Cosmos best-practices skill (a strong model might already "know" the
# answer). The CES/live runner installs a custom agent whose routing
# table instructs the model to `Read <SKILL_BASE>/SKILL.md` first and
# then the relevant `<SKILL_BASE>/rules/*.md` files, and it captures the
# agent's full session transcript as JSONL at
# `$VERIFIER_LOG_DIR/copilot-session.jsonl`.
#
# These checks parse that transcript and assert the agent issued tool
# calls that open the skill index and at least one rule file. This is
# the explicit "skills_read" signal: it fails if the agent solved the
# task without ever opening the skill. It is SDK-agnostic (no SDK token
# in the test names) so it runs for every SDK instance.

SKILL_DIR_MARKER = "cosmosdb-best-practices"
_TRANSCRIPT_NAME = "copilot-session.jsonl"


def _transcript_path() -> str:
    log_dir = os.environ.get("VERIFIER_LOG_DIR", "/logs/verifier")
    return os.path.join(log_dir, _TRANSCRIPT_NAME)


@lru_cache(maxsize=8)
def _load_transcript_events(path: str):
    """Parse a Copilot session transcript into a list of event dicts.

    The runner writes one JSON event per line (JSONL). We fall back to a
    single whole-file JSON parse if the file is not line-delimited.
    Returns [] when the file is missing, empty, or unparseable.
    """
    if not path or not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            raw = fh.read()
    except OSError:
        return []
    if not raw.strip():
        return []
    events = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except Exception:
            continue
    if not events:
        try:
            obj = json.loads(raw)
            if isinstance(obj, list):
                events = [e for e in obj if isinstance(e, dict)]
            elif isinstance(obj, dict):
                events = [obj]
        except Exception:
            return []
    return events


def _tool_call_arg_strings(events):
    """Return a JSON string of the arguments for every tool-invocation
    event — the agent's intent to open a path or run a command. We look
    at `tool.execution_start` (the call itself), which is the strongest,
    lowest-false-positive signal that the agent chose to open a file."""
    out = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        if ev.get("type") != "tool.execution_start":
            continue
        data = ev.get("data") or {}
        args = data.get("arguments")
        if args is None:
            continue
        try:
            out.append(json.dumps(args))
        except Exception:
            out.append(str(args))
    return out


class TestAgentReadSkills:
    """skills_read gate: verify the agent consulted the bundled Cosmos
    best-practices skill, not merely that its output looks compliant."""

    def test_session_transcript_captured(self):
        path = _transcript_path()
        events = _load_transcript_events(path)
        assert events, (
            f"No agent session transcript was found/parsed at {path}. The CES "
            "runner writes the JSONL transcript here after the agent finishes; "
            "without it the skills_read gate cannot verify the agent read the "
            "skill files. If you see this in a real run, the transcript was not "
            "captured (an infrastructure problem, not an agent failure)."
        )

    def test_agent_read_skill_index(self):
        path = _transcript_path()
        events = _load_transcript_events(path)
        if not events:
            pytest.fail(
                f"No transcript at {path}; cannot verify the agent read the "
                "skill index (SKILL.md)."
            )
        arg_strings = _tool_call_arg_strings(events)
        opened_index = any(
            SKILL_DIR_MARKER in a and re.search(r"(?:SKILL|AGENTS)\.md", a)
            for a in arg_strings
        )
        assert opened_index, (
            "skills_read gate failed: the agent never opened the skill index. "
            f"Expected a tool call that reads <skill>/SKILL.md (or AGENTS.md) "
            f"under '{SKILL_DIR_MARKER}'. The custom agent's routing table tells "
            "the model to read SKILL.md first to choose relevant rule files; the "
            "transcript shows it did not, so it did not consult the skill."
        )

    def test_agent_read_at_least_one_rule(self):
        path = _transcript_path()
        events = _load_transcript_events(path)
        if not events:
            pytest.fail(
                f"No transcript at {path}; cannot verify the agent read a rule "
                "file (rules/*.md)."
            )
        arg_strings = _tool_call_arg_strings(events)
        rule_files = set()
        for a in arg_strings:
            if SKILL_DIR_MARKER not in a:
                continue
            for m in re.finditer(r"rules/([A-Za-z0-9._-]+\.md)", a):
                rule_files.add(m.group(1))
        assert rule_files, (
            "skills_read gate failed: the agent opened no rule file under the "
            f"skill's rules/ directory. Expected at least one tool call reading "
            f"<skill>/rules/*.md under '{SKILL_DIR_MARKER}'. Reading (or merely "
            "listing) SKILL.md is not enough — the concrete, SDK-specific "
            "guidance lives in the rule files, so the agent must open one."
        )
