"""
Cosmos DB client initialization and database/container setup.

Best practices applied:
- Singleton CosmosClient (Rule 4.18)
- Async SDK with aiohttp (Rule 4.1, 4.15)
- Gateway mode for emulator compatibility (Rule 4.6)
- SSL verification disabled for emulator (Rule 4.6)
- Environment variable configuration (Rule 4.12)
- Exclude-all-first indexing policy (Rule 5.3)
- Composite indexes matching ORDER BY (Rule 5.1, 5.2)
"""

import os
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey


COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "https://localhost:8081")
COSMOS_KEY = os.environ.get(
    "COSMOS_KEY",
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
)
DATABASE_NAME = "gaming-leaderboard-db"

# Singleton client instance
_client: CosmosClient | None = None
_database = None
_players_container = None
_scores_container = None
_leaderboards_container = None


async def get_cosmos_client() -> CosmosClient:
    """Get or create the singleton CosmosClient (Rule 4.18)."""
    global _client
    if _client is None:
        _client = CosmosClient(
            url=COSMOS_ENDPOINT,
            credential=COSMOS_KEY,
            connection_verify=False,  # Rule 4.6: emulator SSL
        )
    return _client


async def initialize_database():
    """Create database and containers with optimized configuration."""
    global _database, _players_container, _scores_container, _leaderboards_container

    client = await get_cosmos_client()

    # Create database
    _database = await client.create_database_if_not_exists(id=DATABASE_NAME)

    # Players container: partition by /id for efficient point reads (Rule 3.7)
    # Indexing: exclude all, include only queried paths (Rule 5.3)
    players_indexing = {
        "indexingMode": "consistent",
        "automatic": True,
        "includedPaths": [
            {"path": "/region/?"},
            {"path": "/bestScore/?"},
            {"path": "/displayName/?"},
        ],
        "excludedPaths": [{"path": "/*"}],
        "compositeIndexes": [
            [
                {"path": "/bestScore", "order": "descending"},
                {"path": "/displayName", "order": "ascending"},
            ]
        ],
    }
    _players_container = await _database.create_container_if_not_exists(
        id="players",
        partition_key=PartitionKey(path="/id"),
        indexing_policy=players_indexing,
    )

    # Scores container: partition by /playerId for single-partition queries (Rule 3.1)
    scores_indexing = {
        "indexingMode": "consistent",
        "automatic": True,
        "includedPaths": [
            {"path": "/playerId/?"},
            {"path": "/timestamp/?"},
        ],
        "excludedPaths": [{"path": "/*"}],
        "compositeIndexes": [
            [
                {"path": "/timestamp", "order": "descending"},
            ]
        ],
    }
    _scores_container = await _database.create_container_if_not_exists(
        id="scores",
        partition_key=PartitionKey(path="/playerId"),
        indexing_policy=scores_indexing,
    )

    # Leaderboards container: partition by /leaderboardKey (synthetic key, Rule 2.8)
    # Composite index for ORDER BY score DESC, displayName ASC (Rule 5.1)
    leaderboards_indexing = {
        "indexingMode": "consistent",
        "automatic": True,
        "includedPaths": [
            {"path": "/leaderboardKey/?"},
            {"path": "/score/?"},
            {"path": "/displayName/?"},
            {"path": "/playerId/?"},
        ],
        "excludedPaths": [{"path": "/*"}],
        "compositeIndexes": [
            [
                {"path": "/score", "order": "descending"},
                {"path": "/displayName", "order": "ascending"},
            ]
        ],
    }
    _leaderboards_container = await _database.create_container_if_not_exists(
        id="leaderboards",
        partition_key=PartitionKey(path="/leaderboardKey"),
        indexing_policy=leaderboards_indexing,
    )


def get_players_container():
    return _players_container


def get_scores_container():
    return _scores_container


def get_leaderboards_container():
    return _leaderboards_container


async def close_client():
    """Close the Cosmos DB client."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
