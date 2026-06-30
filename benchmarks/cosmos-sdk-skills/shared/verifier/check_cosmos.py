"""Cosmos data-shape checks.

After the API tests have seeded users, inspect the actual documents in
the emulator to verify the agent made the right Cosmos modelling
decisions. These checks are language-agnostic — they look only at what
was persisted, not at the agent's source code.
"""
from __future__ import annotations

import datetime as dt
import re

import pytest
from azure.cosmos import exceptions as cosmos_exc

ISO_8601 = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})$"
)


class TestPartitionKey:
    def test_users_container_has_partition_key(self, cosmos_users_container):
        meta = cosmos_users_container.read()
        pk = meta.get("partitionKey", {}).get("paths", [])
        assert pk, f"users container has no partition key: {meta}"

    def test_users_partition_key_is_not_city(self, cosmos_users_container):
        pk = cosmos_users_container.read().get("partitionKey", {}).get("paths", [])
        assert pk != ["/city"], (
            "Partition key is /city. Cities are a long-tail distribution; this will "
            "create hot partitions for popular cities and waste RUs on small ones. "
            "Use a userId-shaped key (e.g. /userId, /pk where pk == userId)."
        )

    def test_users_partition_key_is_user_shaped(self, cosmos_users_container, seeded_users, api):
        pk_paths = cosmos_users_container.read().get("partitionKey", {}).get("paths", [])
        pk = pk_paths[0].lstrip("/") if pk_paths else ""
        # Acceptable shapes: /id, /userId, /pk where the stored pk value
        # equals the user id, or /partitionKey same thing.
        # Verify by reading one of the seeded users and confirming the pk
        # field's value equals the user id.
        u = seeded_users[0]
        try:
            doc = cosmos_users_container.read_item(item=u["id"], partition_key=u["id"])
        except cosmos_exc.CosmosResourceNotFoundError:
            # Maybe the pk value isn't the user id itself — try querying.
            results = list(cosmos_users_container.query_items(
                query="SELECT * FROM c WHERE c.id = @id",
                parameters=[{"name": "@id", "value": u["id"]}],
                enable_cross_partition_query=True,
            ))
            assert results, f"User {u['id']} not found in container"
            doc = results[0]
        # If pk path is something like /userId, the value should equal id.
        pk_value = doc.get(pk)
        assert pk_value == u["id"] or pk in {"id", "userId", "pk", "partitionKey"}, (
            f"Partition key path is /{pk} but stored value {pk_value!r} != user id {u['id']!r}. "
            "Single-user lookups must hit one logical partition."
        )


class TestIndexingPolicy:
    def test_indexing_policy_present(self, cosmos_users_container):
        pol = cosmos_users_container.read().get("indexingPolicy")
        assert pol, "users container has no indexingPolicy"

    def test_indexing_policy_is_not_pure_default(self, cosmos_users_container):
        """Reject the canonical default everything-indexed policy.
        A reasonable choice is either composite/spatial/vector indexes,
        or excluding noisy paths, or switching from consistent to lazy.
        """
        pol = cosmos_users_container.read().get("indexingPolicy", {})
        included = pol.get("includedPaths", [])
        excluded = pol.get("excludedPaths", [])
        composites = pol.get("compositeIndexes", [])
        # Default policy is: includedPaths = [{"path": "/*"}], excludedPaths = [].
        # Any tailoring counts: excludes present, composites declared, etc.
        is_pure_default = (
            len(included) == 1 and included[0].get("path") == "/*"
            and not excluded
            and not composites
        )
        assert not is_pure_default, (
            "indexingPolicy is the default everything-indexed-no-excludes policy. "
            "For a write-heavy user catalog, exclude noisy paths or declare a "
            "composite index for the city filter (rule index-tailor-policy)."
        )

    def test_indexing_policy_excludes_unused_paths(self, cosmos_users_container):
        """Rule index-exclude-unused: at least one excludedPath beyond
        the system `_etag` entry. The Mosaic schema has 'email' and
        'interests' as plausible exclusion candidates — neither is
        filtered on. We don't require a specific path, only that the
        agent went past the bare-minimum system exclusion."""
        pol = cosmos_users_container.read().get("indexingPolicy", {})
        excluded = pol.get("excludedPaths", []) or []
        # Normalize the system _etag exclusion shapes the SDKs emit.
        def _is_system(p: str) -> bool:
            p = (p or "").strip()
            return p in {
                '/"_etag"/?',
                "/_etag/?",
                '/"_etag"/*',
            }
        meaningful = [e for e in excluded if not _is_system(e.get("path", ""))]
        assert meaningful, (
            "indexingPolicy.excludedPaths only contains the system _etag entry. "
            "Rule index-exclude-unused: drop indexes from fields you never filter "
            "on (the Mosaic schema has `email` and `interests` as obvious candidates). "
            "Every indexed path adds write RU; reducing index breadth on a write-heavy "
            "user catalog cuts write RU 20-80%."
        )


class TestThroughput:
    def test_throughput_configured(self, cosmos_database, cosmos_users_container):
        # Either database-level or container-level throughput must be set.
        db_offer = None
        try:
            db_offer = cosmos_database.get_throughput()
        except cosmos_exc.CosmosHttpResponseError:
            pass
        container_offer = None
        try:
            container_offer = cosmos_users_container.get_throughput()
        except cosmos_exc.CosmosHttpResponseError:
            pass
        assert db_offer is not None or container_offer is not None, (
            "No throughput configured at either the database or container level. "
            "Rule throughput-explicit: declare provisioned RU/s or autoscale on the "
            "container or the shared database."
        )


class TestDocumentShape:
    def test_documents_have_type_discriminator(self, cosmos_users_container, seeded_users):
        docs = list(cosmos_users_container.query_items(
            query="SELECT * FROM c", enable_cross_partition_query=True,
        ))
        assert docs, "no documents in users container"
        TYPE_FIELDS = {"type", "_type", "documentType", "entityType", "kind"}
        for d in docs[:5]:
            assert any(f in d for f in TYPE_FIELDS), (
                f"Document {d.get('id')!r} has no type discriminator. "
                f"Rule model-type-discriminator: add one of {TYPE_FIELDS}."
            )

    def test_documents_have_schema_version(self, cosmos_users_container):
        docs = list(cosmos_users_container.query_items(
            query="SELECT * FROM c", enable_cross_partition_query=True,
        ))
        VERSION_FIELDS = {"schemaVersion", "_version", "version", "v"}
        for d in docs[:5]:
            assert any(f in d for f in VERSION_FIELDS), (
                f"Document {d.get('id')!r} has no schema version field. "
                f"Rule model-schema-version: stamp documents with one of {VERSION_FIELDS}."
            )

    def test_createdAt_is_iso8601_string(self, cosmos_users_container):
        docs = list(cosmos_users_container.query_items(
            query="SELECT * FROM c", enable_cross_partition_query=True,
        ))
        for d in docs[:5]:
            ts = d.get("createdAt") or d.get("created_at")
            assert ts is not None, f"{d.get('id')!r} missing createdAt"
            assert isinstance(ts, str), (
                f"createdAt is {type(ts).__name__}, expected ISO-8601 string. "
                "Rule model-iso8601-timestamps: store timestamps as ISO-8601 strings, "
                "not epoch numbers (Cosmos query / indexing works correctly with strings)."
            )
            assert ISO_8601.match(ts), f"createdAt {ts!r} is not ISO-8601"
            dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))

    def test_interests_stored_as_string_array(self, cosmos_users_container):
        docs = list(cosmos_users_container.query_items(
            query="SELECT * FROM c", enable_cross_partition_query=True,
        ))
        for d in docs[:5]:
            interests = d.get("interests")
            assert isinstance(interests, list), (
                f"interests on {d.get('id')!r} is {type(interests).__name__}, expected list"
            )
            assert all(isinstance(x, str) for x in interests), (
                f"interests on {d.get('id')!r} contains non-strings: {interests}"
            )

    def test_email_and_city_are_strings(self, cosmos_users_container):
        docs = list(cosmos_users_container.query_items(
            query="SELECT * FROM c", enable_cross_partition_query=True,
        ))
        for d in docs[:5]:
            assert isinstance(d.get("email"), str)
            assert isinstance(d.get("city"), str)
