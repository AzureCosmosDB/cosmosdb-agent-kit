# Mosaic — User Profile Service (Node.js)

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

A Node.js HTTP service (Node 20+) exposing four endpoints. The service
must use **Azure Cosmos DB for NoSQL** through the official Node.js SDK.

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
2. **`/app/build.sh`** — `npm install --omit=dev`.
3. **`/app/run.sh`** — foreground process on `$APP_PORT` (default
   `9080`). The verifier waits up to 90s for `GET /health` → `200`.

## How you will be graded
- **Live behavior (primary)** — the verifier builds and starts your
  service, drives the HTTP API, then independently reads the Cosmos
  emulator with its own client to confirm what you persisted: real
  Cosmos documents (not in-memory), API reads/lists matching stored
  docs, duplicate `POST` rejected without a second document, and correct
  city filtering.
- **API conformance** — four endpoints, right status codes, payloads.

Binary reward to `/logs/verifier/reward.txt`.
