"""Shared pytest fixtures for the cosmos-sdk-skills verifier.

Every task's tests/checks.py imports from /verifier/. The fixtures here
read everything from environment variables that the base image and the
per-task test.sh set up:

    SDK                   -- one of python, dotnet, java, nodejs, go
    APP_PORT              -- port the agent's app should be listening on
    APP_WORKDIR           -- where the agent put its source code (/app)
    COSMOS_ENDPOINT       -- https://localhost:8081
    COSMOS_KEY            -- well-known emulator key
    COSMOS_DATABASE       -- mosaic
    COSMOS_USERS_CONTAINER -- users
    VERIFIER_LOG_DIR      -- where per-check logs land

The verifier does not own any test data — the API checks insert their
own deterministic users.
"""
from __future__ import annotations

import json
import os
import re
import urllib3
from pathlib import Path
from typing import Iterable

import pytest
import requests
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

# Deterministic seed users. Shared across check_api.py and check_cosmos.py.
USERS = [
    {"id": "u-alpha",   "name": "Alpha",   "email": "alpha@example.com",   "city": "Seattle",  "interests": ["climbing", "coffee"]},
    {"id": "u-bravo",   "name": "Bravo",   "email": "bravo@example.com",   "city": "Seattle",  "interests": ["hiking"]},
    {"id": "u-charlie", "name": "Charlie", "email": "charlie@example.com", "city": "Portland", "interests": ["cycling", "books", "tea"]},
]


@pytest.fixture(scope="session")
def seeded_users(api):
    """Seed the agent's service with deterministic users via its own API.

    Shared by check_api.py (API conformance) and check_cosmos.py
    (data-shape inspection). Idempotent: re-running with the same data
    against a pre-seeded container returns 409 on each row, which we treat
    as success.
    """
    for u in USERS:
        r = api.api("POST", "/users", json=u)
        assert r.status_code in (201, 409), (
            f"POST /users for {u['id']} returned {r.status_code}: {r.text[:300]}"
        )
    return USERS


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
    if the test is SDK-agnostic.

    Inspects both the class name and the test method name so that
    `TestDirectModeDotnet::test_uses_connection_mode_direct` is
    correctly attributed to dotnet.
    """
    name = nodeid.lower()
    # Strip the file path; keep only the part after "::" (class + method).
    qualified = name.split("::", 1)[-1] if "::" in name else name
    # Sentinel-wrap each segment so token like "_go_" matches
    # "test_go_foo" or "testgoo" but not "test_argo" / "test_django".
    haystack = "_" + qualified.replace("::", "_").replace(".", "_") + "_"
    for sdk_name, tokens in SDK_NAME_TOKENS.items():
        for tok in tokens:
            if tok in haystack:
                return sdk_name
    return None


def pytest_collection_modifyitems(config, items):
    """Deselect tests that target an SDK other than the current one.

    Tests with no SDK token in their name (e.g. `test_provision_only_once`,
    `test_no_real_account_key_literal`) are kept — they either apply to
    every SDK or use the `sdk` fixture + `_need(...)` to self-skip with
    a clear reason.
    """
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
    return os.environ.get("COSMOS_DATABASE", "mosaic")


@pytest.fixture(scope="session")
def cosmos_users_container_name() -> str:
    return os.environ.get("COSMOS_USERS_CONTAINER", "users")


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
def cosmos_users_container(cosmos_database, cosmos_users_container_name: str):
    return cosmos_database.get_container_client(cosmos_users_container_name)


@pytest.fixture(scope="session")
def api(base_url: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    s.request_url_base = base_url  # type: ignore[attr-defined]

    def _request(method, path, **kwargs):
        return requests.request(method, f"{base_url}{path}", timeout=10, **kwargs)

    s.api = _request  # type: ignore[attr-defined]
    return s


# -----------------------------------------------------------------------
# Source code scanning
# -----------------------------------------------------------------------

SOURCE_SUFFIXES = {
    "python": {".py", ".toml", ".txt", ".cfg"},
    "dotnet": {".cs", ".csproj", ".fsproj", ".props", ".targets", ".json"},
    "java": {".java", ".kt", ".xml", ".gradle", ".kts", ".properties"},
    "nodejs": {".js", ".mjs", ".cjs", ".ts", ".json"},
    "go": {".go", ".mod", ".sum"},
}

SKIP_DIRS = {
    "node_modules", ".git", "bin", "obj", "target", "dist", "build",
    "__pycache__", ".pytest_cache", ".venv", "venv", "vendor", ".idea", ".vscode",
}

# Comment-stripping regexes per language family. Used by source-code
# static checks so an agent cannot pass by writing keyword soup in
# comments.
_HASH_LINE = re.compile(r"(?m)#.*$")
_SLASH_LINE = re.compile(r"(?m)//.*$")
_BLOCK_C = re.compile(r"/\*.*?\*/", re.DOTALL)
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
    # dotnet, java, nodejs all use C-style comments
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


@pytest.fixture(scope="session")
def source_text_with_comments(source_files: list[Path]) -> str:
    """Raw concatenated source (comments retained). Used by the
    transparency rubric, which intentionally reads comments and docs."""
    chunks: list[str] = []
    for p in source_files:
        try:
            chunks.append(p.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    return "\n".join(chunks)


@pytest.fixture(scope="session")
def docs_text(workdir: Path) -> str:
    """README + markdown + plain-text files concatenated. Used by the
    transparency / borrowed-from rubric."""
    chunks: list[str] = []
    if not workdir.exists():
        return ""
    for p in workdir.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in {".md", ".markdown", ".txt", ".rst"}:
            try:
                if p.stat().st_size <= 512 * 1024:
                    chunks.append(p.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                pass
    return "\n".join(chunks)


# -----------------------------------------------------------------------
# Per-check log helper
# -----------------------------------------------------------------------

@pytest.fixture(scope="session")
def log_dir() -> Path:
    p = Path(os.environ.get("VERIFIER_LOG_DIR", "/logs/verifier"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_check_log(log_dir: Path, name: str, lines: Iterable[str]) -> None:
    (log_dir / f"{name}.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
