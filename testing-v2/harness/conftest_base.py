"""
Shared pytest fixtures for Cosmos DB Agent Kit testing framework.

These fixtures are available to all scenario test suites via conftest.py
in each scenario's tests/ directory.
"""

import os
import time
import subprocess
import signal
import socket
import yaml
import pytest
import requests
from pathlib import Path
from azure.cosmos import CosmosClient


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def find_iteration_dir():
    """Resolve the iteration directory from the ITERATION_DIR env var."""
    iteration_dir = os.environ.get("ITERATION_DIR")
    if not iteration_dir:
        pytest.skip("ITERATION_DIR environment variable not set")
    path = Path(iteration_dir)
    if not path.exists():
        pytest.fail(f"Iteration directory does not exist: {path}")
    return path


def load_iteration_config(iteration_dir: Path) -> dict:
    """Load iteration-config.yaml from the iteration directory."""
    config_path = iteration_dir / "iteration-config.yaml"
    if not config_path.exists():
        pytest.fail(
            f"iteration-config.yaml not found in {iteration_dir}. "
            "The agent must create this file with build/run/port info."
        )
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Network helpers
# ---------------------------------------------------------------------------

def wait_for_port(host: str, port: int, timeout: float = 120.0):
    """Wait until a TCP port is accepting connections."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            time.sleep(1)
    return False


def wait_for_health(base_url: str, health_path: str = "/health", timeout: float = 120.0):
    """Wait until the app's health endpoint returns 200."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = requests.get(f"{base_url}{health_path}", timeout=5)
            if resp.status_code == 200:
                return True
        except requests.ConnectionError:
            pass
        time.sleep(2)
    return False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def iteration_dir():
    """Path to the iteration directory being tested."""
    return find_iteration_dir()


@pytest.fixture(scope="session")
def iteration_config(iteration_dir):
    """Parsed iteration-config.yaml."""
    return load_iteration_config(iteration_dir)


@pytest.fixture(scope="session")
def app_port(iteration_config):
    """The port the application listens on."""
    return iteration_config.get("port", 8080)


@pytest.fixture(scope="session")
def base_url(app_port):
    """Base URL for API requests."""
    return f"http://localhost:{app_port}"


@pytest.fixture(scope="session")
def app_process(iteration_dir, iteration_config, app_port):
    """
    Build and start the application. Yields the subprocess.
    Tears down after all tests complete.

    Set APP_ALREADY_RUNNING=1 to skip starting the app (useful for local dev).
    """
    if os.environ.get("APP_ALREADY_RUNNING") == "1":
        yield None
        return

    # Build step
    build_cmd = iteration_config.get("build")
    if build_cmd:
        result = subprocess.run(
            build_cmd,
            shell=True,
            cwd=str(iteration_dir),
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            pytest.fail(
                f"Build failed (exit code {result.returncode}):\n"
                f"STDOUT:\n{result.stdout[-2000:]}\n"
                f"STDERR:\n{result.stderr[-2000:]}"
            )

    # Run step
    run_cmd = iteration_config.get("run")
    if not run_cmd:
        pytest.fail("iteration-config.yaml must specify a 'run' command")

    env = os.environ.copy()
    # Pass Cosmos DB connection info
    env.setdefault(
        "COSMOS_ENDPOINT",
        os.environ.get("COSMOS_ENDPOINT", "https://localhost:8081"),
    )
    env.setdefault(
        "COSMOS_KEY",
        os.environ.get(
            "COSMOS_KEY",
            "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
        ),
    )

    proc = subprocess.Popen(
        run_cmd,
        shell=True,
        cwd=str(iteration_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for port
    if not wait_for_port("localhost", app_port, timeout=120):
        stdout = proc.stdout.read().decode(errors="replace")[-2000:] if proc.stdout else ""
        stderr = proc.stderr.read().decode(errors="replace")[-2000:] if proc.stderr else ""
        proc.kill()
        pytest.fail(
            f"App did not start on port {app_port} within 120s.\n"
            f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
        )

    yield proc

    # Teardown
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="session")
def api(base_url, app_process, iteration_config):
    """
    A requests.Session pointed at the running app, ready after health check.
    This is the primary fixture tests should use for HTTP calls.
    """
    health_path = iteration_config.get("health", "/health")
    if not wait_for_health(base_url, health_path, timeout=120):
        pytest.fail(f"Health endpoint {base_url}{health_path} did not return 200 within 120s")

    session = requests.Session()
    session.base_url = base_url  # type: ignore[attr-defined]
    session.headers.update({"Content-Type": "application/json"})

    # Attach a convenience method
    original_request = session.request

    def request_with_base(method, url, **kwargs):
        if url.startswith("/"):
            url = base_url + url
        return original_request(method, url, **kwargs)

    session.request = request_with_base  # type: ignore[assignment]
    return session


@pytest.fixture(scope="session")
def cosmos_client():
    """
    Direct Cosmos DB client for data integrity verification.
    Uses the emulator by default.
    """
    endpoint = os.environ.get("COSMOS_ENDPOINT", "https://localhost:8081")
    key = os.environ.get(
        "COSMOS_KEY",
        "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
    )
    # Emulator uses self-signed cert
    return CosmosClient(endpoint, credential=key)


@pytest.fixture(scope="session")
def cosmos_database(cosmos_client, iteration_config):
    """The Cosmos DB database used by the app."""
    db_name = iteration_config.get("database", "gaming-leaderboard-db")
    return cosmos_client.get_database_client(db_name)
