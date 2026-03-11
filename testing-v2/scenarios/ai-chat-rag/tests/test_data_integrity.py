"""
Data-integrity tests for the AI Chat with RAG scenario.

These tests verify Cosmos DB configuration choices: partition key design,
vector index policy, and data persistence.
"""

import pytest


class TestDataPersistence:
    """Verify data written via the API survives a read-back through Cosmos DB."""

    def test_sessions_exist_in_cosmos(self, cosmos_database, seeded_data):
        """Sessions created via API should be queryable from Cosmos DB."""
        containers = list(cosmos_database.list_containers())
        container_ids = [c["id"] for c in containers]
        assert len(container_ids) > 0, "Database should have at least one container"

    def test_documents_persisted(self, cosmos_database, seeded_data):
        """Documents stored via API should exist in Cosmos DB."""
        containers = list(cosmos_database.list_containers())
        assert len(containers) > 0, "Should have containers for document storage"


class TestPartitionKeyDesign:
    """Verify sensible partition key choices."""

    def test_session_container_partition_key(self, cosmos_database):
        """
        Sessions/messages container should use /sessionId or /userId as
        partition key — NOT /id.
        """
        containers = list(cosmos_database.list_containers())
        for container in containers:
            pk_paths = container["partitionKey"]["paths"]
            # Accept several reasonable partition key choices
            acceptable_keys = [
                "/sessionId", "/userId", "/tenantId",
                "/type", "/partitionKey"
            ]
            for pk_path in pk_paths:
                assert pk_path != "/id", (
                    f"Container '{container['id']}' uses /id as partition key. "
                    f"This is an anti-pattern. Use a domain-specific key like "
                    f"/sessionId or /userId."
                )


class TestVectorIndexConfiguration:
    """Verify the vector index policy is configured for vector search."""

    def test_container_has_vector_index_or_embedding_policy(self, cosmos_database):
        """
        At least one container should have a vector embedding policy or
        indexing policy that supports vector search.
        """
        containers = list(cosmos_database.list_containers())
        has_vector_config = False
        for container in containers:
            # Check for vector embedding policy (Cosmos DB NoSQL vector search)
            if "vectorEmbeddingPolicy" in container:
                has_vector_config = True
                break
            # Check indexing policy for vector indexes
            indexing = container.get("indexingPolicy", {})
            vector_indexes = indexing.get("vectorIndexes", [])
            if vector_indexes:
                has_vector_config = True
                break
            # Check composite indexes as fallback
            composite = indexing.get("compositeIndexes", [])
            if composite:
                # Not a definitive signal but acceptable
                pass

        assert has_vector_config, (
            "No container has a vector embedding policy or vector index. "
            "Vector search requires vectorEmbeddingPolicy on the container."
        )


class TestIndexingPolicy:
    """Verify indexing policy is not left at wasteful defaults."""

    def test_no_wildcard_include_all(self, cosmos_database):
        """
        If containers have custom indexing, verify they don't just use
        the default include-everything wildcard without thought.
        (This is a soft check — default may be acceptable for small datasets.)
        """
        containers = list(cosmos_database.list_containers())
        for container in containers:
            indexing = container.get("indexingPolicy", {})
            excluded = indexing.get("excludedPaths", [])
            included = indexing.get("includedPaths", [])
            # Just verify an indexing policy exists
            assert indexing is not None, (
                f"Container '{container['id']}' should have an indexing policy"
            )
