"""
API Contract Tests for E-Commerce Order API
=============================================

These tests validate that the generated application conforms to the
API contract defined in api-contract.yaml. They test:
- Correct HTTP methods and paths
- Expected request/response schemas
- Correct status codes
- Required fields present in responses
- Correct data types and computed values (totals)
- Query filtering (by customer, status, date range)
"""

import pytest
from datetime import datetime, timezone


# ===================================================================
# HEALTH CHECK
# ===================================================================

class TestHealth:
    """Verify the health endpoint exists and responds."""

    def test_health_returns_200(self, api):
        resp = api.request("GET", "/health")
        assert resp.status_code == 200, (
            "Health endpoint must return 200. "
            "Ensure your app exposes GET /health"
        )


# ===================================================================
# CREATE ORDER
# ===================================================================

class TestCreateOrder:
    """POST /api/orders — Create a new order with items."""

    def test_create_order_returns_201(self, api):
        resp = api.request("POST", "/api/orders", json={
            "customerId": "test-cust-001",
            "items": [
                {"productId": "p1", "productName": "Test Item", "quantity": 1, "unitPrice": 10.00}
            ],
        })
        assert resp.status_code == 201, (
            f"POST /api/orders should return 201, got {resp.status_code}. "
            f"Response: {resp.text[:500]}"
        )

    def test_create_order_response_has_required_fields(self, api):
        resp = api.request("POST", "/api/orders", json={
            "customerId": "test-cust-002",
            "items": [
                {"productId": "p1", "productName": "Field Check", "quantity": 1, "unitPrice": 25.00}
            ],
        })
        assert resp.status_code == 201
        body = resp.json()

        required = ["orderId", "customerId", "status", "items", "total", "createdAt"]
        missing = [f for f in required if f not in body]
        assert not missing, (
            f"Response missing required fields: {missing}. "
            f"Got: {list(body.keys())}. "
            f"See api-contract.yaml create_order.response.body.required"
        )

    def test_new_order_status_is_pending(self, api):
        resp = api.request("POST", "/api/orders", json={
            "customerId": "test-cust-003",
            "items": [
                {"productId": "p1", "productName": "Status Check", "quantity": 1, "unitPrice": 5.00}
            ],
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body.get("status") == "pending", (
            f"New order status should be 'pending', got '{body.get('status')}'"
        )

    def test_create_order_calculates_total(self, api):
        resp = api.request("POST", "/api/orders", json={
            "customerId": "test-cust-004",
            "items": [
                {"productId": "p1", "productName": "Item A", "quantity": 2, "unitPrice": 10.00},
                {"productId": "p2", "productName": "Item B", "quantity": 3, "unitPrice": 5.50},
            ],
        })
        assert resp.status_code == 201
        body = resp.json()
        # Expected: 2*10.00 + 3*5.50 = 36.50
        assert abs(body["total"] - 36.50) < 0.01, (
            f"Order total should be 36.50 (2*10.00 + 3*5.50), got {body['total']}"
        )

    def test_create_order_has_timestamp(self, api):
        resp = api.request("POST", "/api/orders", json={
            "customerId": "test-cust-005",
            "items": [
                {"productId": "p1", "productName": "Time Check", "quantity": 1, "unitPrice": 1.00}
            ],
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body.get("createdAt"), "createdAt must be a non-empty string"

    def test_create_order_returns_items(self, api):
        items = [
            {"productId": "p1", "productName": "Item X", "quantity": 1, "unitPrice": 20.00},
            {"productId": "p2", "productName": "Item Y", "quantity": 2, "unitPrice": 30.00},
        ]
        resp = api.request("POST", "/api/orders", json={
            "customerId": "test-cust-006",
            "items": items,
        })
        assert resp.status_code == 201
        body = resp.json()
        assert isinstance(body["items"], list), "items should be an array"
        assert len(body["items"]) == 2, (
            f"Expected 2 items in response, got {len(body['items'])}"
        )


# ===================================================================
# GET ORDER
# ===================================================================

class TestGetOrder:
    """GET /api/orders/{orderId} — Get order by ID."""

    def test_get_existing_order(self, api, seeded_data):
        order_id = seeded_data["orders"][0]["orderId"]
        resp = api.request("GET", f"/api/orders/{order_id}")
        assert resp.status_code == 200, (
            f"GET /api/orders/{order_id} should return 200, got {resp.status_code}"
        )

    def test_get_order_has_required_fields(self, api, seeded_data):
        order_id = seeded_data["orders"][0]["orderId"]
        resp = api.request("GET", f"/api/orders/{order_id}")
        assert resp.status_code == 200
        body = resp.json()

        required = ["orderId", "customerId", "status", "items", "total", "createdAt"]
        missing = [f for f in required if f not in body]
        assert not missing, (
            f"GET order response missing required fields: {missing}. "
            f"Got: {list(body.keys())}"
        )

    def test_get_order_returns_correct_data(self, api, seeded_data):
        order = seeded_data["orders"][0]
        resp = api.request("GET", f"/api/orders/{order['orderId']}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["customerId"] == "customer-001"
        assert body["orderId"] == order["orderId"]

    def test_get_nonexistent_order_returns_404(self, api):
        resp = api.request("GET", "/api/orders/nonexistent-order-xyz")
        assert resp.status_code == 404, (
            f"GET /api/orders/nonexistent-order-xyz should return 404, "
            f"got {resp.status_code}"
        )


# ===================================================================
# CUSTOMER ORDER HISTORY
# ===================================================================

class TestCustomerOrders:
    """GET /api/customers/{customerId}/orders — Customer order history."""

    def test_customer_orders_returns_200(self, api, seeded_data):
        resp = api.request("GET", "/api/customers/customer-001/orders")
        assert resp.status_code == 200, (
            f"GET /api/customers/customer-001/orders should return 200, "
            f"got {resp.status_code}"
        )

    def test_customer_orders_returns_array(self, api, seeded_data):
        resp = api.request("GET", "/api/customers/customer-001/orders")
        body = resp.json()
        assert isinstance(body, list), (
            f"Customer orders should return an array, got {type(body).__name__}"
        )

    def test_customer_001_has_2_orders(self, api, seeded_data):
        """customer-001 placed 2 orders in seeded data."""
        resp = api.request("GET", "/api/customers/customer-001/orders")
        body = resp.json()
        assert len(body) >= 2, (
            f"customer-001 should have at least 2 orders, got {len(body)}"
        )

    def test_customer_orders_only_contains_own_orders(self, api, seeded_data):
        resp = api.request("GET", "/api/customers/customer-001/orders")
        body = resp.json()
        for order in body:
            assert order["customerId"] == "customer-001", (
                f"Customer-001's order history contains order for {order['customerId']}"
            )

    def test_customer_orders_entries_have_required_fields(self, api, seeded_data):
        resp = api.request("GET", "/api/customers/customer-001/orders")
        body = resp.json()
        assert len(body) > 0

        entry = body[0]
        required = ["orderId", "customerId", "status", "total", "createdAt"]
        missing = [f for f in required if f not in entry]
        assert not missing, (
            f"Customer order entry missing required fields: {missing}. "
            f"Got: {list(entry.keys())}"
        )

    def test_empty_customer_returns_empty_array(self, api, seeded_data):
        resp = api.request("GET", "/api/customers/nonexistent-customer/orders")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list) and len(body) == 0, (
            "Nonexistent customer should return empty array"
        )


# ===================================================================
# QUERY ORDERS BY STATUS
# ===================================================================

class TestQueryByStatus:
    """GET /api/orders?status=pending — Query orders by status."""

    def test_query_by_status_returns_200(self, api, seeded_data):
        resp = api.request("GET", "/api/orders?status=pending")
        assert resp.status_code == 200, (
            f"GET /api/orders?status=pending should return 200, "
            f"got {resp.status_code}"
        )

    def test_query_by_status_returns_array(self, api, seeded_data):
        resp = api.request("GET", "/api/orders?status=pending")
        body = resp.json()
        assert isinstance(body, list), (
            f"Status query should return an array, got {type(body).__name__}"
        )

    def test_all_seeded_orders_are_pending(self, api, seeded_data):
        """All newly created orders should have status 'pending'."""
        resp = api.request("GET", "/api/orders?status=pending")
        body = resp.json()
        assert len(body) >= 5, (
            f"Expected at least 5 pending orders (seeded data), got {len(body)}"
        )

    def test_query_by_status_filters_correctly(self, api, seeded_data):
        resp = api.request("GET", "/api/orders?status=pending")
        body = resp.json()
        for order in body:
            assert order["status"] == "pending", (
                f"Order {order.get('orderId')} has status '{order['status']}', "
                f"expected 'pending'"
            )

    def test_query_shipped_initially_empty(self, api, seeded_data):
        """No orders have been shipped yet, so shipped query should be empty or small."""
        resp = api.request("GET", "/api/orders?status=shipped")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)


# ===================================================================
# QUERY ORDERS BY DATE RANGE
# ===================================================================

class TestQueryByDateRange:
    """GET /api/orders?startDate=X&endDate=Y — Query by date range."""

    def test_query_by_date_range_returns_200(self, api, seeded_data):
        resp = api.request("GET", "/api/orders?startDate=2020-01-01&endDate=2099-12-31")
        assert resp.status_code == 200, (
            f"GET /api/orders?startDate=...&endDate=... should return 200, "
            f"got {resp.status_code}"
        )

    def test_query_by_date_range_returns_array(self, api, seeded_data):
        resp = api.request("GET", "/api/orders?startDate=2020-01-01&endDate=2099-12-31")
        body = resp.json()
        assert isinstance(body, list), (
            f"Date range query should return an array, got {type(body).__name__}"
        )

    def test_wide_date_range_includes_seeded_orders(self, api, seeded_data):
        """A very wide date range should include all seeded orders."""
        resp = api.request("GET", "/api/orders?startDate=2020-01-01&endDate=2099-12-31")
        body = resp.json()
        assert len(body) >= 5, (
            f"Wide date range should include at least 5 seeded orders, got {len(body)}"
        )

    def test_past_date_range_returns_empty(self, api, seeded_data):
        """A date range in the distant past should return no recent orders."""
        resp = api.request("GET", "/api/orders?startDate=2000-01-01&endDate=2000-12-31")
        body = resp.json()
        assert isinstance(body, list) and len(body) == 0, (
            f"Date range 2000-01-01 to 2000-12-31 should return empty, "
            f"got {len(body)} orders"
        )


# ===================================================================
# UPDATE ORDER STATUS
# ===================================================================

class TestUpdateOrderStatus:
    """PATCH /api/orders/{orderId}/status — Update order status."""

    def test_update_status_returns_200(self, api, seeded_data):
        order_id = seeded_data["orders"][0]["orderId"]
        resp = api.request("PATCH", f"/api/orders/{order_id}/status", json={
            "status": "shipped",
        })
        assert resp.status_code == 200, (
            f"PATCH /api/orders/{order_id}/status should return 200, "
            f"got {resp.status_code}. Response: {resp.text[:500]}"
        )

    def test_update_status_response_has_required_fields(self, api, seeded_data):
        order_id = seeded_data["orders"][1]["orderId"]
        resp = api.request("PATCH", f"/api/orders/{order_id}/status", json={
            "status": "shipped",
        })
        assert resp.status_code == 200
        body = resp.json()

        required = ["orderId", "status"]
        missing = [f for f in required if f not in body]
        assert not missing, (
            f"Status update response missing required fields: {missing}. "
            f"Got: {list(body.keys())}"
        )

    def test_update_status_reflects_new_status(self, api, seeded_data):
        order_id = seeded_data["orders"][2]["orderId"]
        resp = api.request("PATCH", f"/api/orders/{order_id}/status", json={
            "status": "delivered",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "delivered", (
            f"Updated status should be 'delivered', got '{body['status']}'"
        )

    def test_updated_status_persists_on_get(self, api, seeded_data):
        """After updating status, GET should return the new status."""
        order_id = seeded_data["orders"][2]["orderId"]
        # Status was already updated to "delivered" in previous test
        resp = api.request("GET", f"/api/orders/{order_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "delivered", (
            f"After PATCH, GET should return updated status 'delivered', "
            f"got '{body['status']}'"
        )

    def test_update_nonexistent_order_returns_404(self, api):
        resp = api.request("PATCH", "/api/orders/nonexistent-xyz/status", json={
            "status": "shipped",
        })
        assert resp.status_code == 404, (
            f"PATCH nonexistent order should return 404, got {resp.status_code}"
        )


# ===================================================================
# CUSTOMER ORDER SUMMARY
# ===================================================================

class TestCustomerSummary:
    """GET /api/customers/{customerId}/orders/summary — Aggregated stats."""

    def test_customer_summary_returns_200(self, api, seeded_data):
        resp = api.request("GET", "/api/customers/customer-001/orders/summary")
        assert resp.status_code == 200, (
            f"GET /api/customers/customer-001/orders/summary should return 200, "
            f"got {resp.status_code}. Response: {resp.text[:500]}"
        )

    def test_customer_summary_has_required_fields(self, api, seeded_data):
        resp = api.request("GET", "/api/customers/customer-001/orders/summary")
        assert resp.status_code == 200
        body = resp.json()

        required = ["customerId", "totalOrders", "totalSpent", "averageOrderValue"]
        missing = [f for f in required if f not in body]
        assert not missing, (
            f"Customer summary missing required fields: {missing}. "
            f"Got: {list(body.keys())}. "
            f"See api-contract.yaml get_customer_summary.response"
        )

    def test_customer_001_summary_correct(self, api, seeded_data):
        """
        customer-001 has 2 orders: $109.97 + $45.00 = $154.97 total.
        averageOrderValue = 154.97 / 2 = 77.485
        """
        resp = api.request("GET", "/api/customers/customer-001/orders/summary")
        assert resp.status_code == 200
        body = resp.json()

        assert body["customerId"] == "customer-001"
        assert body["totalOrders"] >= 2, (
            f"customer-001 should have at least 2 orders, got {body['totalOrders']}"
        )
        assert abs(body["totalSpent"] - 154.97) < 0.02, (
            f"customer-001 totalSpent should be ~154.97, got {body['totalSpent']}"
        )

    def test_customer_003_summary_correct(self, api, seeded_data):
        """
        customer-003 has 1 order: $254.95 total.
        averageOrderValue = 254.95
        """
        resp = api.request("GET", "/api/customers/customer-003/orders/summary")
        assert resp.status_code == 200
        body = resp.json()

        assert body["totalOrders"] >= 1
        assert abs(body["totalSpent"] - 254.95) < 0.02, (
            f"customer-003 totalSpent should be ~254.95, got {body['totalSpent']}"
        )
        # With 1 order, average == total
        if body["totalOrders"] == 1:
            assert abs(body["averageOrderValue"] - 254.95) < 0.02, (
                f"With 1 order, averageOrderValue should equal totalSpent. "
                f"Got {body['averageOrderValue']}"
            )

    def test_customer_summary_average_is_correct(self, api, seeded_data):
        """averageOrderValue must equal totalSpent / totalOrders."""
        resp = api.request("GET", "/api/customers/customer-001/orders/summary")
        body = resp.json()

        expected_avg = body["totalSpent"] / body["totalOrders"]
        assert abs(body["averageOrderValue"] - expected_avg) < 0.02, (
            f"averageOrderValue should be totalSpent/totalOrders = "
            f"{body['totalSpent']}/{body['totalOrders']} = {expected_avg:.2f}, "
            f"got {body['averageOrderValue']}"
        )

    def test_nonexistent_customer_summary_empty(self, api, seeded_data):
        """Summary for nonexistent customer should return 0s or 404."""
        resp = api.request("GET", "/api/customers/nonexistent-xyz/orders/summary")
        # Accept either 200 with zero values or 404
        assert resp.status_code in (200, 404), (
            f"Summary for nonexistent customer should return 200 (with zeros) "
            f"or 404, got {resp.status_code}"
        )
        if resp.status_code == 200:
            body = resp.json()
            assert body["totalOrders"] == 0
            assert body["totalSpent"] == 0


# ===================================================================
# DELETE ORDER
# ===================================================================

class TestDeleteOrder:
    """DELETE /api/orders/{orderId} — Delete a pending order."""

    def test_delete_pending_order_returns_204(self, api, seeded_data):
        # Create a disposable order
        resp = api.request("POST", "/api/orders", json={
            "customerId": "delete-cust-001",
            "items": [{"productId": "p1", "productName": "DeleteMe", "quantity": 1, "unitPrice": 10.00}],
        })
        assert resp.status_code == 201
        order_id = resp.json()["orderId"]

        resp = api.request("DELETE", f"/api/orders/{order_id}")
        assert resp.status_code == 204, (
            f"DELETE pending order should return 204, got {resp.status_code}"
        )

    def test_deleted_order_returns_404_on_get(self, api, seeded_data):
        resp = api.request("POST", "/api/orders", json={
            "customerId": "delete-cust-002",
            "items": [{"productId": "p1", "productName": "DeleteCheck", "quantity": 1, "unitPrice": 5.00}],
        })
        order_id = resp.json()["orderId"]
        api.request("DELETE", f"/api/orders/{order_id}")

        resp = api.request("GET", f"/api/orders/{order_id}")
        assert resp.status_code == 404, (
            f"Deleted order should return 404 on GET, got {resp.status_code}"
        )

    def test_delete_nonexistent_order_returns_404(self, api):
        resp = api.request("DELETE", "/api/orders/nonexistent-xyz")
        assert resp.status_code == 404, (
            f"DELETE nonexistent order should return 404, got {resp.status_code}"
        )

    def test_delete_shipped_order_returns_409(self, api, seeded_data):
        """Only pending orders can be deleted. Shipped orders must return 409."""
        # Create and ship an order
        resp = api.request("POST", "/api/orders", json={
            "customerId": "delete-cust-003",
            "items": [{"productId": "p1", "productName": "ShippedItem", "quantity": 1, "unitPrice": 20.00}],
        })
        order_id = resp.json()["orderId"]
        api.request("PATCH", f"/api/orders/{order_id}/status", json={"status": "shipped"})

        resp = api.request("DELETE", f"/api/orders/{order_id}")
        assert resp.status_code == 409, (
            f"DELETE shipped order should return 409 Conflict, got {resp.status_code}. "
            f"Only pending orders can be deleted."
        )
