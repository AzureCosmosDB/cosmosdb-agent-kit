"""
Gaming Leaderboard API — FastAPI + Azure Cosmos DB (NoSQL API)

Implements a mobile game leaderboard system with real-time score updates,
global and regional leaderboards, and player profile management.

Best practices applied:
- Async Cosmos DB SDK with aiohttp (Rule 4.1, 4.15)
- Singleton CosmosClient (Rule 4.18)
- Point reads for known ID + partition key (Rule 3.7)
- Parameterized queries (Rule 3.6)
- Literal integers for TOP (Rule 3.8)
- Composite indexes for ORDER BY (Rule 5.1, 5.2)
- Exclude unused index paths (Rule 5.3)
- Type discriminators for polymorphic containers (Rule 1.11)
- Emulator SSL configuration (Rule 4.6)
- Project only needed fields (Rule 3.9)
"""

import os
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey, exceptions

# ---------------------------------------------------------------------------
# Configuration — read from environment variables (Rule 4.12)
# ---------------------------------------------------------------------------
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "https://localhost:8081")
COSMOS_KEY = os.environ.get(
    "COSMOS_KEY",
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
)
DATABASE_NAME = os.environ.get("DATABASE_NAME", "gaming-leaderboard-db")

# Container names
PLAYERS_CONTAINER = "players"
SCORES_CONTAINER = "scores"

# ---------------------------------------------------------------------------
# Singleton Cosmos DB client and containers (Rule 4.18)
# ---------------------------------------------------------------------------
cosmos_client: Optional[CosmosClient] = None
players_container = None
scores_container = None


async def init_cosmos() -> None:
    """Initialize the Cosmos DB client, database, and containers."""
    global cosmos_client, players_container, scores_container

    # Rule 4.6 — disable SSL verification for Cosmos DB Emulator
    cosmos_client = CosmosClient(
        url=COSMOS_ENDPOINT,
        credential=COSMOS_KEY,
        connection_verify=False,
    )

    database = await cosmos_client.create_database_if_not_exists(id=DATABASE_NAME)

    # ------------------------------------------------------------------
    # Players container
    # Partition key: /playerId  (high cardinality, immutable — Rule 2.4, 2.5)
    # ------------------------------------------------------------------
    players_indexing_policy = {
        "indexingMode": "consistent",
        "automatic": True,
        "includedPaths": [{"path": "/*"}],
        "excludedPaths": [{"path": '/"_etag"/?'}],
        "compositeIndexes": [
            # For global leaderboard: ORDER BY bestScore DESC, displayName ASC
            [
                {"path": "/bestScore", "order": "descending"},
                {"path": "/displayName", "order": "ascending"},
            ],
            # Inverse pair (Rule 5.1)
            [
                {"path": "/bestScore", "order": "ascending"},
                {"path": "/displayName", "order": "descending"},
            ],
        ],
    }

    players_container = await database.create_container_if_not_exists(
        id=PLAYERS_CONTAINER,
        partition_key=PartitionKey(path="/playerId"),
        indexing_policy=players_indexing_policy,
    )

    # ------------------------------------------------------------------
    # Scores container
    # Partition key: /playerId  (co-locate a player's scores — Rule 2.7)
    # ------------------------------------------------------------------
    scores_indexing_policy = {
        "indexingMode": "consistent",
        "automatic": True,
        "includedPaths": [{"path": "/*"}],
        "excludedPaths": [{"path": '/"_etag"/?'}],
        # Single-property ORDER BY (timestamp) is served by the default
        # range index on /*, so no composite index is needed here.
    }

    scores_container = await database.create_container_if_not_exists(
        id=SCORES_CONTAINER,
        partition_key=PartitionKey(path="/playerId"),
        indexing_policy=scores_indexing_policy,
    )


async def close_cosmos() -> None:
    """Close the Cosmos DB client connection."""
    global cosmos_client
    if cosmos_client:
        await cosmos_client.close()
        cosmos_client = None


# ---------------------------------------------------------------------------
# FastAPI application with lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_cosmos()
    yield
    await close_cosmos()


app = FastAPI(title="Gaming Leaderboard API", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class CreatePlayerRequest(BaseModel):
    playerId: str
    displayName: str
    region: str


class UpdatePlayerRequest(BaseModel):
    displayName: Optional[str] = None
    region: Optional[str] = None


class SubmitScoreRequest(BaseModel):
    playerId: str
    score: int
    gameMode: Optional[str] = None


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return JSONResponse(content={"status": "healthy"}, status_code=200)


# ---------------------------------------------------------------------------
# Player Management
# ---------------------------------------------------------------------------
@app.post("/api/players", status_code=201)
async def create_player(req: CreatePlayerRequest):
    player_doc = {
        "id": req.playerId,
        "playerId": req.playerId,
        "displayName": req.displayName,
        "region": req.region,
        "totalGames": 0,
        "bestScore": 0,
        "averageScore": 0.0,
        "type": "player",  # Type discriminator (Rule 1.11)
    }

    try:
        result = await players_container.create_item(body=player_doc)
    except exceptions.CosmosResourceExistsError:
        raise HTTPException(status_code=409, detail="Player already exists")

    return _player_response(result)


@app.get("/api/players/{player_id}")
async def get_player(player_id: str):
    try:
        # Point read — known ID and partition key (Rule 3.7)
        result = await players_container.read_item(
            item=player_id, partition_key=player_id
        )
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    return _player_response(result)


@app.patch("/api/players/{player_id}")
async def update_player(player_id: str, req: UpdatePlayerRequest):
    try:
        # Point read first (Rule 3.7)
        player = await players_container.read_item(
            item=player_id, partition_key=player_id
        )
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    if req.displayName is not None:
        player["displayName"] = req.displayName
    if req.region is not None:
        player["region"] = req.region

    result = await players_container.replace_item(item=player_id, body=player)
    return _player_response(result)


@app.delete("/api/players/{player_id}", status_code=204)
async def delete_player(player_id: str):
    # Verify the player exists first
    try:
        await players_container.read_item(item=player_id, partition_key=player_id)
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    # Delete the player document
    await players_container.delete_item(item=player_id, partition_key=player_id)

    # Delete all associated scores (Rule: clean up related data)
    query = "SELECT c.id FROM c WHERE c.playerId = @playerId"
    params = [{"name": "@playerId", "value": player_id}]
    score_ids = []
    async for item in scores_container.query_items(
        query=query, parameters=params, partition_key=player_id
    ):
        score_ids.append(item["id"])

    for score_id in score_ids:
        await scores_container.delete_item(item=score_id, partition_key=player_id)

    return JSONResponse(content=None, status_code=204)


# ---------------------------------------------------------------------------
# Score Submission
# ---------------------------------------------------------------------------
@app.post("/api/scores", status_code=201)
async def submit_score(req: SubmitScoreRequest):
    # Verify the player exists
    try:
        player = await players_container.read_item(
            item=req.playerId, partition_key=req.playerId
        )
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    score_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    score_doc = {
        "id": score_id,
        "scoreId": score_id,
        "playerId": req.playerId,
        "score": req.score,
        "gameMode": req.gameMode,
        "timestamp": now,
        "type": "score",  # Type discriminator (Rule 1.11)
    }

    await scores_container.create_item(body=score_doc)

    # Update player stats (denormalize for read-heavy leaderboard — Rule 1.2)
    total_games = player["totalGames"] + 1
    best_score = max(player["bestScore"], req.score)
    # Recalculate running average
    prev_total = player["averageScore"] * player["totalGames"]
    average_score = (prev_total + req.score) / total_games

    player["totalGames"] = total_games
    player["bestScore"] = best_score
    player["averageScore"] = average_score

    await players_container.replace_item(item=req.playerId, body=player)

    return {
        "scoreId": score_id,
        "playerId": req.playerId,
        "score": req.score,
    }


# ---------------------------------------------------------------------------
# Leaderboards
# ---------------------------------------------------------------------------
@app.get("/api/leaderboards/global")
async def global_leaderboard(top: int = Query(default=100, ge=1, le=100)):
    # Rule 3.8 — literal integer for TOP
    # Rule 3.9 — project only needed fields
    query = (
        f"SELECT TOP {int(top)} c.playerId, c.displayName, c.bestScore "
        f"FROM c ORDER BY c.bestScore DESC, c.displayName ASC"
    )

    entries = []
    rank = 1
    async for item in players_container.query_items(
        query=query, enable_cross_partition_query=True
    ):
        entries.append(
            {
                "rank": rank,
                "playerId": item["playerId"],
                "displayName": item["displayName"],
                "score": item["bestScore"],
            }
        )
        rank += 1

    return entries


@app.get("/api/leaderboards/regional/{region}")
async def regional_leaderboard(
    region: str, top: int = Query(default=100, ge=1, le=100)
):
    # Rule 3.6 — parameterized queries for filters
    # Rule 3.8 — literal integer for TOP
    # Rule 3.9 — project only needed fields
    query = (
        f"SELECT TOP {int(top)} c.playerId, c.displayName, c.bestScore "
        f"FROM c WHERE c.region = @region "
        f"ORDER BY c.bestScore DESC, c.displayName ASC"
    )
    params = [{"name": "@region", "value": region}]

    entries = []
    rank = 1
    async for item in players_container.query_items(
        query=query, parameters=params, enable_cross_partition_query=True
    ):
        entries.append(
            {
                "rank": rank,
                "playerId": item["playerId"],
                "displayName": item["displayName"],
                "score": item["bestScore"],
            }
        )
        rank += 1

    return entries


# ---------------------------------------------------------------------------
# Player Ranking
# ---------------------------------------------------------------------------
@app.get("/api/players/{player_id}/rank")
async def player_rank(player_id: str):
    # Verify the player exists and has a score
    try:
        player = await players_container.read_item(
            item=player_id, partition_key=player_id
        )
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    if player["totalGames"] == 0:
        raise HTTPException(
            status_code=404, detail="Player not found or has no scores"
        )

    player_best = player["bestScore"]
    player_name = player["displayName"]

    # Count players ranked above this player
    # A player is ranked above if they have a higher bestScore,
    # or same bestScore with displayName < this player's displayName (tiebreak)
    count_query = (
        "SELECT VALUE COUNT(1) FROM c WHERE "
        "c.bestScore > @bestScore OR "
        "(c.bestScore = @bestScore AND c.displayName < @displayName)"
    )
    count_params = [
        {"name": "@bestScore", "value": player_best},
        {"name": "@displayName", "value": player_name},
    ]

    rank_value = 1
    async for item in players_container.query_items(
        query=count_query,
        parameters=count_params,
        enable_cross_partition_query=True,
    ):
        rank_value = item + 1

    # Get the full sorted leaderboard around this player's position
    # Fetch enough to get ±10 neighbors
    start_rank = max(1, rank_value - 10)
    offset = start_rank - 1
    fetch_count = 21  # ±10 around the player + the player

    neighbor_query = (
        f"SELECT c.playerId, c.displayName, c.bestScore "
        f"FROM c ORDER BY c.bestScore DESC, c.displayName ASC "
        f"OFFSET {int(offset)} LIMIT {int(fetch_count)}"
    )

    neighbors = []
    current_rank = start_rank
    async for item in players_container.query_items(
        query=neighbor_query, enable_cross_partition_query=True
    ):
        neighbors.append(
            {
                "rank": current_rank,
                "playerId": item["playerId"],
                "displayName": item["displayName"],
                "score": item["bestScore"],
            }
        )
        current_rank += 1

    return {
        "playerId": player_id,
        "rank": rank_value,
        "score": player_best,
        "neighbors": neighbors,
    }


# ---------------------------------------------------------------------------
# Score History
# ---------------------------------------------------------------------------
@app.get("/api/players/{player_id}/scores")
async def get_player_scores(
    player_id: str, limit: int = Query(default=10, ge=1, le=100)
):
    # Verify the player exists
    try:
        await players_container.read_item(item=player_id, partition_key=player_id)
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    # Rule 3.6 — parameterized query
    # Rule 3.8 — literal integer for TOP
    # Rule 3.9 — project only needed fields
    query = (
        f"SELECT TOP {int(limit)} c.scoreId, c.playerId, c.score, "
        f"c.gameMode, c.timestamp "
        f"FROM c WHERE c.playerId = @playerId "
        f"ORDER BY c.timestamp DESC"
    )
    params = [{"name": "@playerId", "value": player_id}]

    scores = []
    async for item in scores_container.query_items(
        query=query, parameters=params, partition_key=player_id
    ):
        scores.append(
            {
                "scoreId": item["scoreId"],
                "playerId": item["playerId"],
                "score": item["score"],
                "gameMode": item.get("gameMode"),
                "timestamp": item["timestamp"],
            }
        )

    return scores


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _player_response(doc: dict) -> dict:
    """Build a player response with only the contract-required fields."""
    return {
        "playerId": doc["playerId"],
        "displayName": doc["displayName"],
        "region": doc["region"],
        "totalGames": doc["totalGames"],
        "bestScore": doc["bestScore"],
        "averageScore": doc["averageScore"],
    }
