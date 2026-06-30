# Mosaic — .NET reference implementation

Oracle solution for the `mosaic-dotnet` Harbor task. Single-file
ASP.NET Core minimal API targeting .NET 8 and `Microsoft.Azure.Cosmos`
v3.43.1 (the GA package, not the abandoned `Azure.Cosmos` preview).

## Why each best-practice choice

- **Singleton CosmosClient** — `AddSingleton<CosmosClient>` so the
  process holds exactly one client. Rule `sdk-singleton-client`.
- **`ConnectionMode.Direct`** — the .NET production default. Rule
  `sdk-connection-mode`.
- **`ApplicationPreferredRegions`** — read from
  `COSMOS_PREFERRED_REGIONS` env. Rule `sdk-preferred-regions`.
- **Retry tuning** — `MaxRetryAttemptsOnRateLimitedRequests = 9`,
  `MaxRetryWaitTimeOnRateLimitedRequests = 30s`. Rule
  `sdk-retry-throttled`.
- **Diagnostics** — `ApplicationName = "mosaic-users"` tags every
  request so server-side diagnostics can correlate. Rule
  `sdk-diagnostics`.
- **Env-based config** — endpoint + key from environment. Rule
  `sdk-secrets-from-env`.
- **`/userId` partition key + composite index on `(city, id)`** for the
  city-filtered query. Rules `partition-userId-shaped` and
  `index-tailor-policy`.
- **400 RU/s explicit throughput** at the database level. Rule
  `throughput-explicit`.
- **Document shape** — `type`, `schemaVersion`, ISO-8601 `createdAt`,
  `interests` as `List<string>`. Rules `model-type-discriminator`,
  `model-schema-version`, `model-iso8601-timestamps`.
