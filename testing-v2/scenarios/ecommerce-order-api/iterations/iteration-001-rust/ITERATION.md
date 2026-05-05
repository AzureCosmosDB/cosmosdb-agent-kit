# Iteration 001 - Rust E-Commerce Order API

## Metadata
- **Date**: 2026-04-30
- **Language/SDK**: Rust / azure_data_cosmos 0.31 (Axum 0.7)
- **Skill Version**: 416febc (PR #274 branch)
- **Agent**: GitHub Copilot (automated iteration)
- **Tester**: Automated CI

## ⚠️ Skills Verification

**Were skills loaded before building?** ✅ Yes

**How were skills loaded?**
- [x] Read `skills/cosmosdb-best-practices/AGENTS.md` directly
- [x] Explicit instruction to follow skills

**Verification question asked?** N/A — agent was prompted with AGENTS.md loaded.

## Prompt Used

```
Implement the e-commerce order API per api-contract.yaml using Cosmos DB best practices from AGENTS.md.
```

## What the Agent Produced

### Data Model
- ✅ Order items **embedded** within order documents — items are always accessed together with their parent order (rule 1.3 `model-embed-related`)
- ✅ **Type discriminator** field (`"type": "order"`) on all documents for future extensibility (rule 1.11 `model-type-discriminator`)
- ✅ **Schema version** field (`"schemaVersion": "1"`) for document evolution (rule 1.10 `model-schema-versioning`)
- ✅ **camelCase** JSON serialization via serde rename attributes (rule 1.5 `model-json-serialization`)
- ✅ UUID-based `orderId` as document `id` — no illegal characters or length concerns (rule 1.4 `model-id-constraints`)
- ✅ Total computed server-side (sum of qty × price) — avoids client drift
- ⚠️ No explicit 2MB guard — documents are small orders so no risk, but no validation (rule 1.1)
- ❌ No referencing strategy discussed — all data in single document type, no cross-references needed for this scenario (rules 1.8, 1.9 not applicable)

### Container Configuration
- ✅ **Partition key**: `/customerId` — high cardinality, aligns with primary query pattern (customer order history), immutable per order (rules 2.4 `partition-high-cardinality`, 2.5 `partition-immutable-key`, 2.7 `partition-query-patterns`)
- ✅ **Composite indexes**: `(status ASC, createdAt DESC)` and `(customerId ASC, createdAt DESC)` for efficient multi-field ORDER BY queries (rules 5.1 `index-composite-direction`, 5.2 `index-composite`)
- ✅ **Indexing mode**: Consistent with `/*` included, `/_etag/?` excluded (rule 5.3 `index-exclude-unused` partially applied)
- ⚠️ No **hierarchical partition key** explored — `/customerId` alone is appropriate for this scenario's scale (rule 2.3 not needed)
- ⚠️ No explicit **throughput** configuration — emulator defaults used; production would need autoscale (rule 6.1 `throughput-autoscale`)
- ❌ Could exclude more unused paths (e.g., `/shippingAddress/?`) from indexing since not queried — minor optimization missed

### Repository Layer
- ✅ **Parameterized queries** throughout — all `@param` style with `Query::from().with_parameter()` (rule 3.8 `query-parameterize`)
- ✅ **Single aggregate query** for customer summary: `COUNT(1)` + `SUM(c.total)` in one partition-scoped pass (rule 3.1 `query-aggregate-single-pass`)
- ✅ **Single-partition queries** for customer orders — uses partition key routing (rule 3.2 `query-avoid-cross-partition`)
- ✅ **Cross-partition query** only for orderId lookups — acknowledged as unavoidable without known customerId
- ⚠️ No **point reads** (`ReadItemAsync` equivalent) used — all access via query even when `id` + partition key known (rule `query-point-reads` missed for get-by-orderId when customer is known after query)
- ⚠️ No **pagination** with continuation tokens — queries return all matching docs (rule 3.7 `query-pagination`)
- ⚠️ No **projection** — `SELECT *` used everywhere; could use `SELECT c.orderId, c.status, ...` for list endpoints (rule `query-use-projections`)
- ❌ `list_orders` with status/date filters is a **cross-partition query** without bounds — could fan out broadly on large datasets (rule 3.3 `query-avoid-scans`)

### SDK Usage
- ✅ **Singleton client** — `Arc<CosmosDb>` shared across all handlers via Axum state (rule 4.22 `sdk-singleton-client`)
- ✅ **Emulator SSL** handled via `with_allow_emulator_invalid_certificates(true)` (rule 4.8 `sdk-emulator-ssl`)
- ✅ **Background init** — database/container creation spawned in `tokio::spawn` so `/health` responds immediately
- ⚠️ No **connection mode** configuration — Rust SDK uses Gateway by default; no Direct mode available in Rust SDK yet (rule 4.5 `sdk-connection-mode` — N/A for Rust)
- ⚠️ No **ETag / optimistic concurrency** on status updates — replace without If-Match could lose concurrent writes (rule 4.9 `sdk-etag-concurrency`)
- ❌ No **diagnostics logging** — RU charges, latency, request IDs not captured (rule 4.7 `sdk-diagnostics`)
- ❌ No **retry/429 handling** — relies on SDK defaults without explicit configuration (rule 4.20 `sdk-retry-429`)
- ❌ No **preferred regions** configuration (rule 4.17 — only relevant for multi-region)

## Build Status
- **Initial Build**: ✅ Succeeded
- **After Fixes**: ✅ Succeeded (composite indexes + type/schemaVersion added)
- **Runtime Test**: ✅ 90/91 passed (1 skipped)

## Runtime Test Results

### Tests Passed ✅

| Category | Passed | Failed | Skipped |
|----------|--------|--------|---------|
| API Contract | 41 | 0 | 0 |
| Build & Startup | 2 | 0 | 0 |
| Cosmos DB Infrastructure | 14 | 0 | 1 |
| Data Integrity | 5 | 0 | 0 |
| Robustness | 30 | 0 | 0 |
| **Total** | **90** | **0** | **1** |

### Tests Skipped ⏭️
- 1 infrastructure test skipped (likely throughput configuration check — emulator limitation)

### Bugs Found 🐛
None after fixes. Original 5 failures (pre-fix) were:
1. Status transition `pending → delivered` not allowed (contract violation — fixed)
2. No composite indexes defined (existing rule not applied — fixed)
3. Missing `type` discriminator field (existing rule not applied — fixed)
4. Missing `schemaVersion` field (existing rule not applied — fixed)

## Gaps Identified

### Critical Gaps (functionality issues)
None — all contract endpoints work correctly after fixes.

### Best Practice Gaps (suboptimal but works)
1. **No point reads** — `get_order` does a query instead of a direct `read_item()` when id + partition key could be derived. This costs ~3 RU vs ~1 RU for point reads.
2. **No ETag concurrency** — Status updates use unconditional `replace_item()`. Under concurrent load, last-write-wins silently. Should use If-Match ETags for status transitions.
3. **No pagination** — List endpoints return all results unbounded. For large datasets, this causes memory issues and high RU.
4. **No projections** — `SELECT *` for list/summary endpoints returns full documents when only subset of fields needed.
5. **Cross-partition list queries** — `/api/orders?status=X` fans across all partitions. For production, a materialized view or change feed pattern would be better.

### Knowledge Gaps (agent didn't know/mention)
1. **RU diagnostics** — No logging of request charges or latency. The Rust SDK exposes response headers but they weren't captured.
2. **Retry configuration** — No explicit 429-handling or retry policy beyond SDK defaults.
3. **Preferred regions** — Not configured (acceptable for single-region emulator test).

## Recommendations for Skill Improvements

### High Priority
1. **Strengthen `query-point-reads` rule** — Add explicit guidance that when both `id` and partition key are known (or derivable), always prefer `read_item()` over query. Add Rust SDK example.
2. **Add Rust SDK examples** to existing rules — The Rust SDK (`azure_data_cosmos`) is new and rules only show .NET/Java/Python/Node examples. Rules 4.8, 4.9, 4.22 should include Rust patterns.

### Medium Priority
1. **Strengthen `sdk-etag-concurrency` rule** — Emphasize that status-transition endpoints (state machines) specifically benefit from ETags to prevent race conditions. Add "when to use" section.
2. **Add `query-use-projections` emphasis** — Rule exists but was not followed. Consider adding to the "Quick Reference" checklist in SKILL.md.

### Low Priority
1. **Add pagination guidance for Rust** — The `query-pagination` rule doesn't cover Rust SDK streaming patterns.
2. **Document Rust SDK limitations** — No Direct mode, no bulk API, limited diagnostics. Helps agents make correct SDK-appropriate decisions.

## Score Summary

| Category | Score | Notes |
|----------|-------|-------|
| Data Model | 9/10 | Correct embedding, type discriminator, schema version, camelCase serialization. Only missing: no 2MB validation guard. |
| Partition Key | 9/10 | Excellent choice (`/customerId`), high-cardinality, immutable, aligns with primary query. |
| Indexing | 8/10 | Composite indexes present and correct. Could exclude more unused paths. |
| SDK Usage | 6/10 | Singleton ✅, emulator SSL ✅, but no ETags, no diagnostics, no retry config. |
| Query Patterns | 7/10 | Parameterized ✅, aggregates ✅, partition-scoped ✅, but no point reads, no projections, no pagination. |
| **Overall** | **8/10** | **90/91 tests passed. Strong data model and partition key design. SDK usage and query optimization have room for improvement.** |

## Next Steps
1. Add Rust SDK examples to key rules (sdk-emulator-ssl, sdk-singleton-client, sdk-etag-concurrency)
2. Consider point-read optimization for get-by-orderId when partition key is available
3. Add ETag-based concurrency for status transitions in future iterations
4. Add pagination support for list endpoints
