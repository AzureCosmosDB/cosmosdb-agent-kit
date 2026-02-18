# Iteration 002 - Java Gaming Leaderboard

## Metadata
- **Date**: 2026-02-17
- **Language/SDK**: Java 17 / Spring Boot 3.2.1 / azure-spring-data-cosmos 5.9.0
- **Skill Version**: Post iteration-001-dotnet (57 rules including pattern-efficient-ranking.md, sdk-etag-concurrency.md)
- **Agent**: GitHub Copilot (Claude Opus 4.6)
- **Tester**: Automated test run

## ⚠️ Skills Verification

**Were skills loaded before building?** ✅ Yes

**How were skills loaded?**
- [x] Read `skills/cosmosdb-best-practices/AGENTS.md` directly (6541 lines, full file)
- [x] Extracted all Java-specific rules via targeted search
- [x] Skills auto-loaded from workspace

**Verification**: Agent applied Gateway mode for emulator (Rule 4.6), singleton CosmosClient (Rule 4.16), contentResponseOnWriteEnabled (Rule 4.9), materialized view pattern (Rule 9.1), COUNT-based ranking (Rule 9.2), synthetic partition keys (Rule 2.6), schema versioning (Rule 1.5), type discriminators (Rule 1.6) — all consistent with loaded skills.

## Prompt Used

```
I need to build a Spring Boot 3 REST API for a mobile game leaderboard system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Players submit scores after completing games
2. Display global top 100 leaderboard (sorted by high score)
3. Display regional leaderboards by country
4. Get a specific player's rank and the 10 players above/below them
5. Get player profiles with stats (total games played, best score, average score)
6. Support weekly leaderboard periods (keep historical data)

Expected scale:
- ~500,000 active players
- ~1 million score submissions per day
- Very high read volume on leaderboard queries
- Low latency requirements (< 50ms for leaderboard reads)

Please create:
1. The data model optimized for leaderboard queries
2. The Cosmos DB container configuration
3. A repository layer for data access
4. REST API endpoints for the required operations

Use best practices for Cosmos DB throughout. Consider how to efficiently handle "top N" queries and player ranking.
```

## What the Agent Produced

### Data Model
- ✅ Three containers: `players` (profiles), `scores` (individual submissions), `leaderboard` (materialized views)
- ✅ Denormalized player stats (`bestScore`, `averageScore`, `totalGamesPlayed`, `totalScore`) embedded in Player document (Rule 1.2/1.3)
- ✅ Type discriminator on all models: `"player"`, `"score"`, `"leaderboardEntry"` (Rule 1.6)
- ✅ Schema versioning: `schemaVersion = 1` on Player model (Rule 1.5)
- ✅ Scores correctly separated from players (unbounded growth per player)
- ✅ LeaderboardEntry denormalizes `displayName` and `country` for read performance

### Container Configuration
- ✅ `players` container: `/playerId` partition key — high cardinality, query-aligned (Rule 2.4)
- ✅ `scores` container: `/playerId` partition key — matches lookup pattern
- ✅ `leaderboard` container: `/partitionKey` — synthetic composite key `scope_weekPeriod` (Rule 2.6)
- ✅ Gateway mode for emulator, Direct mode for production (Rule 4.6)
- ❌ No explicit composite index configuration — Spring Data Cosmos doesn't declaratively support it
- ❌ No custom indexing policy (default `/*` indexes unused paths)
- ❌ No throughput configuration discussed

### Repository Layer
- ✅ Spring Data Cosmos repositories extending `CosmosRepository<T, String>` (idiomatic)
- ✅ All leaderboard queries are single-partition via synthetic partition key (Rule 3.1)
- ✅ Parameterized queries throughout using `SqlQuerySpec` + `SqlParameter` (Rule 3.5)
- ✅ Projections used — specific field selection in queries (Rule 3.6)
- ✅ Materialized view pattern — leaderboard entries upserted on score submit (Rule 9.1)
- ✅ COUNT-based rank query for efficient ranking (Rule 9.2) — **improvement over iteration-001-dotnet**
- ✅ Only updates leaderboard entry if new score is higher than existing (efficient upsert)
- ⚠️ OFFSET/LIMIT pagination instead of continuation tokens (same gap as iteration-001)
- ⚠️ `findById` on Player uses cross-partition warning (partitionKey != id path issue)

### SDK Usage
- ✅ Singleton `CosmosClient` via Spring `@Bean` (Rule 4.16)
- ✅ `contentResponseOnWriteEnabled(true)` (Rule 4.9)
- ✅ Session consistency level (Rule 7.2)
- ✅ Query metrics enabled (Rule 8.4)
- ✅ Gateway/Direct auto-detection for emulator vs production (Rule 4.6)
- ✅ `CosmosTemplate` used for advanced queries with `runQuery()` (appropriate for custom SQL)
- ❌ No preferred regions configuration
- ❌ No availability strategy
- ❌ No circuit breaker
- ❌ No diagnostics logging
- ❌ No explicit retry configuration
- ❌ `COSMOS.EMULATOR_SSL_TRUST_ALL` system property used but does NOT work with Netty/OpenSSL — had to use JDK truststore import

## Build Status
- **Initial Build**: ❌ Failed — 3 compilation errors
  1. `CosmosTemplate.runQuery()` method signature wrong (passed `String containerName` instead of `Class<?> domainType`) — **Java SDK API gap in skills**
  2. `Iterable` doesn't have `.stream()` method — needed `StreamSupport.stream(iterable.spliterator(), false)`
  3. SSL trust property doesn't work with Netty — needed JDK truststore import
- **After Fixes**: ✅ Succeeded (BUILD SUCCESS)
- **Runtime Test**: ✅ All endpoints tested and working

## Runtime Test Results

### Tests Passed ✅
| Endpoint | Method | Result |
|----------|--------|--------|
| `/api/players` | POST | Player created with embedded stats, returns full document |
| `/api/players/{id}` | GET | Returns player profile with cumulative stats |
| `/api/players/{nonexistent}` | GET | Returns 404 Not Found |
| `/api/scores` | POST | Score submitted, player stats updated, leaderboard entries upserted |
| `/api/leaderboard/global?top=10` | GET | Returns global top N sorted by score DESC |
| `/api/leaderboard/regional/US?top=10` | GET | US regional leaderboard correctly filtered |
| `/api/leaderboard/regional/UK?top=10` | GET | UK regional leaderboard correctly filtered |
| `/api/players/{id}/rank` | GET | COUNT-based rank + nearby players with correct positions |

### Tests Failed ❌
| Endpoint | Method | Issue |
|----------|--------|-------|
| `/api/players` (empty body) | POST | Returns 500 instead of 400 for validation errors |

### Data Integrity Verified ✅
- Multiple scores for same player correctly update `bestScore` (keeps highest)
- `averageScore` correctly calculated across multiple submissions
- `totalGamesPlayed` incremented on each score submission
- Global leaderboard correctly ordered: DragonSlayer99 (3000) > NinjaCoder42 (2500) > CosmicQueen (2000)
- Regional leaderboards correctly filter by country
- Rank calculation using COUNT-based approach returns correct positions

### Bugs Found 🐛

1. **Validation returns 500 instead of 400** — `GlobalExceptionHandler` only handles `IllegalArgumentException` (400). Spring's `MethodArgumentNotValidException` for `@Valid` failures falls through to the generic `Exception` handler, returning 500. Should add explicit handler for `MethodArgumentNotValidException`.

2. **`partitionKey` serialized as null in JSON** — When returning `LeaderboardEntry` via REST API, the `partitionKey` field shows as `null` in JSON. The value exists in Cosmos DB (queries work), but the getter may not be returning the value after deserialization. Cosmetic but confusing for API consumers.

3. **Cross-partition warning on player lookup** — Spring Data Cosmos logs `WARN: The partitionKey is not id!! Consider using findById(ID id, PartitionKey partitionKey)`. Player model uses `/playerId` as partition key but `findById` doesn't explicitly provide it. Should use overloaded `findById(id, new PartitionKey(id))`.

4. **ReadTimeoutException on first request** — First score submission triggers `io.netty.handler.timeout.ReadTimeoutException` on one of the connections. Recovers automatically on retry. Likely emulator warmup issue, but could indicate connection pool misconfiguration.

## Gaps Identified

### Critical Gaps
None — all functional requirements met. COUNT-based ranking (Rule 9.2) is a significant improvement over iteration-001-dotnet's O(N) approach.

### Best Practice Gaps (suboptimal but works)
1. **OFFSET/LIMIT pagination** — Same gap as iteration-001. Continuation tokens preferred for deep pages (Rule 3.4).
2. **No composite index** — Spring Data Cosmos repositories don't support declarative composite indexes. Would need Azure CLI/Portal/ARM template to create `(partitionKey ASC, score DESC)` on leaderboard container.
3. **No diagnostics logging** — `CosmosClientResponse` diagnostics not captured for slow-operation detection.
4. **No preferred regions** — Missing `preferredRegions()` for multi-region failover.
5. **No custom indexing** — Default `/*` indexes all paths including unused ones on players/scores.
6. **No throughput config** — No discussion of autoscale, provisioned, or burst capacity.
7. **Emulator SSL handling** — `COSMOS.EMULATOR_SSL_TRUST_ALL` system property documented in skills BUT does not work with Java/Netty. Requires actual JDK truststore certificate import.

### Knowledge Gaps
1. **`CosmosTemplate.runQuery()` API** — Agent initially used wrong method signature (3-arg with container name instead of domain class). Spring Data Cosmos API documentation could be clearer.
2. **`Iterable` vs `List`** — Agent assumed `runQuery()` returns a stream-compatible type. It returns `Iterable` which requires `StreamSupport.stream()`.
3. **Netty SSL vs Java SSL** — Agent's `COSMOS.EMULATOR_SSL_TRUST_ALL` is a Cosmos SDK property but Netty uses OpenSSL, bypassing Java's `SSLContext`. Truststore import is the correct approach.

## Comparison with Iteration 001 (.NET)

| Aspect | Iteration 001 (.NET) | Iteration 002 (Java) | Improvement? |
|--------|---------------------|---------------------|--------------|
| Rank computation | ❌ O(N) full scan | ✅ COUNT-based O(1) | ✅ Yes — Rule 9.2 applied |
| Materialized views | ✅ 4 variants | ✅ 2 variants (global + regional) | ➡️ Similar |
| ETag concurrency | ❌ Not used | ⚠️ Used implicitly by Spring Data | ➡️ Marginal |
| Schema versioning | ❌ None | ✅ `schemaVersion` field | ✅ Yes — Rule 1.5 applied |
| Type discriminators | ✅ Present | ✅ Present | ➡️ Same |
| Error handling | ❌ No global handler | ✅ GlobalExceptionHandler (partial) | ✅ Better |
| Build success | ✅ First try | ❌ 3 fixes needed | ❌ Regression (Java API knowledge gaps) |
| SSL handling | ✅ Easy (.NET callback) | ❌ Complex (truststore import) | ❌ Harder |

**Key insight**: The new rules created in iteration-001 (`pattern-efficient-ranking.md`, `sdk-etag-concurrency.md`) directly improved iteration-002. COUNT-based ranking was applied correctly, demonstrating **skill improvement feedback loop working**.

## Recommendations for Skill Improvements

### High Priority
1. **Update `sdk-emulator-ssl.md`** — Document that `COSMOS.EMULATOR_SSL_TRUST_ALL` does NOT work with Java's Netty-based Cosmos SDK. The correct approach is JDK truststore certificate import OR creating a custom truststore. The current rule shows it as an "alternative" but it fails in practice.
2. **Add Spring Data Cosmos API reference** — `CosmosTemplate.runQuery()` signature is `(SqlQuerySpec, Class<?> domainType, Class<T> returnType)` NOT `(SqlQuerySpec, Class<T>, String containerName)`. Document the correct API for common query patterns.

### Medium Priority
3. **Add `Iterable`-to-`List` conversion pattern** — `CosmosTemplate.runQuery()` returns `Iterable<T>`, not `List<T>`. Document `StreamSupport.stream(iterable.spliterator(), false).toList()` as the standard conversion pattern.
4. **Spring Data Cosmos `findById` with PartitionKey** — When `@PartitionKey` field differs from `id`, always use `findById(id, new PartitionKey(pk))` to avoid cross-partition queries.
5. **Strengthen `query-pagination.md`** — Add explicit anti-pattern warning for OFFSET/LIMIT (same gap as iteration-001).

### Low Priority
6. **Document composite index creation outside Spring Data** — Since Spring Data Cosmos doesn't support declarative composite indexes, show how to create them via Azure CLI or ARM template.
7. **Add `MethodArgumentNotValidException` handler pattern** — Spring Boot validation errors should return 400, not fall through to 500.

## Score Summary

| Category | Score | Notes |
|----------|-------|-------|
| Data Model | 9/10 | Excellent denormalization + schema versioning + type discriminators. Improvement over iter-001. |
| Partition Key | 9/10 | High cardinality, synthetic keys, query-aligned. Same quality as iter-001. |
| Indexing | 5/10 | No composite index and no custom indexing policy. Spring Data limitation, but not compensated for. |
| SDK Usage | 7/10 | Core rules applied well. Missing production hardening. Emulator SSL incorrect. |
| Query Patterns | 8/10 | COUNT-based ranking is a significant improvement. Single-partition, parameterized. OFFSET/LIMIT still used. |
| Architecture | 8/10 | Materialized view pattern correct. Inline updates acceptable for MVP. |
| Error Handling | 6/10 | GlobalExceptionHandler present but incomplete (validation → 500). Better than iter-001. |
| Build Quality | 5/10 | 3 compilation errors required fixes. Java SDK API knowledge needs improvement. |
| **Overall** | **7/10** | Same overall score as iteration-001 but with different strengths. Ranking improved (COUNT-based), schema versioning added, but Java-specific API knowledge gaps caused build failures. Skills feedback loop is working — new rules were applied. |

## Next Steps
1. **Update `sdk-emulator-ssl.md`** — Mark `COSMOS.EMULATOR_SSL_TRUST_ALL` as NOT working with Java/Netty. Add JDK truststore import as primary approach.
2. **Add Java `CosmosTemplate` API patterns** — Document correct `runQuery()` method signature and `Iterable` handling.
3. **Strengthen `query-pagination.md`** — Anti-pattern warning for OFFSET/LIMIT.
4. **Run iteration-003 in Python** — Test cross-language effectiveness to identify Python-specific gaps.
5. **Run iteration-003-java** — Re-test with updated SSL and API rules to measure improvement in build success rate.
