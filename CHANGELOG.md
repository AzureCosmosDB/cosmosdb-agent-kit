# Changelog

Dated history of changes to the agent kit, including the `cosmosdb-best-practices` skill (rules, categories, compiled `AGENTS.md`) and the testing framework.

---

## 2026-04-07 — Rule clarifications ([#108](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/108))

Expanded and clarified five existing rules so agents apply them correctly:

- `partition-hierarchical` — clearer guidance on when to use hierarchical partition keys.
- `query-pagination` — expanded pagination patterns and anti-patterns.
- `query-top-literal` — reworked `TOP` vs parameterized-limit guidance.
- `sdk-java-cosmos-config` — added missing config knobs.
- `sdk-spring-data-annotations` — minor correctness fix.
- Also tightened `scripts/validate.js` to catch malformed frontmatter.

## 2026-04-03 — +10 rules, new Full-Text Search category ([#95](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/95))

- Added 4 new SDK rules (4.21–4.24).
- Added a brand-new **Full-Text Search** category with 6 rules (12.1–12.6) covering the capability flag, `fullTextPolicy`, `fullTextIndexes`, BM25 ranking, keyword matching, and hybrid queries.
- Skill now totals 89 rules across 12 categories.

## 2026-04-02 — Cascade delete/update guidance ([#208](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/208))

- Extended `model-denormalize-reads` with explicit cascade semantics:
  - Deleting a source document must also delete all derived/embedded copies in other containers.
  - Updating a field used as a partition key in derived containers requires delete-and-recreate in the new partition.
- Added Python and C# examples for both patterns.
- Surfaced by the batch-191 gaming-leaderboard evaluation.

## 2026-03-12 — New rules: parameterized `TOP` and composite-index directions

- Added `query-top-literal` — `TOP` requires a literal integer; `@param` causes 400 Bad Request.
- Added `index-composite-direction` — composite-index directions must match `ORDER BY`; define both ASC and DESC variants.
- Found via gaming-leaderboard iteration-001-python (testing-v2 PR #4).

## 2026-03-11 — New rule: Python async SDK deps

- Added `sdk-python-async-deps` (rule 4.15) — `azure.cosmos.aio.CosmosClient` requires `aiohttp` to be in `requirements.txt`; `aiohttp` is an optional dependency of `azure-cosmos`.
- Found via gaming-leaderboard iteration-001-python (testing-v2 PR #2).

## 2026-03-02 — Fixed Python ETag example

- Corrected the Python example in `sdk-etag-concurrency`: must use `MatchConditions.IfNotModified` from `azure.core`, not the raw ETag string. The previous example raised `TypeError: Invalid match condition` at runtime.

## 2026-02-18 — Multi-tenant SaaS (Java) rule additions and strengthening

- Added `sdk-java-cosmos-config` — documents the `@PostConstruct` + `@Bean` circular-dependency anti-pattern in Spring Boot and the correct chained-`@Bean` pattern.
- Strengthened `index-composite` with multi-tenant patterns and composite indexes for type-discriminator queries.
- Strengthened `query-pagination` with an explicit unbounded-query anti-pattern.
- Strengthened `sdk-etag-concurrency` with a "denormalized data updates" section and Java examples.

## 2026-02-17 — Gaming leaderboard rule additions

- Added `pattern-efficient-ranking` — replaces O(N) full-partition rank scans with COUNT-based, change-feed pre-computed, or score-bucket approaches.
- Added `sdk-etag-concurrency` — ETag-based optimistic concurrency for read-modify-write operations, with .NET, Java, and Python examples.

## 2026-02-02 — Multi-tenant SaaS (.NET) rule addition

- Added `sdk-newtonsoft-dependency` — explicit `Newtonsoft.Json >= 13.0.3` requirement (security + version-conflict guidance), even when using `System.Text.Json`.

## 2026-01-29 — Vector Search category created

- Created the **Vector Search** category from scratch (rules 10.1–10.4):
  - `vector-enable-feature` — account-level capability flag and SDK version requirements.
  - `vector-embedding-policy` — `VectorEmbeddingPolicy` (path, dataType, dimensions, distanceFunction); cannot be modified post-create.
  - `vector-index-type` — `QuantizedFlat` vs `DiskANN`; vector paths **must** be excluded from regular indexing.
  - `vector-distance-query` — `VectorDistance()` query patterns and parameterization.
- Same day, added two more vector rules from the Python/Azure validation pass:
  - `vector-repository-pattern` — full repository-layer implementation pattern.
  - `vector-normalize-embeddings` — L2 normalization for cosine similarity (production and deterministic test embeddings).

## 2026-01-28 — Cross-iteration review: design patterns + emulator/SDK fixes

- Added the **Design Patterns** category (section 9) and `pattern-change-feed-materialized-views` — converts cross-partition admin queries into single-partition lookups via Change Feed.
- Added `sdk-java-content-response` — Java SDK returns `null` from `createItem` unless `contentResponseOnWriteEnabled(true)` is set.
- Added `sdk-local-dev-config` — `load_dotenv(override=True)` and startup endpoint logging to prevent system env vars from silently pointing local dev at production.
- Enhanced `sdk-emulator-ssl` to cover .NET, Python, and Node.js (previously Java-only).

## 2026-01-27 — Initial iteration findings (ecommerce-order-api)

- Added `sdk-serialization-enums` — fixes a real bug where the .NET SDK stored enums as integers while queries searched for strings, causing status queries to return empty results.

---

## How to update

When a PR changes anything under `skills/cosmosdb-best-practices/` (rules or compiled `AGENTS.md`), add an entry at the top:

```
## YYYY-MM-DD — short summary ([#NNN](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/NNN))

- What changed / why it matters.
```

If the change came out of a testing iteration, include a short summary here and put the full evaluation detail in `testing-v2/IMPROVEMENTS-LOG.md`.
