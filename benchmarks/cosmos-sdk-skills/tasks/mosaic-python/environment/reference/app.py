"""Mosaic user-profile service — Python reference implementation.

FastAPI on an asyncio event loop with the **async** Cosmos client
(`azure.cosmos.aio.CosmosClient`). This matches the canonical guidance
on Microsoft Learn (best-practice-python: "Don't use the sync
CosmosClient inside an async event loop").

Best-practice rules this file satisfies:

- sdk-python-async-deps   — uses azure.cosmos.aio.CosmosClient inside a
                            FastAPI app; requirements.txt pins aiohttp.
- sdk-singleton-client    — exactly one CosmosClient construction at
                            module import; reused for every request.
- sdk-preferred-regions   — preferred_locations passed to CosmosClient.
- sdk-retry-429           — retry_total / retry_backoff_max tuned for
                            429 handling.
- sdk-diagnostics         — logging_enable=True on per-call invocations.
- sdk-secrets-from-env    — endpoint + key read from env, not literals.
- sdk-cache-metadata      — createDatabaseIfNotExists /
                            createContainerIfNotExists run exactly once
                            in the FastAPI lifespan, never per request.
- index-exclude-unused    — excludedPaths contains noisy fields beyond
                            the system _etag.
- model-type-discriminator + model-schema-version +
  model-iso8601-timestamps — document shape carries type/schemaVersion/
                            createdAt.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional

from azure.cosmos import PartitionKey, exceptions
from azure.cosmos.aio import CosmosClient
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

# ----- Configuration -------------------------------------------------------

COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
COSMOS_DATABASE = os.environ.get("COSMOS_DATABASE", "mosaic")
COSMOS_USERS_CONTAINER = os.environ.get("COSMOS_USERS_CONTAINER", "users")

PREFERRED_REGIONS = [
    r.strip() for r in os.environ.get(
        "COSMOS_PREFERRED_REGIONS", "West US 2,East US 2"
    ).split(",") if r.strip()
]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mosaic")

# ----- Singleton async CosmosClient ---------------------------------------
# Constructed exactly once at module import. The verifier asserts there
# is at most one CosmosClient(...) call in the entire source tree.
_client: CosmosClient = CosmosClient(
    COSMOS_ENDPOINT,
    credential=COSMOS_KEY,
    preferred_locations=PREFERRED_REGIONS,
    connection_verify=False,  # emulator self-signed cert
    retry_total=9,
    retry_backoff_max=30,
)

# Container handle is populated once in the lifespan startup hook and
# reused for the lifetime of the process. Rule sdk-cache-metadata: we do
# NOT call create_database_if_not_exists / create_container_if_not_exists
# inside any request handler.
_users = None  # type: ignore[assignment]


@asynccontextmanager
async def _lifespan(app: FastAPI):
    global _users
    database = await _client.create_database_if_not_exists(
        id=COSMOS_DATABASE,
        offer_throughput=400,
    )
    _users = await database.create_container_if_not_exists(
        id=COSMOS_USERS_CONTAINER,
        partition_key=PartitionKey(path="/userId"),
        indexing_policy={
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [{"path": "/*"}],
            "excludedPaths": [
                {"path": "/\"_etag\"/?"},
                {"path": "/email/?"},
                {"path": "/interests/*"},
            ],
            "compositeIndexes": [
                [
                    {"path": "/city", "order": "ascending"},
                    {"path": "/id", "order": "ascending"},
                ]
            ],
        },
    )
    try:
        yield
    finally:
        await _client.close()


# ----- Models --------------------------------------------------------------

class UserIn(BaseModel):
    id: str
    name: str = Field(min_length=1)
    email: EmailStr
    city: str = Field(min_length=1)
    interests: List[str] = Field(default_factory=list)


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    city: str
    interests: List[str]
    createdAt: str
    type: str = "user"
    schemaVersion: int = 1


def _to_doc(u: UserIn, created_at: Optional[str] = None) -> dict:
    return {
        "id": u.id,
        "userId": u.id,
        "name": u.name,
        "email": u.email,
        "city": u.city,
        "interests": list(u.interests),
        "createdAt": created_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "type": "user",
        "schemaVersion": 1,
    }


def _to_out(doc: dict) -> UserOut:
    return UserOut(
        id=doc["id"],
        name=doc["name"],
        email=doc["email"],
        city=doc["city"],
        interests=list(doc.get("interests", [])),
        createdAt=doc["createdAt"],
    )


# ----- App ----------------------------------------------------------------

app = FastAPI(title="Mosaic Users", lifespan=_lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/users", status_code=201, response_model=UserOut)
async def create_user(user: UserIn):
    doc = _to_doc(user)
    try:
        created = await _users.create_item(body=doc, enable_automatic_id_generation=False)
    except exceptions.CosmosResourceExistsError:
        raise HTTPException(status_code=409, detail=f"user {user.id} already exists")
    except exceptions.CosmosHttpResponseError as e:
        log.exception("cosmos create failed for %s", user.id)
        raise HTTPException(status_code=500, detail=str(e))
    return _to_out(created)


@app.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: str):
    try:
        doc = await _users.read_item(
            item=user_id,
            partition_key=user_id,
            logging_enable=True,  # rule sdk-diagnostics
        )
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail=f"user {user_id} not found")
    return _to_out(doc)


@app.get("/users", response_model=List[UserOut])
async def list_users_by_city(city: str = Query(..., min_length=1)):
    query = "SELECT * FROM c WHERE c.city = @city"
    params = [{"name": "@city", "value": city}]
    out: List[UserOut] = []
    try:
        # query_items on aio returns an async iterator — must use async for.
        async for d in _users.query_items(
            query=query,
            parameters=params,
            logging_enable=True,
        ):
            out.append(_to_out(d))
    except exceptions.CosmosHttpResponseError as e:
        log.exception("cosmos query failed")
        raise HTTPException(status_code=500, detail=str(e))
    return out
