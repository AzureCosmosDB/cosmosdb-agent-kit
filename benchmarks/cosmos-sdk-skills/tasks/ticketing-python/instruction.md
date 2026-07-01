# TicketWave — Event Ticketing Service (Python)

You are building **TicketWave**, a local event ticketing platform. The
service is backed by **Azure Cosmos DB for NoSQL**, and the **Cosmos DB
emulator** is already running inside this container at the standard
endpoint.

You can find the emulator endpoint and key in your environment:

```
COSMOS_ENDPOINT  = http://localhost:8081
COSMOS_KEY       = <well-known emulator key, already set>
COSMOS_DATABASE  = ticketwave
COSMOS_EVENTS_CONTAINER = events
COSMOS_TICKETS_CONTAINER = tickets
```

Your code **must** read those values from the environment, not from
hardcoded literals.

## What you are building

A Python HTTP service (FastAPI + uvicorn) exposing six endpoints. The
service must use **Azure Cosmos DB for NoSQL** (no SQLite, no
in-memory dict) to store events and tickets, and reads/writes must go
through the official Cosmos Python SDK.

### API contract

| Method | Path                               | Purpose                          | Success status |
|--------|------------------------------------|----------------------------------|----------------|
| GET    | `/health`                          | Liveness probe                   | `200` with `{"status": "ok"}` |
| POST   | `/events`                          | Create an event                  | `201` (or `409` if id exists) |
| GET    | `/events/{id}`                     | Get event by id                  | `200` (or `404` if missing) |
| GET    | `/events?city=<city>`              | List events filtered by city     | `200` with a JSON array |
| POST   | `/events/{id}/tickets`             | Buy a ticket                     | `201` (or `409` if duplicate ticket id) |
| DELETE | `/events/{id}/tickets/{ticketId}`  | Cancel a ticket                  | `204` (or `412` if ETag mismatch) |

`POST /events` accepts JSON with these fields:

```json
{
  "id": "evt-summer-night",
  "title": "Summer Night Market",
  "description": "Food trucks, live music, and local makers.",
  "city": "Seattle",
  "date": "2026-08-14T19:00:00Z",
  "venue": "Pier Plaza",
  "capacity": 1200
}
```

All six input fields (`title`, `description`, `city`, `date`, `venue`,
`capacity`) are required. `POST` with an already-used event `id`
should return `409`.

`POST /events/{id}/tickets` accepts JSON with these fields:

```json
{
  "id": "t-1001",
  "userId": "u-42",
  "purchaseDate": "2026-08-01T10:15:00Z",
  "status": "active",
  "seatNumber": "A-12"
}
```

`status` is either `active` or `cancelled`. The ticket belongs to the
event identified by the path parameter. Duplicate ticket `id` returns
`409`.

### Scale to keep in mind

You don't have to handle the scale, just **model** for it: TicketWave
expects ~100K events, ~2M tickets, most reads are by event id, with a
smaller set of city-filtered event lists.

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

- **API conformance** — all six endpoints behave per the contract
  above, with the right status codes and payload shapes.
- **Cosmos data shape** — partition key choice, indexing policy,
  throughput, document fields (`type` discriminator, `schemaVersion`,
  `createdAt` as an ISO-8601 string, and event / ticket fields that
  match the contract above).
- **Cosmos SDK best practices** — your loaded skill set covers these
  for Python. The grader will look at your source code (with comments
  stripped) for the relevant patterns.
- **Skills compliance** — no hardcoded account keys, endpoint loaded
  from env, no deprecated package usage.

The grader writes a binary reward (`1` if everything passes, `0`
otherwise) to `/logs/verifier/reward.txt`. Per-category logs land in
the same directory.
