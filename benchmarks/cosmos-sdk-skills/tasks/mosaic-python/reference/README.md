# Mosaic — Python reference implementation

This is the **oracle solution** for the `mosaic-python` Harbor task. The
benchmark verifier copies it into `/app/` when run with the oracle
agent, so you can validate the test infrastructure without an actual
LLM in the loop.

## Files

- `app.py` — FastAPI service. Single CosmosClient (singleton),
  preferred regions, retry tuned for throttling, env-based config,
  `/users` partitioned by `/userId`, composite index for the city
  filter, type + schema version + ISO-8601 timestamps stamped on
  every document.
- `requirements.txt` — pinned versions of fastapi + uvicorn + azure-cosmos.
- `build.sh` — `pip install -r requirements.txt`. Called by the
  verifier first.
- `run.sh` — `uvicorn app:app --host 0.0.0.0 --port $APP_PORT`. Called
  by the verifier second and waited on.

## Why each best-practice choice

- **Singleton client** — one `CosmosClient(...)` at module import,
  reused by every request. Rule `sdk-singleton-client`.
- **`preferred_locations`** — passed to the constructor so reads/writes
  prefer the configured regions. Rule `sdk-preferred-regions`. The
  list is read from `COSMOS_PREFERRED_REGIONS` env so deployments can
  override it without code changes.
- **Retry / throttling** — `retry_total=9, retry_backoff_max=30` on
  the constructor. Rule `sdk-retry-throttled`.
- **Diagnostics** — `logging_enable=True` on per-call operations so
  Cosmos request diagnostics flow into the configured logger. Rule
  `sdk-diagnostics`.
- **No hardcoded key** — endpoint and key are read from env. Rule
  `sdk-secrets-from-env`.
- **Partition key `/userId`** — single-user reads hit one logical
  partition (rule `partition-userId-shaped`). `/id` would be too
  narrow; `/city` would hot-spot popular cities.
- **Composite index on `(city, id)`** — makes the city-filtered list
  query cheap without indexing every field. Rule `index-tailor-policy`.
- **Explicit throughput** — 400 RU/s declared at the database level
  (shared across containers). Rule `throughput-explicit`.
- **`type`, `schemaVersion`, `createdAt`** — every document carries
  a discriminator, a schema version, and an ISO-8601 timestamp string.
  Rules `model-type-discriminator`, `model-schema-version`,
  `model-iso8601-timestamps`.
- **`interests` as `list[str]`** — pydantic enforces the shape so we
  cannot accidentally persist enum values as integers.

This is intentionally minimal (a single file). A production
implementation would split routers, models, and the data layer; for the
benchmark the goal is to exercise every best-practice rule, not to be
production-grade.
