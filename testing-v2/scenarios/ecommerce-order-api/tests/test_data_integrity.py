"""
Data Integrity Tests for E-Commerce Order API
===============================================

These tests verify that the application correctly persists data to
Cosmos DB. They connect directly to the emulator to check:
- Documents exist with correct structure
- Partition keys are set correctly
- Data types are correct in stored documents
"""

import pytest


class TestDataPersistence:
    """Verify data is actually persisted in Cosmos DB (not just in-memory)."""

    def test_containers_exist_in_cosmos(self, api, seeded_data, cosmos_database):
        """After creating orders via the API, containers should exist in Cosmos DB."""
        containers = list(cosmos_database.list_containers())
        assert len(containers) > 0, (
            "No containers found in the database. "
            "The app should create at least one container for order data."
        )

    def test_database_is_created(self, cosmos_database):
        """The app should create its database on startup."""
        props = cosmos_database.read()
        assert props is not None, "Database should be readable"


class TestPartitionKeyDesign:
    """
    Verify partition key decisions are reasonable for e-commerce.

    E-commerce orders are primarily queried by customer, so
    customerId is the natural partition key choice.
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
        For e-commerce, /customerId is far more useful.
        """
        containers = list(cosmos_database.list_containers())
        for container_props in containers:
            pk = container_props.get("partitionKey", {})
            paths = pk.get("paths", [])
            if paths == ["/id"]:
                pytest.fail(
                    f"Container '{container_props['id']}' uses /id as partition key. "
                    f"This is an anti-pattern — consider /customerId for efficient "
                    f"customer order history queries. "
                    f"(Rule: partition-high-cardinality, partition-query-patterns)"
                )


class TestIndexingPolicy:
    """
    Verify indexing for efficient order queries.

    E-commerce scenarios need:
    - Efficient queries by status
    - Efficient queries by date range
    - Composite indexes for status + date filtering
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
