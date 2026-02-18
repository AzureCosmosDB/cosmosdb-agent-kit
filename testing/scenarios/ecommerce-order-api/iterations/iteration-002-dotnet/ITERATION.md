# Iteration 002 - .NET (WITH Skills)

**Date**: January 28, 2026  
**Agent**: GitHub Copilot (Claude Opus 4.5)  
**Skills Loaded**: ✅ YES - Read `skills/cosmosdb-best-practices/AGENTS.md` completely before building

## Skills Verification

- [x] Read AGENTS.md before starting implementation
- [x] Applied rules during implementation
- **Verification question**: "What are the Cosmos DB SDK best practices for connection mode?"
  - **Answer given**: Direct mode and singleton client ✅

## Summary

This iteration was run WITH the Cosmos DB best practices skill kit loaded. The agent read all 52+ rules from AGENTS.md before building the application and applied them throughout the implementation.

**Key improvement over iteration-001**: The enum serialization bug (where status queries returned empty results) was **prevented** by applying Rule 4.10 - Use Consistent Enum Serialization.

## Rules Applied

| Rule | Description | Applied |
|------|-------------|---------|
| 1.1 | Embed Related Data Retrieved Together | ✅ OrderItems embedded in Order |
| 1.4 | Denormalize for Read-Heavy Workloads | ✅ CustomerName/Email in Order |
| 1.5 | Version Your Document Schemas | ✅ SchemaVersion property |
| 1.6 | Use Type Discriminators | ✅ Type = "order" |
| 2.1 | Choose High-Cardinality Partition Keys | ✅ customerId |
| 2.4 | Align Partition Key with Query Patterns | ✅ Customer queries are single-partition |
| 3.1 | Minimize Cross-Partition Queries | ✅ Customer queries use partition key |
| 3.2 | Project Only Needed Fields | ✅ Admin queries return OrderSummary |
| 3.3 | Use Continuation Tokens | ✅ PagedResult with ContinuationToken |
| 3.5 | Use Parameterized Queries | ✅ All queries parameterized |
| 4.1 | Reuse CosmosClient as Singleton | ✅ Registered as Singleton in DI |
| 4.2 | Use Async APIs | ✅ All methods async |
| 4.3 | Handle 429 Errors with Retry | ✅ MaxRetryAttemptsOnRateLimitedRequests = 9 |
| 4.4 | Use Direct Connection Mode | ✅ ConnectionMode.Direct |
| 4.6 | Log Diagnostics | ✅ RequestCharge logged |
| **4.10** | **Use Consistent Enum Serialization** | ✅ **JsonStringEnumConverter configured** |
| 5.1 | Exclude Unused Index Paths | ✅ _etag excluded |
| 5.2 | Use Composite Indexes | ✅ status+createdAt, customerId+createdAt |

## Test Results

All 6 tests PASSED:

```
=== E-Commerce Order API Test ===

1. Creating order...
   Created order: a65ef13c-77cc-46b1-a632-08d87e24d117
   Status: Pending
   Total: 118.77

2. Getting order by ID...
   Found order with 2 items

3. Getting orders by customer...
   Found 3 orders (single-partition query)

4. Updating order status to Shipped...
   Updated status: Shipped

5. [CRITICAL TEST] Querying orders by status 'Shipped'...
   Found 1 order with status 'Shipped'
   SUCCESS: Enum serialization working correctly!

6. Querying orders by date range...
   Found 3 orders in date range
```

### All Status Queries Working:

```
[PASS] Status 'Pending': Found 3 orders
[PASS] Status 'Confirmed': Found 1 orders
[PASS] Status 'Shipped': Found 2 orders
[PASS] Status 'Delivered': Found 1 orders
[PASS] Status 'Cancelled': Found 1 orders
```

## Bug Fix Verified

**Iteration 001 Bug**: Status queries returned empty results because:
- Cosmos SDK stored enums as integers (e.g., `{"status": 1}`)
- Queries searched for strings (e.g., `WHERE c.status = "Shipped"`)

**Iteration 002 Fix**: Applied Rule 4.10 - configured `JsonStringEnumConverter`:
```csharp
var jsonOptions = new JsonSerializerOptions
{
    Converters = { new JsonStringEnumConverter() }
};
var clientOptions = new CosmosClientOptions
{
    Serializer = new CosmosSystemTextJsonSerializer(jsonOptions)
};
```

Now Cosmos stores: `{"status": "Shipped"}` and queries find it correctly.

## Score

| Criteria | Score | Notes |
|----------|-------|-------|
| Compiles and runs | 10/10 | ✅ Builds and runs without errors |
| Data model best practices | 9/10 | ✅ Embedded items, denormalized customer info |
| Partition key design | 9/10 | ✅ customerId (high cardinality, aligns with queries) |
| SDK usage | 10/10 | ✅ Singleton, Direct mode, async, retries, **enum serialization** |
| Query optimization | 9/10 | ✅ Single-partition where possible, projections, pagination |
| Indexing | 8/10 | ✅ Composite indexes for ORDER BY |
| Code quality | 9/10 | ✅ Clean architecture, good separation |

**Overall: 9.1/10** (vs 6/10 in iteration-001 baseline)

## Potential Improvements for Next Iteration

1. **Cross-partition queries**: Status/date queries are necessarily cross-partition since customerId is the partition key. Consider:
   - Maintaining a separate "orders-by-status" container for admin queries
   - Using Change Feed to sync data for different access patterns

2. **Hierarchical Partition Keys**: Could use `/customerId/year` for better time-based partitioning

3. **Availability Strategy (Rule 4.7)**: Not implemented - could add hedging for multi-region deployments

4. **Circuit Breaker (Rule 4.8)**: Not enabled - could add for production resilience

## Files

- `ECommerceOrderApi/` - Complete .NET 8 Web API
- `test-api.ps1` - Basic API test script
- `test-all-statuses.ps1` - Comprehensive status query tests
