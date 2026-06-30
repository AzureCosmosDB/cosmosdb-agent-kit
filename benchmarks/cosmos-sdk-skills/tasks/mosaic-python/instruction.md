# Mosaic — User Profile Service (Python)

You are building **Mosaic**, a local-experiences marketplace. The first
piece is a small user-profile service. The service is backed by **Azure
Cosmos DB for NoSQL**, and the **Cosmos DB emulator** is already running
inside this container at the standard endpoint.

You can find the emulator endpoint and key in your environment:

```
COSMOS_ENDPOINT  = http://localhost:8081
COSMOS_KEY       = <well-known emulator key, already set>
COSMOS_DATABASE  = mosaic
COSMOS_USERS_CONTAINER = users
```

Your code **must** read those values from the environment, not from
hardcoded literals.

## What you are building

A Python HTTP service exposing four endpoints. The service must use
**Azure Cosmos DB for NoSQL** (no SQLite, no in-memory dict) to store
user profiles, and reads/writes must go through the official Cosmos
Python SDK.

### API contract

| Method | Path                       | Purpose                          | Success status |
|--------|----------------------------|----------------------------------|----------------|
| GET    | `/health`                  | Liveness probe                   | `200` with `{"status": "ok"}` |
| POST   | `/users`                   | Create a user                    | `201` with the created user |
| GET    | `/users/{id}`              | Read one user by id              | `200` (or `404` if missing) |
| GET    | `/users?city=<city>`       | List users filtered by city      | `200` with a JSON array (empty if none) |

`POST /users` accepts JSON with these fields:

```json
{
  "id": "u-alpha",
  "name": "Alpha",
  "email": "alpha@example.com",
  "city": "Seattle",
  "interests": ["climbing", "coffee"]
}
```

All four input fields (`name`, `email`, `city`, `interests`) are
required. The order of items in `interests` must round-trip exactly.
`POST` with an already-used `id` should return `409`.

### Scale to keep in mind

You don't have to handle the scale, just **model** for it: Mosaic
expects ~5M users, ~90/10 read/write, and most reads are by user id
with a long-tail of city-filtered lists.

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

- **API conformance** — all four endpoints behave per the contract
  above, with the right status codes and payload shapes.
- **Cosmos data shape** — partition key choice, indexing policy,
  throughput, document fields (`type` discriminator, `schemaVersion`,
  `createdAt` as an ISO-8601 string, `interests` as a string array).
- **Cosmos SDK best practices** — your loaded skill set covers these
  for Python. The grader will look at your source code (with comments
  stripped) for the relevant patterns.
- **Skills compliance** — no hardcoded account keys, endpoint loaded
  from env, no deprecated package usage.

The grader writes a binary reward (`1` if everything passes, `0`
otherwise) to `/logs/verifier/reward.txt`. Per-category logs land in
the same directory.
