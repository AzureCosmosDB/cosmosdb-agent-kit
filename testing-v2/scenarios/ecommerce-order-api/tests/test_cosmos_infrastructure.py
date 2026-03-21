"""
Cosmos DB Infrastructure & SDK Behavior Tests — E-Commerce Order API
=====================================================================

These tests go BELOW the HTTP API surface to verify that the agent
applied Cosmos DB best practices at the SDK and container level.

Test categories:
  1. INFRASTRUCTURE — verify container partition keys, indexing policies,
     throughput mode, composite indexes directly via Cosmos DB Python SDK.
  2. SDK BEHAVIORS — verify that SDK-specific patterns (enum serialization,
     ETag headers, content-response-on-write) are configured correctly.
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

    E-commerce orders are primarily queried by customer, so the main
    container should use /customerId (or a path containing customerId).
    Using /id or a low-cardinality field is an anti-pattern.
    """

    def test_order_container_uses_customer_partition_key(self, cosmos_containers):
        """The primary orders container should partition on customerId."""
        order_containers = [
            c for c in cosmos_containers
            if any(kw in c["id"].lower() for kw in ("order", "ecommerce", "commerce"))
        ]
        if not order_containers:
            # If no container has "order" in its name, check all containers
            order_containers = cosmos_containers

        found_customer_pk = False
        for c in order_containers:
            paths = c.get("partitionKey", {}).get("paths", [])
            for path in paths:
                if "customer" in path.lower():
                    found_customer_pk = True
                    break

        assert found_customer_pk, (
            "No container uses a customerId-based partition key. "
            "For e-commerce, /customerId is the natural partition key choice — "
            "it aligns with the most common query pattern (customer order history) "
            "and has high cardinality. "
            "(Rules: partition-high-cardinality, partition-query-patterns)"
        )

    def test_no_default_id_partition_key(self, cosmos_containers):
        """No container should use /id as its sole partition key."""
        for c in cosmos_containers:
            paths = c.get("partitionKey", {}).get("paths", [])
            assert paths != ["/id"], (
                f"Container '{c['id']}' uses /id as partition key — this is an "
                f"anti-pattern that creates one logical partition per document, "
                f"preventing efficient point reads and range queries. "
                f"(Rule: partition-high-cardinality)"
            )


class TestIndexingPolicies:
    """
    Rules: index-exclude-unused, index-composite

    The default Cosmos DB indexing policy indexes every path (/*),
    which wastes 20-80% write RU. An agent with skills should
    customize the policy: exclude unused paths and add composite
    indexes for common query patterns.
    """

    def test_has_custom_indexing_policy(self, cosmos_containers):
        """At least one container should have a non-default indexing policy."""
        has_custom = False
        for c in cosmos_containers:
            policy = c.get("indexingPolicy", {})
            excluded = policy.get("excludedPaths", [])
            composites = policy.get("compositeIndexes", [])

            # Default policy has only {"path": "/_etag/?"}  in excludedPaths
            non_default_excludes = [
                p for p in excluded
                if p.get("path") not in ("/_etag/?", '"/_etag"/?', "/*")
            ]

            if non_default_excludes or composites:
                has_custom = True
                break

        assert has_custom, (
            "All containers use the default indexing policy (index everything). "
            "This wastes write RU on paths that are never queried. "
            "Best practice: exclude unused paths and add composite indexes "
            "for status+date and customer+date queries. "
            "(Rules: index-exclude-unused, index-composite)"
        )

    def test_has_composite_indexes_for_order_queries(self, cosmos_containers):
        """
        E-commerce needs composite indexes for:
        - status + createdAt (admin: orders by status sorted by date)
        - customerId + createdAt (customer: order history sorted by date)
        """
        has_composite = False
        for c in cosmos_containers:
            policy = c.get("indexingPolicy", {})
            composites = policy.get("compositeIndexes", [])
            if composites:
                has_composite = True
                break

        assert has_composite, (
            "No container has composite indexes defined. "
            "E-commerce queries like 'orders by status sorted by date' need "
            "composite indexes on (status, createdAt) to avoid expensive sorts. "
            "Without them, ORDER BY on multiple fields costs extra RU. "
            "(Rule: index-composite)"
        )


class TestThroughputConfiguration:
    """
    Rules: throughput-autoscale, throughput-provision-rus

    An agent with skills should configure autoscale throughput
    rather than relying on fixed RU/s defaults.
    """

    def test_throughput_is_configured(self, cosmos_database, cosmos_containers):
        """At least one container (or the database) should have throughput set."""
        has_throughput = False

        # Check database-level throughput
        try:
            offer = cosmos_database.read_offer()
            if offer is not None:
                has_throughput = True
        except Exception:
            pass

        # Check container-level throughput
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
            "No throughput configuration found on database or containers. "
            "The app should explicitly configure throughput (autoscale preferred). "
            "(Rule: throughput-autoscale)"
        )


# ============================================================================
# 2. SDK BEHAVIOR TESTS — Serialization & Configuration
# ============================================================================

class TestEnumSerialization:
    """
    Rule: model-json-serialization

    Enum values (like order status) must be stored as strings in Cosmos DB
    so that queries like WHERE c.status = "pending" work correctly.
    Storing enums as integers causes query mismatches between the API layer
    (which shows strings) and the stored data (which has integers).

    This was the #1 bug found in v1 testing (ecommerce-001-dotnet).
    """

    def test_status_stored_as_string(self, api, seeded_data, cosmos_database, cosmos_containers):
        """
        Create an order via the API, then read it DIRECTLY from Cosmos DB
        to verify the status field is stored as a string, not an integer.
        """
        order = seeded_data["orders"][0]
        order_id = order["orderId"]
        customer_id = order["customerId"]

        # Find the container that stores orders
        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT * FROM c WHERE c.id = @id OR c.orderId = @id",
                    parameters=[{"name": "@id", "value": order_id}],
                    enable_cross_partition_query=True,
                    max_item_count=1,
                ))
            except Exception:
                continue

            if not items:
                continue

            doc = items[0]
            # Find the status field (could be "status", "orderStatus", etc.)
            status_value = doc.get("status") or doc.get("orderStatus")
            if status_value is not None:
                assert isinstance(status_value, str), (
                    f"Order status is stored as {type(status_value).__name__} "
                    f"(value: {status_value!r}) instead of string. "
                    f"This causes status queries (WHERE c.status = 'pending') to "
                    f"return empty results because the stored integer doesn't match "
                    f"the string. Configure the SDK serializer to store enums as strings. "
                    f"(Rule: model-json-serialization)"
                )
                return

        pytest.skip("Could not locate order document in Cosmos DB to verify serialization")

    def test_status_query_returns_correct_results(self, api):
        """
        Create a FRESH order, update it to 'shipped', then query by status.
        If enum serialization is wrong, the status query will return empty.
        Uses its own order to avoid conflicts with other tests that mutate
        seeded_data order statuses.
        """
        # Create a fresh order specifically for this test
        resp = api.request("POST", "/api/orders", json={
            "customerId": "customer-infra-enum",
            "items": [{"productId": "p-enum", "productName": "EnumTest", "quantity": 1, "unitPrice": 10.00}],
        })
        assert resp.status_code == 201, (
            f"Failed to create test order: {resp.status_code} {resp.text}"
        )
        order_id = resp.json()["orderId"]

        # Transition pending → shipped
        resp = api.request("PATCH", f"/api/orders/{order_id}/status",
                           json={"status": "shipped"})
        assert resp.status_code in (200, 204), (
            f"Status update failed: {resp.status_code} {resp.text}"
        )

        # Now query by status — this is where enum serialization bugs surface
        # API contract: GET /api/orders?status=shipped (query parameter)
        resp = api.request("GET", "/api/orders", params={"status": "shipped"})
        assert resp.status_code == 200, (
            f"Status query failed: {resp.status_code} {resp.text}"
        )
        data = resp.json()
        orders = data if isinstance(data, list) else data.get("orders", data.get("items", []))
        assert len(orders) > 0, (
            "Status query for 'shipped' returned empty results. "
            "This is the classic enum serialization bug: the SDK stores status "
            "as an integer (e.g., 1) but the query searches for the string 'shipped'. "
            "Fix: configure the Cosmos DB serializer to use string enums. "
            "(Rule: model-json-serialization)"
        )


class TestDocumentStructure:
    """
    Rules: model-embed-related, model-type-discriminator, model-schema-versioning

    Verify that documents stored in Cosmos DB follow data modeling best practices.
    """

    def test_orders_have_embedded_items(self, api, seeded_data, cosmos_database, cosmos_containers):
        """
        Order items should be embedded in the order document, not stored
        in a separate container. This is the core Cosmos DB data modeling
        pattern for 1:N relationships where N is bounded.
        """
        order = seeded_data["orders"][0]
        order_id = order["orderId"]

        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT * FROM c WHERE c.id = @id OR c.orderId = @id",
                    parameters=[{"name": "@id", "value": order_id}],
                    enable_cross_partition_query=True,
                    max_item_count=1,
                ))
            except Exception:
                continue

            if not items:
                continue

            doc = items[0]
            # Check that items/orderItems/lineItems array exists in the document
            has_items = any(
                isinstance(doc.get(field), list) and len(doc.get(field, [])) > 0
                for field in ("items", "orderItems", "lineItems", "products")
            )
            assert has_items, (
                f"Order document does not contain embedded items array. "
                f"Stored fields: {list(doc.keys())}. "
                f"Best practice: embed order items directly in the order document "
                f"(denormalization for read performance). "
                f"(Rule: model-embed-related)"
            )
            return

        pytest.skip("Could not locate order document in Cosmos DB")

    def test_documents_have_type_discriminator(self, api, seeded_data, cosmos_database, cosmos_containers):
        """Documents should have a 'type' or '_type' field for polymorphic containers."""
        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT TOP 1 * FROM c",
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            if not items:
                continue

            doc = items[0]
            has_type = any(
                field in doc
                for field in ("type", "_type", "documentType", "entityType", "discriminator")
            )
            if has_type:
                return

        pytest.fail(
            "No documents have a type discriminator field. "
            "When a container holds multiple entity types (or for future extensibility), "
            "include a 'type' field (e.g., 'order', 'customer') to distinguish them. "
            "(Rule: model-type-discriminator)"
        )

    def test_documents_have_schema_version(self, api, seeded_data, cosmos_database, cosmos_containers):
        """Documents should include a schema version for future evolution."""
        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT TOP 1 * FROM c",
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            if not items:
                continue

            doc = items[0]
            has_version = any(
                field in doc
                for field in ("schemaVersion", "schema_version", "_version", "version", "docVersion")
            )
            if has_version:
                return

        pytest.fail(
            "No documents have a schema version field. "
            "Include a 'schemaVersion' field in documents so future schema changes "
            "can be handled without rewriting all existing data. "
            "(Rule: model-schema-versioning)"
        )


# ============================================================================
# 3. CROSS-BOUNDARY TESTS — API ↔ Cosmos DB Round-Trip Verification
# ============================================================================

class TestCrossBoundaryConsistency:
    """
    Write data through the HTTP API, then read directly from Cosmos DB
    to verify that what the app stores matches what Cosmos DB returns.

    These tests catch serialization mismatches, missing fields, and
    data type inconsistencies that round-trip HTTP tests cannot detect
    (because the same buggy serializer is used for both read and write).
    """

    def test_stored_total_matches_api_total(self, api, seeded_data, cosmos_database, cosmos_containers):
        """
        Verify the total calculated by the app is actually stored in Cosmos DB,
        not just computed on the fly during API responses.
        """
        order = seeded_data["orders"][0]
        api_total = order.get("total")
        order_id = order["orderId"]

        if api_total is None:
            pytest.skip("API response did not include 'total' field")

        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT * FROM c WHERE c.id = @id OR c.orderId = @id",
                    parameters=[{"name": "@id", "value": order_id}],
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            if not items:
                continue

            doc = items[0]
            stored_total = doc.get("total") or doc.get("orderTotal") or doc.get("totalAmount")
            if stored_total is not None:
                assert abs(float(stored_total) - float(api_total)) < 0.01, (
                    f"Stored total ({stored_total}) differs from API total ({api_total}). "
                    f"The order total should be persisted, not computed on the fly."
                )
                return

        pytest.skip("Could not verify stored total in Cosmos DB")

    def test_stored_item_count_matches_api(self, api, seeded_data, cosmos_database, cosmos_containers):
        """Verify the number of items embedded in Cosmos matches the API response."""
        order = seeded_data["orders"][0]
        api_items = order.get("items", [])
        order_id = order["orderId"]

        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT * FROM c WHERE c.id = @id OR c.orderId = @id",
                    parameters=[{"name": "@id", "value": order_id}],
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            if not items:
                continue

            doc = items[0]
            for field in ("items", "orderItems", "lineItems", "products"):
                stored_items = doc.get(field)
                if isinstance(stored_items, list):
                    assert len(stored_items) == len(api_items), (
                        f"Stored item count ({len(stored_items)}) differs from "
                        f"API item count ({len(api_items)}). Data inconsistency."
                    )
                    return

        pytest.skip("Could not verify stored items in Cosmos DB")

    def test_customer_id_stored_correctly(self, api, seeded_data, cosmos_database, cosmos_containers):
        """
        Verify that customerId is stored as a top-level field in the document
        (required for it to work as a partition key path).
        """
        order = seeded_data["orders"][0]
        customer_id = order["customerId"]
        order_id = order["orderId"]

        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT * FROM c WHERE c.id = @id OR c.orderId = @id",
                    parameters=[{"name": "@id", "value": order_id}],
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            if not items:
                continue

            doc = items[0]
            stored_customer = doc.get("customerId") or doc.get("customer_id")
            assert stored_customer == customer_id, (
                f"Stored customerId ({stored_customer!r}) doesn't match "
                f"API customerId ({customer_id!r}). "
                f"If customerId is the partition key, it must be a top-level field "
                f"with the exact value from the request."
            )
            return

        pytest.skip("Could not locate order document in Cosmos DB")

    def test_timestamps_stored_as_iso_strings(self, api, seeded_data, cosmos_database, cosmos_containers):
        """
        Timestamps should be stored as ISO 8601 strings (not epoch integers)
        for human readability and correct lexicographic sorting in queries.
        """
        order = seeded_data["orders"][0]
        order_id = order["orderId"]

        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT * FROM c WHERE c.id = @id OR c.orderId = @id",
                    parameters=[{"name": "@id", "value": order_id}],
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            if not items:
                continue

            doc = items[0]
            for field in ("createdAt", "created_at", "orderDate", "timestamp"):
                ts = doc.get(field)
                if ts is not None:
                    assert isinstance(ts, str), (
                        f"Timestamp field '{field}' is stored as "
                        f"{type(ts).__name__} ({ts!r}), not a string. "
                        f"Store timestamps as ISO 8601 strings for correct "
                        f"lexicographic sorting in ORDER BY queries."
                    )
                    return

        pytest.skip("Could not find timestamp field in stored document")

    def test_status_round_trip_through_cosmos(self, api, seeded_data, cosmos_database, cosmos_containers):
        """
        Update order status via the API, then read directly from Cosmos DB.
        If the app uses a different serializer for API vs Cosmos, the stored
        value may not match the API response.
        """
        order = seeded_data["orders"][0]
        order_id = order["orderId"]
        customer_id = order["customerId"]

        # Update status via API
        resp = api.request("PATCH", f"/api/orders/{order_id}/status",
                           json={"status": "shipped"},
                           params={"customerId": customer_id})
        if resp.status_code not in (200, 204):
            pytest.skip(f"Could not update order status: {resp.status_code}")

        api_status = None
        if resp.status_code == 200:
            body = resp.json()
            api_status = body.get("status") or body.get("orderStatus")

        # Read directly from Cosmos DB
        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT * FROM c WHERE c.id = @id OR c.orderId = @id",
                    parameters=[{"name": "@id", "value": order_id}],
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            if not items:
                continue

            doc = items[0]
            stored_status = doc.get("status") or doc.get("orderStatus")
            if stored_status is not None:
                # The stored value should be a string
                assert isinstance(stored_status, str), (
                    f"Status stored as {type(stored_status).__name__} ({stored_status!r}). "
                    f"Must be a string for queries to work. (Rule: model-json-serialization)"
                )
                # If we got the API response, they should match
                if api_status is not None:
                    assert stored_status.lower() == api_status.lower(), (
                        f"Serialization mismatch: API returns '{api_status}' "
                        f"but Cosmos DB stores '{stored_status}'. "
                        f"The app uses different serializers for HTTP and Cosmos DB."
                    )
                return

        pytest.skip("Could not verify stored status in Cosmos DB")
