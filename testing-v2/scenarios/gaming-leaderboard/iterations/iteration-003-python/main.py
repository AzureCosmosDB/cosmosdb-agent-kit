"""
Gaming Leaderboard API - FastAPI application.

Implements the gaming-leaderboard API contract with Azure Cosmos DB best practices:
- Async SDK throughout (Rule 4.1)
- Singleton CosmosClient (Rule 4.18)
- Point reads where possible (Rule 3.7)
- Single-partition queries (Rule 3.1)
- Parameterized queries (Rule 3.6)
- ETags for optimistic concurrency on player stat updates (Rule 4.7)
- Denormalized leaderboard entries for read-heavy workloads (Rule 1.2)
- Composite indexes for ORDER BY (Rule 5.1)
- Projection of only needed fields (Rule 3.9)
- Literal integers for TOP (Rule 3.8)
"""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from azure.core.exceptions import ResourceNotFoundError
from azure.core import MatchConditions
from azure.cosmos.exceptions import CosmosHttpResponseError
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from cosmos_db import (
    close_client,
    get_leaderboards_container,
    get_players_container,
    get_scores_container,
    initialize_database,
)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialize Cosmos DB on startup, close on shutdown."""
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
async def create_player(body: dict):
    """Create a new player profile."""
    player_id = body.get("playerId")
    display_name = body.get("displayName")
    region = body.get("region")

    if not player_id or not display_name or not region:
        raise HTTPException(status_code=400, detail="playerId, displayName, and region are required")

    container = get_players_container()

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

    await container.create_item(body=player_doc)

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
    """Get player profile with stats. Uses point read (Rule 3.7)."""
    container = get_players_container()
    try:
        player = await container.read_item(item=player_id, partition_key=player_id)
    except (ResourceNotFoundError, CosmosHttpResponseError):
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
    """Update a player's profile fields (displayName and/or region)."""
    container = get_players_container()
    try:
        player = await container.read_item(item=player_id, partition_key=player_id)
    except (ResourceNotFoundError, CosmosHttpResponseError):
        raise HTTPException(status_code=404, detail="Player not found")

    if "displayName" in body:
        player["displayName"] = body["displayName"]
    if "region" in body:
        player["region"] = body["region"]

    updated = await container.replace_item(item=player_id, body=player)

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
    players_container = get_players_container()
    scores_container = get_scores_container()
    leaderboards_container = get_leaderboards_container()

    # Verify player exists
    try:
        await players_container.read_item(item=player_id, partition_key=player_id)
    except (ResourceNotFoundError, CosmosHttpResponseError):
        raise HTTPException(status_code=404, detail="Player not found")

    # Delete all scores for this player (single-partition query, Rule 3.1)
    query = "SELECT c.id FROM c WHERE c.playerId = @playerId"
    parameters = [{"name": "@playerId", "value": player_id}]
    score_items = scores_container.query_items(
        query=query, parameters=parameters, partition_key=player_id
    )
    async for score in score_items:
        await scores_container.delete_item(item=score["id"], partition_key=player_id)

    # Delete leaderboard entries for this player
    lb_query = "SELECT c.id, c.leaderboardKey FROM c WHERE c.playerId = @playerId"
    lb_params = [{"name": "@playerId", "value": player_id}]
    lb_items = leaderboards_container.query_items(
        query=lb_query, parameters=lb_params, enable_cross_partition_query=True
    )
    async for lb_entry in lb_items:
        await leaderboards_container.delete_item(
            item=lb_entry["id"], partition_key=lb_entry["leaderboardKey"]
        )

    # Delete the player document
    await players_container.delete_item(item=player_id, partition_key=player_id)

    return None


# ---------------------------------------------------------------------------
# Score Submission
# ---------------------------------------------------------------------------


@app.post("/api/scores", status_code=201)
async def submit_score(body: dict):
    """
    Submit a game score for a player.
    Updates player stats using ETags for optimistic concurrency (Rule 4.7).
    Upserts denormalized leaderboard entries (Rule 1.2).
    """
    player_id = body.get("playerId")
    score = body.get("score")
    game_mode = body.get("gameMode")

    if not player_id or score is None:
        raise HTTPException(status_code=400, detail="playerId and score are required")

    players_container = get_players_container()
    scores_container = get_scores_container()
    leaderboards_container = get_leaderboards_container()

    # Verify player exists
    try:
        player = await players_container.read_item(item=player_id, partition_key=player_id)
    except (ResourceNotFoundError, CosmosHttpResponseError):
        raise HTTPException(status_code=404, detail="Player not found")

    # Create score document
    score_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    score_doc = {
        "id": score_id,
        "scoreId": score_id,
        "playerId": player_id,
        "score": score,
        "timestamp": now,
        "type": "score",
    }
    if game_mode is not None:
        score_doc["gameMode"] = game_mode

    await scores_container.create_item(body=score_doc)

    # Update player stats with ETag-based optimistic concurrency (Rule 4.7)
    max_retries = 5
    for attempt in range(max_retries):
        try:
            etag = player.get("_etag")
            total_games = player.get("totalGames", 0) + 1
            best_score = max(player.get("bestScore", 0), score)
            # Compute running average
            prev_total = player.get("totalGames", 0)
            prev_avg = player.get("averageScore", 0.0)
            total_score_sum = prev_avg * prev_total + score
            average_score = total_score_sum / total_games if total_games > 0 else 0.0

            player["totalGames"] = total_games
            player["bestScore"] = best_score
            player["averageScore"] = round(average_score, 2)

            await players_container.replace_item(
                item=player_id,
                body=player,
                etag=etag,
                match_condition=MatchConditions.IfNotModified,
            )
            break
        except CosmosHttpResponseError as e:
            if e.status_code == 412 and attempt < max_retries - 1:
                # Re-read and retry (Rule 4.7)
                player = await players_container.read_item(
                    item=player_id, partition_key=player_id
                )
            else:
                raise

    # Upsert leaderboard entries (denormalized, Rule 1.2)
    # Global leaderboard entry
    global_lb_key = "global"
    global_entry_id = f"global_{player_id}"
    await _upsert_leaderboard_entry(
        leaderboards_container,
        entry_id=global_entry_id,
        leaderboard_key=global_lb_key,
        player_id=player_id,
        display_name=player["displayName"],
        best_score=player["bestScore"],
    )

    # Regional leaderboard entry
    region = player.get("region", "")
    if region:
        regional_lb_key = f"region_{region}"
        regional_entry_id = f"region_{region}_{player_id}"
        await _upsert_leaderboard_entry(
            leaderboards_container,
            entry_id=regional_entry_id,
            leaderboard_key=regional_lb_key,
            player_id=player_id,
            display_name=player["displayName"],
            best_score=player["bestScore"],
        )

    return {
        "scoreId": score_id,
        "playerId": player_id,
        "score": score,
    }


async def _upsert_leaderboard_entry(
    container,
    entry_id: str,
    leaderboard_key: str,
    player_id: str,
    display_name: str,
    best_score: int,
):
    """Upsert a denormalized leaderboard entry."""
    entry = {
        "id": entry_id,
        "leaderboardKey": leaderboard_key,
        "playerId": player_id,
        "displayName": display_name,
        "score": best_score,
        "type": "leaderboard_entry",
    }
    await container.upsert_item(body=entry)


# ---------------------------------------------------------------------------
# Leaderboards
# ---------------------------------------------------------------------------


@app.get("/api/leaderboards/global")
async def global_leaderboard(top: int = Query(default=100, ge=1, le=100)):
    """
    Get global top N leaderboard.
    Uses composite index on (score DESC, displayName ASC) (Rule 5.1).
    Literal integer for TOP (Rule 3.8).
    """
    container = get_leaderboards_container()

    # Rule 3.8: Use literal integer for TOP, not a parameter
    safe_top = int(top)
    query = (
        f"SELECT TOP {safe_top} c.playerId, c.displayName, c.score "
        f"FROM c WHERE c.leaderboardKey = @lbKey "
        f"ORDER BY c.score DESC, c.displayName ASC"
    )
    parameters = [{"name": "@lbKey", "value": "global"}]

    items = container.query_items(
        query=query, parameters=parameters, partition_key="global"
    )

    results = []
    rank = 1
    async for item in items:
        results.append({
            "rank": rank,
            "playerId": item["playerId"],
            "displayName": item["displayName"],
            "score": item["score"],
        })
        rank += 1

    return results


@app.get("/api/leaderboards/regional/{region}")
async def regional_leaderboard(region: str, top: int = Query(default=100, ge=1, le=100)):
    """
    Get regional top N leaderboard.
    Single-partition query on leaderboardKey (Rule 3.1).
    """
    container = get_leaderboards_container()
    lb_key = f"region_{region}"

    safe_top = int(top)
    query = (
        f"SELECT TOP {safe_top} c.playerId, c.displayName, c.score "
        f"FROM c WHERE c.leaderboardKey = @lbKey "
        f"ORDER BY c.score DESC, c.displayName ASC"
    )
    parameters = [{"name": "@lbKey", "value": lb_key}]

    items = container.query_items(
        query=query, parameters=parameters, partition_key=lb_key
    )

    results = []
    rank = 1
    async for item in items:
        results.append({
            "rank": rank,
            "playerId": item["playerId"],
            "displayName": item["displayName"],
            "score": item["score"],
        })
        rank += 1

    return results


# ---------------------------------------------------------------------------
# Player Ranking
# ---------------------------------------------------------------------------


@app.get("/api/players/{player_id}/rank")
async def player_rank(player_id: str):
    """
    Get a player's rank and surrounding ±10 neighbors.
    Uses COUNT-based ranking for efficiency.
    """
    container = get_leaderboards_container()

    # Get player's leaderboard entry via point read (Rule 3.7)
    entry_id = f"global_{player_id}"
    try:
        player_entry = await container.read_item(
            item=entry_id, partition_key="global"
        )
    except (ResourceNotFoundError, CosmosHttpResponseError):
        raise HTTPException(status_code=404, detail="Player not found or has no scores")

    player_score = player_entry["score"]
    player_display_name = player_entry["displayName"]

    # Count players with higher score, or same score but earlier displayName (Rule 3.6)
    count_query = (
        "SELECT VALUE COUNT(1) FROM c "
        "WHERE c.leaderboardKey = @lbKey AND ("
        "  c.score > @score OR "
        "  (c.score = @score AND c.displayName < @displayName)"
        ")"
    )
    count_params = [
        {"name": "@lbKey", "value": "global"},
        {"name": "@score", "value": player_score},
        {"name": "@displayName", "value": player_display_name},
    ]

    count_items = container.query_items(
        query=count_query, parameters=count_params, partition_key="global"
    )
    count = 0
    async for c in count_items:
        count = c

    player_rank_value = count + 1

    # Get neighbors: fetch a window of players around this player's score
    # Get players ranked above (higher score or same score + earlier name)
    above_query = (
        "SELECT TOP 10 c.playerId, c.displayName, c.score "
        "FROM c WHERE c.leaderboardKey = @lbKey AND ("
        "  c.score > @score OR "
        "  (c.score = @score AND c.displayName < @displayName)"
        ") ORDER BY c.score ASC, c.displayName DESC"
    )
    above_params = [
        {"name": "@lbKey", "value": "global"},
        {"name": "@score", "value": player_score},
        {"name": "@displayName", "value": player_display_name},
    ]
    above_items = container.query_items(
        query=above_query, parameters=above_params, partition_key="global"
    )
    above_list = []
    async for item in above_items:
        above_list.append(item)
    above_list.reverse()  # Now sorted by rank ascending (highest score first)

    # Get players ranked below (lower score or same score + later name)
    below_query = (
        "SELECT TOP 10 c.playerId, c.displayName, c.score "
        "FROM c WHERE c.leaderboardKey = @lbKey AND ("
        "  c.score < @score OR "
        "  (c.score = @score AND c.displayName > @displayName)"
        ") ORDER BY c.score DESC, c.displayName ASC"
    )
    below_params = [
        {"name": "@lbKey", "value": "global"},
        {"name": "@score", "value": player_score},
        {"name": "@displayName", "value": player_display_name},
    ]
    below_items = container.query_items(
        query=below_query, parameters=below_params, partition_key="global"
    )
    below_list = []
    async for item in below_items:
        below_list.append(item)

    # Build neighbors list with ranks
    neighbors = []
    for i, entry in enumerate(above_list):
        neighbors.append({
            "rank": player_rank_value - len(above_list) + i,
            "playerId": entry["playerId"],
            "displayName": entry["displayName"],
            "score": entry["score"],
        })

    # Add the player themselves
    neighbors.append({
        "rank": player_rank_value,
        "playerId": player_id,
        "displayName": player_display_name,
        "score": player_score,
    })

    for i, entry in enumerate(below_list):
        neighbors.append({
            "rank": player_rank_value + 1 + i,
            "playerId": entry["playerId"],
            "displayName": entry["displayName"],
            "score": entry["score"],
        })

    return {
        "playerId": player_id,
        "rank": player_rank_value,
        "score": player_score,
        "neighbors": neighbors,
    }


# ---------------------------------------------------------------------------
# Score History
# ---------------------------------------------------------------------------


@app.get("/api/players/{player_id}/scores")
async def get_player_scores(player_id: str, limit: int = Query(default=10, ge=1, le=100)):
    """
    Get a player's score history ordered by most recent first.
    Single-partition query (Rule 3.1).
    """
    # Verify player exists
    players_container = get_players_container()
    try:
        await players_container.read_item(item=player_id, partition_key=player_id)
    except (ResourceNotFoundError, CosmosHttpResponseError):
        raise HTTPException(status_code=404, detail="Player not found")

    scores_container = get_scores_container()

    # Rule 3.8: literal integer for TOP
    safe_limit = int(limit)
    query = (
        f"SELECT TOP {safe_limit} c.scoreId, c.playerId, c.score, "
        f"c.gameMode, c.timestamp "
        f"FROM c WHERE c.playerId = @playerId "
        f"ORDER BY c.timestamp DESC"
    )
    parameters = [{"name": "@playerId", "value": player_id}]

    items = scores_container.query_items(
        query=query, parameters=parameters, partition_key=player_id
    )

    results = []
    async for item in items:
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
