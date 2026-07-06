# TicketWave — Event Ticketing Service (.NET)

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

Your code **must** read those values from the environment (or from
configuration that resolves to env), not from hardcoded literals.

## What you are building

A .NET HTTP service (ASP.NET Core, target .NET 8) exposing six
endpoints. The service must use **Azure Cosmos DB for NoSQL** through
the official .NET SDK.

### API contract

| Method | Path                               | Purpose                          | Success status |
|--------|------------------------------------|----------------------------------|----------------|
| GET    | `/health`                          | Liveness probe                   | `200` with `{"status": "ok"}` |
| POST   | `/events`                          | Create an event                  | `201` (or `409` if id exists) |
| GET    | `/events/{id}`                     | Get event by id                  | `200` (or `404` if missing) |
| GET    | `/events?city=<city>`              | List events filtered by city     | `200` with a JSON array |
| POST   | `/events/{id}/tickets`             | Buy a ticket                     | `201` (or `409` if duplicate ticket id) |
| DELETE | `/events/{id}/tickets/{ticketId}`  | Cancel a ticket                  | `204` (or `412` if ETag mismatch) |

`POST /events` accepts JSON of the form:

```json
{ "id": "evt-summer-night", "title": "Summer Night Market",
  "description": "Food trucks, live music, and local makers.",
  "city": "Seattle", "date": "2026-08-14T19:00:00Z",
  "venue": "Pier Plaza", "capacity": 1200 }
```

All six input fields are required; duplicate event `id` returns `409`.
Field names in JSON are camelCase.

`POST /events/{id}/tickets` accepts JSON of the form:

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
~2M tickets, most reads by event id with a smaller set of
city-filtered event lists.

## Build and run conventions (verifier contract)

The verifier expects:

1. Source under `/app/`.
2. **`/app/build.sh`** — one-shot setup. For .NET this typically does
   `dotnet restore` and `dotnet build -c Release -o /app/out`.
3. **`/app/run.sh`** — foreground process that launches the service on
   port `$APP_PORT` (default `9080`). The verifier waits up to 90s
   for `GET http://localhost:$APP_PORT/health` → `200`.

## How you will be graded

- **API conformance** — six endpoints, right status codes, payloads.
- **Data persistence** — the data your service returns matches what is
  actually stored in the Cosmos emulator.

Binary reward (`1` or `0`) lands in `/logs/verifier/reward.txt`.
