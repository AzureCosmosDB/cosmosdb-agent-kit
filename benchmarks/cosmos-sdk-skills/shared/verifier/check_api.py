"""API conformance checks — contract-driven.

Runs against the agent's live HTTP server (already started by runner.sh).
Every assertion is derived from the active scenario contract
(/verifier/contracts/<scenario>.json), so the same engine grades mosaic
(users), ticketing (events) and iot (devices) without code changes.

For each declared *root* entity the contract may define:

    create  -> POST <path>                (required)
    get     -> GET  <path with {id}>      (optional; iot devices have none)
    list    -> GET  <path>?<param>=<v>    (optional; iot devices have none)

Deterministic seed data lives in the contract; seed_roots (conftest)
POSTs it through the agent's own API before these checks read it back.

Child entities (tickets, readings) and scenario-specific endpoints are
graded by each task's /tests/checks.py, not here.
"""
from __future__ import annotations

import pytest

from conftest import CONTRACT, ROOTS, fmt_path, root_ids


class TestHealth:
    def test_health_returns_200(self, api):
        path = CONTRACT.get("health_path", "/health")
        r = api.api("GET", path)
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, dict)
        assert body.get("status") in ("ok", "OK", "healthy", "Healthy"), body


@pytest.mark.parametrize("root", ROOTS, ids=root_ids)
class TestRootApi:
    """Create/read/list conformance for each aggregate-root entity."""

    def test_create_persists_fields(self, root, seed_roots, api):
        get = root.get("get")
        if not get:
            pytest.skip(f"{root['name']} has no GET-by-id endpoint")
        row = root["seed"][0]
        r = api.api("GET", fmt_path(get["path"], id=row["id"]))
        assert r.status_code == 200, r.text
        body = r.json()
        for field in root.get("compare_fields", []):
            assert body.get(field) == row.get(field), (
                f"{root['name']} {row['id']}: field {field!r} = {body.get(field)!r}, "
                f"expected {row.get(field)!r} (order must round-trip for arrays)."
            )

    def test_get_existing_returns_200(self, root, seed_roots, api):
        get = root.get("get")
        if not get:
            pytest.skip(f"{root['name']} has no GET-by-id endpoint")
        row = root["seed"][-1]
        r = api.api("GET", fmt_path(get["path"], id=row["id"]))
        assert r.status_code == 200, r.text

    def test_get_unknown_returns_404(self, root, seed_roots, api):
        get = root.get("get")
        if not get:
            pytest.skip(f"{root['name']} has no GET-by-id endpoint")
        r = api.api("GET", fmt_path(get["path"], id="does-not-exist-zzz"))
        assert r.status_code == 404, (
            f"Expected 404 for missing {root['name']}, got {r.status_code}"
        )

    def test_list_by_filter_returns_matching(self, root, seed_roots, api):
        lst = root.get("list")
        if not lst:
            pytest.skip(f"{root['name']} has no list endpoint")
        field = lst["filter_field"]
        value = root["seed"][0][field]
        r = api.api("GET", lst["path"], params={lst["filter_param"]: value})
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, list), f"Expected list, got {type(body).__name__}"
        expected_ids = {row["id"] for row in root["seed"] if row.get(field) == value}
        got_ids = {item["id"] for item in body}
        assert expected_ids <= got_ids, (
            f"GET {lst['path']}?{lst['filter_param']}={value} returned {sorted(got_ids)}; "
            f"expected it to include {sorted(expected_ids)}."
        )
        assert all(item.get(field) == value for item in body), (
            f"Every returned {root['name']} must have {field}={value!r}: {body}"
        )

    def test_list_no_match_returns_empty(self, root, seed_roots, api):
        lst = root.get("list")
        if not lst:
            pytest.skip(f"{root['name']} has no list endpoint")
        r = api.api("GET", lst["path"], params={lst["filter_param"]: "no-such-value-zzz"})
        assert r.status_code == 200, r.text
        assert r.json() == [], "A filter value with no matches must return an empty array."
