"""
Gaming Leaderboard API — FastAPI + Azure Cosmos DB (NoSQL API)

Implements the gaming-leaderboard API contract with Cosmos DB best practices:
- Async SDK with singleton CosmosClient
- Partition key: playerId (high cardinality, aligned with most queries)
- Composite indexes for ORDER BY score DESC, displayName ASC
- Point reads where id and partition key are known
- Literal TOP in queries (not parameterized)
- SSL disabled for emulator; Gateway mode (Python default)
"""

import os
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "https://localhost:8081")
COSMOS_KEY = os.environ.get(
    "COSMOS_KEY",
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
)
DATABASE_NAME = "gaming-leaderboard"

# ---------------------------------------------------------------------------
# Singleton Cosmos client & containers (reused for the app lifetime)
# ---------------------------------------------------------------------------
cosmos_client: CosmosClient | None = None
players_container = None
scores_container = None


async def _init_cosmos() -> None:
    """Initialize the Cosmos DB client, database, and containers once."""
    global cosmos_client, players_container, scores_container

    # Reuse a single CosmosClient (rule 4.18)
    cosmos_client = CosmosClient(
        url=COSMOS_ENDPOINT,
        credential=COSMOS_KEY,
        # Gateway mode is the Python SDK default — no extra config needed.
        # Disable SSL verification for the local emulator (rule 4.6).
        connection_verify=False,
    )

    database = await cosmos_client.create_database_if_not_exists(id=DATABASE_NAME)

    # ---- Players container ----
    # Partition key: /playerId (high cardinality, immutable, aligned with
    # point reads on player profiles — rules 2.4, 2.5, 2.7, 3.7)
    players_container = await database.create_container_if_not_exists(
        id="players",
        partition_key=PartitionKey(path="/playerId"),
        indexing_policy={
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [{"path": "/*"}],
            "excludedPaths": [{"path": '/"_etag"/?'}],
            "compositeIndexes": [
                # Global / regional leaderboard:
                #   ORDER BY c.bestScore DESC, c.displayName ASC
                [
                    {"path": "/bestScore", "order": "descending"},
                    {"path": "/displayName", "order": "ascending"},
                ],
                # Inverse pair (rule 5.1)
                [
                    {"path": "/bestScore", "order": "ascending"},
                    {"path": "/displayName", "order": "descending"},
                ],
            ],
        },
    )

    # ---- Scores container ----
    # Partition key: /playerId — keeps a player's score history co-located
    # for efficient single-partition queries (rule 2.7).
    scores_container = await database.create_container_if_not_exists(
        id="scores",
        partition_key=PartitionKey(path="/playerId"),
        indexing_policy={
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [{"path": "/*"}],
            "excludedPaths": [{"path": '/"_etag"/?'}],
            "compositeIndexes": [
                # Score history: ORDER BY c.timestamp DESC
                [{"path": "/timestamp", "order": "descending"}],
                [{"path": "/timestamp", "order": "ascending"}],
            ],
        },
    )


async def _close_cosmos() -> None:
    global cosmos_client
    if cosmos_client is not None:
        await cosmos_client.close()
        cosmos_client = None


# ---------------------------------------------------------------------------
# FastAPI lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await _init_cosmos()
    yield
    await _close_cosmos()


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

    player = {
        "id": player_id,
        "playerId": player_id,
        "displayName": display_name,
        "region": region,
        "totalGames": 0,
        "bestScore": 0,
        "averageScore": 0.0,
        "type": "player",
    }

    created = await players_container.create_item(body=player)
    return _player_response(created)


@app.get("/api/players/{player_id}")
async def get_player(player_id: str):
    try:
        # Point read — 1 RU (rule 3.7)
        item = await players_container.read_item(item=player_id, partition_key=player_id)
        return _player_response(item)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")


@app.patch("/api/players/{player_id}")
async def update_player(player_id: str, body: dict):
    try:
        item = await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    if "displayName" in body:
        item["displayName"] = body["displayName"]
    if "region" in body:
        item["region"] = body["region"]

    replaced = await players_container.replace_item(item=item["id"], body=item)
    return _player_response(replaced)


@app.delete("/api/players/{player_id}", status_code=204)
async def delete_player(player_id: str):
    # Delete the player document
    try:
        await players_container.delete_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    # Also delete all associated scores (same partition key in scores container)
    query = "SELECT c.id FROM c WHERE c.playerId = @pid"
    params: list[dict] = [{"name": "@pid", "value": player_id}]
    score_ids: list[str] = []
    async for item in scores_container.query_items(
        query=query, parameters=params, partition_key=player_id
    ):
        score_ids.append(item["id"])

    for sid in score_ids:
        try:
            await scores_container.delete_item(item=sid, partition_key=player_id)
        except CosmosResourceNotFoundError:
            pass

    return JSONResponse(content=None, status_code=204)


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

    score_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    score_doc = {
        "id": score_id,
        "scoreId": score_id,
        "playerId": player_id,
        "score": score_val,
        "timestamp": now,
        "type": "score",
    }
    if game_mode is not None:
        score_doc["gameMode"] = game_mode

    await scores_container.create_item(body=score_doc)

    # Update player stats (denormalize for read-heavy leaderboard — rule 1.2)
    try:
        player = await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    total_games = player.get("totalGames", 0) + 1
    best_score = max(player.get("bestScore", 0), score_val)
    prev_avg = player.get("averageScore", 0.0)
    average_score = prev_avg + (score_val - prev_avg) / total_games

    player["totalGames"] = total_games
    player["bestScore"] = best_score
    player["averageScore"] = round(average_score, 2)

    await players_container.replace_item(item=player["id"], body=player)

    return {
        "scoreId": score_id,
        "playerId": player_id,
        "score": score_val,
    }


# ---------------------------------------------------------------------------
# Score History
# ---------------------------------------------------------------------------
@app.get("/api/players/{player_id}/scores")
async def get_player_scores(player_id: str, limit: int = Query(default=10, ge=1, le=100)):
    # Verify player exists first
    try:
        await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    # Use literal TOP (rule 3.8) — cannot parameterize TOP in Cosmos DB
    safe_limit = int(limit)
    query = f"SELECT * FROM c WHERE c.playerId = @pid ORDER BY c.timestamp DESC OFFSET 0 LIMIT {safe_limit}"
    params: list[dict] = [{"name": "@pid", "value": player_id}]

    results: list[dict] = []
    async for item in scores_container.query_items(
        query=query, parameters=params, partition_key=player_id
    ):
        results.append(
            {
                "scoreId": item["scoreId"],
                "playerId": item["playerId"],
                "score": item["score"],
                "gameMode": item.get("gameMode"),
                "timestamp": item["timestamp"],
            }
        )
    return results


# ---------------------------------------------------------------------------
# Leaderboards
# ---------------------------------------------------------------------------
@app.get("/api/leaderboards/global")
async def global_leaderboard(top: int = Query(default=100, ge=1, le=100)):
    # Cross-partition query — accepted for leaderboard reads.
    # Composite index on (bestScore DESC, displayName ASC) keeps this efficient.
    # Literal TOP (rule 3.8)
    safe_top = int(top)
    query = (
        f"SELECT TOP {safe_top} c.playerId, c.displayName, c.bestScore "
        "FROM c WHERE c.type = 'player' "
        "ORDER BY c.bestScore DESC, c.displayName ASC"
    )

    results: list[dict] = []
    rank = 1
    async for item in players_container.query_items(
        query=query, enable_cross_partition_query=True
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
async def regional_leaderboard(region: str, top: int = Query(default=100, ge=1, le=100)):
    safe_top = int(top)
    query = (
        f"SELECT TOP {safe_top} c.playerId, c.displayName, c.bestScore "
        "FROM c WHERE c.type = 'player' AND c.region = @region "
        "ORDER BY c.bestScore DESC, c.displayName ASC"
    )
    params: list[dict] = [{"name": "@region", "value": region}]

    results: list[dict] = []
    rank = 1
    async for item in players_container.query_items(
        query=query, parameters=params, enable_cross_partition_query=True
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
# Player Rank
# ---------------------------------------------------------------------------
@app.get("/api/players/{player_id}/rank")
async def player_rank(player_id: str):
    # Fetch the player's best score via point read
    try:
        player = await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    best_score = player.get("bestScore", 0)
    display_name = player.get("displayName", "")

    if best_score == 0 and player.get("totalGames", 0) == 0:
        raise HTTPException(status_code=404, detail="Player has no scores")

    # COUNT-based rank (rule 9.2) — count players with a strictly higher score,
    # plus those with the same score but an earlier (ascending) displayName.
    # Rank = higher_count + same_score_earlier_name_count + 1
    count_query = (
        "SELECT VALUE COUNT(1) FROM c WHERE c.type = 'player' AND "
        "(c.bestScore > @score OR (c.bestScore = @score AND c.displayName < @name))"
    )
    params: list[dict] = [
        {"name": "@score", "value": best_score},
        {"name": "@name", "value": display_name},
    ]

    rank_val = 1
    async for val in players_container.query_items(
        query=count_query, parameters=params, enable_cross_partition_query=True
    ):
        rank_val = val + 1

    # Fetch neighbours (±10 positions) using the sorted leaderboard
    # We need ranks from (rank_val - 10) to (rank_val + 10), excluding the player.
    offset = max(0, rank_val - 11)  # 0-based offset for OFFSET/LIMIT
    fetch_count = 21  # enough to cover ±10 around the player

    neighbors_query = (
        "SELECT c.playerId, c.displayName, c.bestScore "
        "FROM c WHERE c.type = 'player' "
        "ORDER BY c.bestScore DESC, c.displayName ASC "
        f"OFFSET {offset} LIMIT {fetch_count}"
    )

    neighbors: list[dict] = []
    current_rank = offset + 1
    async for item in players_container.query_items(
        query=neighbors_query, enable_cross_partition_query=True
    ):
        if item["playerId"] != player_id:
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
        "rank": rank_val,
        "score": best_score,
        "neighbors": neighbors,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _player_response(item: dict) -> dict:
    """Return the canonical player JSON shape expected by the contract."""
    return {
        "playerId": item["playerId"],
        "displayName": item["displayName"],
        "region": item["region"],
        "totalGames": item.get("totalGames", 0),
        "bestScore": item.get("bestScore", 0),
        "averageScore": item.get("averageScore", 0.0),
    }
