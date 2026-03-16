"""
Cosmos DB Infrastructure & SDK Behavior Tests — AI Chat RAG
=============================================================

These tests go BELOW the HTTP API surface to verify that the agent
applied Cosmos DB best practices at the SDK and container level.

Test categories:
  1. INFRASTRUCTURE — verify container partition keys, indexing policies,
     vector indexing, throughput mode directly via Cosmos DB Python SDK.
  2. SDK BEHAVIORS — verify that SDK-specific patterns (embedding storage,
     document structure, metadata handling) are configured correctly.
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
    Rule: partition-high-cardinality, partition-query-patterns

    Sessions are queried by userId, so the sessions container should
    partition on userId. Documents may use a separate container with
    a different key (e.g., category or documentId).
    """

    def test_session_container_uses_user_partition_key(self, cosmos_containers):
        """The sessions container should partition on userId."""
        session_containers = [
            c for c in cosmos_containers
            if any(kw in c["id"].lower() for kw in ("session", "chat", "conversation"))
        ]
        if not session_containers:
            session_containers = cosmos_containers

        found_user_pk = False
        for c in session_containers:
            paths = c.get("partitionKey", {}).get("paths", [])
            for path in paths:
                if "user" in path.lower() or "session" in path.lower():
                    found_user_pk = True
                    break

        assert found_user_pk, (
            "No container uses a userId-based or sessionId-based partition key. "
            "Chat sessions are primarily queried by user, so /userId is the "
            "natural partition key choice. "
            "(Rules: partition-high-cardinality, partition-query-patterns)"
        )

    def test_no_id_only_partition_key(self, cosmos_containers):
        """No container should use just /id as the partition key."""
        for c in cosmos_containers:
            paths = c.get("partitionKey", {}).get("paths", [])
            assert paths != ["/id"], (
                f"Container '{c['id']}' uses /id as its sole partition key. "
                "This creates a 1:1 mapping between partition key and item, "
                "preventing efficient queries. "
                "(Rule: partition-high-cardinality)"
            )

    def test_separate_containers_for_sessions_and_documents(self, cosmos_containers):
        """Sessions and documents should use separate containers or a type discriminator."""
        container_names = [c["id"].lower() for c in cosmos_containers]
        has_session_container = any(
            kw in name for name in container_names
            for kw in ("session", "chat", "conversation")
        )
        has_document_container = any(
            kw in name for name in container_names
            for kw in ("document", "chunk", "knowledge", "embedding", "vector")
        )

        if len(cosmos_containers) == 1:
            # Single container — check for type discriminator via partition key
            # or hierarchical keys. This is acceptable but less ideal.
            pytest.skip(
                "Single container design detected — verify type discrimination manually"
            )

        assert has_session_container or has_document_container, (
            "Expected to find containers with names indicating session/chat "
            "or document/embedding data. Container separation or clear naming "
            "helps organize different entity types. "
            "(Rule: model-type-discriminator)"
        )


# ============================================================================
# 2. INFRASTRUCTURE TESTS — Indexing Policies
# ============================================================================

class TestIndexingPolicies:
    """
    Rule: index-exclude-unused, index-composite

    RAG scenarios benefit from:
    - Vector indexing on the embedding field
    - Custom indexing (not the default index-everything policy)
    - Composite indexes for session queries (userId + createdAt)
    """

    def test_custom_indexing_policy(self, cosmos_containers):
        """At least one container should have a non-default indexing policy."""
        has_custom = False
        for c in cosmos_containers:
            policy = c.get("indexingPolicy", {})
            excluded = policy.get("excludedPaths", [])
            # Default policy has only {"path": "/_etag/?"} in excludedPaths
            if len(excluded) > 1:
                has_custom = True
                break
            composite = policy.get("compositeIndexes", [])
            if composite:
                has_custom = True
                break
            # Vector index policies
            vector_indexes = policy.get("vectorIndexes", [])
            if vector_indexes:
                has_custom = True
                break

        assert has_custom, (
            "All containers use the default indexing policy. "
            "RAG workloads should customize indexing: exclude unused paths, "
            "add vector indexes for embeddings, or add composite indexes "
            "for session listing queries. "
            "(Rules: index-exclude-unused, index-composite)"
        )


class TestVectorIndexing:
    """
    Rule: index-spatial (vector variant)

    RAG scenarios require vector indexing for similarity search.
    The documents container should have a vector index on the embedding field.
    """

    def test_vector_index_configured(self, cosmos_containers):
        """At least one container should have a vector indexing policy or vector embedding policy."""
        has_vector = False
        for c in cosmos_containers:
            policy = c.get("indexingPolicy", {})
            vector_indexes = policy.get("vectorIndexes", [])
            if vector_indexes:
                has_vector = True
                break
            # Also check for vector embedding policy (container-level property)
            vec_policy = c.get("vectorEmbeddingPolicy", {})
            if vec_policy and vec_policy.get("vectorEmbeddings"):
                has_vector = True
                break

        if not has_vector:
            pytest.skip(
                "No vector indexing policy found. This is expected if the app "
                "uses a non-native vector search approach (e.g., brute force or "
                "external search). For production, a vector index is recommended."
            )


# ============================================================================
# 3. INFRASTRUCTURE TESTS — Throughput
# ============================================================================

class TestThroughputConfiguration:
    """
    Rule: throughput-provision-rus

    The application should have explicitly configured throughput
    (either database-level or container-level).
    """

    def test_throughput_is_set(self, cosmos_database, cosmos_containers):
        """Database or containers should have explicit throughput configured."""
        has_throughput = False

        # Check database-level throughput
        try:
            db_offer = cosmos_database.read_offer()
            if db_offer is not None:
                has_throughput = True
        except Exception:
            pass

        # If no database throughput, check containers
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
            "Production workloads should configure throughput explicitly. "
            "(Rule: throughput-provision-rus)"
        )


# ============================================================================
# 4. SDK BEHAVIOR TESTS — Document Structure & Serialization
# ============================================================================

class TestDocumentStructure:
    """
    Rule: model-type-discriminator, model-schema-versioning

    Documents stored in Cosmos DB should have type discriminators
    (especially if sharing a container) and schema version fields.
    """

    def test_type_discriminator_present(self, cosmos_container_map, seeded_data):
        """Documents in Cosmos DB should include a type or entity discriminator field."""
        # Try to find any document and check for type field
        found_type = False
        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query="SELECT TOP 1 * FROM c",
                    enable_cross_partition_query=True,
                    max_item_count=1,
                ))
                if items:
                    doc = items[0]
                    type_fields = ["type", "entityType", "docType", "kind", "_type"]
                    if any(f in doc for f in type_fields):
                        found_type = True
                        break
            except Exception:
                continue

        assert found_type, (
            "No documents contain a type discriminator field (type, entityType, "
            "docType, kind). Type discriminators are essential for distinguishing "
            "entity types, especially in shared containers. "
            "(Rule: model-type-discriminator)"
        )

    def test_schema_version_present(self, cosmos_container_map, seeded_data):
        """Documents should include a schema version field for future migrations."""
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
            "No documents contain a schema version field. Schema versioning "
            "enables safe data model evolution without breaking existing data. "
            "(Rule: model-schema-versioning)"
        )


class TestEmbeddingStorage:
    """
    Rule: model-numeric-precision

    Vector embeddings should be stored as arrays of numbers (floats),
    not as strings or serialized JSON within a string field.
    """

    def test_embeddings_stored_as_arrays(self, cosmos_container_map, seeded_data):
        """Embeddings in Cosmos DB should be stored as number arrays, not strings."""
        # Look for documents with an embedding field
        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query="SELECT TOP 1 * FROM c WHERE IS_DEFINED(c.embedding)",
                    enable_cross_partition_query=True,
                    max_item_count=1,
                ))
                if items:
                    doc = items[0]
                    embedding = doc.get("embedding")
                    assert isinstance(embedding, list), (
                        f"Embedding in container '{name}' is stored as {type(embedding).__name__}, "
                        f"not as an array. Embeddings must be arrays of numbers. "
                        "(Rule: model-numeric-precision)"
                    )
                    if embedding:
                        assert isinstance(embedding[0], (int, float)), (
                            f"Embedding elements are {type(embedding[0]).__name__}, not numbers. "
                            "Each embedding dimension must be a numeric value. "
                            "(Rule: model-numeric-precision)"
                        )
                    return  # Found and verified
            except Exception:
                continue

        pytest.skip("No documents with 'embedding' field found in any container")


class TestTimestampSerialization:
    """
    Rule: model-json-serialization

    Timestamps should be stored as ISO 8601 strings, not epoch integers.
    """

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
                    for key in ("createdAt", "timestamp", "created_at", "updatedAt"):
                        val = doc.get(key)
                        if val is not None:
                            assert isinstance(val, str), (
                                f"Field '{key}' in container '{name}' is stored as "
                                f"{type(val).__name__}, not a string. Timestamps should "
                                "be ISO 8601 strings (e.g., '2024-01-01T00:00:00Z'). "
                                "(Rule: model-json-serialization)"
                            )
                            return  # Found and verified
            except Exception:
                continue

        pytest.skip("No timestamp fields found in stored documents")


# ============================================================================
# 5. CROSS-BOUNDARY TESTS — API vs Cosmos DB Direct Read
# ============================================================================

class TestCrossBoundaryConsistency:
    """
    Write through the HTTP API, then read directly from Cosmos DB.
    Mismatches indicate serialization bugs, missing fields, or wrong
    data formats that HTTP-only tests would never catch.
    """

    def test_session_stored_with_correct_fields(self, cosmos_container_map, seeded_data):
        """Sessions written via API should be stored with all required fields in Cosmos DB."""
        session = seeded_data["sessions"][0]
        session_id = session["sessionId"]

        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query=f"SELECT * FROM c WHERE c.sessionId = '{session_id}'",
                    enable_cross_partition_query=True,
                    max_item_count=1,
                ))
                if items:
                    doc = items[0]
                    assert doc.get("userId") == session["userId"], (
                        f"Session userId mismatch: API returned '{session['userId']}' "
                        f"but Cosmos DB has '{doc.get('userId')}'"
                    )
                    assert doc.get("title") == session["title"], (
                        f"Session title mismatch: API returned '{session['title']}' "
                        f"but Cosmos DB has '{doc.get('title')}'"
                    )
                    return
            except Exception:
                continue

        pytest.fail(
            f"Session {session_id} created via API was not found in any Cosmos DB container"
        )

    def test_document_stored_with_embedding(self, cosmos_container_map, seeded_data):
        """Documents written via API should have their embedding stored in Cosmos DB."""
        doc_ref = seeded_data["documents"][0]
        doc_id = doc_ref["documentId"]

        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query=f"SELECT * FROM c WHERE c.documentId = '{doc_id}'",
                    enable_cross_partition_query=True,
                    max_item_count=1,
                ))
                if items:
                    stored = items[0]
                    assert "embedding" in stored or "vector" in stored, (
                        f"Document {doc_id} in Cosmos DB is missing its embedding field. "
                        "The embedding must be persisted for vector search to work."
                    )
                    emb = stored.get("embedding") or stored.get("vector")
                    assert isinstance(emb, list) and len(emb) > 0, (
                        f"Document {doc_id} embedding is not a non-empty array"
                    )
                    return
            except Exception:
                continue

        pytest.fail(
            f"Document {doc_id} created via API was not found in any Cosmos DB container"
        )

    def test_document_metadata_preserved(self, cosmos_container_map, seeded_data):
        """Document metadata should be preserved in Cosmos DB storage."""
        doc_ref = seeded_data["documents"][0]
        doc_id = doc_ref["documentId"]

        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query=f"SELECT * FROM c WHERE c.documentId = '{doc_id}'",
                    enable_cross_partition_query=True,
                    max_item_count=1,
                ))
                if items:
                    stored = items[0]
                    metadata = stored.get("metadata")
                    if metadata is None:
                        # Metadata might be flattened to top-level fields
                        has_category = "category" in stored
                        has_source = "source" in stored
                        assert has_category or has_source, (
                            f"Document {doc_id} metadata is missing from Cosmos DB. "
                            "Expected category/source either nested or at top level."
                        )
                    else:
                        assert isinstance(metadata, dict), (
                            f"Document metadata is stored as {type(metadata).__name__}, "
                            "expected an object/dict"
                        )
                    return
            except Exception:
                continue

        pytest.fail(
            f"Document {doc_id} created via API was not found in any Cosmos DB container"
        )

    def test_messages_stored_with_session_reference(self, cosmos_container_map, seeded_data):
        """Messages should be stored with a reference to their session."""
        session_id = seeded_data["sessions"][0]["sessionId"]

        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query=f"SELECT * FROM c WHERE c.sessionId = '{session_id}' AND c.role = 'user'",
                    enable_cross_partition_query=True,
                    max_item_count=5,
                ))
                if items:
                    msg = items[0]
                    assert "content" in msg, (
                        "Message document is missing 'content' field in Cosmos DB"
                    )
                    assert msg.get("role") in ("user", "assistant"), (
                        f"Message role in Cosmos DB is '{msg.get('role')}', "
                        "expected 'user' or 'assistant'"
                    )
                    return
            except Exception:
                continue

        # Messages might be embedded within session documents
        for name, container in cosmos_container_map.items():
            try:
                items = list(container.query_items(
                    query=f"SELECT * FROM c WHERE c.sessionId = '{session_id}'",
                    enable_cross_partition_query=True,
                    max_item_count=1,
                ))
                if items:
                    doc = items[0]
                    messages = doc.get("messages", [])
                    if messages:
                        assert isinstance(messages, list), (
                            "Embedded messages should be an array"
                        )
                        return
            except Exception:
                continue

        pytest.fail(
            "Messages for session were not found — neither as separate documents "
            "nor embedded within the session document"
        )
