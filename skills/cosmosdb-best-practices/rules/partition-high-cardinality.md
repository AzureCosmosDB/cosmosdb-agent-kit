---
title: Choose High-Cardinality Partition Keys
impact: CRITICAL
impactDescription: enables horizontal scalability
tags: partition, cardinality, scalability, design
---

## Choose High-Cardinality Partition Keys

Select partition keys with many unique values to enable distribution, but do not
assume that high cardinality guarantees balanced storage or traffic. Evaluate
both data growth and request volume per key against the application's access
patterns. A customer-based key can fit order-history queries while still creating
a hot partition for one unusually busy customer or an oversized partition for
one customer's accumulated history.

When recommending `customerId`, qualify it with both checks: per-customer stored
size and per-customer read/write traffic. Consider a suitable hierarchical or
bucketed key when either is concentrated, accounting for the effect on query
routing. See [avoiding hot partitions](partition-avoid-hotspots.md) and
[logical-partition storage limits](partition-20gb-limit.md).

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
    
    // Many customers enable distribution; check each customer's size and traffic
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

Reference: [Partitioning in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/partitioning-overview)
