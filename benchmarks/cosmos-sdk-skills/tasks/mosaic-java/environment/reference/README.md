# Mosaic — Java reference implementation

Oracle solution for the `mosaic-java` Harbor task. Single-file Spring
Boot 3 / JDK 21 app using `com.azure:azure-cosmos` v4.65.0 (the GA v4
artifact, not the legacy `com.microsoft.azure:azure-documentdb` v2).

## Why each best-practice choice

- **Singleton CosmosClient** — exposed as a Spring `@Bean`; one
  instance for the lifetime of the JVM. Rule `sdk-singleton-client`.
- **`directMode(DirectConnectionConfig.getDefaultConfig())`** — Direct
  is the Java production default. Rule `sdk-connection-mode`.
- **`preferredRegions(...)`** — env-driven. Rule
  `sdk-preferred-regions`.
- **`throttlingRetryOptions(...)`** — 9 attempts / 30s wait. Rule
  `sdk-retry-throttled`.
- **`userAgentSuffix("mosaic-users")`** — tags telemetry / request
  diagnostics. Rule `sdk-diagnostics`.
- **`@PreDestroy shutdown()`** — closes the client on context
  shutdown. Rule `sdk-java-lifecycle`.
- **`/userId` partition key + composite index on `(city, id)`** —
  single-user reads hit one partition; the city-filter list query is
  cheap. Rules `partition-userId-shaped`, `index-tailor-policy`.
- **400 RU/s explicit throughput** at the database level. Rule
  `throughput-explicit`.
- **Document shape** — `type`, `schemaVersion`, ISO-8601 `createdAt`,
  `interests` as `List<String>`.
