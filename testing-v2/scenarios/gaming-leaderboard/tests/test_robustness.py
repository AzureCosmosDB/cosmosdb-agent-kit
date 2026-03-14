"""
Robustness Tests for Gaming Leaderboard
========================================

These tests go beyond basic API contract compliance to verify the application
handles real-world scenarios correctly:
- Invalid / malformed input → proper 4xx responses (not 500)
- Computed field accuracy (averageScore, totalGames math)
- Data type correctness in responses
- Write-read consistency across endpoints
- Duplicate / conflict handling
- Edge cases and boundary conditions

These tests catch the classes of bugs most commonly produced by AI agents:
enum serialization mismatches, missing input validation, incorrect stat
aggregation, and duplicate entity crashes.
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

    def test_create_player_missing_required_fields_returns_4xx(self, api):
        """POST /api/players with missing playerId should return 400, not 500."""
        resp = api.request("POST", "/api/players", json={
            "displayName": "NoId",
            "region": "US",
        })
        assert 400 <= resp.status_code < 500, (
            f"Missing playerId should return 4xx, got {resp.status_code}. "
            f"The app must validate required fields and return 400."
        )

    def test_create_player_empty_body_returns_4xx(self, api):
        """POST /api/players with empty JSON body should not crash."""
        resp = api.request("POST", "/api/players", json={})
        assert 400 <= resp.status_code < 500, (
            f"Empty body should return 4xx, got {resp.status_code}. "
            f"Server must not crash (500) on missing fields."
        )

    def test_submit_score_missing_player_id_returns_4xx(self, api, seeded_data):
        """POST /api/scores without playerId should return 4xx."""
        resp = api.request("POST", "/api/scores", json={
            "score": 1000,
        })
        assert 400 <= resp.status_code < 500, (
            f"Missing playerId in score should return 4xx, got {resp.status_code}. "
            f"Server must validate required fields."
        )

    def test_submit_score_missing_score_returns_4xx(self, api, seeded_data):
        """POST /api/scores without score field should return 4xx."""
        resp = api.request("POST", "/api/scores", json={
            "playerId": "player-001",
        })
        assert 400 <= resp.status_code < 500, (
            f"Missing score field should return 4xx, got {resp.status_code}. "
            f"Server must validate required fields."
        )

    def test_submit_score_negative_value_returns_4xx(self, api, seeded_data):
        """POST /api/scores with negative score should be rejected."""
        resp = api.request("POST", "/api/scores", json={
            "playerId": "player-001",
            "score": -100,
        })
        assert 400 <= resp.status_code < 500, (
            f"Negative score should return 4xx, got {resp.status_code}. "
            f"Scores should be positive integers per the contract."
        )

    def test_submit_score_for_nonexistent_player_returns_4xx(self, api, seeded_data):
        """POST /api/scores for a player that doesn't exist should return 4xx."""
        resp = api.request("POST", "/api/scores", json={
            "playerId": "does-not-exist-xyz",
            "score": 5000,
        })
        assert 400 <= resp.status_code < 500, (
            f"Score for nonexistent player should return 4xx, got {resp.status_code}. "
            f"Server should validate player exists before recording score."
        )


# ===================================================================
# DUPLICATE / CONFLICT HANDLING
# ===================================================================

class TestDuplicateHandling:
    """
    Creating the same entity twice must not crash the server.
    Expected: 409 Conflict, or idempotent 200/201.
    """

    def test_create_duplicate_player_does_not_return_500(self, api):
        """Creating the same player twice must not cause a server error."""
        player = {
            "playerId": "duplicate-test-001",
            "displayName": "DupTest",
            "region": "US",
        }
        resp1 = api.request("POST", "/api/players", json=player)
        assert resp1.status_code == 201, (
            f"First creation should succeed with 201, got {resp1.status_code}"
        )

        resp2 = api.request("POST", "/api/players", json=player)
        assert resp2.status_code != 500, (
            f"Duplicate player creation returned 500 — server crashed. "
            f"Expected 409 Conflict or idempotent 200/201. "
            f"Response: {resp2.text[:300]}"
        )
        assert resp2.status_code < 500, (
            f"Duplicate player creation returned {resp2.status_code} (5xx). "
            f"Expected a client-side error (4xx) or idempotent success (2xx)."
        )


# ===================================================================
# COMPUTED FIELD ACCURACY
# ===================================================================

class TestComputedFieldAccuracy:
    """
    Verify that computed/aggregated fields are mathematically correct.
    This catches bugs where the agent uses wrong formulas or doesn't
    update stats atomically after score submissions.
    """

    def test_average_score_mathematically_correct(self, api, seeded_data):
        """
        player-001 submitted scores: 8200, 7000, 8200 (from seeded data).
        averageScore should be (8200 + 7000 + 8200) / 3 = 7800.0

        Note: additional test scores may have been submitted, so we verify
        the average is reasonable rather than exact if totalGames > 3.
        """
        resp = api.request("GET", "/api/players/player-001")
        assert resp.status_code == 200
        body = resp.json()

        avg = body.get("averageScore", 0)
        best = body.get("bestScore", 0)
        total_games = body.get("totalGames", 0)

        # averageScore must be a positive number if games have been played
        assert avg > 0, (
            f"player-001 has {total_games} games but averageScore is {avg}. "
            f"averageScore should be positive after score submissions."
        )

        # averageScore cannot exceed bestScore
        assert avg <= best, (
            f"averageScore ({avg}) exceeds bestScore ({best}). "
            f"This is mathematically impossible — the average of a set "
            f"can never exceed its maximum."
        )

        # averageScore must be reasonable (between min possible and max possible)
        # Min submitted score for player-001 is 7000, max is 8200
        # With only seeded scores: avg should be 7800
        if total_games == 3:
            assert abs(avg - 7800.0) < 0.01, (
                f"player-001 has 3 games with scores 8200, 7000, 8200. "
                f"averageScore should be 7800.0, got {avg}."
            )

    def test_total_games_count_correct(self, api, seeded_data):
        """player-001 submitted at least 3 scores in seed data."""
        resp = api.request("GET", "/api/players/player-001")
        assert resp.status_code == 200
        body = resp.json()

        total = body.get("totalGames", 0)
        assert total >= 3, (
            f"player-001 submitted 3 scores in seed data but totalGames is {total}. "
            f"Score submissions must increment totalGames."
        )

    def test_best_score_is_maximum(self, api, seeded_data):
        """player-001's bestScore should be max(8200, 7000, 8200) = 8200."""
        resp = api.request("GET", "/api/players/player-001")
        assert resp.status_code == 200
        body = resp.json()

        assert body["bestScore"] == 8200, (
            f"player-001 best score should be 8200 (max of submitted scores), "
            f"got {body['bestScore']}."
        )

    def test_player_with_single_score_stats(self, api, seeded_data):
        """player-004 submitted exactly 1 score (5000). Stats should reflect this."""
        resp = api.request("GET", "/api/players/player-004")
        assert resp.status_code == 200
        body = resp.json()

        assert body.get("totalGames", 0) >= 1, (
            f"player-004 submitted 1 score but totalGames is {body.get('totalGames')}"
        )
        assert body.get("bestScore") == 5000, (
            f"player-004 best score should be 5000, got {body.get('bestScore')}"
        )
        # With a single score, average == best
        if body.get("totalGames") == 1:
            assert abs(body.get("averageScore", 0) - 5000.0) < 0.01, (
                f"With 1 game, averageScore should equal bestScore (5000). "
                f"Got averageScore={body.get('averageScore')}"
            )

    def test_new_score_updates_stats(self, api, seeded_data):
        """
        Submit a new score and verify stats update correctly.
        This catches bugs where stats aren't updated on score submission.
        """
        # Get current stats for player-002
        resp = api.request("GET", "/api/players/player-002")
        assert resp.status_code == 200
        before = resp.json()
        games_before = before.get("totalGames", 0)
        best_before = before.get("bestScore", 0)

        # Submit a new score (lower than best)
        resp = api.request("POST", "/api/scores", json={
            "playerId": "player-002",
            "score": 1000,
        })
        assert resp.status_code == 201

        # Verify stats updated
        resp = api.request("GET", "/api/players/player-002")
        assert resp.status_code == 200
        after = resp.json()

        assert after["totalGames"] == games_before + 1, (
            f"After submitting 1 score, totalGames should increase by 1. "
            f"Before: {games_before}, After: {after['totalGames']}"
        )
        assert after["bestScore"] == best_before, (
            f"New score (1000) is lower than best ({best_before}), "
            f"so bestScore should be unchanged. Got {after['bestScore']}"
        )


# ===================================================================
# DATA TYPE CORRECTNESS
# ===================================================================

class TestDataTypeCorrectness:
    """
    Verify response fields have correct data types.
    Catches serialization bugs where numbers come back as strings.
    """

    def test_player_stats_types(self, api, seeded_data):
        """totalGames, bestScore should be int; averageScore should be number."""
        resp = api.request("GET", "/api/players/player-001")
        assert resp.status_code == 200
        body = resp.json()

        assert isinstance(body["totalGames"], int), (
            f"totalGames should be an integer, got {type(body['totalGames']).__name__}: "
            f"{body['totalGames']!r}"
        )
        assert isinstance(body["bestScore"], (int, float)), (
            f"bestScore should be a number, got {type(body['bestScore']).__name__}: "
            f"{body['bestScore']!r}"
        )
        assert isinstance(body["averageScore"], (int, float)), (
            f"averageScore should be a number, got {type(body['averageScore']).__name__}: "
            f"{body['averageScore']!r}"
        )

    def test_leaderboard_entry_types(self, api, seeded_data):
        """rank and score should be integers in leaderboard entries."""
        resp = api.request("GET", "/api/leaderboards/global")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) > 0

        for entry in body[:5]:
            assert isinstance(entry["rank"], int), (
                f"rank should be integer, got {type(entry['rank']).__name__}: "
                f"{entry['rank']!r}"
            )
            assert isinstance(entry["score"], (int, float)), (
                f"score should be a number, got {type(entry['score']).__name__}: "
                f"{entry['score']!r}"
            )
            assert isinstance(entry["playerId"], str), (
                f"playerId should be string, got {type(entry['playerId']).__name__}"
            )
            assert isinstance(entry["displayName"], str), (
                f"displayName should be string, got {type(entry['displayName']).__name__}"
            )

    def test_score_submission_returns_correct_types(self, api, seeded_data):
        """scoreId should be string, score should be integer."""
        resp = api.request("POST", "/api/scores", json={
            "playerId": "player-003",
            "score": 1234,
        })
        assert resp.status_code == 201
        body = resp.json()

        assert isinstance(body["scoreId"], str), (
            f"scoreId should be string, got {type(body['scoreId']).__name__}"
        )
        assert isinstance(body["score"], (int, float)), (
            f"score should be a number, got {type(body['score']).__name__}: "
            f"{body['score']!r}"
        )


# ===================================================================
# WRITE-READ CONSISTENCY
# ===================================================================

class TestWriteReadConsistency:
    """
    Data written through one endpoint must be correctly readable
    through another. This catches serialization mismatches where
    data is stored in one format but queried in another (e.g., the
    enum serialization bug from v1 testing).
    """

    def test_created_player_fully_retrievable(self, api):
        """Create a player, then GET it — all fields should match."""
        player = {
            "playerId": "consistency-test-001",
            "displayName": "ConsistencyCheck",
            "region": "EU",
        }
        create_resp = api.request("POST", "/api/players", json=player)
        assert create_resp.status_code == 201
        created = create_resp.json()

        get_resp = api.request("GET", "/api/players/consistency-test-001")
        assert get_resp.status_code == 200, (
            f"Player was created successfully but GET returned {get_resp.status_code}. "
            f"Data may not be persisted correctly."
        )
        retrieved = get_resp.json()

        assert retrieved["playerId"] == "consistency-test-001"
        assert retrieved["displayName"] == "ConsistencyCheck"
        assert retrieved["region"] == "EU"

    def test_score_reflected_in_leaderboard(self, api, seeded_data):
        """
        After submitting scores, the leaderboard should include those players.
        This catches query issues where data is stored but queries return empty.
        """
        resp = api.request("GET", "/api/leaderboards/global")
        assert resp.status_code == 200
        body = resp.json()

        player_ids = {e["playerId"] for e in body}
        for expected in ["player-001", "player-002", "player-003", "player-004", "player-005"]:
            assert expected in player_ids, (
                f"{expected} submitted scores but doesn't appear in the global "
                f"leaderboard. This may indicate a query/serialization mismatch "
                f"(e.g., data stored with different case or format than queried). "
                f"Players in leaderboard: {player_ids}"
            )

    def test_regional_filter_matches_stored_region(self, api, seeded_data):
        """
        EU players registered with region='EU' must appear in the EU leaderboard.
        This catches case-sensitivity bugs where 'EU' is stored but query
        matches 'eu' or vice versa.
        """
        resp = api.request("GET", "/api/leaderboards/regional/EU")
        assert resp.status_code == 200
        body = resp.json()

        eu_players = {e["playerId"] for e in body}
        assert "player-003" in eu_players, (
            f"player-003 (region=EU) not found in EU leaderboard. "
            f"Check that the region value is stored and queried with "
            f"consistent casing. Found players: {eu_players}"
        )
        assert "player-004" in eu_players, (
            f"player-004 (region=EU) not found in EU leaderboard. "
            f"Found players: {eu_players}"
        )

    def test_player_rank_score_matches_leaderboard(self, api, seeded_data):
        """
        The score in player rank response should match their score
        in the global leaderboard.
        """
        rank_resp = api.request("GET", "/api/players/player-003/rank")
        assert rank_resp.status_code == 200
        rank_data = rank_resp.json()

        lb_resp = api.request("GET", "/api/leaderboards/global")
        assert lb_resp.status_code == 200
        lb_data = lb_resp.json()

        lb_entry = next((e for e in lb_data if e["playerId"] == "player-003"), None)
        assert lb_entry is not None, "player-003 should be in the global leaderboard"
        assert rank_data["score"] == lb_entry["score"], (
            f"player-003 score mismatch: rank endpoint says {rank_data['score']} "
            f"but leaderboard says {lb_entry['score']}. "
            f"Both endpoints must return consistent data."
        )
        assert rank_data["rank"] == lb_entry["rank"], (
            f"player-003 rank mismatch: rank endpoint says {rank_data['rank']} "
            f"but leaderboard says {lb_entry['rank']}."
        )


# ===================================================================
# EDGE CASES & BOUNDARY CONDITIONS
# ===================================================================

class TestEdgeCases:
    """Test boundary conditions that commonly expose bugs."""

    def test_empty_region_leaderboard(self, api, seeded_data):
        """A region with no players should return an empty array, not an error."""
        resp = api.request("GET", "/api/leaderboards/regional/EMPTY_REGION")
        assert resp.status_code == 200, (
            f"Empty region leaderboard should return 200, got {resp.status_code}. "
            f"Must return empty array for regions with no players."
        )
        body = resp.json()
        assert isinstance(body, list), (
            f"Expected array response, got {type(body).__name__}"
        )
        assert len(body) == 0, (
            f"EMPTY_REGION should have 0 entries, got {len(body)}"
        )

    def test_leaderboard_no_duplicate_players(self, api, seeded_data):
        """Each player should appear at most once in the global leaderboard."""
        resp = api.request("GET", "/api/leaderboards/global")
        assert resp.status_code == 200
        body = resp.json()

        player_ids = [e["playerId"] for e in body]
        duplicates = [pid for pid in set(player_ids) if player_ids.count(pid) > 1]
        assert not duplicates, (
            f"Players appear multiple times in the leaderboard: {duplicates}. "
            f"Each player should appear only once with their best score."
        )

    def test_top_parameter_zero_returns_empty(self, api, seeded_data):
        """top=0 should return empty array or be handled gracefully."""
        resp = api.request("GET", "/api/leaderboards/global?top=0")
        assert resp.status_code < 500, (
            f"top=0 caused a server error ({resp.status_code}). "
            f"Edge case parameters must not crash the server."
        )

    def test_top_parameter_one(self, api, seeded_data):
        """top=1 should return exactly one entry."""
        resp = api.request("GET", "/api/leaderboards/global?top=1")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) == 1, (
            f"top=1 should return exactly 1 entry, got {len(body)}"
        )

    def test_zero_score_submission(self, api, seeded_data):
        """Submitting a score of 0 should be handled (not crash)."""
        resp = api.request("POST", "/api/scores", json={
            "playerId": "player-005",
            "score": 0,
        })
        # Accept either success (201) or validation rejection (4xx), but not 500
        assert resp.status_code < 500, (
            f"Score of 0 caused a server error ({resp.status_code}). "
            f"Edge case values must not crash the server."
        )


# ===================================================================
# RAPID SEQUENTIAL OPERATIONS
# ===================================================================

class TestRapidOperations:
    """
    Verify the application handles rapid sequential writes correctly.
    Stats must be updated for each submission without losing data.
    """

    def test_rapid_score_submissions_all_counted(self, api, seeded_data):
        """
        Submit 5 scores rapidly for the same player.
        totalGames should increase by exactly 5.
        """
        # Get baseline
        resp = api.request("GET", "/api/players/player-005")
        assert resp.status_code == 200
        baseline_games = resp.json().get("totalGames", 0)

        # Submit 5 scores
        scores_submitted = 0
        for i in range(5):
            resp = api.request("POST", "/api/scores", json={
                "playerId": "player-005",
                "score": 1000 + i,
            })
            if resp.status_code == 201:
                scores_submitted += 1

        assert scores_submitted == 5, (
            f"Only {scores_submitted}/5 score submissions succeeded"
        )

        # Verify all counted
        resp = api.request("GET", "/api/players/player-005")
        assert resp.status_code == 200
        final_games = resp.json().get("totalGames", 0)

        assert final_games == baseline_games + 5, (
            f"After submitting 5 scores, totalGames should increase by 5. "
            f"Before: {baseline_games}, After: {final_games}, "
            f"Expected: {baseline_games + 5}. "
            f"This suggests score submissions aren't updating stats atomically "
            f"(possible read-modify-write race condition)."
        )

    def test_concurrent_score_submissions_all_counted(self, api, seeded_data):
        """
        Submit 15 scores CONCURRENTLY for the same player.
        totalGames should increase by exactly 15.

        This catches missing optimistic concurrency (ETag) handling:
        without ETags, concurrent read-modify-write on the player document
        will lose updates (two threads read totalGames=5, both write 6,
        instead of 6 then 7).
        """
        # Create a fresh player for this test to avoid interference
        player_id = "concurrent-test-001"
        resp = api.request("POST", "/api/players", json={
            "playerId": player_id,
            "displayName": "ConcurrentTest",
            "region": "US",
        })
        assert resp.status_code == 201

        num_concurrent = 15

        def submit_score(i):
            return api.request("POST", "/api/scores", json={
                "playerId": player_id,
                "score": 2000 + i,
            })

        # Submit all scores concurrently
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(submit_score, i) for i in range(num_concurrent)]
            results = [f.result() for f in as_completed(futures)]

        succeeded = sum(1 for r in results if r.status_code == 201)
        assert succeeded == num_concurrent, (
            f"Only {succeeded}/{num_concurrent} concurrent submissions succeeded. "
            f"Status codes: {[r.status_code for r in results]}"
        )

        # Verify all were counted
        resp = api.request("GET", f"/api/players/{player_id}")
        assert resp.status_code == 200
        body = resp.json()

        assert body["totalGames"] == num_concurrent, (
            f"After {num_concurrent} concurrent submissions, totalGames should be "
            f"{num_concurrent}, got {body['totalGames']}. "
            f"Lost {num_concurrent - body['totalGames']} updates. "
            f"This is the classic read-modify-write race condition — "
            f"use ETags/optimistic concurrency to prevent lost writes."
        )

        assert body["bestScore"] == 2000 + num_concurrent - 1, (
            f"bestScore should be {2000 + num_concurrent - 1} (highest submitted), "
            f"got {body['bestScore']}"
        )


# ===================================================================
# LEADERBOARD TIEBREAKING
# ===================================================================

class TestLeaderboardTiebreaking:
    """
    When players have the same score, the leaderboard must use
    deterministic tiebreaking (displayName ascending).

    This tests multi-field sort which requires a composite index
    in Cosmos DB (ORDER BY score DESC, displayName ASC).
    Without a composite index, the query either fails or returns
    non-deterministic order.
    """

    def test_tied_scores_sorted_by_display_name_ascending(self, api, seeded_data):
        """
        player-002 (Bob) and player-006 (Adam) both have score 6500.
        player-005 (Eve) and player-007 (Zara) both have score 7800.
        Tiebreaking by displayName ascending means Adam before Bob, Eve before Zara.
        """
        resp = api.request("GET", "/api/leaderboards/global")
        assert resp.status_code == 200
        body = resp.json()

        # Find the two players with score 7800
        tied_7800 = [e for e in body if e["score"] == 7800]
        assert len(tied_7800) >= 2, (
            f"Expected at least 2 players with score 7800, found {len(tied_7800)}. "
            f"Scores: {[(e['playerId'], e['score']) for e in body]}"
        )
        names_7800 = [e["displayName"] for e in tied_7800]
        assert names_7800 == sorted(names_7800), (
            f"Tied players at score 7800 should be sorted by displayName ascending. "
            f"Got: {names_7800}, expected: {sorted(names_7800)}. "
            f"Tiebreaking rule: when scores are equal, sort by displayName ASC."
        )

        # Find the two players with score 6500
        tied_6500 = [e for e in body if e["score"] == 6500]
        assert len(tied_6500) >= 2, (
            f"Expected at least 2 players with score 6500, found {len(tied_6500)}"
        )
        names_6500 = [e["displayName"] for e in tied_6500]
        assert names_6500 == sorted(names_6500), (
            f"Tied players at score 6500 should be sorted by displayName ascending. "
            f"Got: {names_6500}, expected: {sorted(names_6500)}. "
            f"Tiebreaking rule: when scores are equal, sort by displayName ASC."
        )

    def test_tied_scores_have_sequential_ranks(self, api, seeded_data):
        """Even with tied scores, ranks must be sequential (no gaps or duplicates)."""
        resp = api.request("GET", "/api/leaderboards/global")
        assert resp.status_code == 200
        body = resp.json()

        ranks = [e["rank"] for e in body]
        expected = list(range(1, len(ranks) + 1))
        assert ranks == expected, (
            f"Ranks must be sequential even with tied scores. "
            f"Got: {ranks}, expected: {expected}"
        )


# ===================================================================
# UPDATE AND DELETE CONSISTENCY
# ===================================================================

class TestUpdateDeleteConsistency:
    """
    Verify that player updates and deletions are reflected
    consistently across all related endpoints.
    """

    def test_updated_region_reflected_in_regional_leaderboard(self, api, seeded_data):
        """
        Update a player's region and verify they appear in the new
        regional leaderboard and not the old one.
        """
        # Create a player in US
        player_id = "region-change-001"
        api.request("POST", "/api/players", json={
            "playerId": player_id,
            "displayName": "RegionChanger",
            "region": "US",
        })
        api.request("POST", "/api/scores", json={
            "playerId": player_id,
            "score": 3000,
        })

        # Verify in US leaderboard
        resp = api.request("GET", "/api/leaderboards/regional/US")
        us_ids = {e["playerId"] for e in resp.json()}
        assert player_id in us_ids, (
            f"{player_id} should appear in US leaderboard after creation"
        )

        # Move to EU
        resp = api.request("PATCH", f"/api/players/{player_id}", json={
            "region": "EU",
        })
        assert resp.status_code == 200

        # Verify in EU leaderboard
        resp = api.request("GET", "/api/leaderboards/regional/EU")
        eu_ids = {e["playerId"] for e in resp.json()}
        assert player_id in eu_ids, (
            f"{player_id} should appear in EU leaderboard after region change to EU"
        )

        # Verify NOT in US leaderboard anymore
        resp = api.request("GET", "/api/leaderboards/regional/US")
        us_ids = {e["playerId"] for e in resp.json()}
        assert player_id not in us_ids, (
            f"{player_id} should no longer appear in US leaderboard after moving to EU"
        )

    def test_deleted_player_removed_from_leaderboard(self, api, seeded_data):
        """After deleting a player, they must not appear in any leaderboard."""
        player_id = "delete-lb-001"
        api.request("POST", "/api/players", json={
            "playerId": player_id,
            "displayName": "DeleteLB",
            "region": "US",
        })
        api.request("POST", "/api/scores", json={
            "playerId": player_id,
            "score": 4000,
        })

        # Confirm in leaderboard
        resp = api.request("GET", "/api/leaderboards/global")
        assert player_id in {e["playerId"] for e in resp.json()}, (
            f"{player_id} should appear in leaderboard after scoring"
        )

        # Delete
        resp = api.request("DELETE", f"/api/players/{player_id}")
        assert resp.status_code == 204

        # Confirm removed from global leaderboard
        resp = api.request("GET", "/api/leaderboards/global")
        assert player_id not in {e["playerId"] for e in resp.json()}, (
            f"{player_id} should not appear in global leaderboard after deletion"
        )

        # Confirm removed from regional leaderboard
        resp = api.request("GET", "/api/leaderboards/regional/US")
        assert player_id not in {e["playerId"] for e in resp.json()}, (
            f"{player_id} should not appear in regional leaderboard after deletion"
        )

    def test_deleted_player_scores_not_in_history(self, api, seeded_data):
        """After deleting a player, their score history should return 404."""
        player_id = "delete-scores-001"
        api.request("POST", "/api/players", json={
            "playerId": player_id,
            "displayName": "DeleteScores",
            "region": "JP",
        })
        api.request("POST", "/api/scores", json={
            "playerId": player_id,
            "score": 3500,
        })

        # Delete
        resp = api.request("DELETE", f"/api/players/{player_id}")
        assert resp.status_code == 204

        # Score history should return 404
        resp = api.request("GET", f"/api/players/{player_id}/scores")
        assert resp.status_code == 404, (
            f"Score history for deleted player should return 404, "
            f"got {resp.status_code}"
        )
