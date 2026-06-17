# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Best practices for Azure Cosmos DB query optimization: point reads, projections, pagination, parameterization, filter ordering, cross-partition query avoidance, and analytical query detection.

---

## Table of Contents

1. [Query Optimization](#1-query-optimization) — **HIGH**
   - 1.1 [Compute min/max/avg with one scoped aggregate query](#11-compute-min-max-avg-with-one-scoped-aggregate-query)
   - 1.2 [Minimize Cross-Partition Queries](#12-minimize-cross-partition-queries)
   - 1.3 [Avoid Full Container Scans](#13-avoid-full-container-scans)
   - 1.4 [Use DISTINCT keyword to eliminate duplicate results efficiently](#14-use-distinct-keyword-to-eliminate-duplicate-results-efficiently)
   - 1.5 [Query "latest" documents with explicit ORDER BY and TOP 1](#15-query-latest-documents-with-explicit-order-by-and-top-1)
   - 1.6 [Detect and Redirect Analytical Queries Away from Transactional Containers](#16-detect-and-redirect-analytical-queries-away-from-transactional-containers)
   - 1.7 [Order Filters by Selectivity](#17-order-filters-by-selectivity)
   - 1.8 [Use Continuation Tokens for Pagination](#18-use-continuation-tokens-for-pagination)
   - 1.9 [Use Parameterized Queries](#19-use-parameterized-queries)
   - 1.10 [Use Point Reads Instead of Queries for Known ID and Partition Key](#110-use-point-reads-instead-of-queries-for-known-id-and-partition-key)
   - 1.11 [Parameterize TOP Values Safely](#111-parameterize-top-values-safely)
   - 1.12 [Project Only Needed Fields](#112-project-only-needed-fields)

---

## 1. Query Optimization

**Impact: HIGH**

### 1.1 Compute min/max/avg with one scoped aggregate query

**Impact: HIGH** (prevents incorrect stats from partial reads or mismatched filters)

## Compute min/max/avg with one scoped aggregate query

For endpoint statistics, compute `MIN`, `MAX`, and `AVG` from the same filtered dataset in a single Cosmos DB query whenever possible. Avoid mixing values from separate queries, partial pages, or different time windows, which produces mathematically inconsistent results.

**Incorrect (client-side aggregation over partial or inconsistent data):**

```java
// ❌ Reads only first page and computes stats from incomplete data
CosmosPagedIterable<JsonNode> page = container.queryItems(
    "SELECT * FROM c WHERE c.deviceId = @deviceId",
    new CosmosQueryRequestOptions(),
    JsonNode.class
);

List<JsonNode> docs = page.stream().limit(50).toList(); // arbitrary subset
double min = docs.stream().mapToDouble(d -> d.get("temperature").asDouble()).min().orElse(0);
double max = docs.stream().mapToDouble(d -> d.get("temperature").asDouble()).max().orElse(0);
double avg = docs.stream().mapToDouble(d -> d.get("temperature").asDouble()).average().orElse(0);
```

```python
# ❌ Different filters per metric cause inconsistent results
min_q = "SELECT VALUE MIN(c.humidity) FROM c WHERE c.deviceId = @id"
max_q = "SELECT VALUE MAX(c.humidity) FROM c WHERE c.deviceId = @id AND c.timestamp > @start"
avg_q = "SELECT VALUE AVG(c.humidity) FROM c WHERE c.deviceId = @id AND c.timestamp > @start"
```

**Correct (single-pass aggregate query with consistent filters):**

```java
// ✅ One query, one filter set, consistent aggregate outputs
String sql = """
    SELECT
      MIN(c.temperature) AS minTemp,
      MAX(c.temperature) AS maxTemp,
      AVG(c.temperature) AS avgTemp,
      MIN(c.humidity) AS minHumidity,
      MAX(c.humidity) AS maxHumidity,
      AVG(c.humidity) AS avgHumidity
    FROM c
    WHERE c.deviceId = @deviceId
      AND c.timestamp >= @start
      AND c.timestamp <= @end
    """;
```

```python
# ✅ Use one scoped aggregate query
query = """
SELECT
  MIN(c.value) AS minValue,
  MAX(c.value) AS maxValue,
  AVG(c.value) AS avgValue
FROM c
WHERE c.entityId = @id AND c.timestamp >= @start AND c.timestamp <= @end
"""
```

Use a partition key aligned with the aggregation scope (for example, per-entity/per-device stats) so the query stays efficient and predictable.

Reference: [Aggregate functions in Azure Cosmos DB for NoSQL](https://learn.microsoft.com/azure/cosmos-db/nosql/query/aggregate-functions) | [Query performance tips](https://learn.microsoft.com/azure/cosmos-db/nosql/performance-tips-query-sdk)

### 1.2 Minimize Cross-Partition Queries

**Impact: HIGH** (reduces RU by 5-100x)

## Minimize Cross-Partition Queries

Always include partition key in queries when possible. Cross-partition queries fan out to all partitions, consuming RU proportional to partition count.

**Incorrect (cross-partition fan-out):**

```csharp
// Missing partition key - scans ALL partitions
var query = new QueryDefinition("SELECT * FROM c WHERE c.status = @status")
    .WithParameter("@status", "active");

var iterator = container.GetItemQueryIterator<Order>(query);
// If you have 100 physical partitions, this runs 100 queries!
// RU cost = single partition cost × number of partitions
```

**Correct (single-partition query):**

```csharp
// Include partition key for single-partition query
var query = new QueryDefinition(
    "SELECT * FROM c WHERE c.customerId = @customerId AND c.status = @status")
    .WithParameter("@customerId", customerId)
    .WithParameter("@status", "active");

var iterator = container.GetItemQueryIterator<Order>(
    query,
    requestOptions: new QueryRequestOptions
    {
        PartitionKey = new PartitionKey(customerId)  // Single partition!
    });
// Runs against ONE partition only
// Dramatically lower RU and latency
```

```csharp
// When cross-partition is unavoidable, optimize parallelism
var query = new QueryDefinition("SELECT * FROM c WHERE c.status = @status")
    .WithParameter("@status", "active");

var options = new QueryRequestOptions
{
    MaxConcurrency = -1,  // Maximum parallelism
    MaxBufferedItemCount = 100,  // Buffer for smoother streaming
    MaxItemCount = 100  // Items per page
};

var iterator = container.GetItemQueryIterator<Order>(query, requestOptions: options);

// Stream results efficiently
await foreach (var item in iterator)
{
    ProcessItem(item);
}
```

```csharp
// Use GetItemLinqQueryable with partition key
var results = container.GetItemLinqQueryable<Order>(
    requestOptions: new QueryRequestOptions 
    { 
        PartitionKey = new PartitionKey(customerId) 
    })
    .Where(o => o.Status == "active")
    .ToFeedIterator();
```

### Spring Data Cosmos — `@Query` methods bypass partition key routing

Spring Data Cosmos **does not** auto-route partition keys for `@Query`-annotated repository methods. Derived query methods (e.g., `findByTypeAndLeaderboardKey()`) are automatically scoped to the partition key, but `@Query` methods are **not** — they silently perform cross-partition scans even when the repository entity has a partition key annotation. The bug is invisible: queries return HTTP 200 with silently incorrect data (results from all partitions mixed together) and inflated RU charges.

For every `@Query` method, you must either:
1. **Add the partition key to the WHERE clause** explicitly, or
2. **Use a derived query method** instead of `@Query`

**Incorrect — `@Query` without partition key filter (silent cross-partition scan):**

```java
// ❌ Missing partition key filter — performs cross-partition scan
// Returns entries from ALL partitions mixed together (wrong data, high RU)
@Query("SELECT * FROM c WHERE c.type = @type")
List<LeaderboardEntry> findByType(@Param("type") String type);
```

**Correct — explicit partition key in `@Query` WHERE clause:**

```java
// ✅ Partition key included in WHERE clause — single-partition query
@Query("SELECT * FROM c WHERE c.type = @type AND c.leaderboardKey = @leaderboardKey")
List<LeaderboardEntry> findByTypeAndLeaderboardKey(
    @Param("type") String type,
    @Param("leaderboardKey") String leaderboardKey);
```

**Correct — derived query method (auto-routes partition key):**

```java
// ✅ Derived query method — Spring Data auto-routes to the correct partition
List<LeaderboardEntry> findByTypeAndLeaderboardKey(String type, String leaderboardKey);
```

Strategies to avoid cross-partition:
1. Include partition key in WHERE clause
2. Denormalize data to colocate in same partition
3. Create secondary containers with different partition keys for different access patterns
4. In Spring Data Cosmos, prefer derived query methods over `@Query` for automatic partition key routing

Reference: [Query patterns](https://learn.microsoft.com/azure/cosmos-db/nosql/query/getting-started)

### 1.3 Avoid Full Container Scans

**Impact: HIGH** (prevents unbounded RU consumption)

## Avoid Full Container Scans

Ensure queries can use indexes to filter data. Queries that can't use indexes scan entire partitions or containers.

**Incorrect (queries that cause scans):**

```csharp
// Functions on properties prevent index usage
var query = "SELECT * FROM c WHERE LOWER(c.email) = 'john@example.com'";
// Full scan! Index stores 'John@example.com', not lowercased

// CONTAINS without index
var query2 = "SELECT * FROM c WHERE CONTAINS(c.description, 'azure')";
// No full-text index = full scan

// NOT operations
var query3 = "SELECT * FROM c WHERE NOT c.status = 'completed'";
// Often causes scan (depends on index configuration)

// Type checking
var query4 = "SELECT * FROM c WHERE IS_STRING(c.name)";
// Schema checking = full scan

// OR with different properties (in some cases)
var query5 = "SELECT * FROM c WHERE c.firstName = 'John' OR c.lastName = 'Smith'";
// May scan if indexes can't be combined efficiently
```

**Correct (index-friendly queries):**

```csharp
// Store normalized data to avoid functions
public class User
{
    public string Email { get; set; }
    public string EmailLower { get; set; }  // Pre-computed lowercase
}

var query = "SELECT * FROM c WHERE c.emailLower = 'john@example.com'";
// Uses index directly!

// Use range operators that leverage indexes
var query2 = @"
    SELECT * FROM c 
    WHERE c.createdAt >= @start 
    AND c.createdAt < @end";
// Range index on createdAt

// Prefer equality and range over NOT
var query3 = @"
    SELECT * FROM c 
    WHERE c.status IN ('pending', 'processing', 'shipped')";
// Instead of NOT = 'completed'

// Use StartsWith for prefix matching (uses index)
var query4 = "SELECT * FROM c WHERE STARTSWITH(c.name, 'John')";
// Uses range index on name

// Split OR into UNION if needed for large datasets
// Or ensure composite indexes cover both paths
```

```csharp
// Check if query uses index with query metrics
var options = new QueryRequestOptions
{
    PopulateIndexMetrics = true,
    PartitionKey = new PartitionKey(partitionKey)
};

var iterator = container.GetItemQueryIterator<Product>(query, requestOptions: options);
var response = await iterator.ReadNextAsync();

// Check index metrics in diagnostics
Console.WriteLine($"Index Hit: {response.Diagnostics}");
// Look for "IndexLookupTime" vs "ScanTime"
```

Reference: [Query optimization](https://learn.microsoft.com/azure/cosmos-db/nosql/query-metrics)

### 1.4 Use DISTINCT keyword to eliminate duplicate results efficiently

**Impact: MEDIUM** (reduces bandwidth usage and RU consumption by eliminating duplicate results at the query engine level)

## Use DISTINCT keyword to eliminate duplicate results efficiently

**Impact: MEDIUM (reduces unnecessary data transfer and RU consumption)**

Azure Cosmos DB supports `SELECT DISTINCT` to eliminate duplicate values during query execution. Prefer using `DISTINCT` rather than retrieving all results and removing duplicates in application code, which increases network bandwidth, client-side processing, and RU consumption.

`DISTINCT` is particularly useful when returning unique property values such as categories, tags, statuses, or identifiers.

**Incorrect (client-side deduplication):**

```csharp
// Query returns duplicate category values
var query = "SELECT c.category FROM c";

var iterator = container.GetItemQueryIterator<dynamic>(query);

var categories = new HashSet<string>();

while (iterator.HasMoreResults)
{
    var response = await iterator.ReadNextAsync();

    foreach (var item in response)
    {
        categories.Add(item.category.ToString());
    }
}

// Duplicate elimination happens after all results
// have already been transferred to the client
```

**Correct (using DISTINCT in Cosmos DB):**

```csharp
// Cosmos DB removes duplicates before returning results
var query = "SELECT DISTINCT c.category FROM c";

var iterator = container.GetItemQueryIterator<dynamic>(query);

while (iterator.HasMoreResults)
{
    var response = await iterator.ReadNextAsync();

    foreach (var item in response)
    {
        Console.WriteLine(item.category);
    }
}
```

**Correct (using DISTINCT VALUE for scalar results):**

```sql
SELECT DISTINCT VALUE c.category
FROM c
```

### Additional considerations

- `DISTINCT` queries rely on indexes for efficient execution; ensure projected fields are indexed.
- `DISTINCT` queries across partitions still perform a fan-out query; prefer partition-scoped queries whenever possible to reduce RU consumption.
- Use `DISTINCT VALUE` when returning a single scalar field to simplify the result shape.

References:
- https://learn.microsoft.com/azure/cosmos-db/nosql/query/keywords#distinct

### 1.5 Query "latest" documents with explicit ORDER BY and TOP 1

**Impact: HIGH** (prevents stale or nondeterministic "latest item" results)

## Query "latest" documents with explicit ORDER BY and TOP 1

When returning the latest item for an entity (latest reading, latest status, most recent event), always query with an explicit time field sort and `TOP 1`: `ORDER BY <timestampField> DESC`. Without explicit ordering, Cosmos DB does not guarantee result order and may return an older document.

**Incorrect (no deterministic ordering):**

```java
// ❌ No ORDER BY: can return an older document
String sql = "SELECT TOP 1 * FROM c WHERE c.deviceId = @deviceId";
SqlQuerySpec spec = new SqlQuerySpec(
    sql,
    List.of(new SqlParameter("@deviceId", deviceId))
);
```

```python
# ❌ Client picks "first" item from an unordered query
query = "SELECT * FROM c WHERE c.userId = @uid"
items = list(container.query_items(
    query=query,
    parameters=[{"name": "@uid", "value": user_id}],
    enable_cross_partition_query=True
))
latest = items[0] if items else None
```

**Correct (explicit timestamp sort + TOP 1):**

```java
// ✅ Deterministic latest item by timestamp
String sql = """
    SELECT TOP 1 * FROM c
    WHERE c.deviceId = @deviceId AND IS_DEFINED(c.timestamp)
    ORDER BY c.timestamp DESC
    """;
SqlQuerySpec spec = new SqlQuerySpec(
    sql,
    List.of(new SqlParameter("@deviceId", deviceId))
);
```

```python
# ✅ Deterministic latest item
query = """
SELECT TOP 1 * FROM c
WHERE c.userId = @uid AND IS_DEFINED(c.createdAt)
ORDER BY c.createdAt DESC
"""
items = list(container.query_items(
    query=query,
    parameters=[{"name": "@uid", "value": user_id}],
    enable_cross_partition_query=True
))
latest = items[0] if items else None
```

If the query can span partitions, define the needed index policy for your filter + sort pattern (for example, a composite index when required by your query shape).

Reference: [ORDER BY in Azure Cosmos DB for NoSQL](https://learn.microsoft.com/azure/cosmos-db/nosql/query/order-by) | [TOP keyword](https://learn.microsoft.com/azure/cosmos-db/nosql/query/keywords#top)

### 1.6 Detect and Redirect Analytical Queries Away from Transactional Containers

**Impact: HIGH** (prevents RU starvation, 429 throttling cascades, and query timeouts)

## Detect and Redirect Analytical Queries Away from Transactional Containers

**Impact: HIGH (prevents RU starvation, 429 throttling cascades, and query timeouts)**

Cosmos DB's transactional store is optimized for OLTP: point reads, targeted queries within a partition, and bounded result sets. Analytical patterns — COUNT/SUM/AVG across all partitions, GROUP BY over unbounded data, or full-container scans for reporting — consume massive RU, trigger sustained 429 throttling that starves transactional operations, and can exceed the query execution timeout.

Do not run large aggregations, unbounded GROUP BY, or full-container scans against transactional Cosmos DB containers. For analytical workloads, use Azure Synapse Link with analytical store, Change Feed materialized views, or dedicated reporting containers.

Single-partition aggregations scoped to a known partition key with bounded data are acceptable — the concern is unbounded cross-partition scans.

**Correct (enable analytical store and run aggregations via Synapse Link — zero RU impact on transactional store):**

```csharp
// ✅ Enable analytical store on the container
var containerProperties = new ContainerProperties
{
    Id = "orders",
    PartitionKeyPath = "/customerId",
    AnalyticalStoreTimeToLiveInSeconds = -1  // Enable analytical store
};

// ✅ Run aggregations via Synapse Link (no RU consumed on transactional store)
// In Synapse SQL or Spark:
// SELECT region, COUNT(*) as orderCount, SUM(total) as revenue
// FROM cosmos_db.orders WHERE orderDate >= '2025-01-01' GROUP BY region
```

**Correct (pre-compute aggregates incrementally via Change Feed materialized views):**

```csharp
// ✅ Maintain real-time aggregations via Change Feed processor
public class SalesAggregate
{
    public string Id { get; set; }           // "category-electronics"
    public string PartitionKey { get; set; } // "aggregates"
    public string Category { get; set; }
    public long TotalSold { get; set; }
    public decimal AveragePrice { get; set; }
    public DateTime LastUpdated { get; set; }
}

// Dashboard reads pre-computed aggregates: 1 RU per point read
// Instead of recalculating from millions of source documents each time
```

**Correct (single-partition aggregation scoped to a known partition key is acceptable):**

```csharp
// ✅ Bounded, single-partition aggregation — acceptable cost
var query = new QueryDefinition(
    "SELECT VALUE COUNT(1) FROM c WHERE c.customerId = @cid AND c.status = 'pending'")
    .WithParameter("@cid", customerId);

var iterator = container.GetItemQueryIterator<int>(query,
    requestOptions: new QueryRequestOptions
    {
        PartitionKey = new PartitionKey(customerId)  // Scoped to ONE partition
    });
```

**Incorrect (unbounded aggregation across all partitions — fans out to every partition, massive RU):**

```csharp
// ❌ Unbounded aggregation across all partitions
var query = "SELECT c.region, COUNT(1) as orderCount, SUM(c.total) as revenue " +
            "FROM c WHERE c.orderDate >= '2025-01-01' GROUP BY c.region";

var iterator = container.GetItemQueryIterator<dynamic>(query);
// Fans out to ALL partitions, reads ALL matching documents
// At 10M orders: potentially 50,000+ RU per execution
// Blocks transactional traffic with sustained high RU consumption
```

**Incorrect (dashboard refreshing aggregations against transactional store):**

```python
# ❌ Dashboard refreshing aggregations against transactional store
def get_dashboard_metrics(self):
    queries = [
        "SELECT VALUE COUNT(1) FROM c",                           # Full scan
        "SELECT c.status, COUNT(1) FROM c GROUP BY c.status",     # Unbounded GROUP BY
        "SELECT VALUE AVG(c.responseTime) FROM c WHERE c.type = 'request'"  # Cross-partition AVG
    ]
    # Each query scans the entire container
    # Running these every 30 seconds for a dashboard = sustained throttling
```

**Incorrect (reporting query running against operational container):**

```java
// ❌ Reporting query running against operational container
@Query("SELECT c.category, SUM(c.quantity) as totalSold, AVG(c.price) as avgPrice " +
       "FROM c WHERE c.type = 'sale' GROUP BY c.category")
List<CategorySalesReport> getCategorySalesReport();
// Full cross-partition scan + aggregation — hundreds of thousands of RU
// Competes with real-time order processing for the same throughput budget
```

References:
- [Azure Synapse Link for Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/synapse-link)
- [Analytical store overview](https://learn.microsoft.com/azure/cosmos-db/analytical-store-introduction)
- [Change Feed materialized views pattern](https://learn.microsoft.com/azure/cosmos-db/nosql/change-feed-design-patterns#materialized-views)

### 1.7 Order Filters by Selectivity

**Impact: MEDIUM** (reduces intermediate result sets)

## Order Filters by Selectivity

Place most selective filters first in WHERE clauses. The query engine processes filters left-to-right, so selective filters early reduce data scanned.

**Incorrect (least selective filter first):**

```csharp
// Status has low selectivity (few unique values)
// Filters 1M items to 300K, then to 100
var query = @"
    SELECT * FROM c 
    WHERE c.status = 'active'        -- 30% of items match
    AND c.type = 'order'             -- 10% of items match
    AND c.customerId = @customerId"; -- 0.01% match (highly selective)

// Processes: 1M → 300K → 100K → 100
// More intermediate processing than necessary
```

**Correct (most selective filter first):**

```csharp
// CustomerId is highly selective (unique per customer)
var query = @"
    SELECT * FROM c 
    WHERE c.customerId = @customerId  -- 0.01% match (filter first!)
    AND c.type = 'order'              -- Then narrow by type
    AND c.status = 'active'";         -- Finally by status

// Processes: 1M → 1K → 100 → 100
// Much less intermediate data
```

```csharp
// Selectivity guidelines (from most to least selective):
// 1. Unique identifiers: id, customerId, orderId (highest)
// 2. Foreign keys with many values: productId, userId
// 3. Timestamps (range queries): createdAt, modifiedAt
// 4. Categories with many values: categoryId, departmentId
// 5. Status fields: status, state (low selectivity)
// 6. Boolean flags: isActive, isDeleted (lowest - only 2 values)

// Example: Combining timestamp with status
var query = @"
    SELECT * FROM c 
    WHERE c.customerId = @customerId
    AND c.orderDate >= @startDate
    AND c.orderDate < @endDate
    AND c.status = 'completed'";

// Even better with composite index
```

```csharp
// Use BETWEEN with high selectivity values
var query = @"
    SELECT * FROM c 
    WHERE c.orderId >= @startId AND c.orderId <= @endId  -- Very selective range
    AND c.status = 'active'";

// For OR clauses, check if rewriting helps
// Less efficient:
var query1 = "SELECT * FROM c WHERE c.status = 'a' OR c.status = 'b' AND c.customerId = @id";
// Better (explicit grouping):
var query2 = "SELECT * FROM c WHERE (c.status = 'a' OR c.status = 'b') AND c.customerId = @id";
// Best (if possible, use IN):
var query3 = "SELECT * FROM c WHERE c.status IN ('a', 'b') AND c.customerId = @id";
```

Reference: [Query optimization tips](https://learn.microsoft.com/azure/cosmos-db/nosql/performance-tips-query-sdk)

### 1.8 Use Continuation Tokens for Pagination

**Impact: HIGH** (enables efficient large result sets)

## Use Continuation Tokens for Pagination

Use continuation tokens to paginate through large result sets efficiently. **Never use OFFSET/LIMIT for deep pagination** — it is a common anti-pattern with severe performance implications.

### ⚠️ OFFSET/LIMIT Anti-Pattern

**OFFSET/LIMIT is one of the most common and costly Cosmos DB anti-patterns.** The RU cost of OFFSET scales linearly with the offset value because Cosmos DB must read and discard all skipped documents:

| Page | OFFSET | Documents Scanned | Documents Returned | Relative RU Cost |
|------|--------|-------------------|--------------------|------------------|
| 1 | 0 | 100 | 100 | 1x |
| 10 | 900 | 1,000 | 100 | 10x |
| 100 | 9,900 | 10,000 | 100 | 100x |
| 1,000 | 99,900 | 100,000 | 100 | 1,000x |

This pattern is especially dangerous in **leaderboard** and **feed** scenarios where users page through large result sets.

Use OFFSET/LIMIT only when:
- The total result set is small (< 1,000 items)
- You need random access to a specific page (rare)
- Deep pagination is impossible (e.g., top 100 only)

**Incorrect (OFFSET/LIMIT for pagination):**

```csharp
// ❌ Anti-pattern: OFFSET increases cost linearly with page number
public async Task<List<Product>> GetProductsPage(int page, int pageSize)
{
    // Page 1: Skip 0, Page 100: Skip 9900
    var offset = (page - 1) * pageSize;
    
    // OFFSET must scan and discard all previous items!
    var query = $"SELECT * FROM c ORDER BY c.name OFFSET {offset} LIMIT {pageSize}";
    
    var results = await container.GetItemQueryIterator<Product>(query).ReadNextAsync();
    return results.ToList();
    
    // Page 1: Scans 100 items
    // Page 100: Scans 10,000 items, returns 100
    // RU cost grows linearly with page depth!
}
```

**Correct (continuation token pagination):**

```csharp
public class PagedResult<T>
{
    public List<T> Items { get; set; }
    public string ContinuationToken { get; set; }
    public bool HasMore => !string.IsNullOrEmpty(ContinuationToken);
}

public async Task<PagedResult<Product>> GetProductsPage(
    int pageSize, 
    string continuationToken = null)
{
    var query = new QueryDefinition("SELECT * FROM c ORDER BY c.name");
    
    var options = new QueryRequestOptions
    {
        MaxItemCount = pageSize  // Items per page
    };
    
    var iterator = container.GetItemQueryIterator<Product>(
        query,
        continuationToken: continuationToken,  // Resume from last position
        requestOptions: options);
    
    var response = await iterator.ReadNextAsync();
    
    return new PagedResult<Product>
    {
        Items = response.ToList(),
        ContinuationToken = response.ContinuationToken  // For next page
    };
    
    // Every page costs the same RU regardless of depth!
}

// Usage in API
[HttpGet("products")]
public async Task<IActionResult> GetProducts(
    [FromQuery] int pageSize = 20,
    [FromQuery] string continuationToken = null)
{
    // Decode token if passed as query param (URL-safe encoding)
    var token = continuationToken != null 
        ? Encoding.UTF8.GetString(Convert.FromBase64String(continuationToken))
        : null;
    
    var result = await GetProductsPage(pageSize, token);
    
    // Encode token for URL safety
    var nextToken = result.ContinuationToken != null
        ? Convert.ToBase64String(Encoding.UTF8.GetBytes(result.ContinuationToken))
        : null;
    
    return Ok(new { result.Items, NextPage = nextToken });
}
```

```python
# ❌ Anti-pattern: OFFSET/LIMIT cost grows with page depth
async def get_scores_page_with_offset(container, player_id: str, page: int, page_size: int = 20):
    offset = (page - 1) * page_size
    query = (
        "SELECT * FROM c "
        "WHERE c.playerId = @playerId "
        "ORDER BY c.submittedAt DESC "
        f"OFFSET {offset} LIMIT {page_size}"
    )
    items = container.query_items(
        query=query,
        parameters=[{"name": "@playerId", "value": player_id}],
        partition_key=player_id,
    )
    return [item async for item in items]


# ✅ Preferred: continuation token pagination (stable RU per page)
async def get_scores_page(
    container,
    player_id: str,
    page_size: int = 20,
    continuation_token: str | None = None,
):
    query = (
        "SELECT * FROM c "
        "WHERE c.playerId = @playerId "
        "ORDER BY c.submittedAt DESC"
    )

    results = container.query_items(
        query=query,
        parameters=[{"name": "@playerId", "value": player_id}],
        partition_key=player_id,
        max_item_count=page_size,
    )

    pager = results.by_page(continuation_token=continuation_token)
    page = await pager.__anext__()
    items = [item async for item in page]

    return {
        "items": items,
        "continuationToken": pager.continuation_token,
    }
```

Python SDK note: Continuation tokens are supported for single-partition queries. Always set `partition_key` when using `by_page()`.

```csharp
// Streaming through all results
public async IAsyncEnumerable<Product> GetAllProducts()
{
    string continuationToken = null;
    
    do
    {
        var page = await GetProductsPage(100, continuationToken);
        
        foreach (var product in page.Items)
        {
            yield return product;
        }
        
        continuationToken = page.ContinuationToken;
    }
    while (continuationToken != null);
}
```

### ⚠️ Unbounded Query Anti-Pattern

**Fetching all results without any pagination is even worse than OFFSET/LIMIT.** This is commonly seen when developers skip pagination entirely, assuming result sets are small. At scale, unbounded queries cause:

- **Excessive RU consumption** — reading thousands of documents in one call
- **Timeouts** — queries exceeding the 5-second execution limit
- **Memory pressure** — loading all results into memory
- **Cascading failures** — high RU consumption triggers 429 throttling for other operations

```java
// ❌ Anti-pattern: No pagination — returns ALL matching documents
public List<Task> getTasksByProject(String tenantId, String projectId) {
    String query = "SELECT * FROM c WHERE c.tenantId = @tenantId " +
                   "AND c.type = 'task' AND c.projectId = @projectId";
    SqlQuerySpec spec = new SqlQuerySpec(query,
        Arrays.asList(new SqlParameter("@tenantId", tenantId),
                      new SqlParameter("@projectId", projectId)));
    // Returns ALL tasks — at 500 tasks/project this is wasteful,
    // at 50,000 tasks/project this causes timeouts
    return container.queryItems(spec, new CosmosQueryRequestOptions(), Task.class)
        .stream().collect(Collectors.toList());
}

// ✅ Correct: Return paginated results with continuation token
public PagedResult<Task> getTasksByProject(
        String tenantId, String projectId,
        int pageSize, String continuationToken) {
    String query = "SELECT * FROM c WHERE c.tenantId = @tenantId " +
                   "AND c.type = 'task' AND c.projectId = @projectId " +
                   "ORDER BY c.createdAt DESC";
    CosmosQueryRequestOptions options = new CosmosQueryRequestOptions();
    options.setMaxBufferedItemCount(pageSize);
    // Use iterableByPage for continuation token support
    CosmosPagedIterable<Task> results = container.queryItems(
        new SqlQuerySpec(query, params), options, Task.class);
    // Process first page only, return continuation token for next page
}
```

**Rule of thumb:** If a query can return more than 100 items, it **must** use pagination.

Reference: [Pagination in Azure Cosmos DB](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/query/pagination)

### 1.9 Use Parameterized Queries

**Impact: MEDIUM** (improves security and query plan caching)

## Use Parameterized Queries

Always use parameterized queries instead of string concatenation. This prevents injection attacks and enables query plan caching.

**Incorrect (string concatenation):**

```csharp
// SQL injection vulnerability!
public async Task<User> GetUser(string userId)
{
    // NEVER DO THIS - vulnerable to injection
    var query = $"SELECT * FROM c WHERE c.userId = '{userId}'";
    
    // Attacker input: "' OR '1'='1"
    // Results in: SELECT * FROM c WHERE c.userId = '' OR '1'='1'
    // Returns ALL users!
    
    var iterator = container.GetItemQueryIterator<User>(query);
    return (await iterator.ReadNextAsync()).FirstOrDefault();
}

// Also prevents query plan caching
// Each unique query string = new compilation
var query1 = "SELECT * FROM c WHERE c.userId = 'user1'";
var query2 = "SELECT * FROM c WHERE c.userId = 'user2'";
// Two different query plans compiled!
```

**Correct (parameterized queries):**

```csharp
public async Task<User> GetUser(string userId)
{
    var query = new QueryDefinition("SELECT * FROM c WHERE c.userId = @userId")
        .WithParameter("@userId", userId);
    
    // Injection attempt becomes literal string comparison
    // Attacker input "' OR '1'='1" just searches for that literal value
    
    var iterator = container.GetItemQueryIterator<User>(query);
    return (await iterator.ReadNextAsync()).FirstOrDefault();
}

// Query plan is cached and reused
var query1 = new QueryDefinition("SELECT * FROM c WHERE c.userId = @userId")
    .WithParameter("@userId", "user1");
var query2 = new QueryDefinition("SELECT * FROM c WHERE c.userId = @userId")
    .WithParameter("@userId", "user2");
// Same query plan reused!
```

```csharp
// Multiple parameters
var query = new QueryDefinition(@"
    SELECT * FROM c 
    WHERE c.customerId = @customerId 
    AND c.status = @status
    AND c.orderDate >= @startDate")
    .WithParameter("@customerId", customerId)
    .WithParameter("@status", "active")
    .WithParameter("@startDate", startDate);

// Array parameter for IN clauses
var statuses = new[] { "pending", "processing", "shipped" };
var query2 = new QueryDefinition(
    "SELECT * FROM c WHERE ARRAY_CONTAINS(@statuses, c.status)")
    .WithParameter("@statuses", statuses);
```

```csharp
// LINQ (automatically parameterized)
var results = container.GetItemLinqQueryable<Order>()
    .Where(o => o.CustomerId == customerId && o.Status == status)
    .ToFeedIterator();
// SDK handles parameterization automatically
```

Benefits:
- Security: Prevents SQL injection
- Performance: Query plan caching and reuse
- Maintainability: Cleaner, type-safe code

**Rust (`azure_data_cosmos`):**

```rust
use azure_data_cosmos::Query;

// ✅ Parameterized query — safe and cacheable
let query = Query::from("SELECT * FROM c WHERE c.customerId = @customerId")
    .with_parameter("@customerId", customer_id)
    .unwrap();

// Multiple parameters
let query = Query::from(
    "SELECT * FROM c WHERE c.customerId = @cid AND c.status = @status ORDER BY c.createdAt DESC"
)
    .with_parameter("@cid", customer_id).unwrap()
    .with_parameter("@status", "active").unwrap();

// Aggregate query with parameters
let query = Query::from(
    "SELECT COUNT(1) AS totalOrders, SUM(c.total) AS totalSpent FROM c WHERE c.customerId = @cid"
)
    .with_parameter("@cid", customer_id).unwrap();
```

```rust
// ❌ Anti-pattern: String interpolation (no plan caching, injection risk)
let query = Query::from(format!(
    "SELECT * FROM c WHERE c.customerId = '{}'", customer_id
));
```

Reference: [Parameterized queries](https://learn.microsoft.com/azure/cosmos-db/nosql/query/parameterized-queries)

### 1.10 Use Point Reads Instead of Queries for Known ID and Partition Key

**Impact: HIGH** (1 RU vs ~2.5 RU per single-document lookup)

## Use Point Reads Instead of Queries for Known ID and Partition Key

When both the document `id` and partition key value are known, use a point read (`ReadItemAsync` / `read_item` / `readItem`) instead of a query. A point read costs 1 RU for a 1 KB document and bypasses the query engine entirely. An equivalent `SELECT * FROM c WHERE c.id = @id` query costs ~2.5 RU because the query engine still parses, optimizes, and executes even though the result is a single document.

**Incorrect (query when both id and partition key are known):**

```csharp
// ❌ Uses query engine when a point read would suffice
var query = new QueryDefinition("SELECT * FROM c WHERE c.id = @id")
    .WithParameter("@id", orderId);

var iterator = container.GetItemQueryIterator<Order>(query,
    requestOptions: new QueryRequestOptions
    {
        PartitionKey = new PartitionKey(customerId)
    });

var response = await iterator.ReadNextAsync();
return response.FirstOrDefault();
// Cost: ~2.5 RU for a 1 KB document (query engine overhead)
```

```python
# ❌ Query instead of point read
def get_player(self, player_id: str, game_id: str):
    query = "SELECT * FROM c WHERE c.id = @id"
    items = list(self.container.query_items(
        query=query,
        parameters=[{"name": "@id", "value": player_id}],
        partition_key=game_id
    ))
    return items[0] if items else None
    # Unnecessary query engine invocation
```

```typescript
// ❌ Query instead of point read — id and partition key both known
const { resources } = await container.items
  .query<Order>({
    query: 'SELECT * FROM c WHERE c.id = @id',
    parameters: [{ name: '@id', value: orderId }],
  }, { partitionKey: userId })
  .fetchAll();
return resources[0] ?? null;
// ~2.92 RU — goes through the query engine for a single known document
```

**Correct (point read — bypasses query engine):**

```csharp
// ✅ Point read — 1 RU for a 1 KB document, no query engine overhead
var response = await container.ReadItemAsync<Order>(
    orderId,
    new PartitionKey(customerId));
return response.Resource;
```

```python
# ✅ Point read — 1 RU, no query engine overhead
def get_player(self, player_id: str, game_id: str):
    return self.container.read_item(item=player_id, partition_key=game_id)
```

```java
// ✅ Point read in Java SDK
CosmosItemResponse<Order> response = container.readItem(
    orderId,
    new PartitionKey(customerId),
    Order.class);
return response.getItem();
```

```typescript
// ✅ Point read in Node.js — 1 RU, no query engine overhead
const { resource: order } = await container.item(orderId, userId).read<Order>();
return order ?? null;
```

```rust
// ✅ Point read in Rust (azure_data_cosmos) — 1 RU, no query engine
use azure_data_cosmos::PartitionKey;

let container = cosmos.database_client("db").container_client("orders").await;
let pk = PartitionKey::from(customer_id.to_string());
let response = container.read_item::<serde_json::Value>(pk, &order_id, None).await;
match response {
    Ok(item) => {
        let order: Order = serde_json::from_value(item.into_body()).unwrap();
        // Cost: 1 RU for a 1 KB document
    }
    Err(e) if e.http_status() == Some(azure_core::http::StatusCode::NotFound) => {
        // Document not found
    }
    Err(e) => return Err(e),
}
```

### Multiple Known Documents — ReadMany vs. Parallel Point Reads

When fetching multiple documents by known `(id, partitionKey)` pairs, you have two options:

1. **Client-side parallel point reads** — issue individual `ReadItem` calls concurrently
2. **ReadMany** — batch all `(id, partitionKey)` pairs into a single SDK call

ReadMany targets only the relevant partitions and avoids the query engine, but the performance tradeoff depends on batch size, client resources, and document size. Small batches can be slower than aggressively parallel point reads on a well-provisioned client, while larger batches tend to reduce both latency and RU cost. **Benchmark both approaches** with your actual workload before committing to one.

**⚠️ Avoid using OR/IN queries across partition keys — these fan out to all partitions regardless of how many documents you need:**

```csharp
// ❌ OR/IN clause spanning multiple partition keys — cross-partition fan-out
var query = new QueryDefinition(
    "SELECT * FROM c WHERE c.id IN (@id1, @id2, @id3)")
    .WithParameter("@id1", "order-1")
    .WithParameter("@id2", "order-2")
    .WithParameter("@id3", "order-3");
// Fans out to ALL partitions to find 3 documents — RU scales with partition count
```

**✅ ReadMany — targeted reads, no fan-out (best for larger batches; benchmark for your workload):**

```csharp
// ✅ ReadMany — targets only relevant partitions
var items = new List<(string id, PartitionKey partitionKey)>
{
    ("order-1", new PartitionKey("customer-a")),
    ("order-2", new PartitionKey("customer-b")),
    ("order-3", new PartitionKey("customer-a"))
};

var response = await container.ReadManyItemsAsync<Order>(items);
// Consistent cost — no cross-partition fan-out
```

```python
# ✅ ReadMany in Python SDK
items_to_read = [
    ("order-1", "customer-a"),
    ("order-2", "customer-b"),
    ("order-3", "customer-a")
]
results = container.read_many_items(item_identities=items_to_read)
```

**✅ Parallel point reads — alternative for small batches on well-provisioned clients:**

```csharp
// ✅ Parallel point reads — can outperform ReadMany for small batches
var tasks = new[]
{
    container.ReadItemAsync<Order>("order-1", new PartitionKey("customer-a")),
    container.ReadItemAsync<Order>("order-2", new PartitionKey("customer-b")),
    container.ReadItemAsync<Order>("order-3", new PartitionKey("customer-a"))
};

var responses = await Task.WhenAll(tasks);
```

```typescript
// ❌ OR/IN across partitions — fans out to every partition
const { resources } = await container.items.query<Order>({
  query: 'SELECT * FROM c WHERE c.id IN (@a, @b, @c)',
  parameters: [
    { name: '@a', value: 'order-1' },
    { name: '@b', value: 'order-2' },
    { name: '@c', value: 'order-3' },
  ],
}).fetchAll();

// ✅ Parallel point reads (@azure/cosmos v4 does not expose readMany;
//    use bounded-concurrency parallel reads for batched lookups)
const results = await Promise.all([
  container.item('order-1', 'user-alice').read<Order>(),
  container.item('order-2', 'user-bob').read<Order>(),
  container.item('order-3', 'user-alice').read<Order>(),
]);
return results.map(r => r.resource).filter(Boolean);
// Total RU ≈ N × 1.0; bound concurrency with a limiter for larger batches
```

### Validate parent existence with a point read before writing child records

When writing a child/event document that references a parent entity (for example, reading → device, line item → order), do a parent point read first if your API requires rejecting unknown parents. This keeps referential checks cheap and avoids orphaned documents.

```java
// ✅ Fast referential validation (1 RU point read) before write
try {
    container.readItem(deviceId, new PartitionKey(deviceId), Device.class);
} catch (CosmosException ex) {
    if (ex.getStatusCode() == 404) {
        throw new IllegalArgumentException("Unknown deviceId");
    }
    throw ex;
}
// write telemetry only after parent exists
```

```python
# ❌ No existence check: creates orphan child records
container.upsert_item({"id": event_id, "deviceId": device_id, "value": 42})
```

### When to Use Each Approach

| Scenario | Approach |
|----------|----------|
| Single document with known id and partition key | **ReadItem** (point read) |
| Multiple documents with known (id, partitionKey) pairs — large batch | **ReadMany** (benchmark to confirm) |
| Multiple documents with known (id, partitionKey) pairs — small batch | **Parallel point reads** or **ReadMany** (benchmark both) |
| Need filtering, sorting, projection, or aggregation | **Query** |
| Exact ids and partition keys are not known | **Query** |

Reference: [Point reads in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-read-item) | [ReadMany — read multiple items](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-dotnet-read-item#read-multiple-items) | [Read many items fast (Java)](https://devblogs.microsoft.com/cosmosdb/read-many-items-fast-with-the-java-sdk-for-azure-cosmos-db/)

### 1.11 Parameterize TOP Values Safely

**Impact: HIGH** (prevents incorrect query guidance and keeps parameterization secure)

## Parameterize TOP Values Safely

Cosmos DB SQL supports both literal and parameterized values for `TOP`. Prefer parameterized `TOP` values for consistency with secure query practices. Ensure the parameter value is an integer.

**Incorrect (string interpolation for TOP):**

```python
# Avoid string interpolation when parameterization works
top = int(top)
query = f"SELECT TOP {top} * FROM c ORDER BY c.score DESC"
items = container.query_items(query, enable_cross_partition_query=True)
```

```csharp
// Avoid interpolating TOP directly when parameters are available
int topN = 10;
var query = new QueryDefinition($"SELECT TOP {topN} * FROM c ORDER BY c.score DESC");
```

**Correct (parameterized TOP):**

```python
# TOP can be parameterized
query = "SELECT TOP @top * FROM c ORDER BY c.score DESC"
params = [{"name": "@top", "value": int(top)}]
items = container.query_items(query, parameters=params, enable_cross_partition_query=True)
```

```csharp
var query = new QueryDefinition("SELECT TOP @top * FROM c ORDER BY c.score DESC")
    .WithParameter("@top", 10);
```

```python
# Keep all query values parameterized, including TOP
query = "SELECT TOP @top * FROM c WHERE c.gameId = @gameId ORDER BY c.score DESC"
params = [
    {"name": "@top", "value": int(top)},
    {"name": "@gameId", "value": game_id},
]
items = container.query_items(query, parameters=params, enable_cross_partition_query=True)
```

Use a literal integer in `TOP` only when it is genuinely constant at authoring time (for example, `TOP 10`).

References:
- [Parameterized queries](https://learn.microsoft.com/azure/cosmos-db/nosql/query/parameterized-queries)
- [SQL query TOP keyword](https://learn.microsoft.com/azure/cosmos-db/nosql/query/select#top-keyword)

### 1.12 Project Only Needed Fields

**Impact: HIGH** (reduces payload size, network bandwidth, and client memory; RU savings scale with document size (negligible on small flat docs, substantial on multi-KB/MB documents and large result sets))

## Project Only Needed Fields

Select only the fields you need rather than returning entire documents. Reduces both RU consumption and network bandwidth.

**Incorrect (selecting entire document):**

```csharp
// Selecting everything when you only need a few fields
var query = "SELECT * FROM c WHERE c.customerId = @customerId";

// Returns all fields including:
// - Large text content
// - Arrays with hundreds of items
// - Fields you'll never use
var orders = await container.GetItemQueryIterator<Order>(
    new QueryDefinition(query).WithParameter("@customerId", customerId),
    requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(customerId) }
).ReadNextAsync();

// UI only shows: orderId, orderDate, total
// But you transferred and deserialized everything!
```

**Correct (projecting specific fields):**

```csharp
// Project only what's needed
var query = @"
    SELECT 
        c.id,
        c.orderDate,
        c.total,
        c.status
    FROM c 
    WHERE c.customerId = @customerId";

public class OrderSummary
{
    public string Id { get; set; }
    public DateTime OrderDate { get; set; }
    public decimal Total { get; set; }
    public string Status { get; set; }
}

var orders = await container.GetItemQueryIterator<OrderSummary>(
    new QueryDefinition(query).WithParameter("@customerId", customerId),
    requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(customerId) }
).ReadNextAsync();

// Substantial payload-size reduction; RU savings depend on document size
// (significant on large/nested docs, negligible on small flat docs)
```

```csharp
// For nested objects, project specific paths
var query = @"
    SELECT 
        c.id,
        c.customer.name AS customerName,
        c.items[0].productName AS firstProduct,
        ARRAY_LENGTH(c.items) AS itemCount
    FROM c";

// Even more efficient: VALUE for single field
var query2 = "SELECT VALUE c.email FROM c WHERE c.type = 'customer'";
var emails = await container.GetItemQueryIterator<string>(query2).ReadNextAsync();
```

```csharp
// LINQ projection
var orderSummaries = container.GetItemLinqQueryable<Order>(
    requestOptions: new QueryRequestOptions 
    { 
        PartitionKey = new PartitionKey(customerId) 
    })
    .Where(o => o.CustomerId == customerId)
    .Select(o => new OrderSummary
    {
        Id = o.Id,
        OrderDate = o.OrderDate,
        Total = o.Total,
        Status = o.Status
    })
    .ToFeedIterator();
```

### Prefer dedicated result types for projections

When projecting fields, prefer deserializing into a dedicated DTO or record whose properties match the projected fields rather than reusing the full document model class. A dedicated result type makes the projection self-documenting, avoids confusion from null/default-valued properties that were not projected, and reduces the chance of developers reverting to `SELECT *` over time.

```csharp
// ✅ Preferred: Dedicated DTO matches projected fields exactly
public class OrderSummary
{
    public string Id { get; set; }
    public DateTime OrderDate { get; set; }
    public decimal Total { get; set; }
    public string Status { get; set; }
}

var iterator = container.GetItemQueryIterator<OrderSummary>(  // ✅ Matches projection
    new QueryDefinition(query).WithParameter("@cid", customerId));
```

```java
// ✅ Preferred: Dedicated projection record in Java
public record PlayerSummary(String id, String playerName, int score) {}

@Query("SELECT c.id, c.playerName, c.score FROM c WHERE c.leaderboardKey = @key")
List<PlayerSummary> getTopPlayers(@Param("key") String key);
```

⚠️ Deserializing projected results into the full entity type is acceptable when the entity is small, the unprojected fields are not misleading, or the surrounding framework expects that type (e.g., Spring Data repository methods, EF Core entities). In these cases, ensure the intent is clear through comments or naming so that future maintainers do not mistakenly revert to `SELECT *`.

### Node.js / TypeScript (@azure/cosmos v4)

```typescript
// ❌ Anti-pattern: SELECT * pulls every field including future additions
const bad = {
  query: 'SELECT * FROM c WHERE c.userId = @userId ORDER BY c.createdAt DESC',
  parameters: [{ name: '@userId', value: userId }],
};

// ✅ Preferred: project only the fields the caller consumes
const good = {
  query: `
    SELECT c.id, c.userId, c.status, c.total, c.createdAt
    FROM c
    WHERE c.userId = @userId
    ORDER BY c.createdAt DESC
  `,
  parameters: [{ name: '@userId', value: userId }],
};

// TypeScript: dedicated result type matches the projected fields
interface OrderSummary {
  id: string;
  userId: string;
  status: string;
  total: number;
  createdAt: string;
}
const { resources } = await container.items
  .query<OrderSummary>(good, { partitionKey: userId })
  .fetchAll();

// Single-column scalar with SELECT VALUE
const { resources: statuses } = await container.items
  .query<string>({
    query: 'SELECT VALUE c.status FROM c WHERE c.userId = @u',
    parameters: [{ name: '@u', value: userId }],
  }, { partitionKey: userId })
  .fetchAll();
```

Savings multiply with:
- Large documents (MB-sized)
- Large result sets
- High query frequency

Reference: [Project fields in queries](https://learn.microsoft.com/azure/cosmos-db/nosql/query/select)

---

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
