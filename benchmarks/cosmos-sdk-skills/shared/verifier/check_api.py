"""API conformance checks.

These run against the agent's live HTTP server, which test.sh has
already started and waited on. The contract is the same for every SDK:

    GET  /health                  -> 200, {"status": "ok"}
    POST /users                   -> 201, returns the user
    GET  /users/{id}              -> 200 or 404
    GET  /users?city=<city>       -> 200, array of users matching city

Test users are deterministic (no faker, no random) and live in conftest.py
so that check_cosmos.py can also rely on the same seeded fixtures.
"""
from __future__ import annotations

import pytest

from conftest import USERS  # re-exported for backwards compat


class TestHealth:
    def test_health_returns_200(self, api):
        r = api.api("GET", "/health")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, dict)
        assert body.get("status") in ("ok", "OK", "healthy", "Healthy"), body


class TestCreateUser:
    def test_post_user_returns_201_and_persists_fields(self, seeded_users, api):
        u = seeded_users[0]
        r = api.api("GET", f"/users/{u['id']}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["name"] == u["name"]
        assert body["email"] == u["email"]
        assert body["city"] == u["city"]
        assert body["interests"] == u["interests"], (
            f"interests order changed: expected {u['interests']}, got {body['interests']}"
        )


class TestGetUser:
    def test_get_existing_user_200(self, seeded_users, api):
        r = api.api("GET", f"/users/{seeded_users[1]['id']}")
        assert r.status_code == 200, r.text

    def test_get_unknown_user_404(self, seeded_users, api):
        r = api.api("GET", "/users/u-does-not-exist")
        assert r.status_code == 404, f"Expected 404 for missing user, got {r.status_code}"


class TestListByCity:
    def test_list_users_by_city_returns_array(self, seeded_users, api):
        r = api.api("GET", "/users", params={"city": "Seattle"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, list), f"Expected list, got {type(body).__name__}"
        ids = {u["id"] for u in body}
        assert "u-alpha" in ids and "u-bravo" in ids
        # All returned users must actually be in Seattle.
        assert all(u["city"] == "Seattle" for u in body), body

    def test_list_users_by_city_no_match_empty_array(self, seeded_users, api):
        r = api.api("GET", "/users", params={"city": "NoSuchCity"})
        assert r.status_code == 200, r.text
        assert r.json() == []
