import os
import uuid
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceNotFoundError

logger = logging.getLogger("gaming-leaderboard")
logging.basicConfig(level=logging.INFO)

COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "https://localhost:8081")
COSMOS_KEY = os.environ.get(
    "COSMOS_KEY",
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
)
DATABASE_NAME = "gaming-leaderboard"

# Singleton CosmosClient — reuse across the application lifetime
cosmos_client: CosmosClient = None
database = None
players_container = None
scores_container = None


async def initialize_cosmos():
    """Initialize Cosmos DB client, database, and containers."""
    global cosmos_client, database, players_container, scores_container

    cosmos_client = CosmosClient(
        url=COSMOS_ENDPOINT,
        credential=COSMOS_KEY,
    )

    database = await cosmos_client.create_database_if_not_exists(id=DATABASE_NAME)

    # Players container — partition key is playerId for efficient point reads
    players_container = await database.create_container_if_not_exists(
        id="players",
        partition_key=PartitionKey(path="/playerId"),
        indexing_policy={
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [{"path": "/*"}],
            "excludedPaths": [{"path": '/"_etag"/?'}],
            "compositeIndexes": [
                [
                    {"path": "/bestScore", "order": "descending"},
                    {"path": "/displayName", "order": "ascending"},
                ],
                [
                    {"path": "/bestScore", "order": "ascending"},
                    {"path": "/displayName", "order": "descending"},
                ],
                [
                    {"path": "/region", "order": "ascending"},
                    {"path": "/bestScore", "order": "descending"},
                    {"path": "/displayName", "order": "ascending"},
                ],
                [
                    {"path": "/region", "order": "descending"},
                    {"path": "/bestScore", "order": "ascending"},
                    {"path": "/displayName", "order": "descending"},
                ],
            ],
        },
    )

    # Scores container — partition key is playerId for efficient player score lookups
    scores_container = await database.create_container_if_not_exists(
        id="scores",
        partition_key=PartitionKey(path="/playerId"),
        indexing_policy={
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [{"path": "/*"}],
            "excludedPaths": [{"path": '/"_etag"/?'}],
            "compositeIndexes": [
                [
                    {"path": "/playerId", "order": "ascending"},
                    {"path": "/timestamp", "order": "descending"},
                ],
                [
                    {"path": "/playerId", "order": "descending"},
                    {"path": "/timestamp", "order": "ascending"},
                ],
            ],
        },
    )


async def shutdown_cosmos():
    """Close the Cosmos DB client."""
    global cosmos_client
    if cosmos_client:
        await cosmos_client.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_cosmos()
    yield
    await shutdown_cosmos()


app = FastAPI(title="Gaming Leaderboard API", lifespan=lifespan)


@app.get("/health")
async def health():
    return JSONResponse(status_code=200, content={"status": "ok"})


# ----------------------------------------------------------
# Player Management
# ----------------------------------------------------------


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

    try:
        result = await players_container.create_item(body=player)
    except CosmosHttpResponseError as e:
        if e.status_code == 409:
            raise HTTPException(status_code=409, detail="Player already exists")
        raise

    return _format_player(result)


@app.get("/api/players/{player_id}")
async def get_player(player_id: str):
    try:
        # Point read — 1 RU, bypasses query engine
        result = await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    return _format_player(result)


@app.patch("/api/players/{player_id}")
async def update_player(player_id: str, body: dict):
    try:
        existing = await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    if "displayName" in body:
        existing["displayName"] = body["displayName"]
    if "region" in body:
        existing["region"] = body["region"]

    result = await players_container.replace_item(item=player_id, body=existing)
    return _format_player(result)


@app.delete("/api/players/{player_id}", status_code=204)
async def delete_player(player_id: str):
    try:
        await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    # Delete the player document
    await players_container.delete_item(item=player_id, partition_key=player_id)

    # Delete all associated score documents
    query = "SELECT c.id FROM c WHERE c.playerId = @playerId"
    parameters = [{"name": "@playerId", "value": player_id}]
    score_ids = []
    async for item in scores_container.query_items(
        query=query, parameters=parameters, partition_key=player_id
    ):
        score_ids.append(item["id"])

    for score_id in score_ids:
        await scores_container.delete_item(item=score_id, partition_key=player_id)

    return None


# ----------------------------------------------------------
# Score Submission
# ----------------------------------------------------------


@app.post("/api/scores", status_code=201)
async def submit_score(body: dict):
    player_id = body.get("playerId")
    score = body.get("score")
    game_mode = body.get("gameMode")

    if not player_id or score is None:
        raise HTTPException(status_code=400, detail="playerId and score are required")

    # Verify the player exists
    try:
        player = await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    score_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    score_doc = {
        "id": score_id,
        "scoreId": score_id,
        "playerId": player_id,
        "score": score,
        "timestamp": timestamp,
        "type": "score",
    }
    if game_mode:
        score_doc["gameMode"] = game_mode

    await scores_container.create_item(body=score_doc)

    # Update player stats
    total_games = player.get("totalGames", 0) + 1
    best_score = max(player.get("bestScore", 0), score)
    # Compute running average
    old_avg = player.get("averageScore", 0.0)
    old_total = player.get("totalGames", 0)
    new_avg = ((old_avg * old_total) + score) / total_games

    player["totalGames"] = total_games
    player["bestScore"] = best_score
    player["averageScore"] = new_avg

    await players_container.replace_item(item=player_id, body=player)

    response = {
        "scoreId": score_id,
        "playerId": player_id,
        "score": score,
    }
    return response


# ----------------------------------------------------------
# Leaderboards
# ----------------------------------------------------------


@app.get("/api/leaderboards/global")
async def global_leaderboard(top: int = Query(default=100, ge=1, le=100)):
    # Cross-partition query sorted by bestScore DESC, displayName ASC (tiebreaker)
    # Composite index supports this ordering
    query = f"SELECT TOP {top} c.playerId, c.displayName, c.bestScore FROM c WHERE c.type = 'player' ORDER BY c.bestScore DESC, c.displayName ASC"

    results = []
    async for item in players_container.query_items(
        query=query, enable_cross_partition_query=True
    ):
        results.append(item)

    leaderboard = []
    for rank, entry in enumerate(results, start=1):
        leaderboard.append(
            {
                "rank": rank,
                "playerId": entry["playerId"],
                "displayName": entry["displayName"],
                "score": entry["bestScore"],
            }
        )

    return leaderboard


@app.get("/api/leaderboards/regional/{region}")
async def regional_leaderboard(region: str, top: int = Query(default=100, ge=1, le=100)):
    # Use parameterized query for the region filter, literal TOP
    query = f"SELECT TOP {top} c.playerId, c.displayName, c.bestScore FROM c WHERE c.type = 'player' AND c.region = @region ORDER BY c.bestScore DESC, c.displayName ASC"
    parameters = [{"name": "@region", "value": region}]

    results = []
    async for item in players_container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True,
    ):
        results.append(item)

    leaderboard = []
    for rank, entry in enumerate(results, start=1):
        leaderboard.append(
            {
                "rank": rank,
                "playerId": entry["playerId"],
                "displayName": entry["displayName"],
                "score": entry["bestScore"],
            }
        )

    return leaderboard


# ----------------------------------------------------------
# Player Ranking
# ----------------------------------------------------------


@app.get("/api/players/{player_id}/rank")
async def player_rank(player_id: str):
    # Verify the player exists
    try:
        player = await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    if player.get("bestScore", 0) == 0 and player.get("totalGames", 0) == 0:
        raise HTTPException(status_code=404, detail="Player has no scores")

    player_score = player.get("bestScore", 0)
    player_display_name = player.get("displayName", "")

    # Get all players sorted by bestScore DESC, displayName ASC
    query = "SELECT c.playerId, c.displayName, c.bestScore FROM c WHERE c.type = 'player' AND c.totalGames > 0 ORDER BY c.bestScore DESC, c.displayName ASC"

    all_players = []
    async for item in players_container.query_items(
        query=query, enable_cross_partition_query=True
    ):
        all_players.append(item)

    # Find the player's position
    player_index = None
    for i, p in enumerate(all_players):
        if p["playerId"] == player_id:
            player_index = i
            break

    if player_index is None:
        raise HTTPException(status_code=404, detail="Player not found in rankings")

    player_rank_value = player_index + 1

    # Get neighbors (±10 positions)
    start = max(0, player_index - 10)
    end = min(len(all_players), player_index + 11)
    neighbors_slice = all_players[start:end]

    neighbors = []
    for idx, entry in enumerate(neighbors_slice, start=start + 1):
        if entry["playerId"] != player_id:
            neighbors.append(
                {
                    "rank": idx,
                    "playerId": entry["playerId"],
                    "displayName": entry["displayName"],
                    "score": entry["bestScore"],
                }
            )

    return {
        "playerId": player_id,
        "rank": player_rank_value,
        "score": player_score,
        "neighbors": neighbors,
    }


# ----------------------------------------------------------
# Score History
# ----------------------------------------------------------


@app.get("/api/players/{player_id}/scores")
async def get_player_scores(player_id: str, limit: int = Query(default=10, ge=1, le=100)):
    # Verify the player exists via point read
    try:
        await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    # Query scores for this player, ordered by most recent first
    # Partition-scoped query — efficient single-partition read
    query = f"SELECT TOP {limit} c.scoreId, c.playerId, c.score, c.gameMode, c.timestamp FROM c WHERE c.playerId = @playerId ORDER BY c.timestamp DESC"
    parameters = [{"name": "@playerId", "value": player_id}]

    results = []
    async for item in scores_container.query_items(
        query=query, parameters=parameters, partition_key=player_id
    ):
        results.append(item)

    # Build response ensuring all required fields are present
    scores = []
    for item in results:
        score_entry = {
            "scoreId": item["scoreId"],
            "playerId": item["playerId"],
            "score": item["score"],
            "timestamp": item["timestamp"],
        }
        if "gameMode" in item:
            score_entry["gameMode"] = item["gameMode"]
        scores.append(score_entry)

    return scores


# ----------------------------------------------------------
# Helpers
# ----------------------------------------------------------


def _format_player(doc: dict) -> dict:
    """Format player document for API response, using camelCase field names."""
    return {
        "playerId": doc["playerId"],
        "displayName": doc["displayName"],
        "region": doc["region"],
        "totalGames": doc.get("totalGames", 0),
        "bestScore": doc.get("bestScore", 0),
        "averageScore": doc.get("averageScore", 0.0),
    }
