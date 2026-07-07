"""Shared pytest fixtures for the cosmos-sdk-skills verifier.

The verifier is **contract-driven**. Each task image bakes a scenario
contract (shared/contracts/<scenario>.json, copied to
/verifier/contracts/) and selects it with the SCENARIO env var. The
contract declares, per scenario:

  * the Cosmos database + container env vars and their defaults,
  * the "root" entities (aggregate roots reachable via create/get/list),
    their deterministic seed data, field shapes, partition-key rules and
    modelling / indexing / throughput expectations, and
  * the "child" entities (sub-resources such as tickets or readings) and
    the scenario-specific endpoints that operate on them.

The generic engine (check_api / check_behavior / check_cosmos) drives the
root entities from the contract. Scenario-specific behaviour (ticket
buy/cancel/ETag, iot reading ingest / time-range / summary) lives in each
task's /tests/checks.py, which reads the same contract via the fixtures
and helpers exported here.

Everything is read from environment variables the base image and the
per-task test.sh set up:

    SCENARIO              -- mosaic | ticketing | iot (selects the contract)
    SDK                   -- one of python, dotnet, java, nodejs, go
    APP_PORT              -- port the agent's app should be listening on
    APP_WORKDIR           -- where the agent put its source code (/app)
    COSMOS_ENDPOINT       -- http(s)://localhost:8081
    COSMOS_KEY            -- well-known emulator key
    COSMOS_DATABASE       -- scenario database (mosaic | ticketwave | sensorgrid)
    COSMOS_*_CONTAINER    -- per-entity container names
    VERIFIER_LOG_DIR      -- where per-check logs land

The verifier does not own any test data — the seed data lives in the
contract and the checks insert it through the agent's own API.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Iterable

import pytest
import requests
import urllib3
from azure.cosmos import CosmosClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SDK_ALIASES = {
    "py": "python",
    "python": "python",
    "dotnet": "dotnet",
    ".net": "dotnet",
    "csharp": "dotnet",
    "java": "java",
    "node": "nodejs",
    "nodejs": "nodejs",
    "javascript": "nodejs",
    "js": "nodejs",
    "go": "go",
    "golang": "go",
}

# ---------------------------------------------------------------------
# Contract loading (module level so check_*.py can parametrize on it).
# ---------------------------------------------------------------------

CONTRACTS_DIR = Path(os.environ.get("CONTRACTS_DIR", "/verifier/contracts"))


def load_contract() -> dict:
    """Load the active scenario contract selected by the SCENARIO env var.

    Falls back to 'mosaic' so a bare invocation still works. Raises with a
    clear message if the contract file is missing so a mis-wired task
    image fails loudly instead of silently grading nothing.
    """
    scenario = os.environ.get("SCENARIO", "mosaic").strip().lower()
    path = CONTRACTS_DIR / f"{scenario}.json"
    if not path.exists():
        raise RuntimeError(
            f"Contract for scenario {scenario!r} not found at {path}. "
            f"The task image must bake shared/contracts/{scenario}.json into "
            f"{CONTRACTS_DIR} and set SCENARIO={scenario}."
        )
    return json.loads(path.read_text(encoding="utf-8"))


# Loaded once at import. check_*.py parametrize their tests over
# CONTRACT["roots"] / CONTRACT["children"].
CONTRACT = load_contract()
ROOTS = CONTRACT.get("roots", [])
CHILDREN = CONTRACT.get("children", [])


def root_ids(root: dict) -> str:
    return root["name"]


# ---------------------------------------------------------------------
# Cosmos helpers (importable by scenario checks.py)
# ---------------------------------------------------------------------

def container_name(entity: dict) -> str:
    """Resolve an entity's container name from its declared env var,
    falling back to the contract default."""
    return os.environ.get(entity["container_env"], entity["container_default"])


def get_container(database, entity: dict):
    """Container client for a declared entity (root or child)."""
    return database.get_container_client(container_name(entity))


def partition_key_field(container) -> str:
    """The container's partition-key field name (leading '/' stripped)."""
    paths = container.read().get("partitionKey", {}).get("paths", [])
    return paths[0].lstrip("/") if paths else ""


def emulator_docs_for_id(container, doc_id: str) -> list[dict]:
    """Fetch every persisted document with this id straight from the
    emulator using the verifier's OWN Cosmos client — never the agent's
    API. Partition-key-agnostic (cross-partition query by id), so it works
    regardless of which pk path the agent chose. Returns [] when nothing
    was persisted (the signal that the app used an in-memory / SQLite
    store that never touched Cosmos)."""
    return list(container.query_items(
        query="SELECT * FROM c WHERE c.id = @id",
        parameters=[{"name": "@id", "value": doc_id}],
        enable_cross_partition_query=True,
    ))


def fmt_path(template: str, **kw) -> str:
    out = template
    for k, v in kw.items():
        out = out.replace("{" + k + "}", str(v))
    return out


# ---------------------------------------------------------------------
# SDK detection + cross-SDK deselection
# ---------------------------------------------------------------------

def _norm_sdk(raw: str) -> str:
    return SDK_ALIASES.get(raw.strip().lower(), raw.strip().lower())


# Test-name tokens that mark a test as SDK-specific. Used by
# pytest_collection_modifyitems to deselect cross-SDK tests so they
# don't show up as noise in the pytest summary.
SDK_NAME_TOKENS = {
    "python": ("python", "_py_"),
    "dotnet": ("dotnet", "_cs_", "_csharp_"),
    "java":   ("java",),
    "nodejs": ("nodejs", "_node_", "_js_"),
    "go":     ("_go_", "golang"),
}


def _test_sdk_owner(nodeid: str) -> str | None:
    """Return the SDK a test is dedicated to based on its name, or None
    if the test is SDK-agnostic."""
    name = nodeid.lower()
    qualified = name.split("::", 1)[-1] if "::" in name else name
    haystack = "_" + qualified.replace("::", "_").replace(".", "_") + "_"
    for sdk_name, tokens in SDK_NAME_TOKENS.items():
        for tok in tokens:
            if tok in haystack:
                return sdk_name
    return None


def pytest_collection_modifyitems(config, items):
    """Deselect tests that target an SDK other than the current one."""
    raw = os.environ.get("SDK", "")
    if not raw:
        return
    current = _norm_sdk(raw)
    keep, drop = [], []
    for item in items:
        owner = _test_sdk_owner(item.nodeid)
        if owner is None or owner == current:
            keep.append(item)
        else:
            drop.append(item)
    if drop:
        items[:] = keep
        config.hook.pytest_deselected(items=drop)


# ---------------------------------------------------------------------
# Environment / connection fixtures
# ---------------------------------------------------------------------

@pytest.fixture(scope="session")
def contract() -> dict:
    return CONTRACT


@pytest.fixture(scope="session")
def sdk() -> str:
    raw = os.environ.get("SDK", "")
    if not raw:
        pytest.fail("SDK env var must be set in the task's test.sh.")
    return _norm_sdk(raw)


@pytest.fixture(scope="session")
def app_port() -> int:
    return int(os.environ.get("APP_PORT", "8080"))


@pytest.fixture(scope="session")
def base_url(app_port: int) -> str:
    return f"http://localhost:{app_port}"


@pytest.fixture(scope="session")
def workdir() -> Path:
    return Path(os.environ.get("APP_WORKDIR", "/app"))


@pytest.fixture(scope="session")
def cosmos_endpoint() -> str:
    return os.environ["COSMOS_ENDPOINT"]


@pytest.fixture(scope="session")
def cosmos_key() -> str:
    return os.environ["COSMOS_KEY"]


@pytest.fixture(scope="session")
def cosmos_db_name() -> str:
    return os.environ.get(
        CONTRACT.get("database_env", "COSMOS_DATABASE"),
        CONTRACT.get("database_default", "mosaic"),
    )


@pytest.fixture(scope="session")
def cosmos_client(cosmos_endpoint: str, cosmos_key: str) -> CosmosClient:
    return CosmosClient(
        cosmos_endpoint,
        credential=cosmos_key,
        connection_verify=False,  # emulator self-signed cert
    )


@pytest.fixture(scope="session")
def cosmos_database(cosmos_client: CosmosClient, cosmos_db_name: str):
    return cosmos_client.get_database_client(cosmos_db_name)


@pytest.fixture(scope="session")
def root_containers(cosmos_database) -> dict:
    """{entity_name: container_client} for every declared root entity."""
    return {r["name"]: get_container(cosmos_database, r) for r in ROOTS}


@pytest.fixture(scope="session")
def child_containers(cosmos_database) -> dict:
    """{entity_name: container_client} for every declared child entity."""
    return {c["name"]: get_container(cosmos_database, c) for c in CHILDREN}


@pytest.fixture(scope="session")
def api(base_url: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    s.request_url_base = base_url  # type: ignore[attr-defined]

    def _request(method, path, **kwargs):
        return requests.request(method, f"{base_url}{path}", timeout=10, **kwargs)

    s.api = _request  # type: ignore[attr-defined]
    return s


# ---------------------------------------------------------------------
# Root-entity seeding + independent persistence read
# ---------------------------------------------------------------------

@pytest.fixture(scope="session")
def seed_roots(api) -> dict:
    """Seed every root entity's deterministic rows through the agent's
    own API. Idempotent: a duplicate row returns the entity's declared
    duplicate status (usually 409), which we treat as already-seeded.

    Returns {entity_name: [seed_row, ...]}.
    """
    out: dict = {}
    for root in ROOTS:
        path = root["create"]["path"]
        dup = root["create"].get("duplicate_status", 409)
        ok = {201, 200}
        if dup is not None:
            ok.add(dup)
        for row in root["seed"]:
            r = api.api("POST", path, json=row)
            assert r.status_code in ok, (
                f"POST {path} for {root['name']} {row['id']!r} returned "
                f"{r.status_code}: {r.text[:300]}"
            )
        out[root["name"]] = root["seed"]
    return out


@pytest.fixture(scope="session")
def root_persisted(root_containers, seed_roots) -> dict:
    """{entity_name: {id: stored_document_or_None}} read independently
    from the emulator. The backbone of the behavioural suite."""
    out: dict = {}
    for root in ROOTS:
        container = root_containers[root["name"]]
        docs: dict = {}
        for row in root["seed"]:
            rows = emulator_docs_for_id(container, row["id"])
            docs[row["id"]] = rows[0] if rows else None
        out[root["name"]] = docs
    return out


# ---------------------------------------------------------------------
# Source code scanning (used by check_source.py / check_skills.py).
# Language-agnostic — unchanged from the mosaic-era verifier.
# ---------------------------------------------------------------------

SOURCE_SUFFIXES = {
    "python": {".py", ".toml", ".txt", ".cfg"},
    "dotnet": {".cs", ".csproj", ".fsproj", ".props", ".targets", ".json"},
    "java": {".java", ".kt", ".xml", ".gradle", ".kts", ".properties"},
    "nodejs": {".js", ".mjs", ".cjs", ".ts", ".json"},
    "go": {".go", ".mod", ".sum"},
}

SKIP_DIRS = {
    "node_modules", ".git", "bin", "obj", "target", "dist", "build", "out",
    "__pycache__", ".pytest_cache", ".venv", "venv", "vendor", ".idea", ".vscode",
}

_HASH_LINE = re.compile(r"(?m)#.*$")
_SLASH_LINE = re.compile(r"(?m)//.*$")
_BLOCK_C = re.compile(r"/\*.*?\*/", re.DOTALL)
_XML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_TRIPLE_DOUBLE = re.compile(r'"""[\s\S]*?"""')
_TRIPLE_SINGLE = re.compile(r"'''[\s\S]*?'''")


def _strip_comments(text: str, sdk: str) -> str:
    if sdk == "python":
        text = _TRIPLE_DOUBLE.sub("", text)
        text = _TRIPLE_SINGLE.sub("", text)
        return _HASH_LINE.sub("", text)
    if sdk == "go":
        text = _BLOCK_C.sub("", text)
        return _SLASH_LINE.sub("", text)
    text = _XML_COMMENT.sub("", text)
    text = _BLOCK_C.sub("", text)
    return _SLASH_LINE.sub("", text)


@pytest.fixture(scope="session")
def source_files(sdk: str, workdir: Path) -> list[Path]:
    suffixes = SOURCE_SUFFIXES[sdk]
    out: list[Path] = []
    if not workdir.exists():
        return out
    for p in workdir.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in suffixes or p.name.lower() in {
            "package.json", "package-lock.json", "go.mod", "go.sum",
            "pom.xml", "build.gradle", "build.gradle.kts", "requirements.txt",
            "pyproject.toml", "setup.py", "setup.cfg",
        }:
            try:
                if p.stat().st_size <= 512 * 1024:
                    out.append(p)
            except OSError:
                continue
    return out


@pytest.fixture(scope="session")
def source_text(source_files: list[Path], sdk: str) -> str:
    """All source concatenated, with comments stripped per language."""
    chunks: list[str] = []
    for p in source_files:
        try:
            chunks.append(_strip_comments(p.read_text(encoding="utf-8", errors="ignore"), sdk))
        except OSError:
            pass
    return "\n".join(chunks)


# ---------------------------------------------------------------------
# Per-check log helper
# ---------------------------------------------------------------------

@pytest.fixture(scope="session")
def log_dir() -> Path:
    p = Path(os.environ.get("VERIFIER_LOG_DIR", "/logs/verifier"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_check_log(log_dir: Path, name: str, lines: Iterable[str]) -> None:
    (log_dir / f"{name}.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
