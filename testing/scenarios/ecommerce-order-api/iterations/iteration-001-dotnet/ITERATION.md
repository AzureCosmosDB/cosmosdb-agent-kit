# Iteration 001 - .NET E-Commerce Order API

## Metadata
- **Date**: 2026-01-27
- **Language/SDK**: .NET 8 / Microsoft.Azure.Cosmos 3.57.0
- **Skill Version**: Pre-release (before testing framework)
- **Agent**: GitHub Copilot (Claude Opus 4.5)
- **Tester**: Automated test run

## ⚠️ Skills Verification

**Were skills loaded before building?** ❌ **NO - BASELINE TEST**

**How were skills loaded?** Skills were NOT loaded. This iteration tested the agent's baseline Cosmos DB knowledge without the skill kit.

> **Important**: This iteration does NOT test the skill kit effectiveness. 
> It establishes a baseline of what the agent produces WITHOUT skills.
> Issues found here should be compared against a WITH-SKILLS iteration.

## Prompt Used

```
I need to build a .NET 8 Web API for an e-commerce order management system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Customers can place orders containing multiple items
2. Customers can view their order history and specific order details
3. Admins can query orders by status (pending, shipped, delivered, cancelled)
4. Admins can query orders by date range
5. Orders can have their status updated

Expected scale:
- ~100,000 customers
- ~1 million orders per year  
- 3-5 items per order on average

Please create:
1. The data model with appropriate Cosmos DB design
2. The Cosmos DB container configuration
3. A repository layer for data access
4. REST API controllers with the required endpoints

Use best practices for Cosmos DB throughout.
```

## What the Agent Produced

### Data Model
- ✅ Order entity with embedded OrderItems (correct denormalization)
- ✅ Type discriminator field for future extensibility
- ✅ CalculateTotals method for derived values
- ⚠️ No explicit mention of document size considerations

### Container Configuration
- ✅ Partition key: `/customerId` - appropriate for customer order queries
- ✅ Composite indexes for status+date and customer+date queries
- ✅ Consistent indexing mode
- ❌ Did NOT configure autoscale throughput (used defaults)
- ❌ No TTL configuration discussed (though not required for this scenario)

### Repository Layer
- ✅ Point reads with partition key (efficient 1 RU reads)
- ✅ Parameterized queries (prevents injection, enables query plan caching)
- ✅ Single-partition queries for customer order history
- ⚠️ Cross-partition queries for admin endpoints (noted as concern but no mitigation)
- ❌ No pagination implemented
- ❌ No RU consumption logging/diagnostics

### SDK Usage
- ✅ Singleton CosmosClient (correct pattern)
- ✅ Direct connection mode
- ⚠️ Missing: Preferred regions configuration
- ❌ Missing: Retry policy configuration
- ❌ Missing: Bulk operations for high-volume scenarios

## Gaps Identified

### Critical Gaps (functionality issues)
1. **Missing Newtonsoft.Json dependency** - Build failed initially because Cosmos SDK requires explicit reference
2. **Missing Collection<> using directive** - Build error for composite index configuration
3. **🐛 Enum serialization mismatch** - Status queries fail because enums stored as integers but queried as strings

### Best Practice Gaps (not blocking but suboptimal)
1. **No pagination** - GetOrdersByStatus and GetOrdersByDateRange return all results
2. **No diagnostics logging** - No RU consumption tracking
3. **Cross-partition queries without guidance** - Admin queries fan out to all partitions
4. **No retry configuration** - Relying on SDK defaults
5. **No preferred regions** - Missing multi-region configuration

### Knowledge Gaps (agent didn't know/mention)
1. Did not suggest Change Feed for materializing admin views
2. Did not discuss autoscale vs manual throughput
3. Did not mention bulk executor for high-volume ingestion
4. No discussion of consistency levels

## Recommendations for Skill Improvements

### High Priority
1. **NEW**: Add rule for enum serialization consistency between Cosmos SDK and API layer
2. Add rule: "Always include pagination for queries that may return large result sets"
3. Add rule: "Log CosmosDiagnostics for query operations to track RU consumption"
4. Add rule: "For cross-partition queries at scale, consider Change Feed with materialized views"

### Medium Priority
5. Add rule: "Configure preferred regions for multi-region accounts"
6. Add rule: "Implement retry policies with exponential backoff for 429s"
7. Add rule: "Consider autoscale throughput for variable workloads"

### Low Priority
7. Expand model-embed-related.md with size limit considerations
8. Add examples for pagination patterns
9. Add diagnostics logging examples

## Files Created

```
iteration-001-dotnet/
├── ECommerceOrderApi.csproj
├── Program.cs
├── appsettings.json
├── Controllers/
│   └── OrdersController.cs
├── Data/
│   ├── CosmosDbSettings.cs
│   ├── CosmosDbService.cs
│   └── OrderRepository.cs
└── Models/
    ├── Order.cs
    └── OrderDtos.cs
```

## Build Status
- **Initial Build**: ❌ Failed (missing dependencies)
- **After Fixes**: ✅ Succeeded
- **Runtime Test**: ✅ Performed

## Runtime Test Results

### Tests Passed ✅
| Endpoint | Method | Result |
|----------|--------|--------|
| `/api/orders` | POST | 201 Created - Order created with calculated totals |
| `/api/orders/customer/{id}` | GET | 200 OK - Returns customer's orders |
| `/api/orders/{id}?customerId=x` | GET | 200 OK - Point read works |
| `/api/orders/{id}/status` | PATCH | 200 OK - Status updated, dates set |

### Tests Failed ❌
| Endpoint | Method | Issue |
|----------|--------|-------|
| `/api/orders/status/{status}` | GET | Returns `[]` even with matching data |
| `/api/orders/daterange` | GET | Not tested (likely same issue) |

### Bug Found: Enum Serialization Mismatch 🐛

**Root Cause**: The Cosmos SDK's default serializer stores enums as **integers** (0, 1, 2, 3), but:
- The `Order` model uses `[JsonConverter(typeof(JsonStringEnumConverter))]` for API responses
- The query uses `status.ToString()` which produces "Shipped"
- But Cosmos DB contains `"status": 1` (integer)

**Evidence**:
```
# Customer orders query returns data with "Shipped" status
$orders[0].status = "Shipped"  # API deserializes int → string

# But status query returns empty
GET /api/orders/status/Shipped → []
# Query: WHERE c.status = "Shipped" (string)
# Data: { "status": 1 } (integer stored by Cosmos SDK)
```

**Fix Options**:
1. Configure Cosmos SDK to use System.Text.Json with enum string serialization
2. Change query to use integer: `.WithParameter("@status", (int)status)`
3. Use a custom serializer that matches both read/write

**This is a common mistake** - should be added as a skill rule!

## Score Summary

| Category | Score | Notes |
|----------|-------|-------|
| Data Model | 8/10 | Good embedding, missing size discussion |
| Partition Key | 9/10 | Correct choice, well-justified |
| Indexing | 8/10 | Composite indexes present, no spatial/vector |
| SDK Usage | 5/10 | Singleton correct, but serialization bug breaks queries |
| Query Patterns | 5/10 | Works for some, but status queries broken, no pagination |
| **Overall** | **6/10** | Functional for basic CRUD, but admin queries broken |

## Next Steps
1. Fix enum serialization issue (use consistent serializer or query with integers)
2. Add new skill rule about serialization consistency
3. Run iteration 002 with updated skills addressing identified gaps
