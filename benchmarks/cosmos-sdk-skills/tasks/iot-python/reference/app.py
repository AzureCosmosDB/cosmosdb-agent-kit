"""SensorGrid — IoT telemetry service (Python reference implementation).

FastAPI on asyncio with the **async** Cosmos client
(`azure.cosmos.aio.CosmosClient`), a single client constructed once at
import and reused for every request.

Data model:
  * devices  — partition key /id.
  * readings — partition key /deviceId, co-locating every reading for a
               device in one logical partition. This keeps the dominant
               access pattern — "readings for device D over a time range" —
               a single-partition query, which is essential for a
               write-heavy telemetry store. Timestamps are ISO-8601 Zulu
               strings, which sort lexicographically, so range filters use
               plain string comparison.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List

from azure.cosmos import PartitionKey, exceptions
from azure.cosmos.aio import CosmosClient
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

# ----- Configuration -------------------------------------------------------

COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
COSMOS_DATABASE = os.environ.get("COSMOS_DATABASE", "sensorgrid")
COSMOS_DEVICES_CONTAINER = os.environ.get("COSMOS_DEVICES_CONTAINER", "devices")
COSMOS_READINGS_CONTAINER = os.environ.get("COSMOS_READINGS_CONTAINER", "readings")

PREFERRED_REGIONS = [
    r.strip() for r in os.environ.get(
        "COSMOS_PREFERRED_REGIONS", "West US 2,East US 2"
    ).split(",") if r.strip()
]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sensorgrid")

# ----- Singleton async CosmosClient ---------------------------------------

_client: CosmosClient = CosmosClient(
    COSMOS_ENDPOINT,
    credential=COSMOS_KEY,
    preferred_locations=PREFERRED_REGIONS,
    connection_verify=False,  # emulator self-signed cert
    retry_total=9,
    retry_backoff_max=30,
)

_devices = None  # type: ignore[assignment]
_readings = None  # type: ignore[assignment]


@asynccontextmanager
async def _lifespan(app: FastAPI):
    global _devices, _readings
    database = await _client.create_database_if_not_exists(
        id=COSMOS_DATABASE,
        offer_throughput=400,
    )
    _devices = await database.create_container_if_not_exists(
        id=COSMOS_DEVICES_CONTAINER,
        partition_key=PartitionKey(path="/id"),
        indexing_policy={
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [{"path": "/*"}],
            "excludedPaths": [{"path": "/\"_etag\"/?"}],
            "compositeIndexes": [
                [
                    {"path": "/type", "order": "ascending"},
                    {"path": "/location", "order": "ascending"},
                ]
            ],
        },
    )
    _readings = await database.create_container_if_not_exists(
        id=COSMOS_READINGS_CONTAINER,
        partition_key=PartitionKey(path="/deviceId"),
        indexing_policy={
            "indexingMode": "consistent",
            "automatic": True,
            "includedPaths": [{"path": "/*"}],
            "excludedPaths": [{"path": "/\"_etag\"/?"}],
            "compositeIndexes": [
                [
                    {"path": "/deviceId", "order": "ascending"},
                    {"path": "/timestamp", "order": "ascending"},
                ]
            ],
        },
    )
    try:
        yield
    finally:
        await _client.close()


# ----- Models --------------------------------------------------------------

class DeviceIn(BaseModel):
    id: str
    name: str = Field(min_length=1)
    location: str = Field(min_length=1)
    type: str = Field(min_length=1)


class ReadingIn(BaseModel):
    id: str
    deviceId: str = Field(min_length=1)
    timestamp: str = Field(min_length=1)
    value: float
    unit: str = Field(min_length=1)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _device_doc(d: DeviceIn) -> dict:
    return {
        "id": d.id,
        "name": d.name,
        "location": d.location,
        "type": d.type,
        "createdAt": _now_iso(),
        "entityType": "device",
        "schemaVersion": 1,
    }


def _device_out(doc: dict) -> dict:
    return {
        "id": doc["id"],
        "name": doc["name"],
        "location": doc["location"],
        "type": doc["type"],
        "createdAt": doc["createdAt"],
        "schemaVersion": doc.get("schemaVersion", 1),
    }


def _reading_doc(r: ReadingIn) -> dict:
    return {
        "id": r.id,
        "deviceId": r.deviceId,
        "timestamp": r.timestamp,
        "value": r.value,
        "unit": r.unit,
        "type": "reading",
        "schemaVersion": 1,
    }


def _reading_out(doc: dict) -> dict:
    return {
        "id": doc["id"],
        "deviceId": doc["deviceId"],
        "timestamp": doc["timestamp"],
        "value": doc["value"],
        "unit": doc["unit"],
    }


# ----- App ----------------------------------------------------------------

app = FastAPI(title="SensorGrid", lifespan=_lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/devices", status_code=201)
async def register_device(device: DeviceIn):
    try:
        created = await _devices.create_item(body=_device_doc(device))
    except exceptions.CosmosResourceExistsError:
        raise HTTPException(status_code=409, detail=f"device {device.id} already exists")
    return _device_out(created)


@app.post("/readings", status_code=201)
async def ingest_reading(reading: ReadingIn):
    created = await _readings.upsert_item(body=_reading_doc(reading))
    return _reading_out(created)


@app.get("/devices/{device_id}/readings")
async def readings_in_range(
    device_id: str,
    start: str = Query(..., min_length=1),
    end: str = Query(..., min_length=1),
):
    out: List[dict] = []
    async for d in _readings.query_items(
        query=(
            "SELECT * FROM c WHERE c.deviceId = @d "
            "AND c.timestamp >= @s AND c.timestamp <= @e"
        ),
        parameters=[
            {"name": "@d", "value": device_id},
            {"name": "@s", "value": start},
            {"name": "@e", "value": end},
        ],
        partition_key=device_id,
        logging_enable=True,
    ):
        out.append(_reading_out(d))
    return out


@app.get("/devices/{device_id}/summary")
async def device_summary(device_id: str):
    values: List[float] = []
    async for d in _readings.query_items(
        query="SELECT * FROM c WHERE c.deviceId = @d",
        parameters=[{"name": "@d", "value": device_id}],
        partition_key=device_id,
        logging_enable=True,
    ):
        values.append(float(d["value"]))
    count = len(values)
    return {
        "deviceId": device_id,
        "count": count,
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "avg": (sum(values) / count) if count else None,
    }
