"""
API Contract Tests for IoT Device Telemetry
=============================================

These tests validate that the generated application conforms to the
API contract defined in api-contract.yaml. They test:
- Correct HTTP methods and paths
- Expected request/response schemas
- Correct status codes
- Required fields present in responses
- Time-series query patterns
- Bulk ingestion
- Aggregate statistics
"""

import pytest
from datetime import datetime, timezone, timedelta


# ===================================================================
# HEALTH CHECK
# ===================================================================

class TestHealth:
    """Verify the health endpoint exists and responds."""

    def test_health_returns_200(self, api):
        resp = api.request("GET", "/health")
        assert resp.status_code == 200, (
            "Health endpoint must return 200. "
            "Ensure your app exposes GET /health"
        )


# ===================================================================
# DEVICE MANAGEMENT
# ===================================================================

class TestRegisterDevice:
    """POST /api/devices — Register a new IoT device."""

    def test_register_device_returns_201(self, api):
        resp = api.request("POST", "/api/devices", json={
            "deviceId": "test-dev-001",
            "name": "Test Sensor",
            "location": "test-facility",
            "deviceType": "sensor",
        })
        assert resp.status_code == 201, (
            f"POST /api/devices should return 201, got {resp.status_code}. "
            f"Response: {resp.text[:500]}"
        )

    def test_register_device_response_has_required_fields(self, api):
        resp = api.request("POST", "/api/devices", json={
            "deviceId": "test-dev-002",
            "name": "Field Check",
            "location": "test-facility",
            "deviceType": "thermostat",
        })
        assert resp.status_code == 201
        body = resp.json()

        required = ["deviceId", "name", "location", "deviceType"]
        missing = [f for f in required if f not in body]
        assert not missing, (
            f"Response missing required fields: {missing}. "
            f"Got: {list(body.keys())}. "
            f"See api-contract.yaml register_device.response.body.required"
        )

    def test_register_device_returns_correct_data(self, api):
        resp = api.request("POST", "/api/devices", json={
            "deviceId": "test-dev-003",
            "name": "Data Check",
            "location": "building-X",
            "deviceType": "gateway",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["deviceId"] == "test-dev-003"
        assert body["location"] == "building-X"
        assert body["deviceType"] == "gateway"


class TestGetDevice:
    """GET /api/devices/{deviceId} — Get device metadata."""

    def test_get_existing_device(self, api, seeded_data):
        resp = api.request("GET", "/api/devices/device-001")
        assert resp.status_code == 200, (
            f"GET /api/devices/device-001 should return 200, got {resp.status_code}"
        )

    def test_get_device_has_required_fields(self, api, seeded_data):
        resp = api.request("GET", "/api/devices/device-001")
        assert resp.status_code == 200
        body = resp.json()

        required = ["deviceId", "name", "location", "deviceType"]
        missing = [f for f in required if f not in body]
        assert not missing, (
            f"GET device response missing required fields: {missing}. "
            f"Got: {list(body.keys())}"
        )

    def test_get_nonexistent_device_returns_404(self, api):
        resp = api.request("GET", "/api/devices/nonexistent-device-xyz")
        assert resp.status_code == 404, (
            f"GET /api/devices/nonexistent-device-xyz should return 404, "
            f"got {resp.status_code}"
        )


class TestGetDevicesByLocation:
    """GET /api/devices?location=X — Query devices by location."""

    def test_query_by_location_returns_200(self, api, seeded_data):
        resp = api.request("GET", "/api/devices?location=building-A")
        assert resp.status_code == 200, (
            f"GET /api/devices?location=building-A should return 200, "
            f"got {resp.status_code}"
        )

    def test_query_by_location_returns_array(self, api, seeded_data):
        resp = api.request("GET", "/api/devices?location=building-A")
        body = resp.json()
        assert isinstance(body, list), (
            f"Location query should return an array, got {type(body).__name__}"
        )

    def test_building_a_has_2_devices(self, api, seeded_data):
        """building-A has device-001 and device-002."""
        resp = api.request("GET", "/api/devices?location=building-A")
        body = resp.json()
        assert len(body) >= 2, (
            f"building-A should have at least 2 devices, got {len(body)}"
        )

    def test_location_filter_is_correct(self, api, seeded_data):
        resp = api.request("GET", "/api/devices?location=building-A")
        body = resp.json()
        for device in body:
            assert device["location"] == "building-A", (
                f"Device {device.get('deviceId')} has location '{device['location']}', "
                f"expected 'building-A'"
            )


# ===================================================================
# TELEMETRY INGESTION
# ===================================================================

class TestIngestTelemetry:
    """POST /api/telemetry — Ingest a single telemetry reading."""

    def test_ingest_returns_201(self, api, seeded_data):
        resp = api.request("POST", "/api/telemetry", json={
            "deviceId": "device-001",
            "temperature": 20.0,
            "humidity": 50.0,
            "batteryLevel": 90.0,
        })
        assert resp.status_code == 201, (
            f"POST /api/telemetry should return 201, got {resp.status_code}. "
            f"Response: {resp.text[:500]}"
        )

    def test_ingest_response_has_required_fields(self, api, seeded_data):
        resp = api.request("POST", "/api/telemetry", json={
            "deviceId": "device-002",
            "temperature": 18.0,
            "humidity": 60.0,
            "batteryLevel": 85.0,
        })
        assert resp.status_code == 201
        body = resp.json()

        required = ["readingId", "deviceId", "temperature", "humidity", "batteryLevel", "timestamp"]
        missing = [f for f in required if f not in body]
        assert not missing, (
            f"Telemetry response missing required fields: {missing}. "
            f"Got: {list(body.keys())}"
        )

    def test_ingest_returns_correct_values(self, api, seeded_data):
        resp = api.request("POST", "/api/telemetry", json={
            "deviceId": "device-003",
            "temperature": 26.5,
            "humidity": 35.0,
            "batteryLevel": 99.0,
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["deviceId"] == "device-003"
        assert abs(body["temperature"] - 26.5) < 0.01
        assert abs(body["humidity"] - 35.0) < 0.01


class TestBatchIngest:
    """POST /api/telemetry/batch — Bulk ingest telemetry readings."""

    def test_batch_ingest_returns_201(self, api, seeded_data):
        readings = [
            {"deviceId": "device-001", "temperature": 22.0, "humidity": 45.0, "batteryLevel": 93.0},
            {"deviceId": "device-001", "temperature": 22.5, "humidity": 44.0, "batteryLevel": 92.5},
            {"deviceId": "device-002", "temperature": 19.0, "humidity": 55.0, "batteryLevel": 86.0},
        ]
        resp = api.request("POST", "/api/telemetry/batch", json=readings)
        assert resp.status_code == 201, (
            f"POST /api/telemetry/batch should return 201, got {resp.status_code}. "
            f"Response: {resp.text[:500]}"
        )

    def test_batch_ingest_returns_count(self, api, seeded_data):
        readings = [
            {"deviceId": "device-004", "temperature": 24.0, "humidity": 42.0, "batteryLevel": 100.0},
            {"deviceId": "device-005", "temperature": 16.0, "humidity": 68.0, "batteryLevel": 58.0},
        ]
        resp = api.request("POST", "/api/telemetry/batch", json=readings)
        assert resp.status_code == 201
        body = resp.json()
        assert "ingested" in body, (
            f"Batch response must include 'ingested' count. Got: {list(body.keys())}"
        )
        assert body["ingested"] == 2, (
            f"Submitted 2 readings, ingested should be 2, got {body['ingested']}"
        )


# ===================================================================
# LATEST READING
# ===================================================================

class TestLatestReading:
    """GET /api/devices/{deviceId}/telemetry/latest — Latest reading."""

    def test_latest_reading_returns_200(self, api, seeded_data):
        resp = api.request("GET", "/api/devices/device-001/telemetry/latest")
        assert resp.status_code == 200, (
            f"GET latest reading should return 200, got {resp.status_code}"
        )

    def test_latest_reading_has_required_fields(self, api, seeded_data):
        resp = api.request("GET", "/api/devices/device-001/telemetry/latest")
        assert resp.status_code == 200
        body = resp.json()

        required = ["deviceId", "temperature", "humidity", "batteryLevel", "timestamp"]
        missing = [f for f in required if f not in body]
        assert not missing, (
            f"Latest reading missing required fields: {missing}. "
            f"Got: {list(body.keys())}"
        )

    def test_latest_reading_is_for_correct_device(self, api, seeded_data):
        resp = api.request("GET", "/api/devices/device-001/telemetry/latest")
        body = resp.json()
        assert body["deviceId"] == "device-001", (
            f"Latest reading should be for device-001, got {body['deviceId']}"
        )

    def test_nonexistent_device_latest_returns_404(self, api):
        resp = api.request("GET", "/api/devices/nonexistent-xyz/telemetry/latest")
        assert resp.status_code == 404, (
            f"Latest reading for nonexistent device should return 404, "
            f"got {resp.status_code}"
        )


# ===================================================================
# TIME RANGE QUERIES
# ===================================================================

class TestTimeRangeQuery:
    """GET /api/devices/{deviceId}/telemetry?start=X&end=Y — Time range."""

    def test_time_range_returns_200(self, api, seeded_data):
        now = datetime.now(timezone.utc)
        start = (now - timedelta(hours=24)).isoformat()
        end = now.isoformat()
        resp = api.request("GET", f"/api/devices/device-001/telemetry?start={start}&end={end}")
        assert resp.status_code == 200, (
            f"Time range query should return 200, got {resp.status_code}"
        )

    def test_time_range_returns_array(self, api, seeded_data):
        now = datetime.now(timezone.utc)
        start = (now - timedelta(hours=24)).isoformat()
        end = now.isoformat()
        resp = api.request("GET", f"/api/devices/device-001/telemetry?start={start}&end={end}")
        body = resp.json()
        assert isinstance(body, list), (
            f"Time range query should return an array, got {type(body).__name__}"
        )

    def test_time_range_returns_readings_for_device(self, api, seeded_data):
        """device-001 has 3 seeded readings in the last 4 hours."""
        now = datetime.now(timezone.utc)
        start = (now - timedelta(hours=4)).isoformat()
        end = now.isoformat()
        resp = api.request("GET", f"/api/devices/device-001/telemetry?start={start}&end={end}")
        body = resp.json()
        assert len(body) >= 3, (
            f"device-001 should have at least 3 readings in last 4h, got {len(body)}"
        )

    def test_time_range_only_contains_correct_device(self, api, seeded_data):
        now = datetime.now(timezone.utc)
        start = (now - timedelta(hours=24)).isoformat()
        end = now.isoformat()
        resp = api.request("GET", f"/api/devices/device-001/telemetry?start={start}&end={end}")
        body = resp.json()
        for reading in body:
            assert reading["deviceId"] == "device-001", (
                f"Time range for device-001 returned reading for {reading['deviceId']}"
            )

    def test_empty_time_range_returns_empty(self, api, seeded_data):
        """A time range in the distant past should return no readings."""
        resp = api.request(
            "GET",
            "/api/devices/device-001/telemetry?start=2000-01-01T00:00:00Z&end=2000-12-31T23:59:59Z"
        )
        body = resp.json()
        assert isinstance(body, list) and len(body) == 0, (
            f"Time range 2000 should return empty, got {len(body)} readings"
        )


# ===================================================================
# AGGREGATE STATISTICS
# ===================================================================

class TestDeviceStats:
    """GET /api/devices/{deviceId}/telemetry/stats — Aggregate stats."""

    def test_stats_returns_200(self, api, seeded_data):
        resp = api.request("GET", "/api/devices/device-001/telemetry/stats")
        assert resp.status_code == 200, (
            f"GET stats should return 200, got {resp.status_code}"
        )

    def test_stats_has_required_fields(self, api, seeded_data):
        resp = api.request("GET", "/api/devices/device-001/telemetry/stats")
        assert resp.status_code == 200
        body = resp.json()

        required = ["deviceId", "period", "temperature", "humidity", "batteryLevel"]
        missing = [f for f in required if f not in body]
        assert not missing, (
            f"Stats response missing required fields: {missing}. "
            f"Got: {list(body.keys())}"
        )

    def test_stats_temperature_has_min_max_avg(self, api, seeded_data):
        resp = api.request("GET", "/api/devices/device-001/telemetry/stats")
        body = resp.json()
        temp = body.get("temperature", {})
        for field in ["min", "max", "avg"]:
            assert field in temp, (
                f"temperature stats missing '{field}'. "
                f"Got: {list(temp.keys()) if isinstance(temp, dict) else temp}"
            )

    def test_stats_humidity_has_min_max_avg(self, api, seeded_data):
        resp = api.request("GET", "/api/devices/device-001/telemetry/stats")
        body = resp.json()
        hum = body.get("humidity", {})
        for field in ["min", "max", "avg"]:
            assert field in hum, (
                f"humidity stats missing '{field}'. "
                f"Got: {list(hum.keys()) if isinstance(hum, dict) else hum}"
            )

    def test_stats_values_are_numeric(self, api, seeded_data):
        resp = api.request("GET", "/api/devices/device-001/telemetry/stats")
        body = resp.json()
        temp = body.get("temperature", {})
        assert isinstance(temp.get("min"), (int, float)), (
            f"temperature.min should be numeric, got {type(temp.get('min')).__name__}"
        )
        assert isinstance(temp.get("max"), (int, float)), (
            f"temperature.max should be numeric, got {type(temp.get('max')).__name__}"
        )

    def test_stats_with_period_parameter(self, api, seeded_data):
        resp = api.request("GET", "/api/devices/device-001/telemetry/stats?period=24h")
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("period") in ["24h", "24H", "1d", "1D", "24 hours"], (
            f"Stats period should reflect the requested period, got '{body.get('period')}'"
        )
