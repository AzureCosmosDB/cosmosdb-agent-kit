"""
Cosmos DB client initialization and container management.
Follows best practices:
- Async SDK (rule 4.1)
- Singleton CosmosClient (rule 4.18)
- Include aiohttp for async (rule 4.15)
- SSL disabled for emulator (rule 4.6)
- Composite indexes for ORDER BY (rules 5.1, 5.2)
- Exclude unused index paths (rule 5.3)
"""

import os
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey

COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "https://localhost:8081")
COSMOS_KEY = os.environ.get(
    "COSMOS_KEY",
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
)
DATABASE_NAME = "gaming-leaderboard"

# Singleton client and container references
_client: CosmosClient | None = None
_database = None
_container = None


async def get_cosmos_client() -> CosmosClient:
    """Get or create a singleton CosmosClient instance."""
    global _client
    if _client is None:
        _client = CosmosClient(
            COSMOS_ENDPOINT,
            credential=COSMOS_KEY,
            connection_verify=False,
        )
    return _client


async def initialize_database():
    """Create database and container with proper configuration."""
    global _database, _container
    client = await get_cosmos_client()

    _database = await client.create_database_if_not_exists(id=DATABASE_NAME)

    indexing_policy = {
        "indexingMode": "consistent",
        "automatic": True,
        "includedPaths": [{"path": "/*"}],
        "excludedPaths": [{"path": '/"_etag"/?'}],
        "compositeIndexes": [
            [
                {"path": "/bestScore", "order": "descending"},
                {"path": "/displayName", "order": "ascending"},
            ]
        ],
    }

    _container = await _database.create_container_if_not_exists(
        id="leaderboard",
        partition_key=PartitionKey(path="/playerId"),
        indexing_policy=indexing_policy,
    )


async def get_container():
    """Return the leaderboard container."""
    if _container is None:
        await initialize_database()
    return _container


async def close_client():
    """Close the Cosmos DB client."""
    global _client, _database, _container
    if _client is not None:
        await _client.close()
        _client = None
        _database = None
        _container = None
