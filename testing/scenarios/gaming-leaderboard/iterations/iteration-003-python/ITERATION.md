# Iteration 003 - Python Gaming Leaderboard

## Metadata
- **Date**: 2026-03-02
- **Language/SDK**: Python 3.12 / azure-cosmos 4.7.0 / FastAPI 0.115.0
- **Skill Version**: Pre-release (testing-iterations-03-02-26 branch)
- **Agent**: GitHub Copilot (Claude Opus 4.5)
- **Tester**: Automated (agent-driven iteration)

## ⚠️ Skills Verification

**Were skills loaded before building?** ✅ Yes

**How were skills loaded?**
- [x] Read `skills/cosmosdb-best-practices/AGENTS.md` directly
- [ ] Skills auto-loaded from workspace
- [ ] Explicit instruction to follow skills
- [ ] Other

**Verification question asked?** Agent read all 67 rules from AGENTS.md before generating any code, covering data modeling, partition keys, query optimization, SDK practices, indexing, throughput, global distribution, monitoring, and design patterns (including ranking and materialized views specifically relevant to this scenario).

## Prompt Used

```
Build a gaming leaderboard API using Python (FastAPI) and Azure Cosmos DB.

Requirements:
1. Submit scores for players
2. Get global top 100 leaderboard (weekly and all-time)
3. Get regional top 100 by country
4. Get a player's rank with ±10 nearby players
5. Get player profile with aggregated stats
6. Support for multiple game modes

Data should include: player profiles, individual scores, leaderboard rankings.
Scale target: 1M players, 10K concurrent score submissions.
```

## What the Agent Produced

### Data Model
- ✅ Three-container design: players, scores, leaderboards (materialized view)
- ✅ Denormalized player info (displayName, country) into leaderboard entries (Rule 1.2)
- ✅ Type discriminators on all documents (Rule 1.11)
- ✅ Schema versioning field on all documents (Rule 1.10)
- ✅ Synthetic partition key for leaderboards: `{scope}_{period}` (Rule 2.7)
- ✅ Week-key format (ISO week: "2026-W10") for weekly score bucketing

### Container Configuration
- ✅ Partition key = `/id` for players (point reads) (Rule 2.4)
- ✅ Partition key = `/playerId` for scores (per-player queries) (Rule 2.6)
- ✅ Partition key = `/leaderboardKey` for leaderboards (single-partition ranking queries) (Rule 2.6)
- ✅ Custom indexing policies excluding unused paths on all containers (Rule 5.2)
- ✅ Composite index on leaderboards: (bestScore DESC, lastUpdatedAt ASC) (Rule 5.1)

### Repository Layer
- ✅ Single-partition queries for all leaderboard reads (Rule 3.1)
- ✅ Parameterized queries throughout (Rule 3.5)
- ✅ Field projections on all queries (Rule 3.6)
- ✅ COUNT-based ranking (Rule 9.2) — not O(N) scan
- ✅ Point reads for player profiles (~1 RU) (Rule 3.1)
- ✅ Nearby players ±10 using score-based range queries
- ⚠️ Used OFFSET/LIMIT in some queries for bounded result sets — acceptable for small limits (≤100) but noted as potential concern per Rule 3.4

### SDK Usage
- ✅ Singleton client pattern (Rule 4.17)
- ✅ Gateway connection mode (Python SDK default, correct for emulator) (Rule 4.6)
- ✅ SSL verification disabled for emulator only (Rule 4.6)
- ✅ `load_dotenv(override=True)` (Rule 4.12)
- ✅ ETag-based optimistic concurrency with retry loop for player stat updates (Rule 4.7)
- ✅ RU consumption logging via response headers (Rule 8.4)

## Build Status
- **Initial Build**: ❌ Failed (3 issues)
  1. `initialize_database()` returned tuple, `main.py` expected dict → fixed return type
  2. Python SDK ETag API: used `match_condition="IfMatch"` (string), but SDK requires `MatchConditions.IfNotModified` enum from `azure.core` → fixed import
  3. Pydantic response model field mismatches (model fields didn't match constructor args) → fixed models
- **After Fixes**: ✅ Succeeded
- **Runtime Test**: ✅ All 5 endpoints tested and verified

## Runtime Test Results

### Tests Passed ✅
| Endpoint | Method | Result |
|----------|--------|--------|
| `/health` | GET | 200 OK, `{"status": "ok"}` |
| `/scores` | POST | 201 Created, score + 4 leaderboard entries updated |
| `/leaderboards/global?period=all-time` | GET | 5 players in correct rank order |
| `/leaderboards/global?period=weekly` | GET | 5 players, weekly partition key |
| `/leaderboards/regional/US?period=all-time` | GET | 3 US players in correct order |
| `/players/{id}` | GET | Full profile with aggregated stats |
| `/players/{id}/rank?leaderboard=global&period=all-time` | GET | Correct COUNT-based rank + nearby |
| `/players/nonexistent` | GET | 404 Not Found |
| `/players/nonexistent/rank` | GET | 404 Not Found |
| Score update (higher score) | POST | bestScore updated, leaderboard re-ranked correctly |

### Tests Failed ❌
None — all endpoints working correctly.

### Bugs Found 🐛
1. **Python SDK ETag API incorrect in skill rules**: The existing Rule 4.7 Python example used `match_condition=etag` (passing the ETag string), but the Python SDK requires `match_condition=MatchConditions.IfNotModified` from `azure.core`. The string approach raises `TypeError: Invalid match condition`. **FIXED in this iteration** — updated `sdk-etag-concurrency.md` with correct Python example and warning.

## Gaps Identified

### Critical Gaps (functionality issues)
1. **Python SDK ETag API incorrect**: The skill's Python example for ETag concurrency was wrong — used a string value instead of the `MatchConditions` enum. This caused a runtime `TypeError`. **Fixed during this iteration.**

### Best Practice Gaps (suboptimal but works)
1. **OFFSET/LIMIT usage**: Some queries use `OFFSET 0 LIMIT @limit` for bounded results. While acceptable for small limits (≤100, single-partition), Rule 3.4 warns against OFFSET/LIMIT for pagination. The usage here is bounded and always within a single partition, so impact is minimal.
2. **No production throughput configuration**: Containers created without explicit throughput settings (defaults to 400 RU/s). For production, should use autoscale (Rule 6.1) or set appropriate manual throughput.

### Knowledge Gaps (agent didn't know/mention)
1. **No SDK diagnostics logging**: Should log `CosmosDiagnostics` for slow queries (Rule 4.5). Python SDK provides response headers but not diagnostics object as rich as .NET/Java.
2. **No error response model**: 404/409/500 errors return FastAPI defaults rather than structured error responses.

## Recommendations for Skill Improvements

### High Priority
1. ✅ **DONE**: Fixed Python ETag example in `sdk-etag-concurrency.md` — added `MatchConditions.IfNotModified` enum usage with explicit warning about the string pitfall.

### Medium Priority
1. Consider adding a Python-specific rule or section for `azure.core.MatchConditions` enum values and their Cosmos DB use cases.
2. Add guidance for Python SDK diagnostics/logging patterns (less feature-rich than .NET/Java SDKs).

### Low Priority
1. Add guidance for FastAPI-specific patterns (lifespan events for Cosmos client initialization).

## Score Summary

| Category | Score | Notes |
|----------|-------|-------|
| Data Model | 9/10 | Excellent: denormalization, type discriminators, schema versioning, separate containers |
| Partition Key | 10/10 | Perfect: synthetic keys for leaderboards, aligned with query patterns |
| Indexing | 9/10 | Composite indexes, excluded unused paths. Minor: could further optimize |
| SDK Usage | 8/10 | ETag concurrency with retry, singleton client, SSL config. Deduction: initial ETag API was wrong (skill bug), missing diagnostics |
| Query Patterns | 9/10 | COUNT-based ranking, parameterized queries, projections, single-partition reads. Minor OFFSET/LIMIT usage |
| **Overall** | **9/10** | Significant improvement over iterations 001 (7/10) and 002 (7/10). Skills guided correct patterns from the start. Only critical issue was a bug in the skill's own Python ETag example, now fixed. |

## Next Steps
1. ✅ Fixed `sdk-etag-concurrency.md` Python example — recompiled AGENTS.md
2. Consider adding Python SDK diagnostics guidance
3. Test with async Python SDK (`aio` module) in a future iteration
4. Add load testing to validate throughput at scale (Rule 6.1 autoscale)
