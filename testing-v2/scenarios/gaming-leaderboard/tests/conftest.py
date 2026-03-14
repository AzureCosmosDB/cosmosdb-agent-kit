"""
Scenario-level conftest for gaming-leaderboard tests.

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
def test_players():
    """Standard set of test players used across tests."""
    return [
        {"playerId": "player-001", "displayName": "Alice", "region": "US"},
        {"playerId": "player-002", "displayName": "Bob", "region": "US"},
        {"playerId": "player-003", "displayName": "Charlie", "region": "EU"},
        {"playerId": "player-004", "displayName": "Diana", "region": "EU"},
        {"playerId": "player-005", "displayName": "Eve", "region": "JP"},
        # Tiebreaking test data: Adam ties with Bob (6500), Zara ties with Eve (7800)
        {"playerId": "player-006", "displayName": "Adam", "region": "US"},
        {"playerId": "player-007", "displayName": "Zara", "region": "EU"},
    ]


@pytest.fixture(scope="session")
def test_scores():
    """
    Standard scores to submit. Designed so ranking order is deterministic:
    player-003 (9500) > player-001 (8200) > player-005 & player-007 (7800) >
    player-002 & player-006 (6500) > player-004 (5000)

    Tiebreaking by displayName ascending:
    - Eve (7800) before Zara (7800)
    - Adam (6500) before Bob (6500)
    """
    return [
        {"playerId": "player-001", "score": 8200},
        {"playerId": "player-002", "score": 6500},
        {"playerId": "player-003", "score": 9500},
        {"playerId": "player-004", "score": 5000},
        {"playerId": "player-005", "score": 7800},
        # Submit additional scores for stats verification
        {"playerId": "player-001", "score": 7000},
        {"playerId": "player-001", "score": 8200},  # duplicate of best
        {"playerId": "player-003", "score": 9000},
        # Tiebreaking scores
        {"playerId": "player-006", "score": 6500},  # ties with player-002 (Bob)
        {"playerId": "player-007", "score": 7800},  # ties with player-005 (Eve)
    ]


@pytest.fixture(scope="session")
def seeded_data(api, test_players, test_scores):
    """
    Create all test players and submit all test scores.
    Returns a dict with the created data for reference.
    Called once per session before any tests that need data.
    """
    created_players = []
    for player in test_players:
        resp = api.request("POST", "/api/players", json=player)
        assert resp.status_code == 201, (
            f"Failed to create player {player['playerId']}: "
            f"{resp.status_code} {resp.text}"
        )
        created_players.append(resp.json())

    created_scores = []
    for score in test_scores:
        resp = api.request("POST", "/api/scores", json=score)
        assert resp.status_code == 201, (
            f"Failed to submit score for {score['playerId']}: "
            f"{resp.status_code} {resp.text}"
        )
        created_scores.append(resp.json())

    return {
        "players": created_players,
        "scores": created_scores,
    }
