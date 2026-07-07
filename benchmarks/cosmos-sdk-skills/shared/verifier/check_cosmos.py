"""Cosmos data-shape checks — contract-driven.

After the API tests have seeded the root entities, inspect the actual
documents + container metadata in the emulator to verify the agent made
sound Cosmos modelling decisions. Language-agnostic: these look only at
what was persisted and how the container is configured, never at source.

Every expectation is toggled per entity by the contract's `partition`,
`modeling`, `indexing` and `throughput` blocks, so mosaic / ticketing /
iot each get exactly the checks their contract declares.
"""
from __future__ import annotations

import datetime as dt
import re

import pytest
from azure.cosmos import exceptions as cosmos_exc

from conftest import ROOTS, partition_key_field, root_ids

ISO_8601 = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})$"
)


def _all_docs(container):
    return list(container.query_items(
        query="SELECT * FROM c", enable_cross_partition_query=True,
    ))


@pytest.mark.parametrize("root", ROOTS, ids=root_ids)
class TestPartitionKey:
    def test_container_has_partition_key(self, root, seed_roots, root_containers):
        meta = root_containers[root["name"]].read()
        pk = meta.get("partitionKey", {}).get("paths", [])
        assert pk, f"{root['name']} container has no partition key: {meta}"

    def test_partition_key_not_forbidden(self, root, seed_roots, root_containers):
        forbid = root.get("partition", {}).get("forbid_paths", [])
        if not forbid:
            pytest.skip(f"{root['name']} declares no forbidden partition paths")
        pk = root_containers[root["name"]].read().get("partitionKey", {}).get("paths", [])
        assert pk not in ([f] for f in forbid), (
            f"Partition key {pk} is a forbidden low-cardinality / hot-partition choice "
            f"for {root['name']} (forbidden: {forbid}). Use an id-shaped key."
        )


@pytest.mark.parametrize("root", ROOTS, ids=root_ids)
class TestIndexingPolicy:
    def test_indexing_policy_present(self, root, seed_roots, root_containers):
        pol = root_containers[root["name"]].read().get("indexingPolicy")
        assert pol, f"{root['name']} container has no indexingPolicy"

    def test_indexing_policy_is_not_pure_default(self, root, seed_roots, root_containers):
        if not root.get("indexing", {}).get("require_non_default"):
            pytest.skip(f"{root['name']} does not require a tailored indexing policy")
        pol = root_containers[root["name"]].read().get("indexingPolicy", {})
        included = pol.get("includedPaths", [])
        excluded = pol.get("excludedPaths", [])
        composites = pol.get("compositeIndexes", [])
        is_pure_default = (
            len(included) == 1 and included[0].get("path") == "/*"
            and not excluded
            and not composites
        )
        assert not is_pure_default, (
            f"{root['name']} indexingPolicy is the default everything-indexed-no-excludes "
            "policy. Tailor it: exclude noisy paths or declare a composite index "
            "(rule index-tailor-policy)."
        )

    def test_indexing_policy_excludes_unused_paths(self, root, seed_roots, root_containers):
        if not root.get("indexing", {}).get("require_excludes"):
            pytest.skip(f"{root['name']} does not require excluded paths")
        pol = root_containers[root["name"]].read().get("indexingPolicy", {})
        excluded = pol.get("excludedPaths", []) or []

        def _is_system(p: str) -> bool:
            p = (p or "").strip()
            return p in {'/"_etag"/?', "/_etag/?", '/"_etag"/*'}

        meaningful = [e for e in excluded if not _is_system(e.get("path", ""))]
        assert meaningful, (
            f"{root['name']} indexingPolicy.excludedPaths only contains the system _etag "
            "entry. Rule index-exclude-unused: drop indexes from fields you never filter "
            "on. Every indexed path adds write RU."
        )


@pytest.mark.parametrize("root", ROOTS, ids=root_ids)
class TestThroughput:
    def test_throughput_configured(self, root, seed_roots, cosmos_database, root_containers):
        if not root.get("throughput", {}).get("required"):
            pytest.skip(f"{root['name']} does not require explicit throughput")
        db_offer = None
        try:
            db_offer = cosmos_database.get_throughput()
        except cosmos_exc.CosmosHttpResponseError:
            pass
        container_offer = None
        try:
            container_offer = root_containers[root["name"]].get_throughput()
        except cosmos_exc.CosmosHttpResponseError:
            pass
        assert db_offer is not None or container_offer is not None, (
            f"No throughput configured for {root['name']} at either the database or "
            "container level. Rule throughput-explicit: declare provisioned RU/s or "
            "autoscale."
        )


@pytest.mark.parametrize("root", ROOTS, ids=root_ids)
class TestDocumentShape:
    TYPE_FIELDS = {"type", "_type", "documentType", "entityType", "kind"}
    VERSION_FIELDS = {"schemaVersion", "_version", "version", "v"}

    def test_documents_have_type_discriminator(self, root, seed_roots, root_containers):
        if not root.get("modeling", {}).get("type_discriminator"):
            pytest.skip(f"{root['name']} does not require a type discriminator")
        for d in _all_docs(root_containers[root["name"]])[:5]:
            assert any(f in d for f in self.TYPE_FIELDS), (
                f"{root['name']} document {d.get('id')!r} has no type discriminator. "
                f"Rule model-type-discriminator: add one of {self.TYPE_FIELDS}."
            )

    def test_documents_have_schema_version(self, root, seed_roots, root_containers):
        if not root.get("modeling", {}).get("schema_version"):
            pytest.skip(f"{root['name']} does not require a schema version")
        for d in _all_docs(root_containers[root["name"]])[:5]:
            assert any(f in d for f in self.VERSION_FIELDS), (
                f"{root['name']} document {d.get('id')!r} has no schema version field. "
                f"Rule model-schema-version: stamp one of {self.VERSION_FIELDS}."
            )

    def test_timestamp_is_iso8601_string(self, root, seed_roots, root_containers):
        ts_field = root.get("modeling", {}).get("timestamp_field")
        if not ts_field:
            pytest.skip(f"{root['name']} does not require a timestamp field")
        for d in _all_docs(root_containers[root["name"]])[:5]:
            ts = d.get(ts_field)
            assert ts is not None, f"{d.get('id')!r} missing {ts_field}"
            assert isinstance(ts, str), (
                f"{ts_field} on {d.get('id')!r} is {type(ts).__name__}, expected ISO-8601 "
                "string. Rule model-iso8601-timestamps: store timestamps as ISO-8601 "
                "strings, not epoch numbers."
            )
            assert ISO_8601.match(ts), f"{ts_field} {ts!r} is not ISO-8601"
            dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))

    def test_string_array_fields(self, root, seed_roots, root_containers):
        fields = root.get("string_array_fields", [])
        if not fields:
            pytest.skip(f"{root['name']} declares no string-array fields")
        for d in _all_docs(root_containers[root["name"]])[:5]:
            for field in fields:
                arr = d.get(field)
                assert isinstance(arr, list), (
                    f"{field} on {d.get('id')!r} is {type(arr).__name__}, expected list"
                )
                assert all(isinstance(x, str) for x in arr), (
                    f"{field} on {d.get('id')!r} contains non-strings: {arr}"
                )

    def test_string_fields_are_strings(self, root, seed_roots, root_containers):
        fields = root.get("string_fields", [])
        if not fields:
            pytest.skip(f"{root['name']} declares no string fields")
        for d in _all_docs(root_containers[root["name"]])[:5]:
            for field in fields:
                assert isinstance(d.get(field), str), (
                    f"{field} on {d.get('id')!r} is {type(d.get(field)).__name__}, expected str"
                )

    def test_int_fields_are_ints(self, root, seed_roots, root_containers):
        fields = root.get("int_fields", [])
        if not fields:
            pytest.skip(f"{root['name']} declares no integer fields")
        for d in _all_docs(root_containers[root["name"]])[:5]:
            for field in fields:
                v = d.get(field)
                assert isinstance(v, int) and not isinstance(v, bool), (
                    f"{field} on {d.get('id')!r} is {type(v).__name__}, expected int"
                )
