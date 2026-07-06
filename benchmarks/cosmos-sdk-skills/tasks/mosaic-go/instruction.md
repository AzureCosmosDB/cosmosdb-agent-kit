# Mosaic — User Profile Service (Go)

You are building **Mosaic**, a local-experiences marketplace. The first
piece is a small user-profile service, backed by **Azure Cosmos DB for
NoSQL**. The **Cosmos DB emulator** is already running inside this
container at the standard endpoint.

Environment variables already set for you:

```
COSMOS_ENDPOINT  = http://localhost:8081
COSMOS_KEY       = <well-known emulator key>
COSMOS_DATABASE  = mosaic
COSMOS_USERS_CONTAINER = users
```

Your code **must** read those values from the environment, not from
hardcoded literals.

## What you are building

A Go HTTP service (Go 1.22+) exposing four endpoints. The service must
use **Azure Cosmos DB for NoSQL** through the official Go SDK
(`github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos`).

### API contract

| Method | Path                       | Purpose                          | Success status |
|--------|----------------------------|----------------------------------|----------------|
| GET    | `/health`                  | Liveness probe                   | `200` with `{"status": "ok"}` |
| POST   | `/users`                   | Create a user                    | `201` with the created user |
| GET    | `/users/{id}`              | Read one user by id              | `200` (or `404` if missing) |
| GET    | `/users?city=<city>`       | List users filtered by city      | `200` with a JSON array |

`POST /users` payload:

```json
{ "id": "u-alpha", "name": "Alpha", "email": "alpha@example.com",
  "city": "Seattle", "interests": ["climbing", "coffee"] }
```

All four input fields required; `interests` order round-trips;
duplicate `id` → `409`; field names in JSON are camelCase.

### Scale to keep in mind

You don't have to handle the scale, just model for it: ~5M users,
~90/10 read/write, mostly id-based reads with a long-tail of
city-filtered lists.

## Build and run conventions (verifier contract)

1. Source under `/app/`.
2. **`/app/build.sh`** — `go build -o /app/mosaic-users ./...`
3. **`/app/run.sh`** — foreground process on `$APP_PORT` (default
   `9080`). The verifier waits up to 90s for `GET /health` → `200`.

## How you will be graded
- **Live behavior (primary)** — the verifier builds and starts your
  service, drives the HTTP API, then **independently reads the Cosmos
  emulator with its own client** to confirm what you persisted: every
  created user is a real Cosmos document (an in-memory store fails
  here), the API read/list paths agree with the stored documents, a
  duplicate `POST` is rejected without creating a second document, and
  the city filter returns exactly the matching rows.
- **API conformance** — four endpoints, right status codes, payloads.

Binary reward to `/logs/verifier/reward.txt`.

