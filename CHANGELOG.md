# Changelog

Dated history of changes to the agent kit, including the `cosmosdb-best-practices` skill (rules, categories, compiled `AGENTS.md`) and the testing framework.

This is the high-level log. For detailed per-iteration evaluation notes (test results, scores, issues encountered, rules applied, lessons learned), see:

- [`testing-v2/IMPROVEMENTS-LOG.md`](testing-v2/IMPROVEMENTS-LOG.md) — current testing framework (v2)
- [`testing/IMPROVEMENTS-LOG.md`](testing/IMPROVEMENTS-LOG.md) — original testing framework (v1, historical)

---

## 2026-04-18 — README updated to document testing framework

- Expanded `README.md` with a section describing the testing framework and how evaluations flow back into the skill.

## 2026-04-17 — CHANGELOG added

- Added `CHANGELOG.md` (this file) and updated `README.md` to link to it. Backfilled entries from earlier merged PRs and from `testing/IMPROVEMENTS-LOG.md` and `testing-v2/IMPROVEMENTS-LOG.md`.

## 2026-04-15 — Batch #209: Java multitenant SaaS — SDK quirk flagged, no rule changes ([#220](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/220))

- Evaluated 5 Java iterations of the `multitenant-saas` scenario (testing-v2 batch #209).
- Zero always-fail tests. When startup succeeded (3/5 iterations), pass rate was 100% across API contract, Cosmos infrastructure, and data integrity tests.
- Identified a 40% Java startup-failure rate caused by Netty/OpenSSL behavior against the local emulator. Classified as an SDK/framework quirk, not a functional skill gap — `sdk-emulator-ssl` may benefit from a clearer programmatic Java CI bypass in a future pass.
- No rules created or modified.

## 2026-04-14 — Harness fix: guard against 1-of-0 test reporting

- Fixed a batch-aggregation edge case where pytest collection errors produced a misleading "1 of 0 tests passed" summary. The harness now reports zero-test iterations explicitly.

## 2026-04-09 — Website, logo, and integrations section ([#111](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/111), [#112](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/112))

- Added the `docs/` agent-kit website with a GitHub-issue survey, Cosmos DB logo, Google Analytics, and metrics (70+ rules).
- Added an "Integrations" section covering the MCP Server and Claude / Cursor plugins.
- Converted the website submodule to a regular directory.

## 2026-04-07 — README visual + rule clarifications ([#108](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/108), [#109](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/109))

Expanded and clarified five existing rules so agents apply them correctly:

- `partition-hierarchical` — clearer guidance on when to use hierarchical partition keys.
- `query-pagination` — expanded pagination patterns and anti-patterns.
- `query-top-literal` — reworked `TOP` vs parameterized-limit guidance.
- `sdk-java-cosmos-config` — added missing config knobs.
- `sdk-spring-data-annotations` — minor correctness fix.
- Tightened `scripts/validate.js` to catch malformed frontmatter.
- Added a hero image to `README.md`.

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

## 2026-04-01 — Batch workflow fixes

- Reverted explicit `permissions:` blocks that were breaking CI approval gates.
- Fixed a race where post-create issue edits caused single-child failures in batch runs.

## 2026-03-31 — CI permissions and fork workflow docs

- Added required write permissions to the `test-iteration` and `auto-trigger-tests` workflows.
- Added `permissions:` blocks to the batch workflows.
- Documented the fork requirement and upstream-PR workflow in `README.md`.

## 2026-03-30 — Batch aggregate issue→PR resolution fix

- Fixed batch aggregation so parent issues resolve to the correct child PRs when iterating results.

## 2026-03-27 — Five new / enhanced query and partition rules

- Added `query-point-reads` ([#63](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/63)) — prefer `ReadItem` over a query when both `id` and the partition key are known.
- Added `partition-immutable-key` ([#64](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/64)) — warns that partition keys cannot be updated in place.
- Added `query-olap-detection` ([#61](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/61)) — warns against running analytical queries on transactional containers.
- Enhanced `query-use-projections` ([#62](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/62)) with DTO / result-type matching guidance.
- Enhanced `partition-hierarchical` ([#60](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/60)) with explicit broad→narrow level-ordering guidance.

## 2026-03-26 — Pre-computed aggregates + tooling rules ([#58](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/58), [#59](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/59))

- Added intra-document pre-computed aggregates guidance to `model-denormalize-reads`.
- Synced the skill index and added tooling rules covering build / validate scripts.

## 2026-03-24 — Jackson `@JsonIgnoreProperties` rule ([#45](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/45), [#46](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/46))

- Added guidance for `@JsonIgnoreProperties` and global `ObjectMapper` config so Java code tolerates Cosmos DB system-metadata fields (`_rid`, `_self`, `_etag`, `_attachments`, `_ts`).
- Established that evaluation-created rules must be generic, not scenario-specific.

## 2026-03-23 — Java SDK and CI fixes

- `sdk-java-cosmos-config` ([#44](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/44)) — added `createDatabaseIfNotExists`, fixed a `CosmosConfig` class-name collision, and added `AbstractCosmosConfiguration` guidance.
- `query-avoid-cross-partition` ([#43](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/43)) — added a Java / Spring Data Cosmos `@Query` bypass warning.
- `sdk-java-content-response` ([#38](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/38), [#42](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/42)) — added a Reactor NPE warning and `readItem()` / `CosmosItemResponse<T>` unwrapping guidance.
- `sdk-spring-data-annotations` ([#41](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/41)) — partition-key-path matching warning.
- Rule 9.1 `pattern-change-feed-materialized-views` ([#39](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/39)) — added Change Feed idempotency guidance.
- Rule 5.2 `index-exclude-unused` ([#40](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/40)) — reordered so exclude-all-first is the primary indexing pattern.
- CI: narrowed path filters to iteration subdirectories only ([#37](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/37)).

## 2026-03-21 — testing-v2 framework merged ([#35](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/35))

- Merged the `testing-v2` framework with scenarios, API contracts, infrastructure / SDK / behavioral tests, build-signal capture, deep evaluation prompts, automated commit-back, and source archiving.
- Established `testing-v2/` as the current framework; `testing/` retained as a historical reference.

## 2026-03-19 to 2026-03-20 — Batch testing framework + build-startup category

- Added the batch testing framework for statistical significance (multiple iterations per scenario).
- `/batch-start` comment replaces assign-Copilot as the batch trigger; auto-create labels and auto-generate `/aggregate` commands with child-issue numbers.
- Aggregate fixes: iterate runs to find test artifacts, correct issue→PR resolution, per-category stats.
- Added a deep-evaluation step to the batch flow and next-steps instructions in the batch issue body.
- Exposed `build_startup` as a visible test category in reports; fixed summary-PR creation and skipped it for control runs; added auto-generation to `create-scenario`.

## 2026-03-18 — Test + CI hardening

- Added the missing `test_status_query_returns_correct_results` flow using a fresh order and the correct API path.
- Removed `permissions:` / `concurrency:` blocks from CI workflows to match org settings.
- Documented the manual workflow-approval step and why full automation requires a PAT.
- Fixed the control-run re-trigger loop and made archiving conditional.

## 2026-03-16 — Infrastructure and SDK tests; test-category docs

- Added infrastructure tests for `ai-chat-rag` and `multitenant-saas`; updated the scenario-creation recipe.
- Added infrastructure / SDK tests and build-signal capture for all scenarios.
- Documented test categories and build signals in the testing README.

## 2026-03-14 — Harder behavioral contracts + robustness tests

- Expanded API contracts across all three v2 scenarios with harder-to-implement behaviors.
- Added robustness tests to catch real application bugs.
- Added `__pycache__` to `.gitignore`.

## 2026-03-13 — Java SSL fix + CI reliability + skills toggle

- Java emulator SSL: import the Cosmos DB Emulator cert into the Java truststore.
- Enabled Copilot auto-retry (`workflow_call` + detailed CI logs).
- Language-aware common-cause hints + copy-paste `@copilot` prompts.
- Added a skills toggle, deep-evaluation prompt, and control-run support.
- Added automated evaluation, source archiving, and commit-back steps.
- Fixed multiple CI issues: batch-file launcher, hidden-window app launch, system-proxy bypass, `127.0.0.1` to avoid IPv6 timeouts on Windows, explicit `--ref` dispatch, improved emulator retries.

## 2026-03-12 — New rules: parameterized `TOP` and composite-index directions + CI switch

- Added `query-top-literal` — `TOP` requires a literal integer; `@param` causes 400 Bad Request.
- Added `index-composite-direction` — composite-index directions must match `ORDER BY`; define both ASC and DESC variants.
- Found via gaming-leaderboard iteration-001-python (testing-v2 PR #4).
- Switched CI to the Windows emulator and added a gatekeeper workflow.
- Auto-trigger tests for Copilot PRs; support `workflow_dispatch` / `repository_dispatch`.
- Improved emulator polling, emoji encoding, and emulator-failure reporting.

## 2026-03-11 — testing-v2 automation + Python async SDK rule

- Added `sdk-python-async-deps` (rule 4.15) — `azure.cosmos.aio.CosmosClient` requires `aiohttp` in `requirements.txt`.
- Found via gaming-leaderboard iteration-001-python (testing-v2 PR #2).
- Added testing-v2 automation: issue templates, CI workflow, recipes, and 5 scenarios.
- Auto-trigger `@copilot` for startup and test failures; handle app-startup failures gracefully in CI.

## 2026-03-03 — SDK version currency rule

- Added `sdk-validate-version-currency` — best practice for validating that the Cosmos DB SDK version in use is current.

## 2026-03-02 — Fixed Python ETag example ([#21](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/21), [#22](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/22))

- Corrected the Python example in `sdk-etag-concurrency`: must use `MatchConditions.IfNotModified` from `azure.core`, not the raw ETag string. The previous example raised `TypeError: Invalid match condition` at runtime.
- Added iteration-003-python for gaming-leaderboard (9/10).
- Cleaned up iterations (restored missing source-code zip for ecommerce-order-api iteration-004).

## 2026-02-25 — JPA → Spring Data Cosmos rules ([#20](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/20))

- Added best-practice rules for migrating JPA code to Spring Data Cosmos DB.

## 2026-02-20 — Hot partition example ([#19](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/19))

- Updated `partition-avoid-hotspots` with a worked example for popularity skew; recompiled `AGENTS.md`.

## 2026-02-19 — Data modeling / partitioning / change feed expansions

- Added examples, anti-patterns, and extra guidance to the data-modeling, partitioning, and change-feed / materialized-view rules.
- Cosmetic and syntax updates to `model-type-discriminator`, `partition-avoid-hotspots`, `partition-synthetic-keys`, and `pattern-change-feed-materialized-views`; recompiled `AGENTS.md`.

## 2026-02-18 — Multi-tenant SaaS (Java) rule additions and strengthening + Claude Code plugin ([#16](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/16), [#17](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/17), [#18](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/18))

- Added `sdk-java-cosmos-config` — documents the `@PostConstruct` + `@Bean` circular-dependency anti-pattern in Spring Boot and the correct chained-`@Bean` pattern.
- Strengthened `index-composite` with multi-tenant patterns and composite indexes for type-discriminator queries.
- Strengthened `query-pagination` with an explicit unbounded-query anti-pattern.
- Strengthened `sdk-etag-concurrency` with a "denormalized data updates" section and Java examples.
- Added Cosmos DB model constraints (PR #16); `AGENTS.md` recompiled to 61 rules.
- Added Claude Code plugin metadata for marketplace installation (PR #18).

## 2026-02-17 — Gaming leaderboard rule additions ([#15](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/15))

- Added `pattern-efficient-ranking` — replaces O(N) full-partition rank scans with COUNT-based, change-feed pre-computed, or score-bucket approaches.
- Added `sdk-etag-concurrency` — ETag-based optimistic concurrency for read-modify-write operations, with .NET, Java, and Python examples.

## 2026-02-02 — Multi-tenant SaaS (.NET) rule addition ([#14](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/14))

- Added `sdk-newtonsoft-dependency` — explicit `Newtonsoft.Json >= 13.0.3` requirement (security + version-conflict guidance), even when using `System.Text.Json`.

## 2026-01-29 — Vector Search category + IoT telemetry iterations ([#11](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/11))

Created the **Vector Search** category from scratch (rules 10.1–10.4):

- `vector-enable-feature` — account-level capability flag and SDK version requirements.
- `vector-embedding-policy` — `VectorEmbeddingPolicy` (path, dataType, dimensions, distanceFunction); cannot be modified post-create.
- `vector-index-type` — `QuantizedFlat` vs `DiskANN`; vector paths **must** be excluded from regular indexing.
- `vector-distance-query` — `VectorDistance()` query patterns and parameterization.

Same day, added two more vector rules from the Python / Azure validation pass:

- `vector-repository-pattern` — full repository-layer implementation pattern.
- `vector-normalize-embeddings` — L2 normalization for cosine similarity (production and deterministic test embeddings).

Also ran `iot-device-telemetry` end-to-end across three languages:

- **001 — .NET (9.5/10):** 30+ rules applied correctly (hierarchical partition key, synthetic key, composite indexes, autoscale, TTL, singleton client). No rule gaps.
- **002 — Java / Spring Boot (8/10):** Build only succeeded after fixing a Java-version / Spring Boot 3.x mismatch and updating to the current `PartitionKeyDefinition` + `MULTI_HASH` / V2 API.
- **003 — Python / FastAPI (9/10):** Validated `sdk-local-dev-config` (`load_dotenv(override=True)`) and confirmed the Python SDK requires `ThroughputProperties(auto_scale_max_throughput=...)` instead of a dict.

No new rules from IoT iterations — existing rule set covered all observed issues. Also updated the install command to use `skills add` ([#12](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/12)).

## 2026-01-28 — Cross-iteration review: design patterns + emulator/SDK fixes

- Added the **Design Patterns** category (section 9) and `pattern-change-feed-materialized-views` — converts cross-partition admin queries into single-partition lookups via Change Feed.
- Added `sdk-java-content-response` — Java SDK returns `null` from `createItem` unless `contentResponseOnWriteEnabled(true)` is set.
- Added `sdk-local-dev-config` — `load_dotenv(override=True)` and startup endpoint logging to prevent system env vars from silently pointing local dev at production.
- Enhanced `sdk-emulator-ssl` to cover .NET, Python, and Node.js (previously Java-only).
- Added iteration-002-dotnet validating skills on `ecommerce-order-api`.

## 2026-01-27 — Testing framework born + first rule from iteration findings

- Added `sdk-serialization-enums` — fixes a real bug where the .NET SDK stored enums as integers while queries searched for strings, causing status queries to return empty results (ecommerce-order-api baseline).
- Established that every test iteration must load the `cosmosdb-best-practices` skill before code generation — otherwise the iteration is a baseline, not a skill test. Updated `testing/README.md` and the iteration template to require a "Skills Verification" step. Iteration-001-dotnet of `ecommerce-order-api` was retroactively marked as the baseline (no skills).

## 2026-01-23 — Contribution scaffolding

- Added a pull-request template, `CONTRIBUTING.md` reference from `README.md`, and post-install / welcome scripts.
- Simplified the installation story: removed the CLI script and post-install script in favor of `skills add`.

## 2026-01-22 — High-availability and SDK resilience rules

- Added four rules for high availability and SDK resilience (connection modes, retry / backoff, regional failover, client reuse).

## 2026-01-21 — Initial release

- Initial release of the `cosmosdb-best-practices` agent skill: rule set, `SKILL.md`, compiled `AGENTS.md`, build / validate scripts, and README setup instructions.

---

## How to update

When a PR changes anything under `skills/cosmosdb-best-practices/` (rules or compiled `AGENTS.md`), or completes a notable testing iteration or batch evaluation, add an entry at the top:

```
## YYYY-MM-DD — short summary ([#NNN](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/NNN))

- What changed / why it matters.
```

Keep entries concise — a few bullets summarizing the change and the trigger (scenario / iteration / batch). Put the full evaluation detail in `testing-v2/IMPROVEMENTS-LOG.md` (or `testing/IMPROVEMENTS-LOG.md` for historical v1 entries) and link from the changelog if useful.
