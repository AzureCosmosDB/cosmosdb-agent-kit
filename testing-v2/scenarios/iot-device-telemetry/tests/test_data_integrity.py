"""
Data Integrity Tests for IoT Device Telemetry
===============================================

These tests verify that the application correctly persists data to
Cosmos DB and uses appropriate patterns for time-series data.
"""

import pytest


class TestDataPersistence:
    """Verify data is actually persisted in Cosmos DB."""

    def test_containers_exist_in_cosmos(self, api, seeded_data, cosmos_database):
        """After ingesting telemetry, containers should exist."""
        containers = list(cosmos_database.list_containers())
        assert len(containers) > 0, (
            "No containers found in the database. "
            "The app should create containers for device and telemetry data."
        )

    def test_database_is_created(self, cosmos_database):
        """The app should create its database on startup."""
        props = cosmos_database.read()
        assert props is not None, "Database should be readable"


class TestPartitionKeyDesign:
    """
    Verify partition key decisions are correct for time-series data.

    For IoT telemetry:
    - Using timestamp alone as PK is an anti-pattern (hot partition)
    - deviceId is a natural partition key for telemetry data
    - /id as PK prevents efficient per-device queries
    """

    def test_containers_have_partition_keys(self, cosmos_database):
        """Every container should have a partition key defined."""
        containers = list(cosmos_database.list_containers())
        for container_props in containers:
            pk = container_props.get("partitionKey", {})
            paths = pk.get("paths", [])
            assert len(paths) > 0, (
                f"Container '{container_props['id']}' has no partition key. "
                f"Every Cosmos DB container must have a partition key."
            )

    def test_no_container_uses_id_as_sole_partition_key(self, cosmos_database):
        """
        Using /id as partition key is an anti-pattern for IoT data.
        For telemetry, /deviceId enables efficient per-device queries.
        """
        containers = list(cosmos_database.list_containers())
        for container_props in containers:
            pk = container_props.get("partitionKey", {})
            paths = pk.get("paths", [])
            if paths == ["/id"]:
                pytest.fail(
                    f"Container '{container_props['id']}' uses /id as partition key. "
                    f"This is an anti-pattern for IoT — consider /deviceId for "
                    f"efficient per-device time-series queries. "
                    f"(Rule: partition-high-cardinality, partition-avoid-hotspots)"
                )


class TestTTLConfiguration:
    """
    Verify TTL is configured for data retention.

    The scenario requires 30-day automatic data expiration.
    """

    def test_at_least_one_container_has_ttl(self, cosmos_database):
        """
        At least one container (telemetry) should have TTL enabled
        for the 30-day data retention requirement.
        """
        containers = list(cosmos_database.list_containers())
        has_ttl = False
        for container_props in containers:
            ttl = container_props.get("defaultTtl")
            if ttl is not None and ttl > 0:
                has_ttl = True
                break
        assert has_ttl, (
            "No container has TTL (defaultTtl) configured. "
            "The scenario requires 30-day data retention — telemetry "
            "containers should have defaultTtl set to ~2592000 (30 days). "
            "(Rule: Use TTL for time-series data expiration)"
        )


class TestIndexingPolicy:
    """
    Verify indexing for efficient time-series queries.

    IoT telemetry needs:
    - Efficient ORDER BY timestamp queries (for latest reading)
    - Efficient range queries on timestamp (for time-range queries)
    """

    def test_containers_have_indexing_policy(self, cosmos_database):
        """Every container should have an indexing policy."""
        containers = list(cosmos_database.list_containers())
        for container_props in containers:
            policy = container_props.get("indexingPolicy")
            assert policy is not None, (
                f"Container '{container_props['id']}' has no indexing policy. "
                f"Cosmos DB containers should have explicit indexing policies."
            )
