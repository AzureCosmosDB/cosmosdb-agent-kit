"""
Gaming Leaderboard API - FastAPI + Azure Cosmos DB (NoSQL API)

Implements a mobile game leaderboard system with:
- Player management (CRUD)
- Score submission with cumulative stats
- Global and regional leaderboards with deterministic tiebreaking
- Player rank with ±10 neighbor lookup
- Score history ordered most-recent-first

Cosmos DB best practices applied:
- Partition key: /playerId for both containers (high cardinality, aligns with queries)
- Exclude-all-first indexing: only queried paths are indexed
- Composite indexes for ORDER BY bestScore DESC, displayName ASC
- Async SDK (azure.cosmos.aio) for better throughput
- COUNT-based rank query (~3-5 RU) instead of scanning full partition
"""

import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

import urllib3
from azure.cosmos import PartitionKey
from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel

# Suppress SSL warnings for local Cosmos DB emulator
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATABASE_NAME = "gaming-leaderboard"
PLAYERS_CONTAINER = "players"
SCORES_CONTAINER = "scores"

# Module-level references populated during startup
cosmos_client: Optional[CosmosClient] = None
players_container = None
scores_container = None


async def init_cosmos():
    """Initialize Cosmos DB client, database, and containers with optimized indexing."""
    global cosmos_client, players_container, scores_container

    endpoint = os.environ.get("COSMOS_ENDPOINT", "https://localhost:8081")
    key = os.environ.get(
        "COSMOS_KEY",
        "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
    )

    cosmos_client = CosmosClient(endpoint, credential=key, connection_verify=False)
    database = await cosmos_client.create_database_if_not_exists(id=DATABASE_NAME)

    # Best practice: exclude-all-first indexing, include only queried paths.
    # Composite index for ORDER BY bestScore DESC, displayName ASC (leaderboard).
    players_indexing = {
        "indexingMode": "consistent",
        "automatic": True,
        "includedPaths": [
            {"path": "/region/?"},
            {"path": "/bestScore/?"},
            {"path": "/displayName/?"},
        ],
        "excludedPaths": [
            {"path": "/*"},
            {"path": '/"_etag"/?'},
        ],
        "compositeIndexes": [
            [
                {"path": "/bestScore", "order": "descending"},
                {"path": "/displayName", "order": "ascending"},
            ]
        ],
    }

    players_container = await database.create_container_if_not_exists(
        id=PLAYERS_CONTAINER,
        partition_key=PartitionKey(path="/playerId"),
        indexing_policy=players_indexing,
    )

    # Scores container: index timestamp for ORDER BY timestamp DESC
    scores_indexing = {
        "indexingMode": "consistent",
        "automatic": True,
        "includedPaths": [
            {"path": "/timestamp/?"},
        ],
        "excludedPaths": [
            {"path": "/*"},
            {"path": '/"_etag"/?'},
        ],
    }

    scores_container = await database.create_container_if_not_exists(
        id=SCORES_CONTAINER,
        partition_key=PartitionKey(path="/playerId"),
        indexing_policy=scores_indexing,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_cosmos()
    yield
    if cosmos_client:
        await cosmos_client.close()


app = FastAPI(lifespan=lifespan)


# ---------------------------------------------------------------------------
# Request models
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
# Helpers
# ---------------------------------------------------------------------------

def player_response(doc: dict) -> dict:
    """Return only the contract-required fields with camelCase naming."""
    return {
        "playerId": doc["playerId"],
        "displayName": doc["displayName"],
        "region": doc["region"],
        "totalGames": doc.get("totalGames", 0),
        "bestScore": doc.get("bestScore", 0),
        "averageScore": float(doc.get("averageScore", 0)),
    }


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Player Management
# ---------------------------------------------------------------------------

@app.post("/api/players", status_code=201)
async def create_player(req: CreatePlayerRequest):
    doc = {
        "id": req.playerId,
        "playerId": req.playerId,
        "displayName": req.displayName,
        "region": req.region,
        "totalGames": 0,
        "bestScore": 0,
        "averageScore": 0.0,
        "totalScore": 0,  # internal running total for average calculation
    }
    await players_container.create_item(body=doc)
    return player_response(doc)


@app.get("/api/players/{player_id}")
async def get_player(player_id: str):
    try:
        doc = await players_container.read_item(
            item=player_id, partition_key=player_id
        )
        return player_response(doc)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")


@app.patch("/api/players/{player_id}")
async def update_player(player_id: str, req: UpdatePlayerRequest):
    try:
        doc = await players_container.read_item(
            item=player_id, partition_key=player_id
        )
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    if req.displayName is not None:
        doc["displayName"] = req.displayName
    if req.region is not None:
        doc["region"] = req.region

    updated = await players_container.replace_item(item=doc["id"], body=doc)
    return player_response(updated)


@app.delete("/api/players/{player_id}")
async def delete_player(player_id: str):
    try:
        await players_container.read_item(
            item=player_id, partition_key=player_id
        )
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    # Delete associated scores first (partition-scoped query — efficient)
    query = "SELECT c.id FROM c"
    score_ids = []
    async for item in scores_container.query_items(
        query=query, partition_key=player_id
    ):
        score_ids.append(item["id"])

    for score_id in score_ids:
        await scores_container.delete_item(item=score_id, partition_key=player_id)

    # Delete the player document
    await players_container.delete_item(item=player_id, partition_key=player_id)
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Score Submission
# ---------------------------------------------------------------------------

@app.post("/api/scores", status_code=201)
async def submit_score(req: SubmitScoreRequest):
    # Verify player exists and load current stats
    try:
        player_doc = await players_container.read_item(
            item=req.playerId, partition_key=req.playerId
        )
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    score_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    score_doc = {
        "id": score_id,
        "scoreId": score_id,
        "playerId": req.playerId,
        "score": req.score,
        "gameMode": req.gameMode,
        "timestamp": timestamp,
    }
    await scores_container.create_item(body=score_doc)

    # Update player cumulative stats
    total_games = player_doc.get("totalGames", 0) + 1
    total_score = player_doc.get("totalScore", 0) + req.score
    best_score = max(player_doc.get("bestScore", 0), req.score)
    average_score = total_score / total_games

    player_doc["totalGames"] = total_games
    player_doc["totalScore"] = total_score
    player_doc["bestScore"] = best_score
    player_doc["averageScore"] = average_score

    await players_container.replace_item(item=player_doc["id"], body=player_doc)

    return {
        "scoreId": score_id,
        "playerId": req.playerId,
        "score": req.score,
    }


# ---------------------------------------------------------------------------
# Score History
# ---------------------------------------------------------------------------

@app.get("/api/players/{player_id}/scores")
async def get_player_scores(
    player_id: str, limit: int = Query(default=10, ge=1, le=100)
):
    # Verify player exists
    try:
        await players_container.read_item(
            item=player_id, partition_key=player_id
        )
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    # Cosmos DB OFFSET/LIMIT do not support parameterized values;
    # int() cast ensures only integer literals are interpolated.
    query = (
        f"SELECT * FROM c ORDER BY c.timestamp DESC OFFSET 0 LIMIT {int(limit)}"
    )

    results = []
    async for item in scores_container.query_items(
        query=query, partition_key=player_id
    ):
        results.append({
            "scoreId": item["scoreId"],
            "playerId": item["playerId"],
            "score": item["score"],
            "gameMode": item.get("gameMode"),
            "timestamp": item["timestamp"],
        })

    return results


# ---------------------------------------------------------------------------
# Leaderboards
# ---------------------------------------------------------------------------

@app.get("/api/leaderboards/global")
async def global_leaderboard(top: int = Query(default=100, ge=1, le=100)):
    # Cosmos DB OFFSET/LIMIT do not support parameterized values;
    # int() cast ensures only integer literals are interpolated.
    query = (
        "SELECT * FROM c "
        "ORDER BY c.bestScore DESC, c.displayName ASC "
        f"OFFSET 0 LIMIT {int(top)}"
    )

    results = []
    rank = 1
    async for item in players_container.query_items(
        query=query, enable_cross_partition_query=True
    ):
        results.append({
            "rank": rank,
            "playerId": item["playerId"],
            "displayName": item["displayName"],
            "score": item["bestScore"],
        })
        rank += 1

    return results


@app.get("/api/leaderboards/regional/{region}")
async def regional_leaderboard(
    region: str, top: int = Query(default=100, ge=1, le=100)
):
    # Cosmos DB OFFSET/LIMIT do not support parameterized values;
    # int() cast ensures only integer literals are interpolated.
    query = (
        "SELECT * FROM c WHERE c.region = @region "
        "ORDER BY c.bestScore DESC, c.displayName ASC "
        f"OFFSET 0 LIMIT {int(top)}"
    )
    params = [{"name": "@region", "value": region}]

    results = []
    rank = 1
    async for item in players_container.query_items(
        query=query, parameters=params, enable_cross_partition_query=True
    ):
        results.append({
            "rank": rank,
            "playerId": item["playerId"],
            "displayName": item["displayName"],
            "score": item["bestScore"],
        })
        rank += 1

    return results


# ---------------------------------------------------------------------------
# Player Ranking
# ---------------------------------------------------------------------------

@app.get("/api/players/{player_id}/rank")
async def get_player_rank(player_id: str):
    try:
        player_doc = await players_container.read_item(
            item=player_id, partition_key=player_id
        )
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    if player_doc.get("totalGames", 0) == 0:
        raise HTTPException(status_code=404, detail="Player has no scores")

    player_score = player_doc["bestScore"]
    player_name = player_doc["displayName"]

    # Efficient COUNT-based rank: count players ranked above (~3-5 RU)
    count_query = (
        "SELECT VALUE COUNT(1) FROM c "
        "WHERE c.bestScore > @score "
        "   OR (c.bestScore = @score AND c.displayName < @displayName)"
    )
    params = [
        {"name": "@score", "value": player_score},
        {"name": "@displayName", "value": player_name},
    ]

    rank = 1
    async for item in players_container.query_items(
        query=count_query,
        parameters=params,
        enable_cross_partition_query=True,
    ):
        rank = item + 1

    # Fetch neighbors: ±10 positions around the player
    start_rank = max(1, rank - 10)
    end_rank = rank + 10
    offset = start_rank - 1
    limit = end_rank - start_rank + 1

    # Cosmos DB OFFSET/LIMIT do not support parameterized values;
    # int() cast ensures only integer literals are interpolated.
    neighbors_query = (
        "SELECT * FROM c "
        "ORDER BY c.bestScore DESC, c.displayName ASC "
        f"OFFSET {int(offset)} LIMIT {int(limit)}"
    )

    neighbors = []
    current_rank = start_rank
    async for item in players_container.query_items(
        query=neighbors_query, enable_cross_partition_query=True
    ):
        if item["playerId"] != player_id:
            neighbors.append({
                "rank": current_rank,
                "playerId": item["playerId"],
                "displayName": item["displayName"],
                "score": item["bestScore"],
            })
        current_rank += 1

    return {
        "playerId": player_id,
        "rank": rank,
        "score": player_score,
        "neighbors": neighbors,
    }
