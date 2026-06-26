---
title: Detect and Redirect Analytical Queries Away from Transactional Containers
impact: HIGH
impactDescription: prevents RU starvation, 429 throttling cascades, and query timeouts
tags: query, olap, analytical, aggregation, synapse-link, change-feed, materialized-views
---

## Detect and Redirect Analytical Queries Away from Transactional Containers

**Impact: HIGH (prevents RU starvation, 429 throttling cascades, and query timeouts)**

Cosmos DB's transactional store is optimized for OLTP: point reads, targeted queries within a partition, and bounded result sets. Analytical patterns — COUNT/SUM/AVG across all partitions, GROUP BY over unbounded data, or full-container scans for reporting — consume massive RU, trigger sustained 429 throttling that starves transactional operations, and can exceed the query execution timeout.

**Incorrect (unbounded aggregation across all partitions — fans out to every partition, massive RU):**

```csharp
// ❌ Unbounded aggregation across all partitions
var query = "SELECT c.region, COUNT(1) as orderCount, SUM(c.total) as revenue " +
            "FROM c WHERE c.orderDate >= '2025-01-01' GROUP BY c.region";

var iterator = container.GetItemQueryIterator<dynamic>(query);
// Fans out to ALL partitions, reads ALL matching documents
// At 10M orders: potentially 50,000+ RU per execution
```

**Correct (enable analytical store and run aggregations via Synapse Link — zero RU impact on transactional store):**


```csharp
// ✅ Enable analytical store on the container
var containerProperties = new ContainerProperties
{
    Id = "orders",
    PartitionKeyPath = "/customerId",
    AnalyticalStoreTimeToLiveInSeconds = -1  // Enable analytical store
};
```

```csharp
// ✅ Maintain real-time aggregations via Change Feed processor
public class SalesAggregate
{
    public string Id { get; set; }           // "category-electronics"
    public string PartitionKey { get; set; } // "aggregates"
    public string Category { get; set; }
    public long TotalSold { get; set; }
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
> Cross-ref: See `query-parameterize` for parameterized queries.
