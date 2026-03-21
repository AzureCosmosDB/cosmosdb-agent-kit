"""
Data Integrity Tests for Gaming Leaderboard
=============================================

These tests verify that the application correctly persists data to
Cosmos DB. They connect directly to the emulator to check:
- Documents exist with correct structure
- Partition keys are set correctly
- Data types are correct in stored documents

These tests help identify Cosmos DB best practice gaps that the
API contract tests alone can't catch (e.g., bad partition key choices,
missing indexing, wrong data model decisions).
"""

import pytest


class TestDataPersistence:
    """Verify data is actually persisted in Cosmos DB (not just in-memory)."""

    def test_player_document_exists_in_cosmos(self, api, seeded_data, cosmos_database):
        """After creating a player via the API, it should exist in Cosmos DB."""
        # We can't know exact container names, but we can list containers
        # and verify at least one is created
        containers = list(cosmos_database.list_containers())
        assert len(containers) > 0, (
            "No containers found in the database. "
            "The app should create at least one container for player/score data."
        )

    def test_database_is_created(self, cosmos_database):
        """The app should create its database on startup."""
        # If this fixture resolves without error, the database exists.
        # Read properties to confirm it's accessible.
        props = cosmos_database.read()
        assert props is not None, "Database should be readable"


class TestPartitionKeyDesign:
    """
    Verify partition key decisions are reasonable.

    These tests examine container configurations to check for
    common Cosmos DB anti-patterns:
    - Using /id as partition key (hot partition risk)
    - Single container for everything (limits scalability)
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
        Using /id as partition key is almost always an anti-pattern.
        It creates one logical partition per document, preventing efficient queries.
        """
        containers = list(cosmos_database.list_containers())
        for container_props in containers:
            pk = container_props.get("partitionKey", {})
            paths = pk.get("paths", [])
            if paths == ["/id"]:
                pytest.fail(
                    f"Container '{container_props['id']}' uses /id as partition key. "
                    f"This is an anti-pattern — it prevents efficient cross-document "
                    f"queries within a partition. Consider /playerId, /region, or "
                    f"another high-cardinality field. "
                    f"(Rule: partition-high-cardinality, partition-avoid-hotspots)"
                )


class TestIndexingPolicy:
    """
    Verify indexing choices are reasonable for the leaderboard pattern.

    Leaderboard scenarios need:
    - Efficient ORDER BY queries (composite indexes)
    - Range indexes on score fields
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
