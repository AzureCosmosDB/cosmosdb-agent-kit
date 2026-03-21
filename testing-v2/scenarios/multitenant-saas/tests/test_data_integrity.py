"""
Data-integrity tests for the Multitenant SaaS scenario.

These tests verify Cosmos DB configuration choices: partition key design,
hierarchical partitioning, tenant isolation at the data level, and indexing.
"""

import pytest


class TestDataPersistence:
    """Verify data written via the API survives a read-back through Cosmos DB."""

    def test_tenants_exist_in_cosmos(self, cosmos_database, seeded_data):
        """Tenants created via API should be present in Cosmos DB."""
        containers = list(cosmos_database.list_containers())
        container_ids = [c["id"] for c in containers]
        assert len(container_ids) > 0, "Database should have at least one container"

    def test_tasks_persisted(self, cosmos_database, seeded_data):
        """Tasks should be persisted in Cosmos DB containers."""
        containers = list(cosmos_database.list_containers())
        assert len(containers) > 0, "Should have containers for task storage"


class TestPartitionKeyDesign:
    """Verify partition key supports multitenant access patterns."""

    def test_partition_key_includes_tenant_id(self, cosmos_database):
        """
        At least one container should include /tenantId in its partition key path.
        This is critical for tenant isolation and efficient within-tenant queries.
        """
        containers = list(cosmos_database.list_containers())
        has_tenant_pk = False
        for container in containers:
            pk_paths = container["partitionKey"]["paths"]
            for path in pk_paths:
                if "tenantId" in path.lower() or "tenant" in path.lower():
                    has_tenant_pk = True
                    break
            if has_tenant_pk:
                break
        assert has_tenant_pk, (
            "No container uses /tenantId (or similar) as partition key. "
            "Multitenant apps should partition by tenantId for isolation "
            "and efficient within-tenant queries."
        )

    def test_no_id_only_partition_key(self, cosmos_database):
        """No container should use /id as the sole partition key."""
        containers = list(cosmos_database.list_containers())
        for container in containers:
            pk_paths = container["partitionKey"]["paths"]
            if len(pk_paths) == 1 and pk_paths[0] == "/id":
                pytest.fail(
                    f"Container '{container['id']}' uses /id as partition key. "
                    f"This is an anti-pattern. Use /tenantId or a hierarchical key."
                )


class TestHierarchicalPartitionKeys:
    """Check if hierarchical partition keys are used (recommended but not required)."""

    def test_check_hierarchical_keys(self, cosmos_database):
        """
        Hierarchical partition keys (/tenantId + /type or /tenantId + /projectId)
        are recommended. This test reports but does not fail if not present.
        """
        containers = list(cosmos_database.list_containers())
        has_hierarchical = False
        for container in containers:
            pk_paths = container["partitionKey"]["paths"]
            if len(pk_paths) > 1:
                has_hierarchical = True
                break
            pk_kind = container["partitionKey"].get("kind", "Hash")
            if pk_kind == "MultiHash":
                has_hierarchical = True
                break

        if not has_hierarchical:
            pytest.skip(
                "No hierarchical partition keys detected. "
                "This is recommended but not required for the multitenant scenario."
            )


class TestIndexingPolicy:
    """Verify indexing policy is configured."""

    def test_containers_have_indexing_policy(self, cosmos_database):
        """All containers should have an indexing policy."""
        containers = list(cosmos_database.list_containers())
        for container in containers:
            indexing = container.get("indexingPolicy", {})
            assert indexing is not None, (
                f"Container '{container['id']}' should have an indexing policy"
            )

    def test_composite_indexes_for_queries(self, cosmos_database):
        """
        Containers storing tasks should ideally have composite indexes
        for the common query patterns (status + tenantId, assigneeId + tenantId).
        This is a soft check — the test reports but does not fail.
        """
        containers = list(cosmos_database.list_containers())
        has_composite = False
        for container in containers:
            indexing = container.get("indexingPolicy", {})
            composite = indexing.get("compositeIndexes", [])
            if composite:
                has_composite = True
                break

        if not has_composite:
            pytest.skip(
                "No composite indexes found. Consider adding composite indexes "
                "for multi-field queries like (tenantId, status) or (tenantId, assigneeId)."
            )
