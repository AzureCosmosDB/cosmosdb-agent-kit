# TicketWave — Event Ticketing Service (Java)

You are building **TicketWave**, a local event ticketing platform. The
service is backed by **Azure Cosmos DB for NoSQL**, and the **Cosmos DB
emulator** is already running inside this container at the standard
endpoint.

Environment variables already set for you:

```
COSMOS_ENDPOINT  = http://localhost:8081
COSMOS_KEY       = <well-known emulator key>
COSMOS_DATABASE  = ticketwave
COSMOS_EVENTS_CONTAINER = events
COSMOS_TICKETS_CONTAINER = tickets
```

Your code **must** read those values from the environment, not from
hardcoded literals.

## What you are building

A Java HTTP service (JDK 21, Spring Boot) exposing six endpoints. The
service must use **Azure Cosmos DB for NoSQL** through the official Java
SDK.

### API contract

| Method | Path                               | Purpose                          | Success status |
|--------|------------------------------------|----------------------------------|----------------|
| GET    | `/health`                          | Liveness probe                   | `200` with `{"status": "ok"}` |
| POST   | `/events`                          | Create an event                  | `201` (or `409` if id exists) |
| GET    | `/events/{id}`                     | Get event by id                  | `200` (or `404` if missing) |
| GET    | `/events?city=<city>`              | List events filtered by city     | `200` with a JSON array |
| POST   | `/events/{id}/tickets`             | Buy a ticket                     | `201` (or `409` if duplicate ticket id) |
| DELETE | `/events/{id}/tickets/{ticketId}`  | Cancel a ticket                  | `204` (or `412` if ETag mismatch) |

`POST /events` payload:

```json
{ "id": "evt-summer-night", "title": "Summer Night Market",
  "description": "Food trucks, live music, and local makers.",
  "city": "Seattle", "date": "2026-08-14T19:00:00Z",
  "venue": "Pier Plaza", "capacity": 1200 }
```

All six input fields required; duplicate event `id` → `409`; field
names in JSON are camelCase.

`POST /events/{id}/tickets` payload:

```json
{ "id": "t-1001", "userId": "u-42",
  "purchaseDate": "2026-08-01T10:15:00Z", "status": "active",
  "seatNumber": "A-12" }
```

`status` is either `active` or `cancelled`. The ticket belongs to the
event identified by the path parameter. Duplicate ticket `id` returns
`409`.

### Scale to keep in mind

You don't have to handle the scale, just model for it: ~100K events,
~2M tickets, mostly id-based event reads with a smaller set of
city-filtered lists.

## Build and run conventions (verifier contract)

1. Source under `/app/`.
2. **`/app/build.sh`** — `mvn -B package -DskipTests` (or whichever
   build tool you choose); should produce a runnable artifact.
3. **`/app/run.sh`** — foreground process listening on `$APP_PORT`
   (default `9080`). The verifier waits up to 90s for
   `GET /health` → `200`.

## How you will be graded

- **API conformance** — six endpoints, right status codes, payloads.
- **Cosmos data shape** — partition key, indexing policy, throughput,
  and document shape for event / ticket records.
- **Java SDK best practices** — your skill set covers these. The grader
  inspects your source code (comments stripped) for the expected
  patterns.
- **Skills compliance** — no hardcoded keys, env-based config, no
  legacy `com.microsoft.azure:azure-documentdb`.

Binary reward to `/logs/verifier/reward.txt`.
