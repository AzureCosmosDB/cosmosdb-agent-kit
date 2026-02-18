# Iteration 001 - .NET Gaming Leaderboard

## Metadata
- **Date**: 2026-02-17
- **Language/SDK**: .NET 8 / Microsoft.Azure.Cosmos 3.57.0
- **Skill Version**: Post testing-framework merge (afc9881)
- **Agent**: GitHub Copilot (Claude Opus 4.6)
- **Tester**: Automated test run

## ⚠️ Skills Verification

**Were skills loaded before building?** ✅ Yes

**How were skills loaded?**
- [x] Skills auto-loaded from workspace (`AGENTS.md` in workspace root)
- [x] Read `skills/cosmosdb-best-practices/AGENTS.md` directly

**Verification**: Agent applied Direct connection mode, singleton client, enum serialization, composite indexes, materialized view pattern — all consistent with loaded skills.

## Prompt Used

```
I need to build a .NET 8 Web API for a mobile game leaderboard system using Azure Cosmos DB (NoSQL API).

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
- ✅ Three containers: `players` (profiles), `scores` (individual submissions), `leaderboards` (materialized views)
- ✅ Denormalized player stats (`bestScore`, `averageScore`, `totalGamesPlayed`) embedded in Player document
- ✅ Type discriminator on all models (`"player"`, `"score"`, `"leaderboardEntry"`)
- ✅ Scores correctly separated from players (unbounded growth per player)
- ✅ LeaderboardEntry denormalizes `displayName` and `country` for read performance
- ❌ No schema versioning property on any model

### Container Configuration
- ✅ `players` container with `/playerId` partition key — high cardinality, query-aligned
- ✅ `scores` container with `/playerId` partition key — high cardinality, matches lookup pattern
- ✅ `leaderboards` container with `/leaderboardKey` partition key — synthetic composite key
- ✅ Composite index `(bestScore DESC, lastUpdatedAt ASC)` on leaderboards container
- ✅ Consistent indexing mode
- ❌ No custom indexing policy on `players` or `scores` — default `/*` indexes unused paths
- ❌ No throughput configuration (autoscale, provisioned, or serverless noted)

### Repository Layer
- ✅ All queries are single-partition (partition key always specified in `QueryRequestOptions`)
- ✅ Point reads with partition key for player profile lookups (`ReadItemAsync`)
- ✅ Parameterized queries throughout (`QueryDefinition.WithParameter`)
- ✅ Projections used — `SELECT c.playerId, c.displayName, ...` instead of `SELECT *`
- ✅ Materialized view pattern — 4 leaderboard keys updated per score (global weekly, global all-time, regional weekly, regional all-time)
- ⚠️ `GetPlayerRankAsync` scans entire partition to find player rank — O(N) at scale
- ❌ OFFSET/LIMIT pagination instead of continuation tokens
- ❌ No optimistic concurrency (ETag exists on Player model but never used)

### SDK Usage
- ✅ Singleton `CosmosClient` via DI (`AddSingleton<CosmosDbService>`)
- ✅ Direct mode for production, Gateway for emulator
- ✅ Async APIs used throughout
- ✅ System.Text.Json serializer with `JsonStringEnumConverter`
- ✅ Emulator SSL bypass (`DangerousAcceptAnyServerCertificateValidator`)
- ✅ Explicit Newtonsoft.Json 13.0.3 dependency
- ❌ No preferred regions configuration
- ❌ No availability strategy
- ❌ No circuit breaker
- ❌ No diagnostics logging (only Debug-level RU logging)
- ❌ No explicit retry policy configuration

## Build Status
- **Initial Build**: ✅ Succeeded (no modifications needed)
- **Runtime Test**: ✅ All endpoints tested and working

## Runtime Test Results

### Tests Passed ✅
| Endpoint | Method | Result |
|----------|--------|--------|
| `/api/scores` | POST | Score submitted, player created/updated, 4 leaderboard entries upserted |
| `/api/leaderboard/global` | GET | Returns weekly global top N sorted by bestScore DESC |
| `/api/leaderboard/global/all-time` | GET | Returns all-time global rankings correctly |
| `/api/leaderboard/regional/{country}` | GET | Filters to country-specific weekly rankings |
| `/api/leaderboard/regional/{country}/all-time` | GET | Country-specific all-time rankings |
| `/api/leaderboard/player/{playerId}` | GET | Returns player rank + ±10 nearby players |
| `/api/players/{playerId}` | GET | Returns full player profile with cumulative stats |
| `/api/players/{nonexistent}` | GET | Returns 404 Not Found |
| `/api/leaderboard/player/{nonexistent}` | GET | Returns 404 Not Found |
| `/api/leaderboard/regional/BR` | GET | Returns empty entries for country with no data |
| `/api/scores` (missing fields) | POST | Returns 400 Bad Request |

### Tests Failed ❌
None — all endpoints functional.

### Data Integrity Verified ✅
- Multiple scores for same player correctly update `bestScore` (keeps highest)
- `averageScore` correctly calculated across multiple submissions
- `totalGamesPlayed` incremented on each score submission
- Rankings correctly ordered across all leaderboard variants
- Regional leaderboards correctly filter by country

## Bugs Found 🐛

### No Functional Bugs
All endpoints produce correct results. The application compiles, runs, and handles requests properly.

### Potential Issues at Scale
1. **`GetPlayerRankAsync` full partition scan** — Reads ALL entries in a leaderboard partition to find one player's rank. With 500K players in `global_all-time`, this would consume thousands of RU and take seconds. A production system would need a rank index, cached rank offsets, or a count-based approach.

2. **Inline leaderboard updates** — Score submission serially upserts to 4 leaderboard partition keys. At ~1M scores/day, this quadruples write latency. Change Feed processor would decouple reads from writes.

3. **Missing ETag concurrency** — `Player._etag` property exists but is never passed to `UpsertItemAsync`. Concurrent score submissions for the same player can cause lost updates to cumulative stats.

## Gaps Identified

### Critical Gaps
1. **Player rank lookup is O(N)** — Full partition scan for rank. At 500K players, this is unsustainable. No existing rule addresses efficient rank computation patterns.

### Best Practice Gaps (suboptimal but works)
1. **No diagnostics logging** — `response.Diagnostics` never logged; no slow-operation detection
2. **No preferred regions** — Missing `ApplicationPreferredRegions` for multi-region failover
3. **No availability strategy** — No cross-region hedging configured
4. **No circuit breaker** — No partition-level circuit breaker
5. **No throughput configuration** — No autoscale, provisioned, or serverless discussion
6. **Default indexing on players/scores** — Unused paths indexed, increasing write RU cost
7. **OFFSET/LIMIT pagination** — RU cost increases with page depth; continuation tokens preferred
8. **No schema versioning** — No version property for document evolution
9. **No global exception handling** — Unhandled `CosmosException` returns 500 without diagnostics
10. **Missing input validation** — No validation on `displayName`, `country`, `score` upper bound, or `top` parameter

### Knowledge Gaps
1. Did not discuss consistency level trade-offs for leaderboard reads (Eventual/Bounded Staleness would reduce latency)
2. Did not implement Change Feed processor for production-grade materialized views
3. Did not discuss container vs database throughput strategy
4. No mention of burst capacity for traffic spikes during game events

## Proposed Skill Improvements

### New Rules Created During This Iteration

1. ✅ **CREATED: `pattern-efficient-ranking.md`** (HIGH)
   - Documents count-based, cached rank, and score bucket approaches for efficient ranking
   - Prevents the O(N) full partition scan anti-pattern found in `GetPlayerRankAsync`
   - Prevents similar issues in all leaderboard/ranking scenarios

2. ✅ **CREATED: `sdk-etag-concurrency.md`** (HIGH)
   - Documents ETag-based optimistic concurrency for read-modify-write operations
   - Covers .NET, Java, and Python SDK examples with retry logic
   - Prevents lost updates in concurrent write scenarios (e.g., player stat aggregation)

3. ✅ **AGENTS.md regenerated** — Now contains 57 rules (was 55)

### Existing Rule Gaps Identified

1. **`query-pagination.md`** — Agent used OFFSET/LIMIT instead of continuation tokens. Rule exists but could be strengthened with an explicit anti-pattern warning for OFFSET/LIMIT.
2. **Production hardening rules** (preferred regions, diagnostics, monitoring) — Rules exist and are comprehensive but were not applied. May indicate prioritization guidance is needed in the skill kit.

## Score Summary

| Category | Score | Notes |
|----------|-------|-------|
| Data Model | 8/10 | Excellent denormalization, type discriminators, embed vs reference. Missing schema versioning. |
| Partition Key | 9/10 | High cardinality, synthetic keys, query-aligned. Could consider hierarchical PKs for scores. |
| Indexing | 7/10 | Good composite index on leaderboards. Default indexing on other containers wastes write RU. |
| SDK Usage | 7/10 | Core rules applied (singleton, Direct, enum serialization). Missing production hardening (preferred regions, diagnostics, retry config). |
| Query Patterns | 6/10 | Single-partition, parameterized, projections all good. Rank lookup full scan is concerning. OFFSET/LIMIT instead of continuation tokens. |
| Architecture | 8/10 | Materialized view pattern for leaderboards is excellent. Inline updates acceptable for MVP. |
| Error Handling | 5/10 | 404s handled. No global exception handler, no diagnostics on errors, incomplete input validation. |
| **Overall** | **7/10** | Solid implementation with correct Cosmos DB fundamentals. Skills clearly helped (materialized views, denormalization, composite indexes, enum serialization all applied). Main gaps are production hardening and the O(N) rank lookup. |

## Next Steps
1. Consider creating `pattern-efficient-ranking.md` rule for rank computation patterns
2. Consider creating `sdk-etag-concurrency.md` rule for optimistic concurrency
3. Update `query-pagination.md` to explicitly warn against OFFSET/LIMIT anti-pattern
4. Run iteration-002-dotnet WITH explicit focus on production hardening rules to measure improvement
5. Test with Java or Python to compare cross-language skill effectiveness
