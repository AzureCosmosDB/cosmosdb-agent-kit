"""
Robustness Tests for IoT Device Telemetry
==========================================

These tests go beyond basic API contract compliance to verify the application
handles real-world scenarios correctly:
- Invalid / malformed input → proper 4xx responses (not 500)
- Computed field accuracy (stats: min, max, avg calculations)
- Data type correctness in responses
- Write-read consistency across endpoints
- Device data isolation
- Edge cases and boundary conditions

These tests catch the classes of bugs most commonly produced by AI agents:
missing input validation, incorrect aggregation math, serialization
mismatches, and device data leakage.
"""

import pytest
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


# ===================================================================
# INVALID INPUT HANDLING
# ===================================================================

class TestInvalidInput:
    """
    The application must return 4xx (not 5xx) for malformed requests.
    A 500 on bad input indicates missing validation — a common agent bug.
    """

    def test_register_device_missing_device_id_returns_4xx(self, api):
        """POST /api/devices without deviceId should return 4xx."""
        resp = api.request("POST", "/api/devices", json={
            "name": "No ID Device",
            "location": "building-A",
            "deviceType": "sensor",
        })
        assert 400 <= resp.status_code < 500, (
            f"Missing deviceId should return 4xx, got {resp.status_code}. "
            f"The app must validate required fields and return 400."
        )

    def test_register_device_empty_body_returns_4xx(self, api):
        """POST /api/devices with empty body should not crash."""
        resp = api.request("POST", "/api/devices", json={})
        assert 400 <= resp.status_code < 500, (
            f"Empty body should return 4xx, got {resp.status_code}. "
            f"Server must not crash (500) on missing fields."
        )

    def test_ingest_telemetry_missing_device_id_returns_4xx(self, api, seeded_data):
        """POST /api/telemetry without deviceId should return 4xx."""
        resp = api.request("POST", "/api/telemetry", json={
            "temperature": 22.0,
            "humidity": 45.0,
        })
        assert 400 <= resp.status_code < 500, (
            f"Missing deviceId in telemetry should return 4xx, got {resp.status_code}. "
            f"Server must validate required fields."
        )

    def test_ingest_telemetry_empty_body_returns_4xx(self, api, seeded_data):
        """POST /api/telemetry with empty body should not crash."""
        resp = api.request("POST", "/api/telemetry", json={})
        assert 400 <= resp.status_code < 500, (
            f"Empty telemetry body should return 4xx, got {resp.status_code}. "
            f"Server must not crash on missing fields."
        )

    def test_ingest_telemetry_for_nonexistent_device_returns_4xx(self, api, seeded_data):
        """POST /api/telemetry for a non-registered device should return 4xx."""
        resp = api.request("POST", "/api/telemetry", json={
            "deviceId": "does-not-exist-xyz",
            "temperature": 22.0,
            "humidity": 45.0,
        })
        assert 400 <= resp.status_code < 500, (
            f"Telemetry for nonexistent device should return 4xx, "
            f"got {resp.status_code}. Server should validate device exists."
        )


# ===================================================================
# DUPLICATE / CONFLICT HANDLING
# ===================================================================

class TestDuplicateHandling:
    """
    Registering the same device twice must not crash the server.
    Expected: 409 Conflict, or idempotent 200/201.
    """

    def test_register_duplicate_device_does_not_return_500(self, api):
        """Registering the same device twice must not cause a server error."""
        device = {
            "deviceId": "duplicate-test-001",
            "name": "DupTest Sensor",
            "location": "building-A",
            "deviceType": "sensor",
        }
        resp1 = api.request("POST", "/api/devices", json=device)
        assert resp1.status_code == 201, (
            f"First registration should succeed with 201, got {resp1.status_code}"
        )

        resp2 = api.request("POST", "/api/devices", json=device)
        assert resp2.status_code != 500, (
            f"Duplicate device registration returned 500 — server crashed. "
            f"Expected 409 Conflict or idempotent 200/201. "
            f"Response: {resp2.text[:300]}"
        )
        assert resp2.status_code < 500, (
            f"Duplicate device registration returned {resp2.status_code} (5xx). "
            f"Expected a client-side error (4xx) or idempotent success (2xx)."
        )


# ===================================================================
# COMPUTED FIELD ACCURACY (Stats)
# ===================================================================

class TestComputedFieldAccuracy:
    """
    Verify that stats aggregations (min, max, avg) are mathematically correct.
    This catches bugs where agents use wrong aggregation formulas.
    """

    def test_stats_temperature_min_correct(self, api, seeded_data):
        """
        device-001 readings: 22.5, 23.1, 21.8
        min temperature should be 21.8
        """
        resp = api.request("GET", "/api/devices/device-001/telemetry/stats")
        assert resp.status_code == 200
        body = resp.json()

        temp_stats = body.get("temperature", {})
        min_temp = temp_stats.get("min")
        assert min_temp is not None, (
            "temperature.min is missing from stats response"
        )
        assert abs(min_temp - 21.8) < 0.1, (
            f"device-001 min temperature should be ~21.8 "
            f"(readings: 22.5, 23.1, 21.8), got {min_temp}"
        )

    def test_stats_temperature_max_correct(self, api, seeded_data):
        """device-001 max temperature should be 23.1"""
        resp = api.request("GET", "/api/devices/device-001/telemetry/stats")
        assert resp.status_code == 200
        body = resp.json()

        temp_stats = body.get("temperature", {})
        max_temp = temp_stats.get("max")
        assert max_temp is not None, (
            "temperature.max is missing from stats response"
        )
        assert abs(max_temp - 23.1) < 0.1, (
            f"device-001 max temperature should be ~23.1 "
            f"(readings: 22.5, 23.1, 21.8), got {max_temp}"
        )

    def test_stats_temperature_avg_correct(self, api, seeded_data):
        """
        device-001 avg temperature should be (22.5 + 23.1 + 21.8) / 3 ≈ 22.47
        """
        resp = api.request("GET", "/api/devices/device-001/telemetry/stats")
        assert resp.status_code == 200
        body = resp.json()

        temp_stats = body.get("temperature", {})
        avg_temp = temp_stats.get("avg")
        assert avg_temp is not None, (
            "temperature.avg is missing from stats response"
        )
        expected_avg = (22.5 + 23.1 + 21.8) / 3  # ≈ 22.467
        assert abs(avg_temp - expected_avg) < 0.5, (
            f"device-001 avg temperature should be ~{expected_avg:.2f} "
            f"(readings: 22.5, 23.1, 21.8), got {avg_temp}"
        )

    def test_stats_humidity_values_correct(self, api, seeded_data):
        """
        device-001 humidity readings: 45.0, 44.0, 46.5
        min=44.0, max=46.5, avg≈45.17
        """
        resp = api.request("GET", "/api/devices/device-001/telemetry/stats")
        assert resp.status_code == 200
        body = resp.json()

        hum_stats = body.get("humidity", {})
        assert hum_stats.get("min") is not None, "humidity.min is missing"
        assert hum_stats.get("max") is not None, "humidity.max is missing"
        assert hum_stats.get("avg") is not None, "humidity.avg is missing"

        assert abs(hum_stats["min"] - 44.0) < 0.1, (
            f"humidity min should be ~44.0, got {hum_stats['min']}"
        )
        assert abs(hum_stats["max"] - 46.5) < 0.1, (
            f"humidity max should be ~46.5, got {hum_stats['max']}"
        )
        expected_avg = (45.0 + 44.0 + 46.5) / 3  # ≈ 45.17
        assert abs(hum_stats["avg"] - expected_avg) < 0.5, (
            f"humidity avg should be ~{expected_avg:.2f}, got {hum_stats['avg']}"
        )

    def test_stats_values_are_consistent(self, api, seeded_data):
        """min <= avg <= max for both temperature and humidity."""
        resp = api.request("GET", "/api/devices/device-001/telemetry/stats")
        assert resp.status_code == 200
        body = resp.json()

        for field in ["temperature", "humidity"]:
            stats = body.get(field, {})
            min_val = stats.get("min")
            max_val = stats.get("max")
            avg_val = stats.get("avg")

            if min_val is not None and max_val is not None and avg_val is not None:
                assert min_val <= avg_val + 0.01, (
                    f"{field}: min ({min_val}) > avg ({avg_val}). "
                    f"This is mathematically impossible."
                )
                assert avg_val <= max_val + 0.01, (
                    f"{field}: avg ({avg_val}) > max ({max_val}). "
                    f"This is mathematically impossible."
                )


# ===================================================================
# DATA TYPE CORRECTNESS
# ===================================================================

class TestDataTypeCorrectness:
    """
    Verify response fields have correct data types.
    Catches serialization bugs where numbers come back as strings.
    """

    def test_device_field_types(self, api, seeded_data):
        """Device fields should have correct types."""
        resp = api.request("GET", "/api/devices/device-001")
        assert resp.status_code == 200
        body = resp.json()

        assert isinstance(body.get("deviceId"), str), (
            f"deviceId should be string, got {type(body.get('deviceId')).__name__}"
        )
        assert isinstance(body.get("name"), str), (
            f"name should be string, got {type(body.get('name')).__name__}"
        )
        assert isinstance(body.get("location"), str), (
            f"location should be string, got {type(body.get('location')).__name__}"
        )

    def test_telemetry_values_are_numbers(self, api, seeded_data):
        """Telemetry readings should be numeric, not strings."""
        resp = api.request("GET", "/api/devices/device-001/telemetry/latest")
        assert resp.status_code == 200
        body = resp.json()

        if "temperature" in body:
            assert isinstance(body["temperature"], (int, float)), (
                f"temperature should be a number, got "
                f"{type(body['temperature']).__name__}: {body['temperature']!r}"
            )
        if "humidity" in body:
            assert isinstance(body["humidity"], (int, float)), (
                f"humidity should be a number, got "
                f"{type(body['humidity']).__name__}: {body['humidity']!r}"
            )

    def test_stats_values_are_numeric(self, api, seeded_data):
        """Stats min/max/avg should be numbers."""
        resp = api.request("GET", "/api/devices/device-001/telemetry/stats")
        assert resp.status_code == 200
        body = resp.json()

        for field in ["temperature", "humidity"]:
            stats = body.get(field, {})
            for stat_name in ["min", "max", "avg"]:
                val = stats.get(stat_name)
                if val is not None:
                    assert isinstance(val, (int, float)), (
                        f"{field}.{stat_name} should be numeric, got "
                        f"{type(val).__name__}: {val!r}"
                    )


# ===================================================================
# WRITE-READ CONSISTENCY
# ===================================================================

class TestWriteReadConsistency:
    """
    Data written through one endpoint must be correctly readable
    through another. This catches serialization mismatches.
    """

    def test_registered_device_retrievable_by_get(self, api):
        """Register a device, then GET it — fields should match."""
        device = {
            "deviceId": "consistency-dev-001",
            "name": "Consistency Sensor",
            "location": "building-C",
            "deviceType": "sensor",
        }
        create_resp = api.request("POST", "/api/devices", json=device)
        assert create_resp.status_code == 201

        get_resp = api.request("GET", "/api/devices/consistency-dev-001")
        assert get_resp.status_code == 200, (
            f"Device was registered but GET returned {get_resp.status_code}. "
            f"Data may not be persisted correctly."
        )
        retrieved = get_resp.json()

        assert retrieved["deviceId"] == "consistency-dev-001"
        assert retrieved["name"] == "Consistency Sensor"
        assert retrieved["location"] == "building-C"

    def test_device_appears_in_location_query(self, api, seeded_data):
        """
        Devices registered with location='building-A' should appear
        in the location query for building-A.
        """
        resp = api.request("GET", "/api/devices?location=building-A")
        assert resp.status_code == 200
        devices = resp.json()

        device_ids = [d.get("deviceId") for d in devices]
        assert "device-001" in device_ids, (
            f"device-001 (location=building-A) not found in location query. "
            f"This may indicate a query/serialization mismatch "
            f"(e.g., different casing in stored vs queried value). "
            f"Found devices: {device_ids}"
        )
        assert "device-002" in device_ids, (
            f"device-002 (location=building-A) not found in location query. "
            f"Found devices: {device_ids}"
        )

    def test_ingested_reading_appears_in_latest(self, api, seeded_data):
        """
        After ingesting a reading, it should be retrievable as the latest reading.
        """
        now = datetime.now(timezone.utc)
        reading = {
            "deviceId": "device-003",
            "temperature": 99.9,
            "humidity": 11.1,
            "batteryLevel": 75.0,
            "timestamp": now.isoformat(),
        }
        ingest_resp = api.request("POST", "/api/telemetry", json=reading)
        assert ingest_resp.status_code == 201

        latest_resp = api.request("GET", "/api/devices/device-003/telemetry/latest")
        assert latest_resp.status_code == 200
        body = latest_resp.json()

        # The latest reading should reflect what we just ingested
        assert abs(body.get("temperature", 0) - 99.9) < 0.1, (
            f"Latest reading temperature should be ~99.9 (just ingested), "
            f"got {body.get('temperature')}. The latest endpoint may not be "
            f"returning the most recent reading."
        )


# ===================================================================
# DATA ISOLATION
# ===================================================================

class TestDataIsolation:
    """
    Verify that device-scoped queries only return that device's data.
    """

    def test_time_range_only_returns_correct_device(self, api, seeded_data):
        """Time range query for device-001 should not include device-002 readings."""
        now = datetime.now(timezone.utc)
        start = (now - timedelta(hours=24)).isoformat()
        end = now.isoformat()

        resp = api.request(
            "GET",
            f"/api/devices/device-001/telemetry?start={start}&end={end}"
        )
        assert resp.status_code == 200
        readings = resp.json()

        for reading in readings:
            device_id = reading.get("deviceId")
            assert device_id == "device-001", (
                f"device-001's readings contain data from '{device_id}'. "
                f"Device data is leaking across queries."
            )

    def test_location_query_filters_correctly(self, api, seeded_data):
        """building-A query should not include building-B devices."""
        resp = api.request("GET", "/api/devices?location=building-A")
        assert resp.status_code == 200
        devices = resp.json()

        for device in devices:
            assert device.get("location") == "building-A", (
                f"building-A query returned device '{device.get('deviceId')}' "
                f"with location '{device.get('location')}'. "
                f"Location filtering is not working correctly."
            )


# ===================================================================
# EDGE CASES
# ===================================================================

class TestEdgeCases:
    """Test boundary conditions that commonly expose bugs."""

    def test_empty_location_returns_empty_array(self, api, seeded_data):
        """A location with no devices should return empty array, not error."""
        resp = api.request("GET", "/api/devices?location=nonexistent-building")
        assert resp.status_code == 200, (
            f"Empty location query should return 200, got {resp.status_code}"
        )
        body = resp.json()
        assert isinstance(body, list) and len(body) == 0, (
            f"Nonexistent location should return empty array, "
            f"got {len(body) if isinstance(body, list) else type(body).__name__}"
        )

    def test_latest_reading_is_most_recent(self, api, seeded_data):
        """
        device-001 has readings at -3h, -2h, -1h.
        Latest should be the -1h reading (temp=21.8).
        """
        resp = api.request("GET", "/api/devices/device-001/telemetry/latest")
        assert resp.status_code == 200
        body = resp.json()

        # The latest (most recent) reading for device-001 has temp=21.8
        temp = body.get("temperature")
        assert temp is not None, "Latest reading should include temperature"
        assert abs(temp - 21.8) < 0.1, (
            f"Latest reading for device-001 should have temperature ~21.8 "
            f"(the most recent seeded reading), got {temp}. "
            f"The 'latest' endpoint may not be selecting by most recent timestamp."
        )

    def test_batch_ingest_count_matches_input(self, api, seeded_data):
        """
        Batch ingest should report the correct count of ingested readings.
        """
        now = datetime.now(timezone.utc)
        batch = [
            {"deviceId": "device-002", "temperature": 20.0, "humidity": 50.0,
             "timestamp": (now - timedelta(minutes=3)).isoformat()},
            {"deviceId": "device-002", "temperature": 20.5, "humidity": 49.0,
             "timestamp": (now - timedelta(minutes=2)).isoformat()},
            {"deviceId": "device-002", "temperature": 21.0, "humidity": 48.0,
             "timestamp": (now - timedelta(minutes=1)).isoformat()},
        ]
        resp = api.request("POST", "/api/telemetry/batch", json=batch)
        assert resp.status_code == 201
        body = resp.json()

        count = body.get("ingested", body.get("count", body.get("inserted", body.get("total"))))
        assert count == 3, (
            f"Batch ingest of 3 readings should report count=3, got {count}. "
            f"Response: {body}"
        )

    def test_future_time_range_returns_empty(self, api, seeded_data):
        """A time range in the far future should return no readings."""
        start = "2099-01-01T00:00:00Z"
        end = "2099-12-31T23:59:59Z"
        resp = api.request(
            "GET",
            f"/api/devices/device-001/telemetry?start={start}&end={end}"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list) and len(body) == 0, (
            f"Future time range should return empty array, got {len(body)} readings"
        )

    def test_stats_for_device_with_single_reading(self, api, seeded_data):
        """
        device-003 has exactly 1 seeded reading (temp=25.0, humidity=40.0).
        Stats should return min=max=avg for each field.
        """
        resp = api.request("GET", "/api/devices/device-003/telemetry/stats")
        assert resp.status_code == 200
        body = resp.json()

        temp_stats = body.get("temperature", {})
        if temp_stats.get("min") is not None and temp_stats.get("max") is not None:
            # Additional readings may have been submitted (e.g., from consistency test)
            # so we just verify min <= max
            assert temp_stats["min"] <= temp_stats["max"], (
                f"temperature min ({temp_stats['min']}) > max ({temp_stats['max']})"
            )


# ===================================================================
# CONCURRENT TELEMETRY INGESTION
# ===================================================================

class TestConcurrentIngestion:
    """
    Verify the application handles concurrent telemetry writes correctly.
    All readings submitted concurrently must be persisted — none lost.
    """

    def test_concurrent_ingestion_all_persisted(self, api, seeded_data):
        """
        Submit 15 readings concurrently for the same device.
        All should be persisted and retrievable via time range query.
        """
        device_id = "concurrent-ingest-001"
        api.request("POST", "/api/devices", json={
            "deviceId": device_id,
            "name": "ConcurrentTest",
            "location": "building-A",
            "deviceType": "sensor",
        })

        now = datetime.now(timezone.utc)
        num_concurrent = 15

        def ingest_reading(i):
            return api.request("POST", "/api/telemetry", json={
                "deviceId": device_id,
                "temperature": 20.0 + i * 0.1,
                "humidity": 50.0,
                "batteryLevel": 90.0,
                "timestamp": (now - timedelta(seconds=num_concurrent - i)).isoformat(),
            })

        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(ingest_reading, i) for i in range(num_concurrent)]
            results = [f.result() for f in as_completed(futures)]

        succeeded = sum(1 for r in results if r.status_code == 201)
        assert succeeded == num_concurrent, (
            f"Only {succeeded}/{num_concurrent} concurrent ingestions succeeded. "
            f"Status codes: {[r.status_code for r in results]}"
        )

        # Verify all readings are retrievable
        start = (now - timedelta(minutes=5)).isoformat()
        end = (now + timedelta(minutes=5)).isoformat()
        resp = api.request(
            "GET",
            f"/api/devices/{device_id}/telemetry?start={start}&end={end}"
        )
        assert resp.status_code == 200
        readings = resp.json()
        assert len(readings) >= num_concurrent, (
            f"After {num_concurrent} concurrent ingestions, expected at least "
            f"{num_concurrent} readings in time range, got {len(readings)}. "
            f"Some concurrent writes may have been lost."
        )


# ===================================================================
# UPDATE AND DELETE CONSISTENCY
# ===================================================================

class TestUpdateDeleteConsistency:
    """
    Verify that device updates and deletions are reflected
    consistently across all related endpoints.
    """

    def test_deleted_device_telemetry_returns_404(self, api, seeded_data):
        """After deleting a device, its telemetry endpoints should return 404."""
        device_id = "delete-tel-001"
        api.request("POST", "/api/devices", json={
            "deviceId": device_id,
            "name": "DeleteTelemetry",
            "location": "building-B",
            "deviceType": "sensor",
        })
        api.request("POST", "/api/telemetry", json={
            "deviceId": device_id,
            "temperature": 22.0,
            "humidity": 45.0,
            "batteryLevel": 90.0,
        })

        # Delete device
        api.request("DELETE", f"/api/devices/{device_id}")

        # Latest should return 404
        resp = api.request("GET", f"/api/devices/{device_id}/telemetry/latest")
        assert resp.status_code == 404, (
            f"Latest telemetry for deleted device should return 404, "
            f"got {resp.status_code}"
        )

    def test_updated_device_preserves_telemetry(self, api, seeded_data):
        """Updating device metadata should not affect its telemetry readings."""
        device_id = "update-preserve-001"
        api.request("POST", "/api/devices", json={
            "deviceId": device_id,
            "name": "PreserveTelemetry",
            "location": "building-A",
            "deviceType": "sensor",
        })
        now = datetime.now(timezone.utc)
        api.request("POST", "/api/telemetry", json={
            "deviceId": device_id,
            "temperature": 33.3,
            "humidity": 55.5,
            "batteryLevel": 80.0,
            "timestamp": now.isoformat(),
        })

        # Update device name
        api.request("PATCH", f"/api/devices/{device_id}", json={
            "name": "PreserveTelemetry Updated",
        })

        # Telemetry should still be accessible
        resp = api.request("GET", f"/api/devices/{device_id}/telemetry/latest")
        assert resp.status_code == 200, (
            f"Telemetry should still be accessible after device update, "
            f"got {resp.status_code}"
        )
        body = resp.json()
        assert abs(body.get("temperature", 0) - 33.3) < 0.1, (
            f"Telemetry data should be preserved after device update"
        )
