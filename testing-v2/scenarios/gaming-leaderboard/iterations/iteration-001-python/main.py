"""
Gaming Leaderboard API — FastAPI + Azure Cosmos DB (NoSQL API)

Best practices applied:
- Singleton CosmosClient (Rule 4.18)
- Async SDK with aiohttp (Rule 4.15)
- Type discriminators for polymorphic data in single container (Rule 1.11)
- Partition key aligned with query patterns (Rule 2.7)
- Point reads when ID and partition key are known (Rule 3.7)
- Parameterized queries (Rule 3.6)
- Literal integers for TOP (Rule 3.8)
- Composite indexes for ORDER BY (Rule 5.1, 5.2)
- Exclude unused index paths (Rule 5.3)
- Project only needed fields (Rule 3.9)
- COUNT-based ranking instead of full partition scans (Rule 9.2)
- camelCase field naming as required by API contract
"""

import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosHttpResponseError
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# Configuration from environment variables (Rule 4.6, 4.12)
# ---------------------------------------------------------------------------
COSMOS_ENDPOINT = os.environ.get(
    "COSMOS_ENDPOINT", "https://localhost:8081"
)
COSMOS_KEY = os.environ.get(
    "COSMOS_KEY",
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
)
DATABASE_NAME = os.environ.get("DATABASE_NAME", "gaming-leaderboard-db")
CONTAINER_NAME = "leaderboard"

# ---------------------------------------------------------------------------
# Cosmos DB singleton client & container reference (Rule 4.18)
# ---------------------------------------------------------------------------
cosmos_client: CosmosClient | None = None
container = None


async def _get_or_create_container():
    """Ensure database and container exist with optimal configuration."""
    global cosmos_client, container

    # Determine if we're talking to the emulator (Rule 4.6)
    is_emulator = "localhost" in COSMOS_ENDPOINT or "127.0.0.1" in COSMOS_ENDPOINT

    cosmos_client = CosmosClient(
        url=COSMOS_ENDPOINT,
        credential=COSMOS_KEY,
        connection_verify=not is_emulator,  # Disable SSL verification for emulator
    )

    database = await cosmos_client.create_database_if_not_exists(id=DATABASE_NAME)

    # Indexing policy (Rules 5.1, 5.2, 5.3)
    indexing_policy = {
        "indexingMode": "consistent",
        "automatic": True,
        "includedPaths": [{"path": "/*"}],
        "excludedPaths": [{"path": '/"_etag"/?'}],
        "compositeIndexes": [
            # For ORDER BY bestScore DESC, displayName ASC (leaderboard queries)
            [
                {"path": "/bestScore", "order": "descending"},
                {"path": "/displayName", "order": "ascending"},
            ],
            # Inverse pair (Rule 5.1 — always include inverse)
            [
                {"path": "/bestScore", "order": "ascending"},
                {"path": "/displayName", "order": "descending"},
            ],
            # For score history ORDER BY timestamp DESC
            [
                {"path": "/timestamp", "order": "descending"},
            ],
            [
                {"path": "/timestamp", "order": "ascending"},
            ],
        ],
    }

    # Single container with type discriminator (Rule 1.11)
    # Partition key: /playerId — aligns with most query patterns (Rule 2.7)
    # High cardinality, immutable (Rules 2.4, 2.5)
    container = await database.create_container_if_not_exists(
        id=CONTAINER_NAME,
        partition_key=PartitionKey(path="/playerId"),
        indexing_policy=indexing_policy,
    )


# ---------------------------------------------------------------------------
# Lifespan: singleton init & teardown
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await _get_or_create_container()
    yield
    if cosmos_client:
        await cosmos_client.close()


app = FastAPI(title="Gaming Leaderboard API", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Player Management
# ---------------------------------------------------------------------------
@app.post("/api/players", status_code=201)
async def create_player(body: dict):
    player_id = body.get("playerId")
    display_name = body.get("displayName")
    region = body.get("region")

    if not player_id or not display_name or not region:
        raise HTTPException(status_code=400, detail="playerId, displayName, and region are required")

    player_doc = {
        "id": player_id,
        "playerId": player_id,
        "type": "player",  # Type discriminator (Rule 1.11)
        "displayName": display_name,
        "region": region,
        "totalGames": 0,
        "bestScore": 0,
        "averageScore": 0.0,
        "totalScore": 0,  # Internal field for average calculation
    }

    try:
        await container.create_item(body=player_doc)
    except CosmosHttpResponseError as e:
        if e.status_code == 409:
            raise HTTPException(status_code=409, detail="Player already exists")
        raise

    return _player_response(player_doc)


@app.get("/api/players/{player_id}")
async def get_player(player_id: str):
    player = await _read_player(player_id)
    return _player_response(player)


@app.patch("/api/players/{player_id}")
async def update_player(player_id: str, body: dict):
    player = await _read_player(player_id)

    if "displayName" in body:
        player["displayName"] = body["displayName"]
    if "region" in body:
        player["region"] = body["region"]

    await container.replace_item(
        item=player["id"],
        body=player,
        partition_key=player_id,
    )
    return _player_response(player)


@app.delete("/api/players/{player_id}", status_code=204)
async def delete_player(player_id: str):
    # Verify player exists first
    await _read_player(player_id)

    # Delete all score documents for this player
    query = "SELECT c.id FROM c WHERE c.playerId = @pid AND c.type = 'score'"
    params = [{"name": "@pid", "value": player_id}]
    score_ids = []
    async for item in container.query_items(
        query=query, parameters=params, partition_key=player_id
    ):
        score_ids.append(item["id"])

    for sid in score_ids:
        await container.delete_item(item=sid, partition_key=player_id)

    # Delete the player document
    await container.delete_item(item=player_id, partition_key=player_id)

    return JSONResponse(status_code=204, content=None)


# ---------------------------------------------------------------------------
# Score Submission
# ---------------------------------------------------------------------------
@app.post("/api/scores", status_code=201)
async def submit_score(body: dict):
    player_id = body.get("playerId")
    score_val = body.get("score")
    game_mode = body.get("gameMode")

    if not player_id or score_val is None:
        raise HTTPException(status_code=400, detail="playerId and score are required")

    score_val = int(score_val)

    # Verify player exists
    player = await _read_player(player_id)

    score_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    score_doc = {
        "id": score_id,
        "scoreId": score_id,
        "playerId": player_id,
        "type": "score",  # Type discriminator (Rule 1.11)
        "score": score_val,
        "timestamp": now,
    }
    if game_mode:
        score_doc["gameMode"] = game_mode

    await container.create_item(body=score_doc)

    # Update player stats (denormalized for read-heavy workloads, Rule 1.2)
    player["totalGames"] = player.get("totalGames", 0) + 1
    player["totalScore"] = player.get("totalScore", 0) + score_val
    player["bestScore"] = max(player.get("bestScore", 0), score_val)
    player["averageScore"] = player["totalScore"] / player["totalGames"]

    await container.replace_item(
        item=player["id"],
        body=player,
        partition_key=player_id,
    )

    return {
        "scoreId": score_id,
        "playerId": player_id,
        "score": score_val,
    }


# ---------------------------------------------------------------------------
# Leaderboards
# ---------------------------------------------------------------------------
@app.get("/api/leaderboards/global")
async def global_leaderboard(top: int = Query(default=100, ge=1, le=100)):
    top = int(top)  # Ensure safe integer (Rule 3.8)
    # Cross-partition query — project only needed fields (Rule 3.9)
    # TOP must be a literal integer, not a parameter (Rule 3.8)
    # ORDER BY bestScore DESC, displayName ASC for tiebreaking
    query = (
        f"SELECT TOP {top} c.playerId, c.displayName, c.bestScore "
        f"FROM c WHERE c.type = 'player' AND c.bestScore > 0 "
        f"ORDER BY c.bestScore DESC, c.displayName ASC"
    )

    entries = []
    async for item in container.query_items(
        query=query, enable_cross_partition_query=True
    ):
        entries.append(item)

    return _ranked_list(entries)


@app.get("/api/leaderboards/regional/{region}")
async def regional_leaderboard(
    region: str, top: int = Query(default=100, ge=1, le=100)
):
    top = int(top)
    # Parameterized region filter (Rule 3.6), literal TOP (Rule 3.8)
    query = (
        f"SELECT TOP {top} c.playerId, c.displayName, c.bestScore "
        f"FROM c WHERE c.type = 'player' AND c.region = @region AND c.bestScore > 0 "
        f"ORDER BY c.bestScore DESC, c.displayName ASC"
    )
    params = [{"name": "@region", "value": region}]

    entries = []
    async for item in container.query_items(
        query=query, parameters=params, enable_cross_partition_query=True
    ):
        entries.append(item)

    return _ranked_list(entries)


# ---------------------------------------------------------------------------
# Player Ranking  (COUNT-based approach — Rule 9.2)
# ---------------------------------------------------------------------------
@app.get("/api/players/{player_id}/rank")
async def player_rank(player_id: str):
    player = await _read_player(player_id)

    best_score = player.get("bestScore", 0)
    if best_score == 0 and player.get("totalGames", 0) == 0:
        raise HTTPException(status_code=404, detail="Player has no scores")

    # COUNT-based rank: count players with higher bestScore (Rule 9.2)
    # For tiebreaking (same score, displayName ASC), count those with same score but earlier name
    display_name = player.get("displayName", "")
    count_query = (
        "SELECT VALUE COUNT(1) FROM c WHERE c.type = 'player' AND c.bestScore > 0 AND "
        "("
        "  c.bestScore > @score OR "
        "  (c.bestScore = @score AND c.displayName < @name)"
        ")"
    )
    params = [
        {"name": "@score", "value": best_score},
        {"name": "@name", "value": display_name},
    ]

    rank = 1
    async for count_val in container.query_items(
        query=count_query, parameters=params, enable_cross_partition_query=True
    ):
        rank = count_val + 1

    # Get neighbors: players ranked near this player (±10 positions)
    # First get all players sorted, find the window around our player
    # We need rank-11 to rank+10 in the sorted list — fetch a window
    skip_start = max(0, rank - 11)
    window_size = 21  # ±10 + self

    # Use OFFSET LIMIT to get the window of neighbors
    neighbor_query = (
        f"SELECT c.playerId, c.displayName, c.bestScore "
        f"FROM c WHERE c.type = 'player' AND c.bestScore > 0 "
        f"ORDER BY c.bestScore DESC, c.displayName ASC "
        f"OFFSET {int(skip_start)} LIMIT {int(window_size)}"
    )

    neighbors_raw = []
    async for item in container.query_items(
        query=neighbor_query, enable_cross_partition_query=True
    ):
        neighbors_raw.append(item)

    # Build neighbors list with ranks, excluding the player themselves
    neighbors = []
    for i, item in enumerate(neighbors_raw):
        item_rank = skip_start + i + 1
        if item["playerId"] != player_id:
            neighbors.append(
                {
                    "rank": item_rank,
                    "playerId": item["playerId"],
                    "displayName": item["displayName"],
                    "score": item["bestScore"],
                }
            )

    return {
        "playerId": player_id,
        "rank": rank,
        "score": best_score,
        "neighbors": neighbors,
    }


# ---------------------------------------------------------------------------
# Score History
# ---------------------------------------------------------------------------
@app.get("/api/players/{player_id}/scores")
async def get_player_scores(
    player_id: str, limit: int = Query(default=10, ge=1, le=100)
):
    # Verify player exists (returns 404 if not)
    await _read_player(player_id)

    limit = int(limit)
    # Single-partition query (partition key = playerId, Rule 3.1)
    # Literal TOP (Rule 3.8), ordered by timestamp DESC (most recent first)
    query = (
        f"SELECT TOP {limit} c.scoreId, c.playerId, c.score, c.gameMode, c.timestamp "
        f"FROM c WHERE c.type = 'score' "
        f"ORDER BY c.timestamp DESC"
    )

    scores = []
    async for item in container.query_items(
        query=query, partition_key=player_id
    ):
        scores.append(item)

    return scores


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _read_player(player_id: str) -> dict:
    """Point-read a player document (Rule 3.7)."""
    try:
        player = await container.read_item(item=player_id, partition_key=player_id)
        if player.get("type") != "player":
            raise HTTPException(status_code=404, detail="Player not found")
        return player
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")


def _player_response(player: dict) -> dict:
    """Project only the fields required by the API contract."""
    return {
        "playerId": player["playerId"],
        "displayName": player["displayName"],
        "region": player["region"],
        "totalGames": player.get("totalGames", 0),
        "bestScore": player.get("bestScore", 0),
        "averageScore": player.get("averageScore", 0.0),
    }


def _ranked_list(entries: list[dict]) -> list[dict]:
    """Convert raw query results to ranked leaderboard entries (1-based rank)."""
    return [
        {
            "rank": i + 1,
            "playerId": e["playerId"],
            "displayName": e["displayName"],
            "score": e["bestScore"],
        }
        for i, e in enumerate(entries)
    ]
