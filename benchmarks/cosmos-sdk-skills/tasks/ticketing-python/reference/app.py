"""TicketWave — event ticketing service (Python reference implementation).

FastAPI on asyncio with the **async** Cosmos client
(`azure.cosmos.aio.CosmosClient`), a single client constructed once at
import and reused for every request.

Data model:
  * events  — partition key /id (reads are overwhelmingly by event id).
  * tickets — partition key /eventId, so every ticket for an event lives
              in one logical partition (event-scoped ticket queries stay
              single-partition). Ticket cancellation uses the document
              ETag as an optimistic-concurrency guard.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional

from azure.core import MatchConditions
from azure.cosmos import PartitionKey, exceptions
from azure.cosmos.aio import CosmosClient
from fastapi import FastAPI, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field

# ----- Configuration -------------------------------------------------------

COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
COSMOS_DATABASE = os.environ.get("COSMOS_DATABASE", "ticketwave")
COSMOS_EVENTS_CONTAINER = os.environ.get("COSMOS_EVENTS_CONTAINER", "events")
COSMOS_TICKETS_CONTAINER = os.environ.get("COSMOS_TICKETS_CONTAINER", "tickets")

PREFERRED_REGIONS = [
    r.strip() for r in os.environ.get(
        "COSMOS_PREFERRED_REGIONS", "West US 2,East US 2"
    ).split(",") if r.strip()
]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ticketwave")

# ----- Singleton async CosmosClient ---------------------------------------

_client: CosmosClient = CosmosClient(
    COSMOS_ENDPOINT,
    credential=COSMOS_KEY,
    preferred_locations=PREFERRED_REGIONS,
    connection_verify=False,  # emulator self-signed cert
    retry_total=9,
    retry_backoff_max=30,
)

_events = None  # type: ignore[assignment]
_tickets = None  # type: ignore[assignment]


@asynccontextmanager
async def _lifespan(app: FastAPI):
    global _events, _tickets
    database = await _client.create_database_if_not_exists(
        id=COSMOS_DATABASE,
        offer_throughput=400,
    )
    _events = await database.create_container_if_not_exists(
        id=COSMOS_EVENTS_CONTAINER,
        partition_key=PartitionKey(path="/id"),
        indexing_policy={
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [{"path": "/*"}],
            "excludedPaths": [
                {"path": "/\"_etag\"/?"},
                {"path": "/description/?"},
            ],
            "compositeIndexes": [
                [
                    {"path": "/city", "order": "ascending"},
                    {"path": "/date", "order": "ascending"},
                ]
            ],
        },
    )
    _tickets = await database.create_container_if_not_exists(
        id=COSMOS_TICKETS_CONTAINER,
        partition_key=PartitionKey(path="/eventId"),
    )
    try:
        yield
    finally:
        await _client.close()


# ----- Models --------------------------------------------------------------

class EventIn(BaseModel):
    id: str
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    city: str = Field(min_length=1)
    date: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    capacity: int


class TicketIn(BaseModel):
    id: str
    userId: str = Field(min_length=1)
    purchaseDate: str = Field(min_length=1)
    status: str = Field(min_length=1)
    seatNumber: str = Field(min_length=1)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _event_doc(e: EventIn) -> dict:
    return {
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "city": e.city,
        "date": e.date,
        "venue": e.venue,
        "capacity": e.capacity,
        "createdAt": _now_iso(),
        "type": "event",
        "schemaVersion": 1,
    }


def _event_out(doc: dict) -> dict:
    return {
        "id": doc["id"],
        "title": doc["title"],
        "description": doc["description"],
        "city": doc["city"],
        "date": doc["date"],
        "venue": doc["venue"],
        "capacity": doc["capacity"],
        "createdAt": doc["createdAt"],
        "type": doc.get("type", "event"),
        "schemaVersion": doc.get("schemaVersion", 1),
    }


def _ticket_doc(event_id: str, t: TicketIn) -> dict:
    return {
        "id": t.id,
        "eventId": event_id,
        "userId": t.userId,
        "purchaseDate": t.purchaseDate,
        "status": t.status,
        "seatNumber": t.seatNumber,
        "createdAt": _now_iso(),
        "type": "ticket",
        "schemaVersion": 1,
    }


def _ticket_out(doc: dict) -> dict:
    return {
        "id": doc["id"],
        "eventId": doc["eventId"],
        "userId": doc["userId"],
        "purchaseDate": doc["purchaseDate"],
        "status": doc["status"],
        "seatNumber": doc["seatNumber"],
    }


# ----- App ----------------------------------------------------------------

app = FastAPI(title="TicketWave", lifespan=_lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/events", status_code=201)
async def create_event(event: EventIn):
    try:
        created = await _events.create_item(body=_event_doc(event))
    except exceptions.CosmosResourceExistsError:
        raise HTTPException(status_code=409, detail=f"event {event.id} already exists")
    return _event_out(created)


@app.get("/events/{event_id}")
async def get_event(event_id: str):
    try:
        doc = await _events.read_item(item=event_id, partition_key=event_id, logging_enable=True)
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail=f"event {event_id} not found")
    return _event_out(doc)


@app.get("/events")
async def list_events_by_city(city: str = Query(..., min_length=1)):
    out: List[dict] = []
    async for d in _events.query_items(
        query="SELECT * FROM c WHERE c.city = @city",
        parameters=[{"name": "@city", "value": city}],
        logging_enable=True,
    ):
        out.append(_event_out(d))
    return out


@app.post("/events/{event_id}/tickets", status_code=201)
async def buy_ticket(event_id: str, ticket: TicketIn):
    # The event must exist before tickets can be sold for it.
    try:
        await _events.read_item(item=event_id, partition_key=event_id)
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail=f"event {event_id} not found")
    try:
        created = await _tickets.create_item(body=_ticket_doc(event_id, ticket))
    except exceptions.CosmosResourceExistsError:
        raise HTTPException(status_code=409, detail=f"ticket {ticket.id} already exists")
    return _ticket_out(created)


@app.delete("/events/{event_id}/tickets/{ticket_id}", status_code=204)
async def cancel_ticket(
    event_id: str,
    ticket_id: str,
    if_match: Optional[str] = Header(default=None, alias="If-Match"),
):
    kwargs: dict = {}
    if if_match:
        kwargs["etag"] = if_match.strip('"')
        kwargs["match_condition"] = MatchConditions.IfNotModified
    try:
        await _tickets.delete_item(item=ticket_id, partition_key=event_id, **kwargs)
    except exceptions.CosmosAccessConditionFailedError:
        raise HTTPException(status_code=412, detail="etag mismatch")
    except exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=404, detail=f"ticket {ticket_id} not found")
    return Response(status_code=204)
