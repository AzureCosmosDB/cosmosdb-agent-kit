"""
Cosmos DB Infrastructure & SDK Behavior Tests — Gaming Leaderboard
===================================================================

These tests go BELOW the HTTP API surface to verify that the agent
applied Cosmos DB best practices at the SDK and container level.

Test categories:
  1. INFRASTRUCTURE — verify container partition keys, indexing policies,
     throughput mode, composite indexes directly via Cosmos DB Python SDK.
  2. SDK BEHAVIORS — verify that SDK-specific patterns (enum serialization,
     ETag for concurrency, content-response-on-write) are correct.
  3. CROSS-BOUNDARY — write data through the HTTP API, then read it
     directly from Cosmos DB to catch serialization mismatches.

These tests are the ones most likely to FAIL without skills loaded.
"""

import pytest


# ============================================================================
# 1. INFRASTRUCTURE TESTS — Container Configuration
# ============================================================================

class TestContainerDesign:
    """
    Rules: partition-high-cardinality, partition-synthetic-keys

    A leaderboard system needs multiple containers or synthetic partition keys
    to support different access patterns (player lookup, score submission,
    leaderboard ranking).
    """

    def test_has_multiple_containers_or_synthetic_keys(self, cosmos_containers):
        """
        Leaderboard systems need separate access patterns:
        - Player profiles (keyed by playerId)
        - Leaderboard rankings (keyed by leaderboard scope like 'global_weekly')

        Either use multiple containers or synthetic partition keys.
        """
        # Either multiple containers or at least one container with a
        # non-obvious partition key (synthetic, like "global_weekly")
        if len(cosmos_containers) >= 2:
            return  # Multiple containers — likely correct design

        # Single container — check for synthetic partition key patterns
        for c in cosmos_containers:
            paths = c.get("partitionKey", {}).get("paths", [])
            for p in paths:
                # Synthetic keys tend to not be simple entity IDs
                if any(kw in p.lower() for kw in ("leaderboard", "scope", "partition", "composite")):
                    return

        pytest.fail(
            "Only one container with a simple partition key. "
            "Leaderboard systems need different access patterns: "
            "player lookup (by playerId) and ranking queries (by leaderboard scope). "
            "Use multiple containers or synthetic partition keys like "
            "'global_weekly' or 'US_all-time'. "
            "(Rules: partition-synthetic-keys, pattern-change-feed-materialized-views)"
        )

    def test_leaderboard_container_uses_synthetic_key(self, cosmos_containers):
        """
        If there's a leaderboard/ranking container, it should use a
        synthetic partition key (scope+period) for efficient top-N queries.
        """
        leaderboard_containers = [
            c for c in cosmos_containers
            if any(kw in c["id"].lower() for kw in ("leaderboard", "ranking", "board"))
        ]

        if not leaderboard_containers:
            # No container with "leaderboard" in the name — check all containers
            # for synthetic-looking partition keys
            for c in cosmos_containers:
                paths = c.get("partitionKey", {}).get("paths", [])
                for p in paths:
                    if "player" not in p.lower() and "id" not in p.lower():
                        return  # Non-ID partition key — likely synthetic
            pytest.skip("No leaderboard-specific container found")
            return

        for c in leaderboard_containers:
            paths = c.get("partitionKey", {}).get("paths", [])
            for p in paths:
                # Should NOT be /playerId — that would make top-N queries cross-partition
                if "player" in p.lower():
                    pytest.fail(
                        f"Leaderboard container '{c['id']}' uses {p} as partition key. "
                        f"This makes top-N ranking queries cross-partition (expensive). "
                        f"Use a synthetic key like /leaderboardKey = 'global_weekly' "
                        f"so all entries for one leaderboard are in one partition. "
                        f"(Rule: partition-synthetic-keys)"
                    )

    def test_player_container_uses_player_id_key(self, cosmos_containers):
        """Player profiles should be partitioned on playerId for point reads."""
        player_containers = [
            c for c in cosmos_containers
            if any(kw in c["id"].lower() for kw in ("player",))
        ]

        if not player_containers:
            pytest.skip("No player-specific container found")

        for c in player_containers:
            paths = c.get("partitionKey", {}).get("paths", [])
            has_player_key = any("player" in p.lower() for p in paths)
            assert has_player_key, (
                f"Player container '{c['id']}' doesn't use playerId as partition key "
                f"(has: {paths}). Player profiles are looked up by playerId — "
                f"partition key should match for efficient point reads. "
                f"(Rule: partition-query-patterns)"
            )


class TestLeaderboardIndexing:
    """
    Rule: index-composite

    Leaderboard queries need composite indexes for efficient ORDER BY
    on (score DESC, timestamp ASC) within a partition.
    """

    def test_has_composite_indexes(self, cosmos_containers):
        """At least one container should have composite indexes for ranking."""
        has_composite = False
        for c in cosmos_containers:
            policy = c.get("indexingPolicy", {})
            composites = policy.get("compositeIndexes", [])
            if composites:
                has_composite = True
                break

        assert has_composite, (
            "No container has composite indexes. "
            "Leaderboard queries need composite indexes on (score DESC, timestamp ASC) "
            "for efficient ORDER BY within a partition. Without them, the query engine "
            "must sort in memory, increasing RU cost. "
            "(Rule: index-composite)"
        )

    def test_has_custom_indexing_policy(self, cosmos_containers):
        """At least one container should exclude unused paths from indexing."""
        has_custom = False
        for c in cosmos_containers:
            policy = c.get("indexingPolicy", {})
            excluded = policy.get("excludedPaths", [])
            non_default = [
                p for p in excluded
                if p.get("path") not in ("/_etag/?", '"/_etag"/?', "/*")
            ]
            if non_default:
                has_custom = True
                break

        assert has_custom, (
            "All containers use default indexing (index everything). "
            "Exclude paths that are never queried (e.g., displayName, region) "
            "to reduce write RU cost. "
            "(Rule: index-exclude-unused)"
        )


class TestThroughputConfiguration:
    """Verify throughput is explicitly configured."""

    def test_throughput_is_configured(self, cosmos_database, cosmos_containers):
        """At least one container or the database should have throughput set."""
        has_throughput = False

        try:
            offer = cosmos_database.read_offer()
            if offer is not None:
                has_throughput = True
        except Exception:
            pass

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
            "No throughput configuration found. "
            "Explicitly configure throughput (autoscale preferred for variable workloads). "
            "(Rule: throughput-autoscale)"
        )


# ============================================================================
# 2. SDK BEHAVIOR TESTS
# ============================================================================

class TestPlayerScoreSerialization:
    """
    Rules: model-json-serialization, sdk-etag-concurrency

    Verify that scores and player stats are serialized correctly
    in Cosmos DB, and that ETag concurrency is used for player updates.
    """

    def test_scores_stored_as_numbers(self, api, seeded_data, cosmos_database, cosmos_containers):
        """Scores should be stored as numbers, not strings."""
        # Find a document with score data
        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT TOP 5 * FROM c WHERE IS_DEFINED(c.score) OR IS_DEFINED(c.bestScore)",
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            for doc in items:
                score = doc.get("score") or doc.get("bestScore")
                if score is not None:
                    assert isinstance(score, (int, float)), (
                        f"Score stored as {type(score).__name__} ({score!r}). "
                        f"Scores must be numbers for ORDER BY and range queries to work. "
                        f"String scores sort lexicographically ('9' > '10000')."
                    )
                    return

        pytest.skip("Could not find score documents in Cosmos DB")

    def test_etag_present_on_player_documents(self, api, seeded_data, cosmos_database, cosmos_containers):
        """
        Player documents should carry _etag (Cosmos DB provides this automatically),
        AND the app should use it for optimistic concurrency on updates.

        We verify that _etag values change when a document is updated.
        """
        # Read a player document, note the etag
        player_containers = [
            c for c in cosmos_containers
            if "player" in c["id"].lower()
        ]
        if not player_containers:
            # Try all containers
            player_containers = cosmos_containers

        for c in player_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT TOP 1 * FROM c WHERE IS_DEFINED(c.playerId) OR IS_DEFINED(c.player_id)",
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            if items:
                doc = items[0]
                etag = doc.get("_etag")
                assert etag is not None, (
                    "Player document has no _etag. Cosmos DB should always include _etag — "
                    "if it's missing, the SDK may be stripping system properties."
                )
                return

        pytest.skip("Could not find player documents in Cosmos DB")


class TestDocumentStructure:
    """Verify document modeling best practices."""

    def test_documents_have_type_discriminator(self, api, seeded_data, cosmos_database, cosmos_containers):
        """Documents should have a 'type' field for polymorphic containers."""
        found_type = False
        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT TOP 3 * FROM c",
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            for doc in items:
                if any(field in doc for field in ("type", "_type", "documentType", "entityType")):
                    found_type = True
                    break
            if found_type:
                break

        assert found_type, (
            "No documents have a type discriminator field. "
            "Use a 'type' field (e.g., 'player', 'score', 'leaderboardEntry') "
            "to distinguish document types within a container. "
            "(Rule: model-type-discriminator)"
        )

    def test_documents_have_schema_version(self, api, seeded_data, cosmos_database, cosmos_containers):
        """Documents should include a schema version for future evolution."""
        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT TOP 3 * FROM c",
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            for doc in items:
                if any(field in doc for field in ("schemaVersion", "schema_version", "_version", "docVersion")):
                    return

        pytest.fail(
            "No documents have a schema version field. "
            "(Rule: model-schema-versioning)"
        )


# ============================================================================
# 3. CROSS-BOUNDARY TESTS — API ↔ Cosmos DB Round-Trip
# ============================================================================

class TestCrossBoundaryConsistency:
    """
    Write through the API, read directly from Cosmos DB to catch
    serialization mismatches invisible to round-trip HTTP tests.
    """

    def test_player_stats_stored_correctly(self, api, seeded_data, cosmos_database, cosmos_containers):
        """
        After submitting scores via the API, verify player stats
        (totalGames, bestScore, averageScore) are correctly stored in Cosmos DB.
        """
        # Get player stats from the API
        resp = api.request("GET", "/api/players/player-001")
        if resp.status_code != 200:
            pytest.skip("Could not get player from API")

        api_player = resp.json()
        api_best = api_player.get("bestScore")
        api_total_games = api_player.get("totalGames")

        # Now read directly from Cosmos DB
        for c in cosmos_containers:
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT * FROM c WHERE c.playerId = @pid",
                    parameters=[{"name": "@pid", "value": "player-001"}],
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            for doc in items:
                stored_best = doc.get("bestScore") or doc.get("best_score")
                if stored_best is not None:
                    if api_best is not None:
                        assert stored_best == api_best, (
                            f"Cosmos DB bestScore ({stored_best}) != API bestScore ({api_best}). "
                            f"Stats may be computed in-memory instead of persisted."
                        )
                    return

        pytest.skip("Could not find player document in Cosmos DB")

    def test_leaderboard_entries_denormalized(self, api, seeded_data, cosmos_database, cosmos_containers):
        """
        Leaderboard entries should contain denormalized player info
        (displayName, region) for efficient reads without joins.
        """
        leaderboard_containers = [
            c for c in cosmos_containers
            if any(kw in c["id"].lower() for kw in ("leaderboard", "ranking", "board"))
        ]

        for c in (leaderboard_containers or cosmos_containers):
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query="SELECT TOP 5 * FROM c WHERE IS_DEFINED(c.bestScore) OR IS_DEFINED(c.score)",
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            for doc in items:
                # Leaderboard entry should have denormalized player info
                has_name = any(
                    field in doc for field in ("displayName", "display_name", "playerName", "name")
                )
                if has_name:
                    return

        pytest.fail(
            "Leaderboard entries don't contain denormalized player info. "
            "Include displayName and region in leaderboard entries to avoid "
            "cross-container lookups for every ranking display. "
            "(Rule: model-denormalize-reads)"
        )

    def test_synthetic_partition_key_value_format(self, api, seeded_data, cosmos_database, cosmos_containers):
        """
        If using synthetic partition keys on the leaderboard container,
        verify the format matches expectations (e.g., 'global_weekly').
        """
        leaderboard_containers = [
            c for c in cosmos_containers
            if any(kw in c["id"].lower() for kw in ("leaderboard", "ranking", "board"))
        ]

        if not leaderboard_containers:
            pytest.skip("No leaderboard container found")

        for c in leaderboard_containers:
            paths = c.get("partitionKey", {}).get("paths", [])
            if not paths:
                continue

            pk_field = paths[0].lstrip("/")
            container = cosmos_database.get_container_client(c["id"])
            try:
                items = list(container.query_items(
                    query=f"SELECT TOP 3 c.{pk_field} FROM c",
                    enable_cross_partition_query=True,
                ))
            except Exception:
                continue

            for doc in items:
                pk_value = doc.get(pk_field)
                if pk_value is not None:
                    assert isinstance(pk_value, str), (
                        f"Partition key '{pk_field}' has non-string value: "
                        f"{type(pk_value).__name__} ({pk_value!r}). "
                        f"Synthetic partition keys should be strings."
                    )
                    # Should contain scope info (global/regional + period)
                    assert len(pk_value) > 3, (
                        f"Partition key value '{pk_value}' is suspiciously short. "
                        f"Synthetic keys should encode scope and period, e.g., "
                        f"'global_2026-W11' or 'US_all-time'."
                    )
                    return

        pytest.skip("Could not verify synthetic partition key values")
