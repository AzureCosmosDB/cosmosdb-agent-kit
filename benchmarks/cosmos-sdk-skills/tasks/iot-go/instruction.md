# SensorGrid — IoT Telemetry Dashboard (Go)

You are building **SensorGrid**, an industrial IoT monitoring platform.
The service is backed by **Azure Cosmos DB for NoSQL**, and the
**Cosmos DB emulator** is already running inside this container at the
standard endpoint.

Environment variables already set for you:

```
COSMOS_ENDPOINT  = http://localhost:8081
COSMOS_KEY       = <well-known emulator key>
COSMOS_DATABASE  = sensorgrid
COSMOS_DEVICES_CONTAINER = devices
COSMOS_READINGS_CONTAINER = readings
```

Your code **must** read those values from the environment, not from
hardcoded literals.

## What you are building

A Go HTTP service (Go 1.22+, net/http) exposing five endpoints. The
service must use **Azure Cosmos DB for NoSQL** through the official Go
SDK (`github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos`).

### API contract

| Method | Path                                      | Purpose                          | Success status |
|--------|-------------------------------------------|----------------------------------|----------------|
| GET    | `/health`                                 | Liveness probe                   | `200` with `{"status": "ok"}` |
| POST   | `/devices`                                | Register a device                | `201` (or `409` if id exists) |
| POST   | `/readings`                               | Ingest a sensor reading          | `201` |
| GET    | `/devices/{id}/readings?start=<iso>&end=<iso>` | Get readings in a time range | `200` with a JSON array |
| GET    | `/devices/{id}/summary`                   | Get device stats                 | `200` |

`POST /devices` payload:

```json
{ "id": "dev-100", "name": "Boiler Room Sensor",
  "location": "Plant A / Boiler Room", "type": "temperature" }
```

All three input fields required; `type` is one of `temperature`,
`humidity`, or `pressure`; duplicate device `id` → `409`; field names
in JSON are camelCase.

`POST /readings` payload:

```json
{ "id": "r-9001", "deviceId": "dev-100",
  "timestamp": "2026-09-01T12:00:00Z", "value": 72.4,
  "unit": "C" }
```

All four input fields are required.

### Scale to keep in mind

You don't have to handle the scale, just model for it: ~50K devices,
~500M readings, an extremely write-heavy workload (~10:1 write/read),
and most queries by device plus time range.

## Build and run conventions (verifier contract)

1. Source under `/app/`.
2. **`/app/build.sh`** — `go mod download && go build -o /app/sensorgrid ./...`
3. **`/app/run.sh`** — foreground process on `$APP_PORT` (default
   `9080`). The verifier waits up to 90s for `GET /health` → `200`.

## How you will be graded

- **API conformance** — five endpoints, right status codes, payloads.
- **Cosmos data shape** — partition key, indexing policy, throughput,
  and document shape for device / reading records.
- **Go SDK best practices** — your skill set covers these. The grader
  inspects your source code (comments stripped) for the expected
  patterns.
- **Skills compliance** — no hardcoded keys, env-based config, latest
  SDK package id.

Binary reward to `/logs/verifier/reward.txt`.
