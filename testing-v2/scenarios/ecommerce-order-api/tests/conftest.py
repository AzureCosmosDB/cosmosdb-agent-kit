"""
Scenario-level conftest for ecommerce-order-api tests.

Imports shared harness fixtures and adds scenario-specific helpers.
"""

import sys
from pathlib import Path

# Add harness to path so shared fixtures are importable
harness_dir = Path(__file__).resolve().parent.parent.parent.parent / "harness"
sys.path.insert(0, str(harness_dir))

from conftest_base import *  # noqa: F401,F403 — re-export all shared fixtures

import pytest


# ---------------------------------------------------------------------------
# Scenario-specific fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_orders():
    """
    Standard set of test orders used across tests.
    Deterministic data: 3 customers, 5 orders with known totals.
    """
    return [
        {
            "customerId": "customer-001",
            "items": [
                {"productId": "prod-A", "productName": "Widget A", "quantity": 2, "unitPrice": 29.99},
                {"productId": "prod-B", "productName": "Widget B", "quantity": 1, "unitPrice": 49.99},
            ],
            "shippingAddress": "123 Main St",
            # Expected total: 2*29.99 + 1*49.99 = 109.97
        },
        {
            "customerId": "customer-001",
            "items": [
                {"productId": "prod-C", "productName": "Gadget C", "quantity": 3, "unitPrice": 15.00},
            ],
            # Expected total: 3*15.00 = 45.00
        },
        {
            "customerId": "customer-002",
            "items": [
                {"productId": "prod-A", "productName": "Widget A", "quantity": 1, "unitPrice": 29.99},
                {"productId": "prod-D", "productName": "Gadget D", "quantity": 2, "unitPrice": 75.00},
            ],
            # Expected total: 1*29.99 + 2*75.00 = 179.99
        },
        {
            "customerId": "customer-002",
            "items": [
                {"productId": "prod-B", "productName": "Widget B", "quantity": 1, "unitPrice": 49.99},
            ],
            # Expected total: 49.99
        },
        {
            "customerId": "customer-003",
            "items": [
                {"productId": "prod-A", "productName": "Widget A", "quantity": 5, "unitPrice": 29.99},
                {"productId": "prod-C", "productName": "Gadget C", "quantity": 2, "unitPrice": 15.00},
                {"productId": "prod-D", "productName": "Gadget D", "quantity": 1, "unitPrice": 75.00},
            ],
            # Expected total: 5*29.99 + 2*15.00 + 1*75.00 = 254.95
        },
    ]


@pytest.fixture(scope="session")
def expected_totals():
    """Expected order totals matching test_orders, for assertions."""
    return [109.97, 45.00, 179.99, 49.99, 254.95]


@pytest.fixture(scope="session")
def seeded_data(api, test_orders):
    """
    Create all test orders via the API.
    Returns a dict with the created data for reference.
    Called once per session before any tests that need data.
    """
    created_orders = []
    for order in test_orders:
        resp = api.request("POST", "/api/orders", json=order)
        assert resp.status_code == 201, (
            f"Failed to create order for {order['customerId']}: "
            f"{resp.status_code} {resp.text}"
        )
        created_orders.append(resp.json())

    return {
        "orders": created_orders,
    }
