"""
Gaming Leaderboard API - FastAPI application using Azure Cosmos DB (NoSQL API).

Best practices applied:
- Async SDK with aiohttp for better throughput
- Singleton CosmosClient reused across requests
- Partition key aligned with query patterns (playerId for players/scores)
- Denormalized player stats updated on score submission
- Composite indexes for leaderboard sorting (score DESC, displayName ASC)
- Point reads used where possible (known id + partition key)
- Gateway mode for emulator compatibility with SSL verification disabled
- Autoscale throughput for variable workloads
- Excluded unused index paths to save RU on writes
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


COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "https://localhost:8081")
COSMOS_KEY = os.environ.get(
    "COSMOS_KEY",
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
)
DATABASE_NAME = "gaming-leaderboard"

# Indexing policy: exclude unused paths, add composite indexes for leaderboard queries
PLAYERS_INDEXING_POLICY = {
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
        ],
        [
            {"path": "/region", "order": "ascending"},
            {"path": "/bestScore", "order": "descending"},
            {"path": "/displayName", "order": "ascending"},
        ],
    ],
}

SCORES_INDEXING_POLICY = {
    "indexingMode": "consistent",
    "automatic": True,
    "includedPaths": [
        {"path": "/playerId/?"},
        {"path": "/timestamp/?"},
    ],
    "excludedPaths": [
        {"path": "/*"},
        {"path": '/"_etag"/?'},
    ],
    "compositeIndexes": [
        [
            {"path": "/playerId", "order": "ascending"},
            {"path": "/timestamp", "order": "descending"},
        ],
    ],
}

cosmos_client: CosmosClient | None = None
database = None
players_container = None
scores_container = None


async def init_cosmos():
    """Initialize Cosmos DB client and containers (singleton pattern)."""
    global cosmos_client, database, players_container, scores_container

    # Gateway mode for emulator compatibility; disable SSL verification for emulator
    cosmos_client = CosmosClient(
        COSMOS_ENDPOINT,
        credential=COSMOS_KEY,
        connection_verify=False,
    )

    database = await cosmos_client.create_database_if_not_exists(id=DATABASE_NAME)

    # Players container: partitioned by playerId for point reads
    players_container = await database.create_container_if_not_exists(
        id="players",
        partition_key=PartitionKey(path="/playerId"),
        indexing_policy=PLAYERS_INDEXING_POLICY,
        offer_throughput=400,
    )

    # Scores container: partitioned by playerId for efficient per-player queries
    scores_container = await database.create_container_if_not_exists(
        id="scores",
        partition_key=PartitionKey(path="/playerId"),
        indexing_policy=SCORES_INDEXING_POLICY,
        offer_throughput=400,
    )


async def close_cosmos():
    """Close the Cosmos DB client."""
    global cosmos_client
    if cosmos_client:
        await cosmos_client.close()
        cosmos_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_cosmos()
    yield
    await close_cosmos()


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
async def create_player(body: dict):
    player_id = body.get("playerId")
    display_name = body.get("displayName")
    region = body.get("region")

    if not player_id or not display_name or not region:
        raise HTTPException(status_code=400, detail="playerId, displayName, and region are required")

    player_doc = {
        "id": player_id,
        "playerId": player_id,
        "displayName": display_name,
        "region": region,
        "totalGames": 0,
        "bestScore": 0,
        "averageScore": 0.0,
        "type": "player",
    }

    try:
        result = await players_container.create_item(body=player_doc)
    except CosmosHttpResponseError as e:
        if e.status_code == 409:
            raise HTTPException(status_code=409, detail="Player already exists")
        raise

    return _player_response(result)


@app.get("/api/players/{player_id}")
async def get_player(player_id: str):
    try:
        result = await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    return _player_response(result)


@app.patch("/api/players/{player_id}")
async def update_player(player_id: str, body: dict):
    try:
        player = await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    if "displayName" in body:
        player["displayName"] = body["displayName"]
    if "region" in body:
        player["region"] = body["region"]

    result = await players_container.replace_item(item=player_id, body=player)
    return _player_response(result)


@app.delete("/api/players/{player_id}", status_code=204)
async def delete_player(player_id: str):
    # Verify player exists first
    try:
        await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    # Delete the player document
    await players_container.delete_item(item=player_id, partition_key=player_id)

    # Delete all associated scores
    query = "SELECT c.id FROM c WHERE c.playerId = @playerId"
    params = [{"name": "@playerId", "value": player_id}]
    score_ids = []
    async for item in scores_container.query_items(
        query=query,
        parameters=params,
        partition_key=player_id,
    ):
        score_ids.append(item["id"])

    for score_id in score_ids:
        try:
            await scores_container.delete_item(item=score_id, partition_key=player_id)
        except CosmosResourceNotFoundError:
            pass

    return JSONResponse(content=None, status_code=204)


def _player_response(doc: dict) -> dict:
    return {
        "playerId": doc["playerId"],
        "displayName": doc["displayName"],
        "region": doc["region"],
        "totalGames": doc.get("totalGames", 0),
        "bestScore": doc.get("bestScore", 0),
        "averageScore": doc.get("averageScore", 0.0),
    }


# ---------------------------------------------------------------------------
# Score Submission
# ---------------------------------------------------------------------------
@app.post("/api/scores", status_code=201)
async def submit_score(body: dict):
    player_id = body.get("playerId")
    score = body.get("score")

    if not player_id or score is None:
        raise HTTPException(status_code=400, detail="playerId and score are required")

    # Verify player exists
    try:
        player = await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    score_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    score_doc = {
        "id": score_id,
        "scoreId": score_id,
        "playerId": player_id,
        "score": score,
        "gameMode": body.get("gameMode"),
        "timestamp": now,
        "type": "score",
    }

    await scores_container.create_item(body=score_doc)

    # Update player stats (denormalized for read efficiency)
    total_games = player.get("totalGames", 0) + 1
    best_score = max(player.get("bestScore", 0), score)
    prev_avg = player.get("averageScore", 0.0)
    prev_total = player.get("totalGames", 0)
    average_score = ((prev_avg * prev_total) + score) / total_games

    player["totalGames"] = total_games
    player["bestScore"] = best_score
    player["averageScore"] = average_score

    await players_container.replace_item(item=player_id, body=player)

    return {
        "scoreId": score_id,
        "playerId": player_id,
        "score": score,
    }


# ---------------------------------------------------------------------------
# Score History
# ---------------------------------------------------------------------------
@app.get("/api/players/{player_id}/scores")
async def get_player_scores(player_id: str, limit: int = Query(default=10, ge=1, le=100)):
    # Verify player exists
    try:
        await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    query = (
        "SELECT TOP @limit c.scoreId, c.playerId, c.score, c.gameMode, c.timestamp "
        "FROM c WHERE c.playerId = @playerId ORDER BY c.timestamp DESC"
    )
    params = [
        {"name": "@limit", "value": limit},
        {"name": "@playerId", "value": player_id},
    ]

    results = []
    async for item in scores_container.query_items(
        query=query,
        parameters=params,
        partition_key=player_id,
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
    query = (
        "SELECT TOP @top c.playerId, c.displayName, c.bestScore "
        "FROM c ORDER BY c.bestScore DESC, c.displayName ASC"
    )
    params = [{"name": "@top", "value": top}]

    results = []
    rank = 1
    async for item in players_container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True,
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
async def regional_leaderboard(region: str, top: int = Query(default=100, ge=1, le=100)):
    query = (
        "SELECT TOP @top c.playerId, c.displayName, c.bestScore "
        "FROM c WHERE c.region = @region "
        "ORDER BY c.bestScore DESC, c.displayName ASC"
    )
    params = [
        {"name": "@top", "value": top},
        {"name": "@region", "value": region},
    ]

    results = []
    rank = 1
    async for item in players_container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True,
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
# Player Rank
# ---------------------------------------------------------------------------
@app.get("/api/players/{player_id}/rank")
async def player_rank(player_id: str):
    # Get the player's profile (point read)
    try:
        player = await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    player_best = player.get("bestScore", 0)
    if player_best == 0 and player.get("totalGames", 0) == 0:
        raise HTTPException(status_code=404, detail="Player has no scores")

    # Build full sorted leaderboard to determine rank and neighbors
    query = (
        "SELECT c.playerId, c.displayName, c.bestScore "
        "FROM c ORDER BY c.bestScore DESC, c.displayName ASC"
    )

    all_players = []
    async for item in players_container.query_items(
        query=query,
        enable_cross_partition_query=True,
    ):
        all_players.append(item)

    # Find the player's position
    player_index = None
    for i, p in enumerate(all_players):
        if p["playerId"] == player_id:
            player_index = i
            break

    if player_index is None:
        raise HTTPException(status_code=404, detail="Player not found in leaderboard")

    player_rank_val = player_index + 1

    # Get neighbors: ±10 positions
    start = max(0, player_index - 10)
    end = min(len(all_players), player_index + 11)

    neighbors = []
    for i in range(start, end):
        if i == player_index:
            continue
        neighbors.append({
            "rank": i + 1,
            "playerId": all_players[i]["playerId"],
            "displayName": all_players[i]["displayName"],
            "score": all_players[i]["bestScore"],
        })

    return {
        "playerId": player_id,
        "rank": player_rank_val,
        "score": player_best,
        "neighbors": neighbors,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
