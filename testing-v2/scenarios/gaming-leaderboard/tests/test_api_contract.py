"""
API Contract Tests for Gaming Leaderboard
==========================================

These tests validate that the generated application conforms to the
API contract defined in api-contract.yaml. They test:
- Correct HTTP methods and paths
- Expected request/response schemas
- Correct status codes
- Required fields present in responses
- Correct data types
- Business logic (ranking, stats aggregation)

Each test is designed to produce a clear, actionable failure message
that helps identify whether the issue is:
- A missing/wrong endpoint path
- A missing required field
- A wrong data type
- A business logic error
"""

import pytest


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
# PLAYER MANAGEMENT
# ===================================================================

class TestCreatePlayer:
    """POST /api/players — Create a new player profile."""

    def test_create_player_returns_201(self, api):
        resp = api.request("POST", "/api/players", json={
            "playerId": "test-create-001",
            "displayName": "TestPlayer",
            "region": "US",
        })
        assert resp.status_code == 201, (
            f"POST /api/players should return 201, got {resp.status_code}. "
            f"Response: {resp.text[:500]}"
        )

    def test_create_player_response_has_required_fields(self, api):
        resp = api.request("POST", "/api/players", json={
            "playerId": "test-create-002",
            "displayName": "FieldCheck",
            "region": "EU",
        })
        assert resp.status_code == 201
        body = resp.json()

        required = ["playerId", "displayName", "region", "totalGames", "bestScore", "averageScore"]
        missing = [f for f in required if f not in body]
        assert not missing, (
            f"Response missing required fields: {missing}. "
            f"Got: {list(body.keys())}. "
            f"See api-contract.yaml create_player.response.body.required"
        )

    def test_new_player_has_zero_stats(self, api):
        resp = api.request("POST", "/api/players", json={
            "playerId": "test-create-003",
            "displayName": "ZeroStats",
            "region": "JP",
        })
        assert resp.status_code == 201
        body = resp.json()

        assert body.get("totalGames") == 0, (
            f"New player totalGames should be 0, got {body.get('totalGames')}"
        )
        assert body.get("bestScore") == 0, (
            f"New player bestScore should be 0, got {body.get('bestScore')}"
        )
        assert body.get("averageScore") == 0, (
            f"New player averageScore should be 0, got {body.get('averageScore')}"
        )

    def test_create_player_returns_correct_data(self, api):
        resp = api.request("POST", "/api/players", json={
            "playerId": "test-create-004",
            "displayName": "DataCheck",
            "region": "EU",
        })
        assert resp.status_code == 201
        body = resp.json()

        assert body["playerId"] == "test-create-004"
        assert body["displayName"] == "DataCheck"
        assert body["region"] == "EU"


class TestGetPlayer:
    """GET /api/players/{playerId} — Get player profile with stats."""

    def test_get_existing_player(self, api, seeded_data):
        resp = api.request("GET", "/api/players/player-001")
        assert resp.status_code == 200, (
            f"GET /api/players/player-001 should return 200, got {resp.status_code}"
        )

    def test_get_player_has_required_fields(self, api, seeded_data):
        resp = api.request("GET", "/api/players/player-001")
        assert resp.status_code == 200
        body = resp.json()

        required = ["playerId", "displayName", "region", "totalGames", "bestScore", "averageScore"]
        missing = [f for f in required if f not in body]
        assert not missing, (
            f"GET player response missing required fields: {missing}. "
            f"Got: {list(body.keys())}"
        )

    def test_get_player_stats_updated_after_scores(self, api, seeded_data):
        """Player-001 submitted 3 scores: 8200, 7000, 8200. Stats should reflect this."""
        resp = api.request("GET", "/api/players/player-001")
        assert resp.status_code == 200
        body = resp.json()

        assert body["totalGames"] >= 3, (
            f"player-001 submitted 3 scores, totalGames should be >= 3, "
            f"got {body['totalGames']}"
        )
        assert body["bestScore"] == 8200, (
            f"player-001 best score should be 8200, got {body['bestScore']}"
        )

    def test_get_nonexistent_player_returns_404(self, api):
        resp = api.request("GET", "/api/players/nonexistent-player-xyz")
        assert resp.status_code == 404, (
            f"GET /api/players/nonexistent-player-xyz should return 404, "
            f"got {resp.status_code}"
        )


# ===================================================================
# SCORE SUBMISSION
# ===================================================================

class TestSubmitScore:
    """POST /api/scores — Submit a game score."""

    def test_submit_score_returns_201(self, api, seeded_data):
        resp = api.request("POST", "/api/scores", json={
            "playerId": "player-001",
            "score": 5000,
        })
        assert resp.status_code == 201, (
            f"POST /api/scores should return 201, got {resp.status_code}. "
            f"Response: {resp.text[:500]}"
        )

    def test_submit_score_response_has_required_fields(self, api, seeded_data):
        resp = api.request("POST", "/api/scores", json={
            "playerId": "player-002",
            "score": 3000,
        })
        assert resp.status_code == 201
        body = resp.json()

        required = ["scoreId", "playerId", "score"]
        missing = [f for f in required if f not in body]
        assert not missing, (
            f"Score response missing required fields: {missing}. "
            f"Got: {list(body.keys())}. "
            f"See api-contract.yaml submit_score.response.body.required"
        )

    def test_submit_score_returns_correct_data(self, api, seeded_data):
        resp = api.request("POST", "/api/scores", json={
            "playerId": "player-002",
            "score": 4200,
        })
        assert resp.status_code == 201
        body = resp.json()

        assert body["playerId"] == "player-002"
        assert body["score"] == 4200
        assert "scoreId" in body and body["scoreId"], "scoreId must be a non-empty string"


# ===================================================================
# GLOBAL LEADERBOARD
# ===================================================================

class TestGlobalLeaderboard:
    """GET /api/leaderboards/global — Global top N leaderboard."""

    def test_global_leaderboard_returns_200(self, api, seeded_data):
        resp = api.request("GET", "/api/leaderboards/global")
        assert resp.status_code == 200, (
            f"GET /api/leaderboards/global should return 200, got {resp.status_code}"
        )

    def test_global_leaderboard_returns_array(self, api, seeded_data):
        resp = api.request("GET", "/api/leaderboards/global")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list), (
            f"Global leaderboard should return an array, got {type(body).__name__}"
        )

    def test_global_leaderboard_entries_have_required_fields(self, api, seeded_data):
        resp = api.request("GET", "/api/leaderboards/global")
        body = resp.json()
        assert len(body) > 0, "Leaderboard should not be empty after submitting scores"

        entry = body[0]
        required = ["rank", "playerId", "displayName", "score"]
        missing = [f for f in required if f not in entry]
        assert not missing, (
            f"Leaderboard entry missing required fields: {missing}. "
            f"Got: {list(entry.keys())}"
        )

    def test_global_leaderboard_sorted_descending(self, api, seeded_data):
        resp = api.request("GET", "/api/leaderboards/global")
        body = resp.json()
        scores = [entry["score"] for entry in body]
        assert scores == sorted(scores, reverse=True), (
            f"Leaderboard must be sorted by score descending. "
            f"Got scores: {scores[:10]}"
        )

    def test_global_leaderboard_ranks_sequential(self, api, seeded_data):
        resp = api.request("GET", "/api/leaderboards/global")
        body = resp.json()
        ranks = [entry["rank"] for entry in body]
        expected = list(range(1, len(ranks) + 1))
        assert ranks == expected, (
            f"Ranks should be sequential starting from 1. "
            f"Got: {ranks[:10]}, expected: {expected[:10]}"
        )

    def test_global_leaderboard_top_player_is_highest_scorer(self, api, seeded_data):
        """player-003 has best score 9500, should be rank 1."""
        resp = api.request("GET", "/api/leaderboards/global")
        body = resp.json()
        assert len(body) > 0
        assert body[0]["playerId"] == "player-003", (
            f"Top player should be player-003 (score 9500), "
            f"got {body[0]['playerId']} (score {body[0].get('score')})"
        )

    def test_global_leaderboard_respects_top_parameter(self, api, seeded_data):
        resp = api.request("GET", "/api/leaderboards/global?top=3")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) <= 3, (
            f"Requested top=3 but got {len(body)} entries"
        )


# ===================================================================
# REGIONAL LEADERBOARD
# ===================================================================

class TestRegionalLeaderboard:
    """GET /api/leaderboards/regional/{region} — Regional top N."""

    def test_regional_leaderboard_returns_200(self, api, seeded_data):
        resp = api.request("GET", "/api/leaderboards/regional/US")
        assert resp.status_code == 200, (
            f"GET /api/leaderboards/regional/US should return 200, "
            f"got {resp.status_code}"
        )

    def test_regional_leaderboard_only_contains_region_players(self, api, seeded_data):
        resp = api.request("GET", "/api/leaderboards/regional/US")
        body = resp.json()

        # US players: player-001 (8200), player-002 (6500)
        player_ids = {entry["playerId"] for entry in body}
        assert "player-003" not in player_ids, (
            "player-003 is EU, should not appear in US leaderboard"
        )
        assert "player-005" not in player_ids, (
            "player-005 is JP, should not appear in US leaderboard"
        )

    def test_regional_leaderboard_sorted_descending(self, api, seeded_data):
        resp = api.request("GET", "/api/leaderboards/regional/US")
        body = resp.json()
        scores = [entry["score"] for entry in body]
        assert scores == sorted(scores, reverse=True), (
            f"Regional leaderboard must be sorted descending. Got: {scores}"
        )

    def test_regional_leaderboard_entries_have_required_fields(self, api, seeded_data):
        resp = api.request("GET", "/api/leaderboards/regional/EU")
        body = resp.json()
        assert len(body) > 0, "EU leaderboard should not be empty"

        entry = body[0]
        required = ["rank", "playerId", "displayName", "score"]
        missing = [f for f in required if f not in entry]
        assert not missing, (
            f"Regional entry missing required fields: {missing}. "
            f"Got: {list(entry.keys())}"
        )


# ===================================================================
# PLAYER RANK
# ===================================================================

class TestPlayerRank:
    """GET /api/players/{playerId}/rank — Player rank + neighbors."""

    def test_player_rank_returns_200(self, api, seeded_data):
        resp = api.request("GET", "/api/players/player-001/rank")
        assert resp.status_code == 200, (
            f"GET /api/players/player-001/rank should return 200, "
            f"got {resp.status_code}"
        )

    def test_player_rank_has_required_fields(self, api, seeded_data):
        resp = api.request("GET", "/api/players/player-001/rank")
        assert resp.status_code == 200
        body = resp.json()

        required = ["playerId", "rank", "score", "neighbors"]
        missing = [f for f in required if f not in body]
        assert not missing, (
            f"Rank response missing required fields: {missing}. "
            f"Got: {list(body.keys())}"
        )

    def test_player_rank_correct_for_top_player(self, api, seeded_data):
        """player-003 has best score (9500), should be rank 1."""
        resp = api.request("GET", "/api/players/player-003/rank")
        assert resp.status_code == 200
        body = resp.json()

        assert body["rank"] == 1, (
            f"player-003 (score 9500) should be rank 1, got rank {body['rank']}"
        )
        assert body["score"] == 9500

    def test_player_rank_neighbors_is_array(self, api, seeded_data):
        resp = api.request("GET", "/api/players/player-001/rank")
        body = resp.json()

        assert isinstance(body["neighbors"], list), (
            f"neighbors should be an array, got {type(body['neighbors']).__name__}"
        )

    def test_player_rank_neighbors_have_required_fields(self, api, seeded_data):
        resp = api.request("GET", "/api/players/player-001/rank")
        body = resp.json()

        for neighbor in body["neighbors"]:
            required = ["rank", "playerId", "displayName", "score"]
            missing = [f for f in required if f not in neighbor]
            assert not missing, (
                f"Neighbor entry missing required fields: {missing}. "
                f"Got: {list(neighbor.keys())}"
            )

    def test_nonexistent_player_rank_returns_404(self, api):
        resp = api.request("GET", "/api/players/nonexistent-xyz/rank")
        assert resp.status_code == 404, (
            f"Rank for nonexistent player should return 404, "
            f"got {resp.status_code}"
        )


# ===================================================================
# SCORE HISTORY
# ===================================================================

class TestGetPlayerScores:
    """GET /api/players/{playerId}/scores — Player score history."""

    def test_score_history_returns_200(self, api, seeded_data):
        resp = api.request("GET", "/api/players/player-001/scores")
        assert resp.status_code == 200, (
            f"GET /api/players/player-001/scores should return 200, "
            f"got {resp.status_code}. "
            f"Response: {resp.text[:500]}"
        )

    def test_score_history_returns_array(self, api, seeded_data):
        resp = api.request("GET", "/api/players/player-001/scores")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list), (
            f"Score history should return an array, got {type(body).__name__}"
        )

    def test_score_history_entries_have_required_fields(self, api, seeded_data):
        resp = api.request("GET", "/api/players/player-001/scores")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) > 0, "player-001 submitted scores, history should not be empty"

        entry = body[0]
        required = ["scoreId", "playerId", "score", "timestamp"]
        missing = [f for f in required if f not in entry]
        assert not missing, (
            f"Score history entry missing required fields: {missing}. "
            f"Got: {list(entry.keys())}. "
            f"See api-contract.yaml get_player_scores.response"
        )

    def test_score_history_contains_all_player_scores(self, api, seeded_data):
        """player-001 submitted 3 scores in seed data: 8200, 7000, 8200."""
        resp = api.request("GET", "/api/players/player-001/scores")
        assert resp.status_code == 200
        body = resp.json()

        scores = [entry["score"] for entry in body]
        assert len(scores) >= 3, (
            f"player-001 submitted 3 scores in seed data but history has {len(scores)} entries"
        )

    def test_score_history_ordered_by_most_recent_first(self, api, seeded_data):
        """Scores should be returned with most recent first (timestamp descending)."""
        resp = api.request("GET", "/api/players/player-001/scores")
        assert resp.status_code == 200
        body = resp.json()

        timestamps = [entry["timestamp"] for entry in body]
        assert timestamps == sorted(timestamps, reverse=True), (
            f"Score history should be ordered by timestamp descending (most recent first). "
            f"Got timestamps: {timestamps[:5]}"
        )

    def test_score_history_respects_limit(self, api, seeded_data):
        """limit=2 should return at most 2 scores."""
        resp = api.request("GET", "/api/players/player-001/scores?limit=2")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) <= 2, (
            f"Requested limit=2 but got {len(body)} entries"
        )

    def test_score_history_for_nonexistent_player_returns_404(self, api):
        resp = api.request("GET", "/api/players/nonexistent-xyz/scores")
        assert resp.status_code == 404, (
            f"Score history for nonexistent player should return 404, "
            f"got {resp.status_code}"
        )

    def test_score_history_only_shows_own_scores(self, api, seeded_data):
        """player-004 submitted exactly 1 score. History should only contain their scores."""
        resp = api.request("GET", "/api/players/player-004/scores")
        assert resp.status_code == 200
        body = resp.json()

        for entry in body:
            assert entry["playerId"] == "player-004", (
                f"Score history for player-004 contains score from {entry['playerId']}. "
                f"History must only contain the requested player's scores."
            )


# ===================================================================
# UPDATE PLAYER
# ===================================================================

class TestUpdatePlayer:
    """PATCH /api/players/{playerId} — Update player profile."""

    def test_update_player_returns_200(self, api, seeded_data):
        resp = api.request("PATCH", "/api/players/player-005", json={
            "displayName": "Eve Updated",
        })
        assert resp.status_code == 200, (
            f"PATCH /api/players/player-005 should return 200, "
            f"got {resp.status_code}. Response: {resp.text[:500]}"
        )

    def test_update_player_response_has_required_fields(self, api, seeded_data):
        resp = api.request("PATCH", "/api/players/player-005", json={
            "displayName": "Eve V2",
        })
        assert resp.status_code == 200
        body = resp.json()

        required = ["playerId", "displayName", "region", "totalGames", "bestScore", "averageScore"]
        missing = [f for f in required if f not in body]
        assert not missing, (
            f"Update response missing required fields: {missing}. "
            f"Got: {list(body.keys())}"
        )

    def test_update_player_reflects_new_display_name(self, api, seeded_data):
        resp = api.request("PATCH", "/api/players/player-004", json={
            "displayName": "Diana Renamed",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["displayName"] == "Diana Renamed", (
            f"Updated displayName should be 'Diana Renamed', got '{body['displayName']}'"
        )

        # Verify GET also returns the updated name
        get_resp = api.request("GET", "/api/players/player-004")
        assert get_resp.status_code == 200
        assert get_resp.json()["displayName"] == "Diana Renamed", (
            f"GET after PATCH should return updated displayName"
        )

    def test_update_player_preserves_stats(self, api, seeded_data):
        """Updating displayName should not reset stats."""
        before = api.request("GET", "/api/players/player-004").json()

        api.request("PATCH", "/api/players/player-004", json={
            "displayName": "Diana Stats Check",
        })

        after = api.request("GET", "/api/players/player-004").json()
        assert after["totalGames"] == before["totalGames"], (
            f"PATCH should not reset totalGames. Before: {before['totalGames']}, After: {after['totalGames']}"
        )
        assert after["bestScore"] == before["bestScore"], (
            f"PATCH should not reset bestScore. Before: {before['bestScore']}, After: {after['bestScore']}"
        )

    def test_update_nonexistent_player_returns_404(self, api):
        resp = api.request("PATCH", "/api/players/nonexistent-xyz", json={
            "displayName": "Ghost",
        })
        assert resp.status_code == 404, (
            f"PATCH nonexistent player should return 404, got {resp.status_code}"
        )


# ===================================================================
# DELETE PLAYER
# ===================================================================

class TestDeletePlayer:
    """DELETE /api/players/{playerId} — Delete player and their data."""

    def test_delete_player_returns_204(self, api, seeded_data):
        # Create a disposable player for deletion
        api.request("POST", "/api/players", json={
            "playerId": "delete-me-001",
            "displayName": "DeleteMe",
            "region": "US",
        })
        resp = api.request("DELETE", "/api/players/delete-me-001")
        assert resp.status_code == 204, (
            f"DELETE /api/players/delete-me-001 should return 204, "
            f"got {resp.status_code}"
        )

    def test_deleted_player_returns_404_on_get(self, api, seeded_data):
        """After deletion, GET should return 404."""
        api.request("POST", "/api/players", json={
            "playerId": "delete-me-002",
            "displayName": "DeleteMe2",
            "region": "US",
        })
        api.request("DELETE", "/api/players/delete-me-002")

        resp = api.request("GET", "/api/players/delete-me-002")
        assert resp.status_code == 404, (
            f"Deleted player should return 404 on GET, got {resp.status_code}"
        )

    def test_delete_nonexistent_player_returns_404(self, api):
        resp = api.request("DELETE", "/api/players/nonexistent-xyz")
        assert resp.status_code == 404, (
            f"DELETE nonexistent player should return 404, got {resp.status_code}"
        )
