"""Gaming Leaderboard API - FastAPI application with Azure Cosmos DB."""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="Gaming Leaderboard API")

COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "https://localhost:8081")
COSMOS_KEY = os.environ.get(
    "COSMOS_KEY",
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
)
DATABASE_NAME = "gaming-leaderboard-db"

PLAYERS_CONTAINER = "players"
SCORES_CONTAINER = "scores"
LEADERBOARD_CONTAINER = "leaderboard"

cosmos_client: Optional[CosmosClient] = None
database = None
players_container = None
scores_container = None
leaderboard_container = None


@app.on_event("startup")
async def startup():
    """Initialize Cosmos DB client and ensure database/containers exist."""
    global cosmos_client, database, players_container, scores_container, leaderboard_container

    cosmos_client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
    database = await cosmos_client.create_database_if_not_exists(id=DATABASE_NAME)

    # Players container - partitioned by playerId for efficient point reads
    players_container = await database.create_container_if_not_exists(
        id=PLAYERS_CONTAINER,
        partition_key=PartitionKey(path="/playerId"),
    )

    # Scores container - partitioned by playerId for efficient player score history queries
    scores_container = await database.create_container_if_not_exists(
        id=SCORES_CONTAINER,
        partition_key=PartitionKey(path="/playerId"),
    )

    # Leaderboard container - partitioned by region for efficient regional queries
    # Global leaderboard uses region="GLOBAL"
    leaderboard_container = await database.create_container_if_not_exists(
        id=LEADERBOARD_CONTAINER,
        partition_key=PartitionKey(path="/region"),
    )


@app.on_event("shutdown")
async def shutdown():
    """Close Cosmos DB client."""
    global cosmos_client
    if cosmos_client:
        await cosmos_client.close()
        cosmos_client = None


@app.get("/health")
async def health():
    """Health check endpoint."""
    return JSONResponse(content={"status": "healthy"}, status_code=200)


@app.post("/api/players", status_code=201)
async def create_player(body: dict):
    """Create a new player profile."""
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

    await players_container.create_item(body=player_doc)

    return {
        "playerId": player_doc["playerId"],
        "displayName": player_doc["displayName"],
        "region": player_doc["region"],
        "totalGames": player_doc["totalGames"],
        "bestScore": player_doc["bestScore"],
        "averageScore": player_doc["averageScore"],
    }


@app.get("/api/players/{player_id}")
async def get_player(player_id: str):
    """Get player profile with stats."""
    try:
        # Point read using id and partition key - most efficient (1 RU)
        player = await players_container.read_item(item=player_id, partition_key=player_id)
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
async def update_player(player_id: str, body: dict):
    """Update a player's profile fields."""
    try:
        player = await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    old_region = player["region"]

    if "displayName" in body:
        player["displayName"] = body["displayName"]
    if "region" in body:
        player["region"] = body["region"]

    updated = await players_container.replace_item(item=player_id, body=player)

    # Update leaderboard entries if player has scores
    if updated["totalGames"] > 0:
        if "region" in body and body["region"] != old_region:
            # Region changed - delete old regional entry and create new one
            try:
                await leaderboard_container.delete_item(
                    item=f"regional_{player_id}", partition_key=old_region
                )
            except CosmosResourceNotFoundError:
                pass
            regional_entry = {
                "id": f"regional_{player_id}",
                "playerId": player_id,
                "displayName": updated["displayName"],
                "score": updated["bestScore"],
                "region": updated["region"],
                "type": "leaderboardEntry",
            }
            await leaderboard_container.upsert_item(body=regional_entry)

        if "displayName" in body:
            # Update display name in global leaderboard entry
            try:
                global_entry = await leaderboard_container.read_item(
                    item=f"global_{player_id}", partition_key="GLOBAL"
                )
                global_entry["displayName"] = body["displayName"]
                await leaderboard_container.replace_item(
                    item=f"global_{player_id}", body=global_entry
                )
            except CosmosResourceNotFoundError:
                pass

            # Update display name in regional leaderboard entry
            if "region" not in body or body["region"] == old_region:
                try:
                    regional_entry = await leaderboard_container.read_item(
                        item=f"regional_{player_id}", partition_key=updated["region"]
                    )
                    regional_entry["displayName"] = body["displayName"]
                    await leaderboard_container.replace_item(
                        item=f"regional_{player_id}", body=regional_entry
                    )
                except CosmosResourceNotFoundError:
                    pass

    return {
        "playerId": updated["playerId"],
        "displayName": updated["displayName"],
        "region": updated["region"],
        "totalGames": updated["totalGames"],
        "bestScore": updated["bestScore"],
        "averageScore": updated["averageScore"],
    }


@app.delete("/api/players/{player_id}", status_code=204)
async def delete_player(player_id: str):
    """Delete a player and all their associated score data."""
    try:
        player = await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    region = player["region"]

    # Delete the player document
    await players_container.delete_item(item=player_id, partition_key=player_id)

    # Delete all score documents for this player (same partition)
    query = "SELECT c.id FROM c WHERE c.playerId = @playerId"
    params = [{"name": "@playerId", "value": player_id}]
    score_ids = []
    async for item in scores_container.query_items(
        query=query, parameters=params, partition_key=player_id
    ):
        score_ids.append(item["id"])

    for score_id in score_ids:
        await scores_container.delete_item(item=score_id, partition_key=player_id)

    # Delete leaderboard entries using point reads (efficient)
    try:
        await leaderboard_container.delete_item(
            item=f"global_{player_id}", partition_key="GLOBAL"
        )
    except CosmosResourceNotFoundError:
        pass

    try:
        await leaderboard_container.delete_item(
            item=f"regional_{player_id}", partition_key=region
        )
    except CosmosResourceNotFoundError:
        pass

    return None


@app.post("/api/scores", status_code=201)
async def submit_score(body: dict):
    """Submit a game score for a player."""
    player_id = body.get("playerId")
    score = body.get("score")
    game_mode = body.get("gameMode")

    if not player_id or score is None:
        raise HTTPException(status_code=400, detail="playerId and score are required")

    # Verify the player exists using a point read
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
    if game_mode is not None:
        score_doc["gameMode"] = game_mode

    await scores_container.create_item(body=score_doc)

    # Update player stats inline (update aggregate at write time)
    total_games = player["totalGames"] + 1
    best_score = max(player["bestScore"], score)
    current_total = player["averageScore"] * player["totalGames"]
    average_score = (current_total + score) / total_games

    player["totalGames"] = total_games
    player["bestScore"] = best_score
    player["averageScore"] = average_score

    await players_container.replace_item(item=player_id, body=player)

    # Update leaderboard entries if this is a new best score
    if score >= best_score:
        await _upsert_leaderboard_entry(player_id, player["displayName"], player["region"], best_score)

    return {
        "scoreId": score_id,
        "playerId": player_id,
        "score": score,
    }


@app.get("/api/players/{player_id}/scores")
async def get_player_scores(player_id: str, limit: int = Query(default=10, ge=1, le=100)):
    """Get a player's score history ordered by most recent first."""
    # Verify the player exists
    try:
        await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    # Single-partition query (efficient) - scores partitioned by playerId
    query = (
        "SELECT c.scoreId, c.playerId, c.score, c.gameMode, c.timestamp "
        "FROM c WHERE c.playerId = @playerId "
        "ORDER BY c.timestamp DESC OFFSET 0 LIMIT @limit"
    )
    params = [
        {"name": "@playerId", "value": player_id},
        {"name": "@limit", "value": limit},
    ]

    results = []
    async for item in scores_container.query_items(
        query=query, parameters=params, partition_key=player_id
    ):
        entry = {
            "scoreId": item["scoreId"],
            "playerId": item["playerId"],
            "score": item["score"],
            "timestamp": item["timestamp"],
        }
        if "gameMode" in item and item["gameMode"] is not None:
            entry["gameMode"] = item["gameMode"]
        results.append(entry)

    return results


@app.get("/api/leaderboards/global")
async def global_leaderboard(top: int = Query(default=100, ge=1, le=100)):
    """Get global top N leaderboard sorted by best score descending."""
    # Query the leaderboard container with region="GLOBAL"
    # Single-partition query for efficiency
    query = (
        "SELECT c.playerId, c.displayName, c.score "
        "FROM c WHERE c.region = 'GLOBAL' "
        "ORDER BY c.score DESC, c.displayName ASC "
        "OFFSET 0 LIMIT @top"
    )
    params = [{"name": "@top", "value": top}]

    results = []
    rank = 0
    async for item in leaderboard_container.query_items(
        query=query, parameters=params, partition_key="GLOBAL"
    ):
        rank += 1
        results.append(
            {
                "rank": rank,
                "playerId": item["playerId"],
                "displayName": item["displayName"],
                "score": item["score"],
            }
        )

    return results


@app.get("/api/leaderboards/regional/{region}")
async def regional_leaderboard(region: str, top: int = Query(default=100, ge=1, le=100)):
    """Get regional top N leaderboard sorted by best score descending."""
    # Single-partition query using region as partition key
    query = (
        "SELECT c.playerId, c.displayName, c.score "
        "FROM c WHERE c.region = @region "
        "ORDER BY c.score DESC, c.displayName ASC "
        "OFFSET 0 LIMIT @top"
    )
    params = [{"name": "@region", "value": region}]

    results = []
    rank = 0
    async for item in leaderboard_container.query_items(
        query=query, parameters=params, partition_key=region
    ):
        rank += 1
        results.append(
            {
                "rank": rank,
                "playerId": item["playerId"],
                "displayName": item["displayName"],
                "score": item["score"],
            }
        )

    return results


@app.get("/api/players/{player_id}/rank")
async def get_player_rank(player_id: str):
    """Get a player's rank on the global leaderboard and neighboring players."""
    # Verify player exists
    try:
        player = await players_container.read_item(item=player_id, partition_key=player_id)
    except CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    if player["bestScore"] == 0 and player["totalGames"] == 0:
        raise HTTPException(status_code=404, detail="Player has no scores")

    player_score = player["bestScore"]
    player_display_name = player["displayName"]

    # Use COUNT-based rank query (efficient - ~3-5 RU)
    count_query = (
        "SELECT VALUE COUNT(1) FROM c "
        "WHERE c.region = 'GLOBAL' AND "
        "(c.score > @score OR (c.score = @score AND c.displayName < @displayName))"
    )
    count_params = [
        {"name": "@score", "value": player_score},
        {"name": "@displayName", "value": player_display_name},
    ]

    rank = 1
    async for count_result in leaderboard_container.query_items(
        query=count_query, parameters=count_params, partition_key="GLOBAL"
    ):
        rank = count_result + 1

    # Get neighbors (±10 positions) using the global leaderboard
    # Fetch enough entries around the player's rank
    offset = max(0, rank - 11)
    neighbor_query = (
        "SELECT c.playerId, c.displayName, c.score "
        "FROM c WHERE c.region = 'GLOBAL' "
        "ORDER BY c.score DESC, c.displayName ASC "
        "OFFSET @offset LIMIT 21"
    )
    neighbor_params = [{"name": "@offset", "value": offset}]

    neighbors = []
    current_rank = offset
    async for item in leaderboard_container.query_items(
        query=neighbor_query, parameters=neighbor_params, partition_key="GLOBAL"
    ):
        current_rank += 1
        if item["playerId"] != player_id:
            neighbors.append(
                {
                    "rank": current_rank,
                    "playerId": item["playerId"],
                    "displayName": item["displayName"],
                    "score": item["score"],
                }
            )

    return {
        "playerId": player_id,
        "rank": rank,
        "score": player_score,
        "neighbors": neighbors,
    }


async def _upsert_leaderboard_entry(player_id: str, display_name: str, region: str, score: int):
    """Upsert leaderboard entries for both global and regional leaderboards."""
    # Global leaderboard entry
    global_entry = {
        "id": f"global_{player_id}",
        "playerId": player_id,
        "displayName": display_name,
        "score": score,
        "region": "GLOBAL",
        "type": "leaderboardEntry",
    }
    await leaderboard_container.upsert_item(body=global_entry)

    # Regional leaderboard entry
    regional_entry = {
        "id": f"regional_{player_id}",
        "playerId": player_id,
        "displayName": display_name,
        "score": score,
        "region": region,
        "type": "leaderboardEntry",
    }
    await leaderboard_container.upsert_item(body=regional_entry)

