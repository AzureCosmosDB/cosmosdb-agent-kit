"""
Cosmos DB Infrastructure & SDK Behavior Tests — IoT Device Telemetry
=====================================================================

These tests go BELOW the HTTP API surface to verify that the agent
applied Cosmos DB best practices at the SDK and container level.

Test categories:
  1. INFRASTRUCTURE — verify container partition keys, indexing policies,
     throughput mode, TTL configuration directly via Cosmos DB Python SDK.
  2. SDK BEHAVIORS — verify serialization, timestamp handling, and
     telemetry-specific patterns.
  3. CROSS-BOUNDARY — write data through the HTTP API, then read it
     directly from Cosmos DB to catch serialization mismatches.

These tests are the ones most likely to FAIL without skills loaded.
"""

import pytest


# ============================================================================
# 1. INFRASTRUCTURE TESTS — Container Configuration
# ============================================================================

class TestContainerPartitionKeys:
    """
    Rules: partition-high-cardinality, partition-query-patterns

    IoT telemetry is primarily queried by device, so the telemetry
    container should use /deviceId as partition key. This aligns with
    the primary access pattern (device time-series) and has high cardinality.
    """

    def test_telemetry_container_uses_device_partition_key(self, cosmos_containers):
        """The telemetry container should partition on deviceId."""
        telemetry_containers = [
            c for c in cosmos_containers
            if any(kw in c["id"].lower()
                   for kw in ("telemetry", "reading", "metric", "data", "event"))
        ]
        if not telemetry_containers:
            telemetry_containers = cosmos_containers

        found_device_pk = False
        for c in telemetry_containers:
            paths = c.get("partitionKey", {}).get("paths", [])
            for path in paths:
                if "device" in path.lower():
                    found_device_pk = True
                    break

        assert found_device_pk, (
            "No container uses a deviceId-based partition key. "
            "For IoT telemetry, /deviceId is the natural partition key — "
            "it aligns with time-series queries per device and has high cardinality. "
            "(Rules: partition-high-cardinality, partition-query-patterns)"
        )

    def test_no_default_id_partition_key(self, cosmos_containers):
        """No container should use /id as its sole partition key."""
        for c in cosmos_containers:
            paths = c.get("partitionKey", {}).get("paths", [])
            assert paths != ["/id"], (
                f"Container '{c['id']}' uses /id as partition key — "
                f"this prevents efficient time-range queries per device. "
                f"(Rule: partition-high-cardinality)"
            )

    def test_device_metadata_separate_from_telemetry(self, cosmos_containers):
        """
        Device metadata (name, location, type) should be in a separate
        container from high-volume telemetry data, or clearly differentiated.
        """
        if len(cosmos_containers) >= 2:
            return  # Multiple containers — likely correct separation

        # Single container — check if it uses type discriminators
        for c in cosmos_containers:
            container_id = c["id"]
            if any(kw in container_id.lower() for kw in ("device", "metadata")):
                # Single container named "devices" — that's fine if telemetry is separate
                continue

        # Acceptable even with single container if types are discriminated
        pytest.skip(
            "Could not determine if device metadata is separated from telemetry. "
            "Using a single container is acceptable if documents have a type discriminator."
        )


class TestTelemetryIndexing:
    """
    Rule: index-exclude-unused, index-composite

    Telemetry data has known query patterns:
    - Time-range queries per device
    - Aggregations over specific fields
    Unused fields (like raw sensor arrays) should be excluded from indexing.
    """

    def test_has_custom_indexing_policy(self, cosmos_containers):
        """At least one container should have non-default indexing."""
        has_custom = False
        for c in cosmos_containers:
            policy = c.get("indexingPolicy", {})
            excluded = policy.get("excludedPaths", [])
            composites = policy.get("compositeIndexes", [])
            non_default = [
                p for p in excluded
                if p.get("path") not in ("/_etag/?", '"/_etag"/?', "/*")
            ]
            if non_default or composites:
                has_custom = True
                break

        assert has_custom, (
            "All containers use the default indexing policy. "
            "IoT telemetry has predictable query patterns — exclude unused paths "
            "and add composite indexes for (deviceId, timestamp) queries. "
            "(Rules: index-exclude-unused, index-composite)"
        )


class TestTTLConfiguration:
    """
    IoT telemetry data often has a retention period.
    Best practice: configure TTL to automatically expire old readings.
    """

    def test_telemetry_container_has_ttl_option(self, cosmos_containers):
        """
        The telemetry container should have TTL enabled (defaultTtl >= -1),
        even if individual documents set their own TTL.
        """
        telemetry_containers = [
            c for c in cosmos_containers
            if any(kw in c["id"].lower()
                   for kw in ("telemetry", "reading", "metric", "data", "event"))
        ]

        if not telemetry_containers:
            telemetry_containers = cosmos_containers

        for c in telemetry_containers:
            ttl = c.get("defaultTtl")
            if ttl is not None and ttl != 0:
                return  # TTL is configured

        # TTL not required but recommended — use a warning-level skip
        pytest.skip(
            "No container has TTL configured. For IoT telemetry, consider setting "
            "a TTL to automatically expire old readings and manage storage costs."
        )


class TestThroughputConfiguration:
    """Verify throughput is explicitly configured."""

    def test_throughput_is_configured(self, cosmos_database, cosmos_containers):
        """At least one container or the database should have throughput set."""
        has_throughput = False

        try:
            offer = cosmos_database.read_offer()
            if offer is not None:
                has_throughput = True
        except Exception:
            pass

        if not has_throughput:
            for c in cosmos_containers:
                try:
                    container = cosmos_database.get_container_client(c["id"])
                    offer = container.read_offer()
                    if offer is not None:
                        has_throughput = True
                        break
                except Exception:
                    pass

        assert has_throughput, (
            "No throughput configuration found. "
            "IoT workloads have variable ingestion rates — autoscale throughput is recommended. "
            "(Rule: throughput-autoscale)"
        )


# ============================================================================
# 2. SDK BEHAVIOR TESTS
# ============================================================================

class TestTelemetrySerialization:
    """
    Verify that telemetry data is stored with correct types in Cosmos DB.
    Numeric sensor values must be numbers (not strings) for aggregation queries.
    Timestamps must be strings for range queries with ORDER BY.
    """

    def test_sensor_values_stored_as_numbers(self, api, seeded_data, cosmos_database, cosmos_containers):
        """Temperature, humidity, battery values should be numeric, not strings."""
        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT TOP 3 * FROM c WHERE IS_DEFINED(c.temperature) OR IS_DEFINED(c.humidity)",
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            for doc in items:
                for field in ("temperature", "humidity", "batteryLevel", "battery_level"):
                    value = doc.get(field)
                    if value is not None:
                        assert isinstance(value, (int, float)), (
                            f"Sensor field '{field}' stored as {type(value).__name__} "
                            f"({value!r}). Must be a number for AVG/MIN/MAX aggregations. "
                            f"String values break aggregation queries."
                        )
                return  # Found telemetry docs

        pytest.skip("Could not find telemetry documents in Cosmos DB")

    def test_timestamps_stored_as_iso_strings(self, api, seeded_data, cosmos_database, cosmos_containers):
        """Timestamps should be ISO 8601 strings for correct sorting."""
        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT TOP 3 * FROM c WHERE IS_DEFINED(c.timestamp) OR IS_DEFINED(c.createdAt)",
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            for doc in items:
                for field in ("timestamp", "createdAt", "created_at", "readingTime", "eventTime"):
                    ts = doc.get(field)
                    if ts is not None:
                        assert isinstance(ts, str), (
                            f"Timestamp '{field}' stored as {type(ts).__name__} ({ts!r}). "
                            f"Store as ISO 8601 string for correct ORDER BY sorting. "
                            f"Epoch integers sort correctly but are not human-readable."
                        )
                        return

        pytest.skip("Could not find timestamp field in stored documents")


class TestDocumentStructure:
    """Verify document modeling best practices."""

    def test_documents_have_type_discriminator(self, api, seeded_data, cosmos_database, cosmos_containers):
        """Documents should have a 'type' field for polymorphic containers."""
        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT TOP 3 * FROM c",
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            for doc in items:
                if any(field in doc for field in ("type", "_type", "documentType", "entityType")):
                    return

        pytest.fail(
            "No documents have a type discriminator field. "
            "Use a 'type' field (e.g., 'device', 'telemetry', 'alert') "
            "to distinguish document types. "
            "(Rule: model-type-discriminator)"
        )

    def test_documents_have_schema_version(self, api, seeded_data, cosmos_database, cosmos_containers):
        """Documents should include a schema version for future evolution."""
        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT TOP 3 * FROM c",
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            for doc in items:
                if any(field in doc for field in ("schemaVersion", "schema_version", "_version", "docVersion")):
                    return

        pytest.fail(
            "No documents have a schema version field. "
            "(Rule: model-schema-versioning)"
        )


# ============================================================================
# 3. CROSS-BOUNDARY TESTS — API ↔ Cosmos DB Round-Trip
# ============================================================================

class TestCrossBoundaryConsistency:
    """
    Write through the API, read directly from Cosmos DB to catch
    serialization mismatches invisible to round-trip HTTP tests.
    """

    def test_telemetry_stored_with_all_fields(self, api, seeded_data, cosmos_database, cosmos_containers):
        """
        Verify that a telemetry reading sent via the API has all expected
        fields stored in Cosmos DB (temperature, humidity, batteryLevel, timestamp).
        """
        reading = seeded_data["readings"][0]
        device_id = reading.get("deviceId")

        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT * FROM c WHERE c.deviceId = @did",
                    parameters=[{"name": "@did", "value": device_id}],
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            # Look for telemetry documents (have temperature field)
            for doc in items:
                if doc.get("temperature") is not None or doc.get("humidity") is not None:
                    # Found a telemetry doc — verify key fields are present
                    has_device = doc.get("deviceId") == device_id
                    has_temp = doc.get("temperature") is not None
                    has_timestamp = any(
                        doc.get(f) is not None
                        for f in ("timestamp", "createdAt", "readingTime")
                    )

                    assert has_device, "Telemetry doc missing deviceId"
                    assert has_temp, "Telemetry doc missing temperature"
                    assert has_timestamp, "Telemetry doc missing timestamp"
                    return

        pytest.skip("Could not find telemetry documents in Cosmos DB")

    def test_device_metadata_stored_correctly(self, api, seeded_data, cosmos_database, cosmos_containers):
        """
        Verify device metadata (name, location, deviceType) is persisted.
        """
        device = seeded_data["devices"][0]
        device_id = device.get("deviceId")

        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT * FROM c WHERE c.deviceId = @did",
                    parameters=[{"name": "@did", "value": device_id}],
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            for doc in items:
                # Look for the device registration record (has name/location)
                doc_name = doc.get("name") or doc.get("deviceName")
                doc_location = doc.get("location") or doc.get("facility")
                if doc_name is not None and doc_location is not None:
                    assert doc_name == device.get("name"), (
                        f"Stored name ({doc_name!r}) != API name ({device.get('name')!r})"
                    )
                    assert doc_location == device.get("location"), (
                        f"Stored location ({doc_location!r}) != API location ({device.get('location')!r})"
                    )
                    return

        pytest.skip("Could not find device metadata document in Cosmos DB")

    def test_aggregation_values_match_raw_data(self, api, seeded_data, cosmos_database, cosmos_containers):
        """
        If the API returns aggregated values (avg temp, min/max), verify
        them against raw telemetry stored in Cosmos DB.
        """
        # Get aggregation from API
        resp = api.request("GET", "/api/telemetry/device-001/summary",
                           params={"hours": 24})
        if resp.status_code != 200:
            pytest.skip("Summary endpoint not available or returned non-200")

        api_summary = resp.json()
        api_avg_temp = api_summary.get("avgTemperature") or api_summary.get("averageTemperature")
        if api_avg_temp is None:
            pytest.skip("API summary doesn't include avgTemperature")

        # Calculate from raw Cosmos DB telemetry
        temps = []
        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT c.temperature FROM c WHERE c.deviceId = 'device-001' AND IS_DEFINED(c.temperature)",
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            for doc in items:
                t = doc.get("temperature")
                if isinstance(t, (int, float)):
                    temps.append(t)

        if not temps:
            pytest.skip("Could not find raw telemetry for device-001")

        cosmos_avg = sum(temps) / len(temps)
        assert abs(float(api_avg_temp) - cosmos_avg) < 0.1, (
            f"API average temperature ({api_avg_temp}) doesn't match "
            f"Cosmos DB raw data average ({cosmos_avg:.2f}). "
            f"The aggregation may be computed incorrectly or from stale data."
        )
