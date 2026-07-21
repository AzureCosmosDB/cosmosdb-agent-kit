"""Behavioral checks — the concrete, hard-to-game core of the grader.

Contract-driven. For every declared *root* entity we:

    1. Seed deterministic rows through the agent's public HTTP API
       (seed_roots, in conftest).
    2. Independently read the persisted documents straight from the
       Cosmos emulator with the verifier's OWN client (root_persisted).
    3. Assert the API, the persisted bytes and the contract all agree.

This catches what regex cannot: an app that answers HTTP but stores
nothing in Cosmos (in-memory dict / SQLite), a wrong partition-key value,
a filter that returns the wrong rows, or a "create" that silently
overwrites duplicates.

SDK-agnostic: no SDK token in the test names, so these run for every SDK.
"""
from __future__ import annotations

import pytest
from azure.cosmos import exceptions as cosmos_exc

from conftest import ROOTS, emulator_docs_for_id, fmt_path, partition_key_field, root_ids


@pytest.mark.parametrize("root", ROOTS, ids=root_ids)
class TestPersistenceIsReal:
    """Every row POSTed through the API must exist as a real document in
    the emulator. An in-memory / SQLite backend makes these reads empty."""

    def test_every_seeded_row_is_persisted(self, root, seed_roots, root_persisted):
        docs = root_persisted[root["name"]]
        missing = [row["id"] for row in root["seed"] if docs.get(row["id"]) is None]
        assert not missing, (
            f"These {root['name']} rows were accepted by the API but are NOT in "
            f"Cosmos: {missing}. The service must persist through the Cosmos SDK — "
            "an in-memory or SQLite store that never writes to Cosmos fails this gate."
        )

    def test_persisted_fields_match_input(self, root, seed_roots, root_persisted):
        docs = root_persisted[root["name"]]
        for row in root["seed"]:
            doc = docs[row["id"]]
            assert doc is not None, f"{row['id']} not persisted"
            for field in root.get("compare_fields", []):
                assert doc.get(field) == row.get(field), (
                    f"{root['name']} {row['id']}: {field!r} stored as {doc.get(field)!r}, "
                    f"expected {row.get(field)!r} (arrays must round-trip in order)."
                )


@pytest.mark.parametrize("root", ROOTS, ids=root_ids)
class TestRoundTripIntegrity:
    """GET must return what is actually stored in Cosmos, not a cached
    copy that has drifted from the persisted document."""

    def test_api_read_matches_emulator(self, root, seed_roots, root_persisted, api):
        get = root.get("get")
        if not get:
            pytest.skip(f"{root['name']} has no GET-by-id endpoint")
        row = root["seed"][0]
        stored = root_persisted[root["name"]][row["id"]]
        assert stored is not None, f"{row['id']} not persisted; cannot compare"
        r = api.api("GET", fmt_path(get["path"], id=row["id"]))
        assert r.status_code == 200, r.text
        body = r.json()
        for field in root.get("compare_fields", []):
            assert body.get(field) == stored.get(field), (
                f"GET {row['id']} field {field!r} = {body.get(field)!r} but the persisted "
                f"Cosmos document has {stored.get(field)!r}. Reads must serve from Cosmos."
            )


@pytest.mark.parametrize("root", ROOTS, ids=root_ids)
class TestDuplicateRejection:
    """POSTing an already-used id must be rejected AND must not create a
    second document — the observable contract of a conditional create
    (If-None-Match), proven by behavior instead of scanning source."""

    def test_duplicate_post_is_rejected(self, root, seed_roots, api):
        dup = root["create"].get("duplicate_status")
        if dup is None:
            pytest.skip(f"{root['name']} does not require duplicate rejection")
        row = root["seed"][0]
        r = api.api("POST", root["create"]["path"], json=row)
        assert r.status_code == dup, (
            f"Re-POSTing existing {root['name']} id {row['id']!r} returned "
            f"{r.status_code}, expected {dup}. Unique creates must reject duplicates "
            "atomically (rule sdk-conditional-create-etag), not overwrite or 500."
        )

    def test_duplicate_post_does_not_create_second_doc(self, root, seed_roots, api, root_containers):
        dup = root["create"].get("duplicate_status")
        if dup is None:
            pytest.skip(f"{root['name']} does not require duplicate rejection")
        row = root["seed"][0]
        api.api("POST", root["create"]["path"], json=row)
        rows = emulator_docs_for_id(root_containers[root["name"]], row["id"])
        assert len(rows) == 1, (
            f"Expected exactly 1 persisted {root['name']} for id {row['id']!r}, found "
            f"{len(rows)}. A duplicate create must not add or overwrite a second copy."
        )


@pytest.mark.parametrize("root", ROOTS, ids=root_ids)
class TestPartitionKeyCorrectness:
    def test_stored_partition_value_equals_id(self, root, seed_roots, root_persisted, root_containers):
        if not root.get("partition", {}).get("value_equals_id"):
            pytest.skip(f"{root['name']} partition key is not id-shaped")
        pk = partition_key_field(root_containers[root["name"]])
        assert pk, f"{root['name']} container has no partition key path"
        if pk == "id":
            return
        docs = root_persisted[root["name"]]
        for row in root["seed"]:
            doc = docs[row["id"]]
            assert doc is not None, f"{row['id']} not persisted"
            assert doc.get(pk) == row["id"], (
                f"Partition key is /{pk} but {row['id']}'s stored value is {doc.get(pk)!r}. "
                "The pk value must equal the id so a point read targets one partition."
            )

    def test_point_read_by_partition_succeeds(self, root, seed_roots, root_persisted, root_containers):
        if not root.get("partition", {}).get("value_equals_id"):
            pytest.skip(f"{root['name']} partition key is not id-shaped")
        container = root_containers[root["name"]]
        pk = partition_key_field(container)
        row = root["seed"][0]
        doc = root_persisted[root["name"]][row["id"]]
        assert doc is not None, f"{row['id']} not persisted"
        pk_value = row["id"] if pk in ("", "id") else doc.get(pk, row["id"])
        try:
            got = container.read_item(item=row["id"], partition_key=pk_value)
        except cosmos_exc.CosmosResourceNotFoundError:
            raise AssertionError(
                f"Point read of ({row['id']!r}, pk={pk_value!r}) failed. A single-entity "
                "read must be a single-partition point read; the stored id and pk value "
                "are inconsistent."
            )
        assert got["id"] == row["id"]


@pytest.mark.parametrize("root", ROOTS, ids=root_ids)
class TestFilterQueryCorrectness:
    def test_api_filter_matches_emulator(self, root, seed_roots, api, root_containers):
        lst = root.get("list")
        if not lst:
            pytest.skip(f"{root['name']} has no list endpoint")
        field = lst["filter_field"]
        value = root["seed"][0][field]
        r = api.api("GET", lst["path"], params={lst["filter_param"]: value})
        assert r.status_code == 200, r.text
        api_ids = {item["id"] for item in r.json()}

        emulator_ids = {
            item["id"]
            for item in root_containers[root["name"]].query_items(
                query=f"SELECT c.id FROM c WHERE c.{field} = @v",
                parameters=[{"name": "@v", "value": value}],
                enable_cross_partition_query=True,
            )
        }
        assert api_ids == emulator_ids, (
            f"GET {lst['path']}?{lst['filter_param']}={value} returned {sorted(api_ids)} but "
            f"the emulator holds {sorted(emulator_ids)}. The list endpoint must query Cosmos "
            "and return exactly the matching rows (no extras, no misses)."
        )
