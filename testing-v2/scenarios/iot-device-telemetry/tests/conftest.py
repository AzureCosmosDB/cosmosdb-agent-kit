"""
Scenario-level conftest for iot-device-telemetry tests.

Imports shared harness fixtures and adds scenario-specific helpers.
"""

import sys
from pathlib import Path

# Add harness to path so shared fixtures are importable
harness_dir = Path(__file__).resolve().parent.parent.parent.parent / "harness"
sys.path.insert(0, str(harness_dir))

from conftest_base import *  # noqa: F401,F403 — re-export all shared fixtures

import pytest
from datetime import datetime, timezone, timedelta


# ---------------------------------------------------------------------------
# Scenario-specific fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_devices():
    """Standard set of test IoT devices."""
    return [
        {"deviceId": "device-001", "name": "Temp Sensor A1", "location": "building-A", "deviceType": "sensor"},
        {"deviceId": "device-002", "name": "Temp Sensor A2", "location": "building-A", "deviceType": "sensor"},
        {"deviceId": "device-003", "name": "Thermostat B1", "location": "building-B", "deviceType": "thermostat"},
        {"deviceId": "device-004", "name": "Gateway B1", "location": "building-B", "deviceType": "gateway"},
        {"deviceId": "device-005", "name": "Sensor C1", "location": "warehouse-1", "deviceType": "sensor"},
    ]


@pytest.fixture(scope="session")
def test_readings():
    """
    Standard telemetry readings with deterministic values.
    Timestamps are spread across recent hours for time-range queries.
    """
    now = datetime.now(timezone.utc)
    return [
        {"deviceId": "device-001", "temperature": 22.5, "humidity": 45.0, "batteryLevel": 95.0,
         "timestamp": (now - timedelta(hours=3)).isoformat()},
        {"deviceId": "device-001", "temperature": 23.1, "humidity": 44.0, "batteryLevel": 94.5,
         "timestamp": (now - timedelta(hours=2)).isoformat()},
        {"deviceId": "device-001", "temperature": 21.8, "humidity": 46.5, "batteryLevel": 94.0,
         "timestamp": (now - timedelta(hours=1)).isoformat()},
        {"deviceId": "device-002", "temperature": 19.0, "humidity": 55.0, "batteryLevel": 88.0,
         "timestamp": (now - timedelta(hours=2)).isoformat()},
        {"deviceId": "device-002", "temperature": 19.5, "humidity": 54.0, "batteryLevel": 87.5,
         "timestamp": (now - timedelta(hours=1)).isoformat()},
        {"deviceId": "device-003", "temperature": 25.0, "humidity": 40.0, "batteryLevel": 100.0,
         "timestamp": (now - timedelta(hours=1)).isoformat()},
        {"deviceId": "device-005", "temperature": 15.0, "humidity": 70.0, "batteryLevel": 60.0,
         "timestamp": (now - timedelta(hours=1)).isoformat()},
    ]


@pytest.fixture(scope="session")
def seeded_data(api, test_devices, test_readings):
    """
    Register all test devices and ingest all telemetry readings.
    Returns a dict with the created data for reference.
    """
    created_devices = []
    for device in test_devices:
        resp = api.request("POST", "/api/devices", json=device)
        assert resp.status_code == 201, (
            f"Failed to register device {device['deviceId']}: "
            f"{resp.status_code} {resp.text}"
        )
        created_devices.append(resp.json())

    created_readings = []
    for reading in test_readings:
        resp = api.request("POST", "/api/telemetry", json=reading)
        assert resp.status_code == 201, (
            f"Failed to ingest reading for {reading['deviceId']}: "
            f"{resp.status_code} {resp.text}"
        )
        created_readings.append(resp.json())

    return {
        "devices": created_devices,
        "readings": created_readings,
    }
