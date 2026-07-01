# Mosaic — Node.js reference implementation

Oracle solution for the `mosaic-nodejs` Harbor task. Single-file
Express app on Node 20 using `@azure/cosmos` v4 (the official package;
the legacy `documentdb` npm package is forbidden).

## Transparency note — borrowed guidance

Microsoft Learn has **no `best-practice-nodejs` page** for Cosmos DB.
SDK-level guidance for Node comes from the
[`@azure/cosmos` GitHub README](https://github.com/Azure/azure-sdk-for-js/tree/main/sdk/cosmosdb/cosmos)
and the Node quickstart. Where those don't address a topic, the
decisions below are **borrowed from** the .NET / Java best-practice
pages and labelled as such — they are not claimed as "official Node.js
recommendations".

## Why each best-practice choice

- **Singleton CosmosClient** — `new CosmosClient(...)` runs once at
  module load; reused for every request. Rule `sdk-singleton-client`.
- **`connectionPolicy.preferredLocations`** — read from
  `COSMOS_PREFERRED_REGIONS` env. **Inferred from** the .NET
  `ApplicationPreferredRegions` rule.
- **`connectionPolicy.retryOptions`** — 9 attempts / 30s wait.
  **Borrowed from** the .NET `MaxRetryAttemptsOnRateLimitedRequests`
  numbers in `sdk-retry-429`; no Node-specific recommendation exists
  for the exact values.
- **`userAgentSuffix`** — tags requests with the app name for
  server-side diagnostics. Rule `sdk-diagnostics`.
- **Env-based config** — endpoint + key from `process.env`. Rule
  `sdk-secrets-from-env`.
- **`/userId` partition key + composite index** on `(city, id)`. Rules
  `partition-userId-shaped`, `index-tailor-policy`.
- **400 RU/s explicit throughput** at the database level. Rule
  `throughput-explicit`.
- **Index exclusions** on `/email/?` and `/interests/*` (beyond the
  system `_etag`). Rule `index-exclude-unused`.
- **db/container provisioned once at startup** via top-level `await`
  before `app.listen`; route handlers reuse the cached `container`
  handle. Rule `sdk-cache-metadata`.
- **Document shape** — `type`, `schemaVersion`, ISO-8601 `createdAt`,
  `interests` as a string array.
