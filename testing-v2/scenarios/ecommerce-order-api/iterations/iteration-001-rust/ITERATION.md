# iteration-001-rust - Rust Ecommerce Order Api

## Metadata
- **Date**: 2026-04-30
- **Language/SDK**: Rust
- **Agent**: GitHub Copilot (automated iteration)
- **Tester**: Automated CI
- **Run Type**: Normal run (skills loaded)

## Skills Verification

**Were skills loaded before building?** Yes (via issue prompt referencing AGENTS.md)

## Cosmos DB Patterns Detected

| Pattern | Status | Related Rule |
|---------|--------|--------------|
| Singleton CosmosClient | Detected | `sdk-singleton-client` |
| Direct connection mode | Not detected | `sdk-connection-mode` |
| Gateway connection mode | Detected | `sdk-connection-mode` |
| Partition key configured | Detected | `partition-high-cardinality` |
| Bulk operations | Not detected | `sdk-bulk-operations` |
| ETag optimistic concurrency | Not detected | `sdk-etag-concurrency` |
| Point reads (by ID + partition key) | Detected | `query-avoid-scans` |
| Cross-partition queries | Detected | `query-avoid-cross-partition` |
| Custom indexing policy | Not detected | `index-exclude-unused` |
| Throughput configuration | Not detected | `throughput-provision-rus` |
| Change feed usage | Not detected | `pattern-change-feed` |
| Diagnostics/logging | Not detected | `sdk-diagnostics` |

## Test Results

**Pass rate: 93.4%** (85/91 tests passed (93.4%))

| Status | Count |
|--------|-------|
| Passed | 85 |
| Failed | 5 |
| Errors | 0 |
| Skipped | 1 |

### Failures

- **testing-v2.scenarios.ecommerce-order-api.tests.test_api_contract.TestUpdateOrderStatus::test_update_status_reflects_new_status**
  > assert 409 == 200
 +  where 409 = <Response [409]>.status_code

- **testing-v2.scenarios.ecommerce-order-api.tests.test_api_contract.TestUpdateOrderStatus::test_updated_status_persists_on_get**
  > AssertionError: After PATCH, GET should return updated status 'delivered', got 'pending'
assert 'pending' == 'delivered'
  
  - delivered
  + pending

- **testing-v2.scenarios.ecommerce-order-api.tests.test_cosmos_infrastructure.TestIndexingPolicies::test_has_composite_indexes_for_order_queries**
  > AssertionError: No container has composite indexes defined. E-commerce queries like 'orders by status sorted by date' need composite indexes on (status, createdAt) to avoid expensive sorts. Without th

- **testing-v2.scenarios.ecommerce-order-api.tests.test_cosmos_infrastructure.TestDocumentStructure::test_documents_have_type_discriminator**
  > Failed: No documents have a type discriminator field. When a container holds multiple entity types (or for future extensibility), include a 'type' field (e.g., 'order', 'customer') to distinguish them

- **testing-v2.scenarios.ecommerce-order-api.tests.test_cosmos_infrastructure.TestDocumentStructure::test_documents_have_schema_version**
  > Failed: No documents have a schema version field. Include a 'schemaVersion' field in documents so future schema changes can be handled without rewriting all existing data. (Rule: model-schema-versioni

## Source Files

Source code archived in `source-code.zip` (1079 files).

## Build & Startup Signals

- **Build**: PASS
- **Startup**: PASS

## Results by Category

| Category | Passed | Failed | Skipped |
|----------|--------|--------|---------|
| api_contract | 39 | 2 | 0 |
| build_startup | 2 | 0 | 0 |
| cosmos_infrastructure | 11 | 3 | 1 |
| data_integrity | 5 | 0 | 0 |
| robustness | 30 | 0 | 0 |

## Score Summary

| Category | Score | Notes |
|----------|-------|-------|
| API Conformance | 8/10 | 93.4% pass rate; 3 infrastructure failures |
| **Overall** | **8/10** | **85/91 tests passed (93.4%)** |
