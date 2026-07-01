"""Behavioral checks — the concrete, hard-to-game core of the grader.

Unlike check_source.py / check_advanced_source.py (which regex-scan the
agent's source and therefore prove nothing about runtime behavior), every
test here follows the pattern the MSBench lessons doc calls the only
defensible one:

    1. The app has already been built and started by runner.sh.
    2. We exercise the public HTTP API (the `api` fixture).
    3. We independently read persisted state straight from the Cosmos
       emulator with the verifier's OWN client (never the agent's API).
    4. We assert the two agree AND match the contract.

This catches the failure modes regex cannot: an app that compiles and
answers HTTP but stores nothing in Cosmos (in-memory dict / SQLite), a
wrong partition-key value, a city filter that returns the wrong rows, or a
"create" that silently overwrites duplicates. These map to the Cosmos data
rules (partition-*, model-*, sdk-conditional-create-etag) but are proven by
behavior, not by token matching.

SDK-agnostic: these tests carry no SDK token in their names, so
pytest_collection_modifyitems keeps them for every SDK instance.
"""
from __future__ import annotations

from azure.cosmos import exceptions as cosmos_exc

from conftest import emulator_docs_for_id


# ---------------------------------------------------------------------
# Persistence really happens (the anti-"in-memory fake" gate)
# ---------------------------------------------------------------------

class TestPersistenceIsReal:
    """Every user POSTed through the API must exist as a real document in
    the Cosmos emulator. If the agent backed the service with a dict, a
    list, or SQLite, these reads return nothing and the check fails."""

    def test_every_seeded_user_is_persisted_in_cosmos(self, seeded_users, persisted_docs):
        missing = [u["id"] for u in seeded_users if persisted_docs.get(u["id"]) is None]
        assert not missing, (
            f"These users were accepted by the API but are NOT in the Cosmos "
            f"emulator: {missing}. The service must persist through the Cosmos "
            "SDK — an in-memory or SQLite store that never writes to Cosmos "
            "fails this gate."
        )

    def test_persisted_fields_match_the_input(self, seeded_users, persisted_docs):
        for u in seeded_users:
            doc = persisted_docs[u["id"]]
            assert doc is not None, f"{u['id']} not persisted"
            assert doc.get("name") == u["name"], f"{u['id']}: name mismatch in Cosmos"
            assert doc.get("email") == u["email"], f"{u['id']}: email mismatch in Cosmos"
            assert doc.get("city") == u["city"], f"{u['id']}: city mismatch in Cosmos"
            assert doc.get("interests") == u["interests"], (
                f"{u['id']}: interests changed on persist. Expected {u['interests']}, "
                f"stored {doc.get('interests')!r} — order must round-trip exactly."
            )


# ---------------------------------------------------------------------
# Round-trip integrity: API read == persisted document
# ---------------------------------------------------------------------

class TestRoundTripIntegrity:
    """GET /users/{id} must return what is actually stored in Cosmos, not a
    cached copy that has drifted from the persisted document."""

    def test_api_read_matches_emulator(self, seeded_users, persisted_docs, api):
        u = seeded_users[0]
        stored = persisted_docs[u["id"]]
        assert stored is not None, f"{u['id']} not persisted; cannot compare"

        r = api.api("GET", f"/users/{u['id']}")
        assert r.status_code == 200, r.text
        body = r.json()
        for field in ("name", "email", "city", "interests"):
            assert body.get(field) == stored.get(field), (
                f"GET /users/{u['id']} field {field!r} = {body.get(field)!r} but the "
                f"persisted Cosmos document has {stored.get(field)!r}. The read path "
                "must serve the document from Cosmos."
            )


# ---------------------------------------------------------------------
# Conditional create / duplicate rejection (sdk-conditional-create-etag)
# ---------------------------------------------------------------------

class TestDuplicateRejection:
    """POSTing an already-used id must be rejected (409) AND must not create
    a second document. This is the observable contract of a conditional
    create (If-None-Match) — proven by behavior instead of scanning source
    for `IfNoneMatchEtag`."""

    def test_duplicate_post_returns_409(self, seeded_users, api):
        u = seeded_users[0]
        r = api.api("POST", "/users", json=u)
        assert r.status_code == 409, (
            f"Re-POSTing existing id {u['id']!r} returned {r.status_code}, expected 409. "
            "Creates that must be unique should reject duplicates atomically "
            "(rule sdk-conditional-create-etag), not overwrite or 500."
        )

    def test_duplicate_post_does_not_create_second_doc(self, seeded_users, api, cosmos_users_container):
        u = seeded_users[0]
        # Attempt the duplicate (idempotent 409) then count what Cosmos holds.
        api.api("POST", "/users", json=u)
        rows = emulator_docs_for_id(cosmos_users_container, u["id"])
        assert len(rows) == 1, (
            f"Expected exactly 1 persisted document for id {u['id']!r}, found {len(rows)}. "
            "A duplicate create must not add or overwrite a second copy."
        )


# ---------------------------------------------------------------------
# Partition-key correctness (partition-* rules), proven against Cosmos
# ---------------------------------------------------------------------

class TestPartitionKeyCorrectness:
    def test_stored_partition_value_equals_user_id(
        self, seeded_users, persisted_docs, users_partition_key_field
    ):
        pk = users_partition_key_field
        assert pk, "users container has no partition key path"
        # /id is trivially the user id. Any other pk path must carry the
        # user id as its value so single-user lookups hit one partition.
        if pk == "id":
            return
        for u in seeded_users:
            doc = persisted_docs[u["id"]]
            assert doc is not None, f"{u['id']} not persisted"
            assert doc.get(pk) == u["id"], (
                f"Partition key is /{pk} but {u['id']}'s stored value is "
                f"{doc.get(pk)!r}. The pk value must equal the user id so a point "
                "read targets exactly one logical partition."
            )

    def test_point_read_by_partition_succeeds(
        self, seeded_users, persisted_docs, users_partition_key_field, cosmos_users_container
    ):
        pk = users_partition_key_field
        u = seeded_users[0]
        doc = persisted_docs[u["id"]]
        assert doc is not None, f"{u['id']} not persisted"
        pk_value = u["id"] if pk in ("", "id") else doc.get(pk, u["id"])
        try:
            got = cosmos_users_container.read_item(item=u["id"], partition_key=pk_value)
        except cosmos_exc.CosmosResourceNotFoundError:
            raise AssertionError(
                f"Point read of ({u['id']!r}, pk={pk_value!r}) failed. A single-user "
                "read must be a single-partition point read; the stored id and pk "
                "value are inconsistent."
            )
        assert got["id"] == u["id"]


# ---------------------------------------------------------------------
# City filter correctness, cross-checked against the emulator's own query
# ---------------------------------------------------------------------

class TestCityQueryCorrectness:
    def test_api_city_list_matches_emulator(self, seeded_users, api, cosmos_users_container):
        city = "Seattle"
        r = api.api("GET", "/users", params={"city": city})
        assert r.status_code == 200, r.text
        api_ids = {row["id"] for row in r.json()}

        emulator_ids = {
            row["id"]
            for row in cosmos_users_container.query_items(
                query="SELECT c.id FROM c WHERE c.city = @city",
                parameters=[{"name": "@city", "value": city}],
                enable_cross_partition_query=True,
            )
        }
        assert api_ids == emulator_ids, (
            f"GET /users?city={city} returned {sorted(api_ids)} but the emulator holds "
            f"{sorted(emulator_ids)} for that city. The list endpoint must query Cosmos "
            "and return exactly the matching rows (no extras, no misses)."
        )

    def test_unknown_city_returns_empty(self, seeded_users, api):
        r = api.api("GET", "/users", params={"city": "NoSuchCity"})
        assert r.status_code == 200, r.text
        assert r.json() == [], "A city with no users must return an empty array."
