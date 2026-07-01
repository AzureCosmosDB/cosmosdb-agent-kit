# Mosaic — User Profile Service (.NET)

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

Your code **must** read those values from the environment (or from
configuration that resolves to env), not from hardcoded literals.

## What you are building

A .NET HTTP service (ASP.NET Core, target .NET 8) exposing four
endpoints. The service must use **Azure Cosmos DB for NoSQL** through
the official .NET SDK.

### API contract

| Method | Path                       | Purpose                          | Success status |
|--------|----------------------------|----------------------------------|----------------|
| GET    | `/health`                  | Liveness probe                   | `200` with `{"status": "ok"}` |
| POST   | `/users`                   | Create a user                    | `201` with the created user |
| GET    | `/users/{id}`              | Read one user by id              | `200` (or `404` if missing) |
| GET    | `/users?city=<city>`       | List users filtered by city      | `200` with a JSON array |

`POST /users` accepts JSON of the form:

```json
{ "id": "u-alpha", "name": "Alpha", "email": "alpha@example.com",
  "city": "Seattle", "interests": ["climbing", "coffee"] }
```

All four input fields are required; `interests` order must round-trip
exactly; duplicate `id` returns `409`. Field names in JSON are
camelCase.

### Scale to keep in mind

You don't have to handle the scale, just model for it: ~5M users,
~90/10 read/write, most reads by user id with a long-tail of
city-filtered lists.

## Build and run conventions (verifier contract)

The verifier expects:

1. Source under `/app/`.
2. **`/app/build.sh`** — one-shot setup. For .NET this typically does
   `dotnet restore` and `dotnet build -c Release -o /app/out`.
3. **`/app/run.sh`** — foreground process that launches the service on
   port `$APP_PORT` (default `9080`). The verifier waits up to 90s
   for `GET http://localhost:$APP_PORT/health` → `200`.

## How you will be graded
- **Live behavior (primary)** — the verifier builds and starts your
  service, drives the HTTP API, then **independently reads the Cosmos
  emulator with its own client** to confirm what you persisted: every
  created user is a real Cosmos document (an in-memory store fails
  here), the API read/list paths agree with the stored documents, the
  partition-key value equals the user id, a duplicate `POST` is rejected
  without creating a second document, and the city filter returns
  exactly the matching rows.
- **API conformance** — four endpoints, right status codes, payloads.
- **Cosmos data shape** — partition key, indexing policy, throughput,
  document shape (`type`, `schemaVersion`, ISO-8601 `createdAt`,
  `interests` as string array).
- **.NET SDK best practices (secondary, static)** — rules that a
  single-node emulator can't prove behaviorally (retry, preferred
  regions, Direct mode, diagnostics) are checked by scanning your
  source (comments stripped). These apply equally to every submission.
- **Skills compliance** — no hardcoded account keys, endpoint from
  env or `appsettings`, no deprecated package usage.

Binary reward (`1` or `0`) lands in `/logs/verifier/reward.txt`.
