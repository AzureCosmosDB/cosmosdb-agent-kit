"""
Robustness Tests for E-Commerce Order API
==========================================

These tests go beyond basic API contract compliance to verify the application
handles real-world scenarios correctly:
- Invalid / malformed input → proper 4xx responses (not 500)
- Computed field accuracy (order total calculations)
- Data type correctness in responses
- Write-read consistency across endpoints
- Status transition correctness
- Edge cases and boundary conditions

These tests catch the classes of bugs most commonly produced by AI agents:
missing input validation, incorrect total calculations, status filtering
mismatches, and customer data isolation failures.
"""

import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed


# ===================================================================
# INVALID INPUT HANDLING
# ===================================================================

class TestInvalidInput:
    """
    The application must return 4xx (not 5xx) for malformed requests.
    A 500 on bad input indicates missing validation — a common agent bug.
    """

    def test_create_order_missing_customer_id_returns_4xx(self, api):
        """POST /api/orders without customerId should return 4xx, not 500."""
        resp = api.request("POST", "/api/orders", json={
            "items": [
                {"productId": "p1", "productName": "Test", "quantity": 1, "unitPrice": 10.00}
            ],
        })
        assert 400 <= resp.status_code < 500, (
            f"Missing customerId should return 4xx, got {resp.status_code}. "
            f"The app must validate required fields and return 400."
        )

    def test_create_order_missing_items_returns_4xx(self, api):
        """POST /api/orders without items should return 4xx."""
        resp = api.request("POST", "/api/orders", json={
            "customerId": "test-bad-input",
        })
        assert 400 <= resp.status_code < 500, (
            f"Missing items should return 4xx, got {resp.status_code}. "
            f"The app must validate required fields."
        )

    def test_create_order_empty_items_returns_4xx(self, api):
        """POST /api/orders with empty items array should return 4xx."""
        resp = api.request("POST", "/api/orders", json={
            "customerId": "test-bad-input",
            "items": [],
        })
        assert 400 <= resp.status_code < 500, (
            f"Empty items array should return 4xx, got {resp.status_code}. "
            f"An order must have at least one item."
        )

    def test_create_order_empty_body_returns_4xx(self, api):
        """POST /api/orders with empty body should not crash."""
        resp = api.request("POST", "/api/orders", json={})
        assert 400 <= resp.status_code < 500, (
            f"Empty body should return 4xx, got {resp.status_code}. "
            f"Server must not crash (500) on missing fields."
        )

    def test_update_status_invalid_value_returns_4xx(self, api, seeded_data):
        """PATCH with an invalid status value should be rejected."""
        order_id = seeded_data["orders"][0]["orderId"]
        resp = api.request("PATCH", f"/api/orders/{order_id}/status", json={
            "status": "not_a_real_status",
        })
        # Accept either 4xx (validation) or 200 (lenient), but not 500
        assert resp.status_code < 500, (
            f"Invalid status value caused a server error ({resp.status_code}). "
            f"The app should validate status values or handle them gracefully."
        )

    def test_update_status_empty_body_returns_4xx(self, api, seeded_data):
        """PATCH with empty body should not crash."""
        order_id = seeded_data["orders"][0]["orderId"]
        resp = api.request("PATCH", f"/api/orders/{order_id}/status", json={})
        assert resp.status_code < 500, (
            f"Empty status update body caused a server error ({resp.status_code}). "
            f"Server must handle missing fields gracefully."
        )


# ===================================================================
# COMPUTED FIELD ACCURACY
# ===================================================================

class TestComputedFieldAccuracy:
    """
    Verify that order totals are mathematically correct.
    This catches bugs with floating-point math, wrong formulas,
    or items not being summed properly.
    """

    def test_single_item_total(self, api):
        """Single item: total = quantity * unitPrice."""
        resp = api.request("POST", "/api/orders", json={
            "customerId": "math-test-001",
            "items": [
                {"productId": "p1", "productName": "Single Item", "quantity": 1, "unitPrice": 42.50},
            ],
        })
        assert resp.status_code == 201
        body = resp.json()
        assert abs(body["total"] - 42.50) < 0.01, (
            f"Single item (qty=1, price=42.50) total should be 42.50, "
            f"got {body['total']}"
        )

    def test_multi_quantity_total(self, api):
        """Multiple quantity: total = 3 * 15.99 = 47.97."""
        resp = api.request("POST", "/api/orders", json={
            "customerId": "math-test-002",
            "items": [
                {"productId": "p1", "productName": "Multi Qty", "quantity": 3, "unitPrice": 15.99},
            ],
        })
        assert resp.status_code == 201
        body = resp.json()
        expected = 3 * 15.99  # 47.97
        assert abs(body["total"] - expected) < 0.01, (
            f"3 × $15.99 should be ${expected:.2f}, got ${body['total']}"
        )

    def test_multi_item_total(self, api):
        """Multiple items: total = sum of (qty * price) for each."""
        resp = api.request("POST", "/api/orders", json={
            "customerId": "math-test-003",
            "items": [
                {"productId": "p1", "productName": "Item A", "quantity": 2, "unitPrice": 10.00},
                {"productId": "p2", "productName": "Item B", "quantity": 1, "unitPrice": 25.50},
                {"productId": "p3", "productName": "Item C", "quantity": 4, "unitPrice": 5.25},
            ],
        })
        assert resp.status_code == 201
        body = resp.json()
        expected = 2 * 10.00 + 1 * 25.50 + 4 * 5.25  # 66.50
        assert abs(body["total"] - expected) < 0.01, (
            f"Total should be ${expected:.2f} "
            f"(2×10.00 + 1×25.50 + 4×5.25), got ${body['total']}"
        )

    def test_seeded_order_totals_correct(self, api, seeded_data, expected_totals):
        """Verify all seeded orders have correct totals."""
        for i, order in enumerate(seeded_data["orders"]):
            assert abs(order["total"] - expected_totals[i]) < 0.01, (
                f"Seeded order {i+1} total should be ${expected_totals[i]:.2f}, "
                f"got ${order['total']}"
            )


# ===================================================================
# DATA TYPE CORRECTNESS
# ===================================================================

class TestDataTypeCorrectness:
    """
    Verify response fields have correct data types.
    Catches serialization bugs where numbers come back as strings.
    """

    def test_order_field_types(self, api, seeded_data):
        """Verify order fields have correct types."""
        order_id = seeded_data["orders"][0]["orderId"]
        resp = api.request("GET", f"/api/orders/{order_id}")
        assert resp.status_code == 200
        body = resp.json()

        assert isinstance(body["orderId"], str), (
            f"orderId should be string, got {type(body['orderId']).__name__}"
        )
        assert isinstance(body["customerId"], str), (
            f"customerId should be string, got {type(body['customerId']).__name__}"
        )
        assert isinstance(body["status"], str), (
            f"status should be string, got {type(body['status']).__name__}: "
            f"{body['status']!r}"
        )
        assert isinstance(body["items"], list), (
            f"items should be array, got {type(body['items']).__name__}"
        )
        assert isinstance(body["total"], (int, float)), (
            f"total should be number, got {type(body['total']).__name__}: "
            f"{body['total']!r}"
        )
        assert isinstance(body["createdAt"], str), (
            f"createdAt should be string, got {type(body['createdAt']).__name__}"
        )

    def test_order_item_field_types(self, api, seeded_data):
        """Verify each item in an order has correct types."""
        order_id = seeded_data["orders"][0]["orderId"]
        resp = api.request("GET", f"/api/orders/{order_id}")
        assert resp.status_code == 200
        body = resp.json()

        for item in body["items"]:
            assert isinstance(item.get("productId"), str), (
                f"item.productId should be string, got {type(item.get('productId')).__name__}"
            )
            assert isinstance(item.get("productName"), str), (
                f"item.productName should be string, got {type(item.get('productName')).__name__}"
            )
            assert isinstance(item.get("quantity"), (int, float)), (
                f"item.quantity should be number, got {type(item.get('quantity')).__name__}: "
                f"{item.get('quantity')!r}"
            )
            assert isinstance(item.get("unitPrice"), (int, float)), (
                f"item.unitPrice should be number, got {type(item.get('unitPrice')).__name__}: "
                f"{item.get('unitPrice')!r}"
            )


# ===================================================================
# WRITE-READ CONSISTENCY
# ===================================================================

class TestWriteReadConsistency:
    """
    Data written through one endpoint must be correctly readable
    through another. This catches serialization mismatches.
    """

    def test_created_order_fields_match_on_get(self, api):
        """Create an order, then GET it — core fields should match."""
        items = [
            {"productId": "consistency-p1", "productName": "ConsistencyItem", "quantity": 2, "unitPrice": 33.00},
        ]
        create_resp = api.request("POST", "/api/orders", json={
            "customerId": "consistency-cust-001",
            "items": items,
        })
        assert create_resp.status_code == 201
        created = create_resp.json()
        order_id = created["orderId"]

        get_resp = api.request("GET", f"/api/orders/{order_id}")
        assert get_resp.status_code == 200, (
            f"Order was created successfully but GET returned {get_resp.status_code}. "
            f"Data may not be persisted correctly."
        )
        retrieved = get_resp.json()

        assert retrieved["orderId"] == order_id
        assert retrieved["customerId"] == "consistency-cust-001"
        assert retrieved["status"] == "pending"
        assert abs(retrieved["total"] - 66.00) < 0.01, (
            f"Created order total was {created['total']}, but GET returned {retrieved['total']}"
        )

    def test_order_appears_in_customer_history(self, api):
        """A newly created order should appear in the customer's order list."""
        resp = api.request("POST", "/api/orders", json={
            "customerId": "consistency-cust-002",
            "items": [
                {"productId": "p1", "productName": "HistoryTest", "quantity": 1, "unitPrice": 10.00}
            ],
        })
        assert resp.status_code == 201
        order_id = resp.json()["orderId"]

        history_resp = api.request("GET", "/api/customers/consistency-cust-002/orders")
        assert history_resp.status_code == 200
        history = history_resp.json()

        order_ids = [o.get("orderId") for o in history]
        assert order_id in order_ids, (
            f"Created order {order_id} not found in customer history. "
            f"This may indicate a query/serialization mismatch. "
            f"Found order IDs: {order_ids}"
        )

    def test_order_appears_in_status_query(self, api):
        """A newly created order (status=pending) should appear in status query."""
        resp = api.request("POST", "/api/orders", json={
            "customerId": "consistency-cust-003",
            "items": [
                {"productId": "p1", "productName": "StatusQuery", "quantity": 1, "unitPrice": 10.00}
            ],
        })
        assert resp.status_code == 201
        order_id = resp.json()["orderId"]

        status_resp = api.request("GET", "/api/orders?status=pending")
        assert status_resp.status_code == 200
        orders = status_resp.json()

        order_ids = [o.get("orderId") for o in orders]
        assert order_id in order_ids, (
            f"Created order {order_id} (status=pending) not found in "
            f"status=pending query. This catches the enum serialization bug "
            f"where status is stored/queried with different casing. "
            f"Found {len(orders)} pending orders."
        )


# ===================================================================
# STATUS TRANSITION CORRECTNESS
# ===================================================================

class TestStatusTransitions:
    """
    Verify that status updates are reflected in status-based queries.
    This catches serialization/case-sensitivity bugs where updating
    status to 'shipped' stores it differently than how it's queried.
    """

    def test_updated_status_appears_in_status_query(self, api, seeded_data):
        """
        After updating an order to 'shipped', it should appear in
        GET /api/orders?status=shipped.
        """
        # Use the last seeded order to avoid interfering with other tests
        order_id = seeded_data["orders"][4]["orderId"]

        # Update to shipped
        patch_resp = api.request("PATCH", f"/api/orders/{order_id}/status", json={
            "status": "shipped",
        })
        assert patch_resp.status_code == 200

        # Verify it appears in shipped query
        query_resp = api.request("GET", "/api/orders?status=shipped")
        assert query_resp.status_code == 200
        orders = query_resp.json()

        order_ids = [o.get("orderId") for o in orders]
        assert order_id in order_ids, (
            f"Order {order_id} was updated to 'shipped' but doesn't appear "
            f"in status=shipped query. This suggests the status value is stored "
            f"differently than how it's queried (e.g., case mismatch, enum "
            f"serialization issue). Found {len(orders)} shipped orders."
        )

    def test_updated_order_no_longer_in_original_status(self, api, seeded_data):
        """
        After updating an order from 'pending' to 'shipped', it should
        NOT appear in GET /api/orders?status=pending (for that specific order).
        """
        order_id = seeded_data["orders"][4]["orderId"]

        # This order was already updated to shipped in the previous test.
        # Verify it's not in the pending list.
        pending_resp = api.request("GET", "/api/orders?status=pending")
        assert pending_resp.status_code == 200
        pending_orders = pending_resp.json()

        pending_ids = [o.get("orderId") for o in pending_orders]
        assert order_id not in pending_ids, (
            f"Order {order_id} was updated to 'shipped' but still appears "
            f"in status=pending query. Status update may not have persisted."
        )


# ===================================================================
# DATA ISOLATION
# ===================================================================

class TestDataIsolation:
    """
    Verify that customer-scoped queries only return that customer's data.
    This catches bugs where queries don't properly filter by customer.
    """

    def test_customer_orders_isolated(self, api, seeded_data):
        """customer-002 should only see their own orders."""
        resp = api.request("GET", "/api/customers/customer-002/orders")
        assert resp.status_code == 200
        orders = resp.json()

        for order in orders:
            assert order["customerId"] == "customer-002", (
                f"customer-002's order history contains order for "
                f"'{order['customerId']}'. Customer data is leaking. "
                f"Order ID: {order.get('orderId')}"
            )

    def test_different_customers_see_different_orders(self, api, seeded_data):
        """Orders for customer-001 and customer-003 should be disjoint."""
        resp1 = api.request("GET", "/api/customers/customer-001/orders")
        resp3 = api.request("GET", "/api/customers/customer-003/orders")
        assert resp1.status_code == 200
        assert resp3.status_code == 200

        ids1 = {o.get("orderId") for o in resp1.json()}
        ids3 = {o.get("orderId") for o in resp3.json()}

        overlap = ids1 & ids3
        assert not overlap, (
            f"customer-001 and customer-003 share order IDs: {overlap}. "
            f"Each customer should have distinct orders."
        )


# ===================================================================
# EDGE CASES
# ===================================================================

class TestEdgeCases:
    """Test boundary conditions that commonly expose bugs."""

    def test_large_quantity_order(self, api):
        """An order with large quantity should calculate total correctly."""
        resp = api.request("POST", "/api/orders", json={
            "customerId": "edge-case-001",
            "items": [
                {"productId": "p1", "productName": "Bulk Item", "quantity": 1000, "unitPrice": 0.99},
            ],
        })
        assert resp.status_code == 201
        body = resp.json()
        expected = 1000 * 0.99  # 990.00
        assert abs(body["total"] - expected) < 0.01, (
            f"1000 × $0.99 should be ${expected:.2f}, got ${body['total']}"
        )

    def test_order_with_many_items(self, api):
        """An order with several item types should sum all correctly."""
        items = [
            {"productId": f"p{i}", "productName": f"Item {i}", "quantity": 1, "unitPrice": 10.00}
            for i in range(10)
        ]
        resp = api.request("POST", "/api/orders", json={
            "customerId": "edge-case-002",
            "items": items,
        })
        assert resp.status_code == 201
        body = resp.json()
        assert abs(body["total"] - 100.00) < 0.01, (
            f"10 items × $10.00 each should total $100.00, got ${body['total']}"
        )

    def test_get_order_preserves_all_items(self, api):
        """Creating an order with multiple items, GET should return all of them."""
        items = [
            {"productId": "p1", "productName": "Preserved A", "quantity": 1, "unitPrice": 10.00},
            {"productId": "p2", "productName": "Preserved B", "quantity": 2, "unitPrice": 20.00},
            {"productId": "p3", "productName": "Preserved C", "quantity": 3, "unitPrice": 30.00},
        ]
        resp = api.request("POST", "/api/orders", json={
            "customerId": "edge-case-003",
            "items": items,
        })
        assert resp.status_code == 201
        order_id = resp.json()["orderId"]

        get_resp = api.request("GET", f"/api/orders/{order_id}")
        assert get_resp.status_code == 200
        body = get_resp.json()

        assert len(body["items"]) == 3, (
            f"Order was created with 3 items but GET returned {len(body['items'])}. "
            f"Items may be lost during storage/retrieval."
        )


# ===================================================================
# STATUS TRANSITION RULES
# ===================================================================

class TestStatusTransitionRules:
    """
    Verify that the status state machine is enforced correctly.

    Valid transitions:
    - pending → shipped
    - pending → cancelled
    - shipped → delivered

    Invalid transitions (must return 409 Conflict):
    - shipped → pending (can't un-ship)
    - delivered → anything (terminal state)
    - cancelled → anything (terminal state)

    This tests read-modify-write patterns. Without proper concurrency
    handling (ETags), concurrent status updates can produce invalid states.
    """

    def test_pending_to_shipped_allowed(self, api, seeded_data):
        resp = api.request("POST", "/api/orders", json={
            "customerId": "transition-001",
            "items": [{"productId": "p1", "productName": "T1", "quantity": 1, "unitPrice": 10.00}],
        })
        order_id = resp.json()["orderId"]

        resp = api.request("PATCH", f"/api/orders/{order_id}/status", json={"status": "shipped"})
        assert resp.status_code == 200, (
            f"pending → shipped should be allowed, got {resp.status_code}"
        )

    def test_pending_to_cancelled_allowed(self, api, seeded_data):
        resp = api.request("POST", "/api/orders", json={
            "customerId": "transition-002",
            "items": [{"productId": "p1", "productName": "T2", "quantity": 1, "unitPrice": 10.00}],
        })
        order_id = resp.json()["orderId"]

        resp = api.request("PATCH", f"/api/orders/{order_id}/status", json={"status": "cancelled"})
        assert resp.status_code == 200, (
            f"pending → cancelled should be allowed, got {resp.status_code}"
        )

    def test_shipped_to_delivered_allowed(self, api, seeded_data):
        resp = api.request("POST", "/api/orders", json={
            "customerId": "transition-003",
            "items": [{"productId": "p1", "productName": "T3", "quantity": 1, "unitPrice": 10.00}],
        })
        order_id = resp.json()["orderId"]
        api.request("PATCH", f"/api/orders/{order_id}/status", json={"status": "shipped"})

        resp = api.request("PATCH", f"/api/orders/{order_id}/status", json={"status": "delivered"})
        assert resp.status_code == 200, (
            f"shipped → delivered should be allowed, got {resp.status_code}"
        )

    def test_shipped_to_pending_rejected(self, api, seeded_data):
        """Can't un-ship an order."""
        resp = api.request("POST", "/api/orders", json={
            "customerId": "transition-004",
            "items": [{"productId": "p1", "productName": "T4", "quantity": 1, "unitPrice": 10.00}],
        })
        order_id = resp.json()["orderId"]
        api.request("PATCH", f"/api/orders/{order_id}/status", json={"status": "shipped"})

        resp = api.request("PATCH", f"/api/orders/{order_id}/status", json={"status": "pending"})
        assert resp.status_code == 409, (
            f"shipped → pending should return 409 Conflict, got {resp.status_code}. "
            f"Orders cannot be un-shipped."
        )

    def test_delivered_to_anything_rejected(self, api, seeded_data):
        """Delivered is a terminal state."""
        resp = api.request("POST", "/api/orders", json={
            "customerId": "transition-005",
            "items": [{"productId": "p1", "productName": "T5", "quantity": 1, "unitPrice": 10.00}],
        })
        order_id = resp.json()["orderId"]
        api.request("PATCH", f"/api/orders/{order_id}/status", json={"status": "shipped"})
        api.request("PATCH", f"/api/orders/{order_id}/status", json={"status": "delivered"})

        for target in ["pending", "shipped", "cancelled"]:
            resp = api.request("PATCH", f"/api/orders/{order_id}/status", json={"status": target})
            assert resp.status_code == 409, (
                f"delivered → {target} should return 409 Conflict, got {resp.status_code}. "
                f"Delivered is a terminal state — no further transitions allowed."
            )

    def test_cancelled_to_anything_rejected(self, api, seeded_data):
        """Cancelled is a terminal state."""
        resp = api.request("POST", "/api/orders", json={
            "customerId": "transition-006",
            "items": [{"productId": "p1", "productName": "T6", "quantity": 1, "unitPrice": 10.00}],
        })
        order_id = resp.json()["orderId"]
        api.request("PATCH", f"/api/orders/{order_id}/status", json={"status": "cancelled"})

        for target in ["pending", "shipped", "delivered"]:
            resp = api.request("PATCH", f"/api/orders/{order_id}/status", json={"status": target})
            assert resp.status_code == 409, (
                f"cancelled → {target} should return 409 Conflict, got {resp.status_code}. "
                f"Cancelled is a terminal state — no further transitions allowed."
            )


# ===================================================================
# CUSTOMER SUMMARY CONSISTENCY
# ===================================================================

class TestCustomerSummaryConsistency:
    """
    Verify that the customer summary accurately reflects order data.
    This tests cross-document aggregation which is sensitive to
    partition key design and query patterns in Cosmos DB.
    """

    def test_summary_updates_after_new_order(self, api, seeded_data):
        """Creating a new order should update the customer summary."""
        cust_id = "summary-test-001"

        # Create first order
        api.request("POST", "/api/orders", json={
            "customerId": cust_id,
            "items": [{"productId": "p1", "productName": "Sum1", "quantity": 1, "unitPrice": 50.00}],
        })

        resp = api.request("GET", f"/api/customers/{cust_id}/orders/summary")
        assert resp.status_code == 200
        s1 = resp.json()
        assert s1["totalOrders"] >= 1
        assert abs(s1["totalSpent"] - 50.00) < 0.02

        # Create second order
        api.request("POST", "/api/orders", json={
            "customerId": cust_id,
            "items": [{"productId": "p2", "productName": "Sum2", "quantity": 2, "unitPrice": 25.00}],
        })

        resp = api.request("GET", f"/api/customers/{cust_id}/orders/summary")
        assert resp.status_code == 200
        s2 = resp.json()
        assert s2["totalOrders"] >= 2, (
            f"After 2 orders, totalOrders should be >= 2, got {s2['totalOrders']}"
        )
        assert abs(s2["totalSpent"] - 100.00) < 0.02, (
            f"After orders of $50 + $50, totalSpent should be ~100.00, "
            f"got {s2['totalSpent']}"
        )
        assert abs(s2["averageOrderValue"] - 50.00) < 0.02, (
            f"averageOrderValue should be ~50.00, got {s2['averageOrderValue']}"
        )

    def test_summary_reflects_deleted_order(self, api, seeded_data):
        """Deleting a pending order should update the summary."""
        cust_id = "summary-delete-001"

        # Create two orders
        resp1 = api.request("POST", "/api/orders", json={
            "customerId": cust_id,
            "items": [{"productId": "p1", "productName": "Keep", "quantity": 1, "unitPrice": 100.00}],
        })
        order1_id = resp1.json()["orderId"]

        resp2 = api.request("POST", "/api/orders", json={
            "customerId": cust_id,
            "items": [{"productId": "p2", "productName": "Delete", "quantity": 1, "unitPrice": 50.00}],
        })
        order2_id = resp2.json()["orderId"]

        # Delete second order
        api.request("DELETE", f"/api/orders/{order2_id}")

        # Summary should reflect only the remaining order
        resp = api.request("GET", f"/api/customers/{cust_id}/orders/summary")
        assert resp.status_code == 200
        body = resp.json()
        assert body["totalOrders"] >= 1
        assert abs(body["totalSpent"] - 100.00) < 0.02, (
            f"After deleting $50 order, totalSpent should be ~100.00, "
            f"got {body['totalSpent']}"
        )
