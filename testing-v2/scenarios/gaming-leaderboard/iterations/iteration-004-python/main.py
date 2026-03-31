"""Gaming Leaderboard API - FastAPI with Azure Cosmos DB.

Implements the gaming-leaderboard API contract with Cosmos DB best practices:
- Async SDK with singleton CosmosClient
- Materialized view pattern for leaderboards (Change Feed concept)
- Count-based ranking for efficient rank lookups
- Denormalized player stats for read-heavy workloads
- Composite indexes for multi-property ORDER BY
- Point reads for known ID + partition key lookups
- Parameterized queries to prevent injection
- Excluded unused index paths to reduce write RU cost
"""

import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from azure.cosmos import PartitionKey, exceptions
from azure.cosmos.aio import CosmosClient
from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel

# Configuration from environment variables (never hardcoded)
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT", "https://localhost:8081")
COSMOS_KEY = os.environ.get("COSMOS_KEY")
DATABASE_NAME = "gaming-leaderboard"

# Cosmos DB references (singleton pattern - rule 4.18)
cosmos_client: Optional[CosmosClient] = None
database = None
players_container = None
scores_container = None
leaderboards_container = None


async def init_cosmos():
    """Initialize Cosmos DB client singleton and create database/containers."""
    global cosmos_client, database
    global players_container, scores_container, leaderboards_container

    cosmos_client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
    database = await cosmos_client.create_database_if_not_exists(id=DATABASE_NAME)

    # Players container - partition key: /playerId (high cardinality, immutable)
    players_container = await database.create_container_if_not_exists(
        id="players",
        partition_key=PartitionKey(path="/playerId"),
        indexing_policy={
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [
                {"path": "/playerId/?"},
                {"path": "/displayName/?"},
                {"path": "/region/?"},
            ],
            "excludedPaths": [{"path": "/*"}],
        },
    )

    # Scores container - partition key: /playerId (aligned with query patterns)
    scores_container = await database.create_container_if_not_exists(
        id="scores",
        partition_key=PartitionKey(path="/playerId"),
        indexing_policy={
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [
                {"path": "/playerId/?"},
                {"path": "/timestamp/?"},
            ],
            "excludedPaths": [{"path": "/*"}],
        },
    )

    # Leaderboards container - materialized view (rule 9.1)
    # Partition key: /region enables single-partition queries for both
    # regional and global (region="global") leaderboards
    # Composite indexes match ORDER BY directions (rules 5.1, 5.2)
    leaderboards_container = await database.create_container_if_not_exists(
        id="leaderboards",
        partition_key=PartitionKey(path="/region"),
        indexing_policy={
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [
                {"path": "/score/?"},
                {"path": "/displayName/?"},
                {"path": "/playerId/?"},
            ],
            "excludedPaths": [{"path": "/*"}],
            "compositeIndexes": [
                [
                    {"path": "/score", "order": "descending"},
                    {"path": "/displayName", "order": "ascending"},
                ],
                [
                    {"path": "/score", "order": "ascending"},
                    {"path": "/displayName", "order": "descending"},
                ],
            ],
        },
    )


async def close_cosmos():
    """Close Cosmos DB client on shutdown."""
    global cosmos_client
    if cosmos_client:
        await cosmos_client.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: init Cosmos on startup, close on shutdown."""
    await init_cosmos()
    yield
    await close_cosmos()


app = FastAPI(title="Gaming Leaderboard API", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Pydantic request models
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
# Response formatting helpers (project only needed fields - rule 3.9)
# ---------------------------------------------------------------------------


def _format_player(player: dict) -> dict:
    return {
        "playerId": player["playerId"],
        "displayName": player["displayName"],
        "region": player["region"],
        "totalGames": player.get("totalGames", 0),
        "bestScore": player.get("bestScore", 0),
        "averageScore": player.get("averageScore", 0),
    }


def _format_score(score: dict) -> dict:
    result = {
        "scoreId": score["scoreId"],
        "playerId": score["playerId"],
        "score": score["score"],
        "timestamp": score["timestamp"],
    }
    if score.get("gameMode") is not None:
        result["gameMode"] = score["gameMode"]
    return result


def _format_leaderboard_entry(entry: dict, rank: int) -> dict:
    return {
        "rank": rank,
        "playerId": entry["playerId"],
        "displayName": entry["displayName"],
        "score": entry["score"],
    }


# ---------------------------------------------------------------------------
# Leaderboard materialized-view helpers
# ---------------------------------------------------------------------------


async def _upsert_leaderboard_entries(player: dict, old_region: Optional[str] = None):
    """Upsert leaderboard entries for both global and regional partitions.

    When a player's region changes, the old regional entry is deleted.
    Uses absolute values (not deltas) for idempotent upserts (rule 9.1).
    """
    pid = player["playerId"]
    display_name = player["displayName"]
    region = player["region"]
    score = player.get("bestScore", 0)

    base = {
        "id": pid,
        "playerId": pid,
        "displayName": display_name,
        "score": score,
        "type": "leaderboardEntry",
        "schemaVersion": 1,
    }

    # Global entry
    await leaderboards_container.upsert_item(body={**base, "region": "global"})

    # If region changed, remove stale regional entry
    if old_region is not None and old_region != region:
        try:
            await leaderboards_container.delete_item(item=pid, partition_key=old_region)
        except exceptions.CosmosResourceNotFoundError:
            pass

    # Current regional entry
    await leaderboards_container.upsert_item(body={**base, "region": region})


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# Player Management
# ---------------------------------------------------------------------------


@app.post("/api/players", status_code=201)
async def create_player(req: CreatePlayerRequest):
    """Create a new player profile with zeroed stats."""
    player_doc = {
        "id": req.playerId,
        "playerId": req.playerId,
        "displayName": req.displayName,
        "region": req.region,
        "totalGames": 0,
        "bestScore": 0,
        "averageScore": 0,
        "type": "player",
        "schemaVersion": 1,
    }
    try:
        await players_container.create_item(body=player_doc)
    except exceptions.CosmosResourceExistsError:
        raise HTTPException(status_code=409, detail="Player already exists")
    return _format_player(player_doc)


@app.get("/api/players/{player_id}")
async def get_player(player_id: str):
    """Get player profile — point read (1 RU, rule 3.7)."""
    try:
        player = await players_container.read_item(
            item=player_id, partition_key=player_id
        )
        return _format_player(player)
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")


@app.patch("/api/players/{player_id}")
async def update_player(player_id: str, req: UpdatePlayerRequest):
    """Update player profile fields (displayName and/or region)."""
    try:
        player = await players_container.read_item(
            item=player_id, partition_key=player_id
        )
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    old_region = player["region"]
    if req.displayName is not None:
        player["displayName"] = req.displayName
    if req.region is not None:
        player["region"] = req.region

    await players_container.replace_item(item=player_id, body=player)

    # Propagate changes to leaderboard materialized view
    if player.get("bestScore", 0) > 0:
        region_changed = req.region is not None and req.region != old_region
        await _upsert_leaderboard_entries(
            player, old_region=old_region if region_changed else None
        )

    return _format_player(player)


@app.delete("/api/players/{player_id}", status_code=204)
async def delete_player(player_id: str):
    """Delete a player and all associated score + leaderboard data."""
    try:
        player = await players_container.read_item(
            item=player_id, partition_key=player_id
        )
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    region = player["region"]

    # Delete all scores (single-partition query, rule 3.1)
    query = "SELECT c.id FROM c WHERE c.playerId = @pid"
    params = [{"name": "@pid", "value": player_id}]
    score_ids = []
    async for item in scores_container.query_items(
        query=query, parameters=params, partition_key=player_id
    ):
        score_ids.append(item["id"])
    for sid in score_ids:
        await scores_container.delete_item(item=sid, partition_key=player_id)

    # Delete leaderboard entries (global + regional)
    for pk in ("global", region):
        try:
            await leaderboards_container.delete_item(item=player_id, partition_key=pk)
        except exceptions.CosmosResourceNotFoundError:
            pass

    # Delete player document
    await players_container.delete_item(item=player_id, partition_key=player_id)
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Score Submission
# ---------------------------------------------------------------------------


@app.post("/api/scores", status_code=201)
async def submit_score(req: SubmitScoreRequest):
    """Submit a game score and update denormalized player stats (rule 1.2)."""
    # Verify player exists — point read
    try:
        player = await players_container.read_item(
            item=req.playerId, partition_key=req.playerId
        )
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    # Create score document
    score_id = uuid.uuid4().hex
    timestamp = datetime.now(timezone.utc).isoformat()
    score_doc = {
        "id": score_id,
        "scoreId": score_id,
        "playerId": req.playerId,
        "score": req.score,
        "timestamp": timestamp,
        "type": "score",
        "schemaVersion": 1,
    }
    if req.gameMode is not None:
        score_doc["gameMode"] = req.gameMode

    await scores_container.create_item(body=score_doc)

    # Update denormalized aggregates on the player document
    old_total = player.get("totalGames", 0)
    old_best = player.get("bestScore", 0)
    old_avg = player.get("averageScore", 0)

    new_total = old_total + 1
    new_best = max(old_best, req.score)
    new_avg = ((old_avg * old_total) + req.score) / new_total

    player["totalGames"] = new_total
    player["bestScore"] = new_best
    player["averageScore"] = new_avg

    await players_container.replace_item(item=req.playerId, body=player)

    # Propagate to leaderboard materialized view when best score improves
    if new_best > old_best:
        await _upsert_leaderboard_entries(player)

    return {"scoreId": score_id, "playerId": req.playerId, "score": req.score}


# ---------------------------------------------------------------------------
# Score History
# ---------------------------------------------------------------------------


@app.get("/api/players/{player_id}/scores")
async def get_player_scores(
    player_id: str, limit: int = Query(default=10, ge=1, le=100)
):
    """Player score history, most recent first (single-partition query)."""
    # Verify player exists
    try:
        await players_container.read_item(item=player_id, partition_key=player_id)
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    # Literal integer for TOP (rule 3.8), project only needed fields (rule 3.9)
    query = (
        f"SELECT TOP {int(limit)} c.scoreId, c.playerId, c.score, "
        f"c.gameMode, c.timestamp FROM c ORDER BY c.timestamp DESC"
    )
    scores = []
    async for item in scores_container.query_items(
        query=query, partition_key=player_id
    ):
        scores.append(_format_score(item))
    return scores


# ---------------------------------------------------------------------------
# Leaderboards
# ---------------------------------------------------------------------------


@app.get("/api/leaderboards/global")
async def get_global_leaderboard(top: int = Query(default=100, ge=1, le=100)):
    """Global top-N leaderboard — single-partition query on region='global'."""
    # Literal TOP integer (rule 3.8); composite index matches ORDER BY (rule 5.1)
    query = (
        f"SELECT TOP {int(top)} c.playerId, c.displayName, c.score "
        f"FROM c ORDER BY c.score DESC, c.displayName ASC"
    )
    entries = []
    rank = 1
    async for item in leaderboards_container.query_items(
        query=query, partition_key="global"
    ):
        entries.append(_format_leaderboard_entry(item, rank))
        rank += 1
    return entries


@app.get("/api/leaderboards/regional/{region}")
async def get_regional_leaderboard(
    region: str, top: int = Query(default=100, ge=1, le=100)
):
    """Regional top-N leaderboard — single-partition query on region."""
    query = (
        f"SELECT TOP {int(top)} c.playerId, c.displayName, c.score "
        f"FROM c ORDER BY c.score DESC, c.displayName ASC"
    )
    entries = []
    rank = 1
    async for item in leaderboards_container.query_items(
        query=query, partition_key=region
    ):
        entries.append(_format_leaderboard_entry(item, rank))
        rank += 1
    return entries


# ---------------------------------------------------------------------------
# Player Ranking
# ---------------------------------------------------------------------------


@app.get("/api/players/{player_id}/rank")
async def get_player_rank(player_id: str):
    """Player rank via count-based ranking (rule 9.2) + ±10 neighbors."""
    # Point read for player
    try:
        player = await players_container.read_item(
            item=player_id, partition_key=player_id
        )
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Player not found")

    best_score = player.get("bestScore", 0)
    display_name = player["displayName"]

    if best_score == 0:
        raise HTTPException(status_code=404, detail="Player has no scores")

    # Count-based rank: count players with strictly better position (rule 9.2)
    rank_query = (
        "SELECT VALUE COUNT(1) FROM c WHERE "
        "c.score > @score OR (c.score = @score AND c.displayName < @name)"
    )
    rank_params = [
        {"name": "@score", "value": best_score},
        {"name": "@name", "value": display_name},
    ]
    rank = 1
    async for count in leaderboards_container.query_items(
        query=rank_query, parameters=rank_params, partition_key="global"
    ):
        rank = count + 1

    # Neighbors above (up to 10 with higher rank / better score)
    above_query = (
        "SELECT TOP 10 c.playerId, c.displayName, c.score FROM c "
        "WHERE c.score > @score OR (c.score = @score AND c.displayName < @name) "
        "ORDER BY c.score ASC, c.displayName DESC"
    )
    above = []
    async for item in leaderboards_container.query_items(
        query=above_query, parameters=rank_params, partition_key="global"
    ):
        above.append(item)
    above.reverse()  # closest-first → descending score order

    # Neighbors below (up to 10 with lower rank / worse score)
    below_query = (
        "SELECT TOP 10 c.playerId, c.displayName, c.score FROM c "
        "WHERE c.score < @score OR (c.score = @score AND c.displayName > @name) "
        "ORDER BY c.score DESC, c.displayName ASC"
    )
    below = []
    async for item in leaderboards_container.query_items(
        query=below_query, parameters=rank_params, partition_key="global"
    ):
        below.append(item)

    # Assemble neighbors list with computed ranks
    neighbors = []
    current_rank = rank - len(above)
    for entry in above:
        neighbors.append(_format_leaderboard_entry(entry, current_rank))
        current_rank += 1

    # Include the player themselves
    neighbors.append(
        {
            "rank": rank,
            "playerId": player_id,
            "displayName": display_name,
            "score": best_score,
        }
    )
    current_rank = rank + 1

    for entry in below:
        neighbors.append(_format_leaderboard_entry(entry, current_rank))
        current_rank += 1

    return {
        "playerId": player_id,
        "rank": rank,
        "score": best_score,
        "neighbors": neighbors,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
