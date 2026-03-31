"""
Gaming Leaderboard API — FastAPI application.

Implements the gaming-leaderboard API contract with Azure Cosmos DB best practices:
- Async SDK with aiohttp transport (rules 4.1, 4.15)
- Singleton CosmosClient (rule 4.18)
- Point reads for known id + partition key (rule 3.7)
- Parameterized queries (rule 3.6)
- Literal integers for TOP (rule 3.8)
- Composite indexes for ORDER BY (rules 5.1, 5.2)
- Pre-computed aggregates for player stats (rule 1.2)
- Type discriminators for polymorphic data (rule 1.11)
- camelCase field names throughout
"""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from azure.cosmos.exceptions import CosmosResourceNotFoundError
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from cosmos_db import close_client, get_container, initialize_database


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class CreatePlayerRequest(BaseModel):
    playerId: str
    displayName: str
    region: str


class UpdatePlayerRequest(BaseModel):
    displayName: str | None = None
    region: str | None = None


class SubmitScoreRequest(BaseModel):
    playerId: str
    score: int
    gameMode: str | None = None


# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_database()
    yield
    await close_client()


app = FastAPI(title="Gaming Leaderboard API", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return JSONResponse(content={"status": "ok"}, status_code=200)


# ---------------------------------------------------------------------------
# Player Management
# ---------------------------------------------------------------------------


@app.post("/api/players", status_code=201)
async def create_player(req: CreatePlayerRequest):
    container = await get_container()

    player = {
        "id": req.playerId,
        "playerId": req.playerId,
        "type": "player",
        "displayName": req.displayName,
        "region": req.region,
        "totalGames": 0,
        "bestScore": 0,
        "averageScore": 0.0,
    }

    await container.create_item(body=player)

    return {
        "playerId": player["playerId"],
        "displayName": player["displayName"],
        "region": player["region"],
        "totalGames": player["totalGames"],
        "bestScore": player["bestScore"],
        "averageScore": player["averageScore"],
    }


@app.get("/api/players/{player_id}")
async def get_player(player_id: str):
    container = await get_container()

    try:
        # Point read: known id + partition key (rule 3.7)
        player = await container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    return {
        "playerId": player["playerId"],
        "displayName": player["displayName"],
        "region": player["region"],
        "totalGames": player["totalGames"],
        "bestScore": player["bestScore"],
        "averageScore": player["averageScore"],
    }


@app.patch("/api/players/{player_id}")
async def update_player(player_id: str, req: UpdatePlayerRequest):
    container = await get_container()

    try:
        player = await container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    if req.displayName is not None:
        player["displayName"] = req.displayName
    if req.region is not None:
        player["region"] = req.region

    await container.replace_item(item=player_id, body=player)

    return {
        "playerId": player["playerId"],
        "displayName": player["displayName"],
        "region": player["region"],
        "totalGames": player["totalGames"],
        "bestScore": player["bestScore"],
        "averageScore": player["averageScore"],
    }


@app.delete("/api/players/{player_id}", status_code=204)
async def delete_player(player_id: str):
    container = await get_container()

    # Check player exists
    try:
        await container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    # Delete all score documents for this player (partition-aligned query)
    query = "SELECT c.id FROM c WHERE c.playerId = @playerId AND c.type = 'score'"
    parameters = [{"name": "@playerId", "value": player_id}]

    score_ids = []
    async for item in container.query_items(
        query=query,
        parameters=parameters,
        partition_key=player_id,
    ):
        score_ids.append(item["id"])

    for score_id in score_ids:
        await container.delete_item(item=score_id, partition_key=player_id)

    # Delete the player document
    await container.delete_item(item=player_id, partition_key=player_id)

    return None


# ---------------------------------------------------------------------------
# Score Submission
# ---------------------------------------------------------------------------


@app.post("/api/scores", status_code=201)
async def submit_score(req: SubmitScoreRequest):
    container = await get_container()

    # Verify player exists
    try:
        player = await container.read_item(
            item=req.playerId, partition_key=req.playerId
        )
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    score_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    score_doc = {
        "id": score_id,
        "playerId": req.playerId,
        "type": "score",
        "score": req.score,
        "gameMode": req.gameMode,
        "timestamp": timestamp,
    }

    await container.create_item(body=score_doc)

    # Update player's pre-computed aggregates (rule 1.2 — denormalize)
    total_games = player["totalGames"] + 1
    best_score = max(player["bestScore"], req.score)

    # Compute running average
    prev_total = player["averageScore"] * player["totalGames"]
    average_score = (prev_total + req.score) / total_games

    player["totalGames"] = total_games
    player["bestScore"] = best_score
    player["averageScore"] = average_score

    await container.replace_item(item=req.playerId, body=player)

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
    container = await get_container()

    # Rule 3.8: Use literal integer for TOP, never parameters
    query = (
        f"SELECT TOP {int(top)} c.playerId, c.displayName, c.bestScore "
        f"FROM c WHERE c.type = 'player' "
        f"ORDER BY c.bestScore DESC, c.displayName ASC"
    )

    results = []
    rank = 1
    async for item in container.query_items(
        query=query,
        enable_cross_partition_query=True,
    ):
        results.append(
            {
                "rank": rank,
                "playerId": item["playerId"],
                "displayName": item["displayName"],
                "score": item["bestScore"],
            }
        )
        rank += 1

    return results


@app.get("/api/leaderboards/regional/{region}")
async def regional_leaderboard(
    region: str, top: int = Query(default=100, ge=1, le=100)
):
    container = await get_container()

    # Rule 3.6: Parameterized queries (except TOP which must be literal per rule 3.8)
    query = (
        f"SELECT TOP {int(top)} c.playerId, c.displayName, c.bestScore "
        f"FROM c WHERE c.type = 'player' AND c.region = @region "
        f"ORDER BY c.bestScore DESC, c.displayName ASC"
    )
    parameters = [{"name": "@region", "value": region}]

    results = []
    rank = 1
    async for item in container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True,
    ):
        results.append(
            {
                "rank": rank,
                "playerId": item["playerId"],
                "displayName": item["displayName"],
                "score": item["bestScore"],
            }
        )
        rank += 1

    return results


# ---------------------------------------------------------------------------
# Player Ranking
# ---------------------------------------------------------------------------


@app.get("/api/players/{player_id}/rank")
async def player_rank(player_id: str):
    container = await get_container()

    # Verify player exists and has scores
    try:
        player = await container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    if player["totalGames"] == 0:
        raise HTTPException(status_code=404, detail="Player has no scores")

    # Get all players sorted by bestScore DESC, displayName ASC to determine rank
    query = (
        "SELECT c.playerId, c.displayName, c.bestScore "
        "FROM c WHERE c.type = 'player' AND c.totalGames > 0 "
        "ORDER BY c.bestScore DESC, c.displayName ASC"
    )

    all_players = []
    async for item in container.query_items(
        query=query,
        enable_cross_partition_query=True,
    ):
        all_players.append(item)

    # Find the player's position
    player_index = -1
    for i, p in enumerate(all_players):
        if p["playerId"] == player_id:
            player_index = i
            break

    if player_index == -1:
        raise HTTPException(status_code=404, detail="Player not found in rankings")

    player_rank_value = player_index + 1  # 1-based rank

    # Get neighbors: ±10 positions
    start = max(0, player_index - 10)
    end = min(len(all_players), player_index + 11)

    neighbors = []
    for i in range(start, end):
        if i == player_index:
            continue
        neighbors.append(
            {
                "rank": i + 1,
                "playerId": all_players[i]["playerId"],
                "displayName": all_players[i]["displayName"],
                "score": all_players[i]["bestScore"],
            }
        )

    return {
        "playerId": player_id,
        "rank": player_rank_value,
        "score": player["bestScore"],
        "neighbors": neighbors,
    }


# ---------------------------------------------------------------------------
# Score History
# ---------------------------------------------------------------------------


@app.get("/api/players/{player_id}/scores")
async def get_player_scores(
    player_id: str, limit: int = Query(default=10, ge=1, le=100)
):
    container = await get_container()

    # Check player exists
    try:
        await container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    # Rule 3.8: Literal TOP; Rule 3.6: Parameterized query
    query = (
        f"SELECT TOP {int(limit)} c.id, c.playerId, c.score, c.gameMode, c.timestamp "
        f"FROM c WHERE c.playerId = @playerId AND c.type = 'score' "
        f"ORDER BY c.timestamp DESC"
    )
    parameters = [{"name": "@playerId", "value": player_id}]

    results = []
    async for item in container.query_items(
        query=query,
        parameters=parameters,
        partition_key=player_id,
    ):
        results.append(
            {
                "scoreId": item["id"],
                "playerId": item["playerId"],
                "score": item["score"],
                "gameMode": item.get("gameMode"),
                "timestamp": item["timestamp"],
            }
        )

    return results
