---
title: Minimize Cross-Partition Queries
impact: HIGH
impactDescription: reduces RU by 5-100x
tags: query, cross-partition, performance, optimization
---

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

Strategies to avoid cross-partition:
1. Include partition key in WHERE clause
2. Denormalize data to colocate in same partition
3. Create secondary containers with different partition keys for different access patterns

Reference: [Query patterns](https://learn.microsoft.com/azure/cosmos-db/nosql/query/getting-started)
