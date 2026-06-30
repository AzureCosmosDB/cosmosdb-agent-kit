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

- API conformance and Cosmos data shape (partition key, indexing,
  throughput, document shape) are scored directly like the other SDKs.
- A small number of Go-specific source-code checks: singleton client,
  latest SDK package id.
- A **transparency rubric** specific to this task: be transparent in
  `/app/README.md` about how you decided on best practices that aren't
  covered by Go-specific guidance.

That last point matters: the local skill set bundled with this
benchmark has comprehensive Python / .NET / Java / Node.js guidance for
preferred regions, retries, diagnostics, and connection mode, but **no
Go-specific entries** for those topics. The verifier therefore expects
you to either:

- ask for clarification, or
- explicitly state in `/app/README.md` which other SDK / cross-SDK
  source you borrowed each non-Go-specific decision from (e.g.
  "borrowed from the .NET preferred-regions rule", "inferred from the
  general retry guidance"), or
- explicitly say "no SDK-specific local guidance for X, used my own
  judgement".

The verifier looks for phrases like:

- "borrowed from"
- "adapted from"
- "inferred from"
- "no SDK-specific guidance"
- "asked for clarification"
- "general retry / resilience guidance"

The verifier also penalises fabricated certainty: do **not** write
things like "official Go SDK best practice recommends ..." for topics
where there is no such official guidance.

Binary reward to `/logs/verifier/reward.txt`.

