# SensorGrid — IoT Telemetry Dashboard (Python)

You are building **SensorGrid**, an industrial IoT monitoring platform.
The service is backed by **Azure Cosmos DB for NoSQL**, and the
**Cosmos DB emulator** is already running inside this container at the
standard endpoint.

You can find the emulator endpoint and key in your environment:

```
COSMOS_ENDPOINT  = http://localhost:8081
COSMOS_KEY       = <well-known emulator key, already set>
COSMOS_DATABASE  = sensorgrid
COSMOS_DEVICES_CONTAINER = devices
COSMOS_READINGS_CONTAINER = readings
```

Your code **must** read those values from the environment, not from
hardcoded literals.

## What you are building

A Python HTTP service (FastAPI + uvicorn) exposing five endpoints. The
service must use **Azure Cosmos DB for NoSQL** (no SQLite, no
in-memory dict) to store devices and readings, and reads/writes must go
through the official Cosmos Python SDK.

### API contract

| Method | Path                                      | Purpose                          | Success status |
|--------|-------------------------------------------|----------------------------------|----------------|
| GET    | `/health`                                 | Liveness probe                   | `200` with `{"status": "ok"}` |
| POST   | `/devices`                                | Register a device                | `201` (or `409` if id exists) |
| POST   | `/readings`                               | Ingest a sensor reading          | `201` |
| GET    | `/devices/{id}/readings?start=<iso>&end=<iso>` | Get readings in a time range | `200` with a JSON array |
| GET    | `/devices/{id}/summary`                   | Get device stats                 | `200` |

`POST /devices` accepts JSON with these fields:

```json
{
  "id": "dev-100",
  "name": "Boiler Room Sensor",
  "location": "Plant A / Boiler Room",
  "type": "temperature"
}
```

All three input fields (`name`, `location`, `type`) are required.
`type` is one of `temperature`, `humidity`, or `pressure`. `POST` with
an already-used device `id` should return `409`.

`POST /readings` accepts JSON with these fields:

```json
{
  "id": "r-9001",
  "deviceId": "dev-100",
  "timestamp": "2026-09-01T12:00:00Z",
  "value": 72.4,
  "unit": "C"
}
```

All four input fields (`deviceId`, `timestamp`, `value`, `unit`) are
required.

### Scale to keep in mind

You don't have to handle the scale, just **model** for it: SensorGrid
expects ~50K devices, ~500M readings, an extremely write-heavy workload
(~10:1 write/read), and most queries are by device plus time range.

## Build and run conventions (verifier contract)

The verifier in this container is language-agnostic. It expects:

1. Your final source code lives under `/app/`.
2. You produce **`/app/build.sh`** — a one-shot setup script the
   verifier will run first. For Python this typically does
   `pip install -r requirements.txt` (or `pip install` of your
   `pyproject.toml`).
3. You produce **`/app/run.sh`** — a foreground process that starts the
   HTTP server and listens on port `$APP_PORT` (defaults to `9080`).
   The verifier waits up to 90 seconds for `GET http://localhost:$APP_PORT/health`
   to return `200`. The server must stay in the foreground (no
   `nohup`, no `&`).

Both scripts will be `chmod +x`'d by the verifier if needed.

## How you will be graded

A pytest-based verifier runs after your service is up. It checks:

- **API conformance** — all five endpoints behave per the contract
  above, with the right status codes and payload shapes.
- **Cosmos data shape** — partition key choice, indexing policy,
  throughput, document fields (`type` discriminator, `schemaVersion`,
  `createdAt` as an ISO-8601 string, and device / reading fields that
  match the contract above).
- **Cosmos SDK best practices** — your loaded skill set covers these
  for Python. The grader will look at your source code (with comments
  stripped) for the relevant patterns.
- **Skills compliance** — no hardcoded account keys, endpoint loaded
  from env, no deprecated package usage.

The grader writes a binary reward (`1` if everything passes, `0`
otherwise) to `/logs/verifier/reward.txt`. Per-category logs land in
the same directory.
