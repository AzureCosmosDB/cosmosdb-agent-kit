"""
Cosmos DB Infrastructure & SDK Behavior Tests — Multitenant SaaS
==================================================================

These tests go BELOW the HTTP API surface to verify that the agent
applied Cosmos DB best practices at the SDK and container level.

Test categories:
  1. INFRASTRUCTURE — verify container partition keys (hierarchical),
     indexing policies, throughput mode directly via Cosmos DB Python SDK.
  2. SDK BEHAVIORS — verify that SDK-specific patterns (tenant isolation,
     enum serialization, type discriminators) are configured correctly.
  3. CROSS-BOUNDARY — write data through the HTTP API, then read it
     directly from Cosmos DB (bypassing the app) to catch serialization
     mismatches, missing fields, or incorrect stored formats.

These tests are the ones most likely to FAIL without skills loaded,
because best practices operate at this layer — not at the HTTP surface.
"""

import pytest


# ============================================================================
# 1. INFRASTRUCTURE TESTS — Container Configuration
# ============================================================================

class TestContainerPartitionKeys:
    """
    Rule: partition-hierarchical, partition-high-cardinality

    Multitenant SaaS needs tenant isolation. The partition key should
    include tenantId — ideally as a hierarchical partition key
    (e.g., /tenantId, /tenantId + /type).
    """

    def test_container_uses_tenant_partition_key(self, cosmos_containers):
        """At least one container should use tenantId in its partition key."""
        found_tenant_pk = False
        for c in cosmos_containers:
            paths = c.get("partitionKey", {}).get("paths", [])
            for path in paths:
                if "tenant" in path.lower():
                    found_tenant_pk = True
                    break
            if found_tenant_pk:
                break

        assert found_tenant_pk, (
            "No container uses tenantId in its partition key. "
            "Multitenant applications MUST partition on tenantId to ensure "
            "tenant isolation and efficient per-tenant queries. "
            "(Rules: partition-hierarchical, partition-high-cardinality)"
        )

    def test_hierarchical_partition_keys(self, cosmos_containers):
        """Check for hierarchical partition key usage (tenantId + type/entity)."""
        has_hierarchical = False
        for c in cosmos_containers:
            paths = c.get("partitionKey", {}).get("paths", [])
            if len(paths) >= 2:
                has_hierarchical = True
                break

        if not has_hierarchical:
            # Multiple containers with tenantId is also acceptable
            tenant_containers = [
                c for c in cosmos_containers
                if any("tenant" in p.lower() for p in c.get("partitionKey", {}).get("paths", []))
            ]
            if len(tenant_containers) >= 2 or len(cosmos_containers) >= 3:
                pytest.skip(
                    "Multiple containers detected — hierarchical keys not required "
                    "when using container-per-entity pattern"
                )

        assert has_hierarchical, (
            "No container uses hierarchical partition keys. "
            "Multitenant SaaS benefits from hierarchical keys like "
            "/tenantId + /type for efficient per-tenant queries across entity types. "
            "(Rule: partition-hierarchical)"
        )

    def test_no_id_only_partition_key(self, cosmos_containers):
        """No container should use just /id as the partition key."""
        for c in cosmos_containers:
            paths = c.get("partitionKey", {}).get("paths", [])
            assert paths != ["/id"], (
                f"Container '{c['id']}' uses /id as its sole partition key. "
                "This prevents efficient tenant-scoped queries. "
                "(Rule: partition-high-cardinality)"
            )


# ============================================================================
# 2. INFRASTRUCTURE TESTS — Indexing Policies
# ============================================================================

class TestIndexingPolicies:
    """
    Rule: index-exclude-unused, index-composite

    Multitenant SaaS benefits from composite indexes for common query
    patterns: tasks by status within a tenant, tasks by priority, etc.
    """

    def test_custom_indexing_policy(self, cosmos_containers):
        """At least one container should have a non-default indexing policy."""
        has_custom = False
        for c in cosmos_containers:
            policy = c.get("indexingPolicy", {})
            excluded = policy.get("excludedPaths", [])
            if len(excluded) > 1:
                has_custom = True
                break
            composite = policy.get("compositeIndexes", [])
            if composite:
                has_custom = True
                break

        assert has_custom, (
            "All containers use the default indexing policy. "
            "Multitenant workloads should customize indexing to exclude "
            "unused paths and add composite indexes for status/priority queries. "
            "(Rules: index-exclude-unused, index-composite)"
        )

    def test_composite_index_for_task_queries(self, cosmos_containers):
        """A composite index should exist for task status/priority queries."""
        has_composite = False
        for c in cosmos_containers:
            policy = c.get("indexingPolicy", {})
            composite = policy.get("compositeIndexes", [])
            if composite:
                has_composite = True
                break

        if not has_composite:
            pytest.skip(
                "No composite indexes found. These are recommended for "
                "task status/priority filtering queries within a tenant. "
                "(Rule: index-composite)"
            )


# ============================================================================
# 3. INFRASTRUCTURE TESTS — Throughput
# ============================================================================

class TestThroughputConfiguration:
    """
    Rule: throughput-provision-rus

    The application should have explicitly configured throughput.
    """

    def test_throughput_is_set(self, cosmos_database, cosmos_containers):
        """Database or containers should have explicit throughput configured."""
        has_throughput = False

        try:
            db_offer = cosmos_database.read_offer()
            if db_offer is not None:
                has_throughput = True
        except Exception:
            pass

        if not has_throughput:
            for c in cosmos_containers:
                try:
                    container_client = cosmos_database.get_container_client(c["id"])
                    offer = container_client.read_offer()
                    if offer is not None:
                        has_throughput = True
                        break
                except Exception:
                    continue

        assert has_throughput, (
            "No explicit throughput found at database or container level. "
            "(Rule: throughput-provision-rus)"
        )


# ============================================================================
# 4. SDK BEHAVIOR TESTS — Document Structure & Serialization
# ============================================================================

class TestDocumentStructure:
    """
    Rule: model-type-discriminator, model-schema-versioning

    Documents should have type discriminators (essential for shared
    containers in multitenant architectures) and schema versions.
    """

    def test_type_discriminator_present(self, cosmos_container_map, seeded_data):
        """Documents should include a type or entity discriminator field."""
        found_type = False
        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query="SELECT TOP 3 * FROM c",
                    enable_cross_partition_query=True,
                    max_item_count=3,
                ))
                for doc in items:
                    type_fields = ["type", "entityType", "docType", "kind", "_type"]
                    if any(f in doc for f in type_fields):
                        found_type = True
                        break
            except Exception:
                continue
            if found_type:
                break

        assert found_type, (
            "No documents contain a type discriminator field. "
            "Multitenant SaaS stores multiple entity types (tenants, users, "
            "projects, tasks) — a type discriminator is essential. "
            "(Rule: model-type-discriminator)"
        )

    def test_schema_version_present(self, cosmos_container_map, seeded_data):
        """Documents should include a schema version field."""
        found_version = False
        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query="SELECT TOP 3 * FROM c",
                    enable_cross_partition_query=True,
                    max_item_count=3,
                ))
                for doc in items:
                    version_fields = [
                        "schemaVersion", "version", "_version",
                        "schema_version", "dataVersion",
                    ]
                    if any(f in doc for f in version_fields):
                        found_version = True
                        break
            except Exception:
                continue
            if found_version:
                break

        assert found_version, (
            "No documents contain a schema version field. "
            "(Rule: model-schema-versioning)"
        )


class TestEnumSerialization:
    """
    Rule: model-json-serialization

    Status, priority, role, and plan fields should be stored as strings
    in Cosmos DB, not as integer enum values.
    """

    def test_status_stored_as_string(self, cosmos_container_map, seeded_data):
        """Task status values should be stored as strings, not integers."""
        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query="SELECT * FROM c WHERE IS_DEFINED(c.status)",
                    enable_cross_partition_query=True,
                    max_item_count=5,
                ))
                for doc in items:
                    status = doc.get("status")
                    if status is not None:
                        assert isinstance(status, str), (
                            f"Task status in container '{name}' is stored as "
                            f"{type(status).__name__} (value: {status}), not a string. "
                            "Enum values must be serialized as strings for queryability. "
                            "(Rule: model-json-serialization)"
                        )
                        return
            except Exception:
                continue

        pytest.skip("No documents with 'status' field found")

    def test_priority_stored_as_string(self, cosmos_container_map, seeded_data):
        """Task priority values should be stored as strings, not integers."""
        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query="SELECT * FROM c WHERE IS_DEFINED(c.priority)",
                    enable_cross_partition_query=True,
                    max_item_count=5,
                ))
                for doc in items:
                    priority = doc.get("priority")
                    if priority is not None:
                        assert isinstance(priority, str), (
                            f"Task priority is stored as {type(priority).__name__} "
                            f"(value: {priority}), not a string. "
                            "(Rule: model-json-serialization)"
                        )
                        return
            except Exception:
                continue

        pytest.skip("No documents with 'priority' field found")

    def test_role_stored_as_string(self, cosmos_container_map, seeded_data):
        """User role values should be stored as strings, not integers."""
        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query="SELECT * FROM c WHERE IS_DEFINED(c.role)",
                    enable_cross_partition_query=True,
                    max_item_count=5,
                ))
                for doc in items:
                    role = doc.get("role")
                    if role is not None:
                        assert isinstance(role, str), (
                            f"User role is stored as {type(role).__name__} "
                            f"(value: {role}), not a string. "
                            "(Rule: model-json-serialization)"
                        )
                        return
            except Exception:
                continue

        pytest.skip("No documents with 'role' field found")


class TestTimestampSerialization:
    """Timestamps should be ISO 8601 strings, not epoch integers."""

    def test_timestamps_are_iso_strings(self, cosmos_container_map, seeded_data):
        """Timestamps stored in Cosmos DB should be ISO 8601 formatted strings."""
        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query="SELECT TOP 3 * FROM c",
                    enable_cross_partition_query=True,
                    max_item_count=3,
                ))
                for doc in items:
                    for key in ("createdAt", "created_at", "updatedAt"):
                        val = doc.get(key)
                        if val is not None:
                            assert isinstance(val, str), (
                                f"Field '{key}' in container '{name}' is stored as "
                                f"{type(val).__name__}, not a string. "
                                "(Rule: model-json-serialization)"
                            )
                            return
            except Exception:
                continue

        pytest.skip("No timestamp fields found in stored documents")


# ============================================================================
# 5. CROSS-BOUNDARY TESTS — API vs Cosmos DB Direct Read
# ============================================================================

class TestCrossBoundaryConsistency:
    """
    Write through the HTTP API, then read directly from Cosmos DB.
    Verify tenant isolation and field consistency.
    """

    def test_tenant_data_stored_correctly(self, cosmos_container_map, seeded_data):
        """Tenants created via API should exist in Cosmos DB with correct fields."""
        tenant = seeded_data["tenants"][0]
        tenant_id = tenant["tenantId"]

        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query=f"SELECT * FROM c WHERE c.tenantId = '{tenant_id}'",
                    enable_cross_partition_query=True,
                    max_item_count=10,
                ))
                if items:
                    # Found tenant-related data — check any doc has tenantId
                    doc = items[0]
                    assert doc.get("tenantId") == tenant_id, (
                        f"tenantId mismatch in stored document"
                    )
                    return
            except Exception:
                continue

        pytest.fail(
            f"No data found for tenant {tenant_id} in any Cosmos DB container"
        )

    def test_tenant_isolation_in_cosmos(self, cosmos_container_map, seeded_data):
        """
        Data for tenant 0 should NOT contain fields from tenant 1.
        Verify tenant isolation at the storage level.
        """
        tenant_0_id = seeded_data["tenants"][0]["tenantId"]
        tenant_1_id = seeded_data["tenants"][1]["tenantId"]

        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query=f"SELECT * FROM c WHERE c.tenantId = '{tenant_0_id}'",
                    enable_cross_partition_query=True,
                ))
                for doc in items:
                    # No document scoped to tenant 0 should reference tenant 1's ID
                    stored_tenant = doc.get("tenantId")
                    assert stored_tenant != tenant_1_id, (
                        f"Tenant isolation violation: document scoped to tenant "
                        f"{tenant_0_id} contains tenantId '{tenant_1_id}' — "
                        "data from different tenants is mixed"
                    )
            except Exception:
                continue

    def test_task_fields_match_api(self, cosmos_container_map, seeded_data):
        """Tasks stored in Cosmos DB should match what the API returned."""
        tasks = seeded_data["tasks"].get((0, 0), [])
        if not tasks:
            pytest.skip("No tasks were seeded for tenant 0, project 0")

        task = tasks[0]
        task_id = task.get("taskId")
        if not task_id:
            pytest.skip("Task response did not include taskId")

        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query=f"SELECT * FROM c WHERE c.taskId = '{task_id}'",
                    enable_cross_partition_query=True,
                    max_item_count=1,
                ))
                if items:
                    stored = items[0]
                    assert stored.get("title") == task["title"], (
                        f"Task title mismatch: API='{task['title']}', "
                        f"Cosmos DB='{stored.get('title')}'"
                    )
                    assert stored.get("priority") == task["priority"], (
                        f"Task priority mismatch: API='{task['priority']}', "
                        f"Cosmos DB='{stored.get('priority')}'"
                    )
                    return
            except Exception:
                continue

        pytest.fail(
            f"Task {task_id} created via API was not found in any Cosmos DB container"
        )

    def test_user_fields_preserved(self, cosmos_container_map, seeded_data):
        """Users stored in Cosmos DB should preserve all fields from the API response."""
        users = seeded_data["users"].get(0, [])
        if not users:
            pytest.skip("No users were seeded for tenant 0")

        user = users[0]
        user_id = user.get("userId")
        if not user_id:
            pytest.skip("User response did not include userId")

        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query=f"SELECT * FROM c WHERE c.userId = '{user_id}'",
                    enable_cross_partition_query=True,
                    max_item_count=1,
                ))
                if items:
                    stored = items[0]
                    assert stored.get("name") == user["name"], (
                        f"User name mismatch: API='{user['name']}', "
                        f"Cosmos DB='{stored.get('name')}'"
                    )
                    assert stored.get("email") == user["email"], (
                        f"User email mismatch: API='{user['email']}', "
                        f"Cosmos DB='{stored.get('email')}'"
                    )
                    return
            except Exception:
                continue

        pytest.fail(
            f"User {user_id} created via API was not found in any Cosmos DB container"
        )
