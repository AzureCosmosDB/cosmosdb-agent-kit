---
title: Choose High-Cardinality Partition Keys
impact: CRITICAL
impactDescription: enables horizontal scalability
tags: partition, cardinality, scalability, design
---

## Choose High-Cardinality Partition Keys

Select partition keys with many unique values to ensure even data distribution. Low-cardinality keys create hot partitions.

**Incorrect (low cardinality creates hotspots):**

```csharp
// Anti-pattern: using status as partition key
public class Order
{
    public string Id { get; set; }
    
    // Only 5-10 unique values: "pending", "processing", "shipped", "delivered", "cancelled"
    public string Status { get; set; }  // ❌ BAD partition key!
}

// Result: All "pending" orders in ONE partition
// That partition becomes a hotspot during peak ordering!
```

```csharp
// Anti-pattern: using country as partition key
public class User
{
    public string Id { get; set; }
    
    // Only ~195 countries, uneven distribution
    public string Country { get; set; }  // ❌ BAD - US/India will be hot
}
```

**Correct (high cardinality with even distribution):**

```csharp
// Good: using unique identifier as partition key
public class Order
{
    public string Id { get; set; }
    
    // Millions of unique customers = even distribution
    public string CustomerId { get; set; }  // ✅ GOOD partition key
    
    public string Status { get; set; }  // Just a regular property now
}

// Good: using tenant ID for multi-tenant apps
public class Document
{
    public string Id { get; set; }
    
    // Each tenant gets their own partition(s)
    public string TenantId { get; set; }  // ✅ GOOD - natural isolation
}

// Good: using device ID for IoT
public class Telemetry
{
    public string Id { get; set; }
    
    // Thousands/millions of devices
    public string DeviceId { get; set; }  // ✅ GOOD partition key
    
    public DateTime Timestamp { get; set; }
    public double Temperature { get; set; }
}
```

Good partition keys typically:
- Have thousands to millions of unique values
- Match your most common query patterns
- Distribute writes evenly (no single key dominates)

### Cardinality vs. Query Patterns

High cardinality is important for even distribution, but it should not be the sole factor when selecting a partition key.

For read-heavy workloads where most queries filter on a specific field, prefer a partition key aligned with the dominant query pattern even if its cardinality is lower than `/id`. Single-partition reads are often more efficient than maximizing distribution that the workload does not require.

A bare `/id` partition key is most appropriate when point reads by id are the dominant access pattern or when write throughput requires maximum distribution. If the dominant query pattern filters on another field, consider whether aligning the partition key with that field would reduce cross-partition queries.

See also: `partition-query-patterns`.

Reference: [Partitioning in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/partitioning-overview)
