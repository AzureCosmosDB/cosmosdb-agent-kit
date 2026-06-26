---
title: Align Partition Key with Query Patterns
impact: CRITICAL
impactDescription: enables single-partition queries
tags: partition, query-patterns, design, performance
---

## Align Partition Key with Query Patterns

Choose a partition key that supports your most frequent queries. Single-partition queries are orders of magnitude faster than cross-partition.

**Incorrect (partition key misaligned with queries):**

```csharp
// Document partitioned by category
public class Product
{
    public string Id { get; set; }
    public string Category { get; set; }  // Partition key
    public string SellerId { get; set; }
```

**Correct (partition key matches query patterns):**


```csharp
// Step 1: Analyze your query patterns
// - 80% of queries: "Get all products for seller X"

// Step 2: Choose partition key for dominant pattern
public class Product
{
```

```csharp
// E-commerce example: Orders partitioned by CustomerId
public class Order
{
    public string Id { get; set; }
    public string CustomerId { get; set; }  // Partition key
    public DateTime OrderDate { get; set; }
```

> Cross-ref: See `query-parameterize` for parameterized queries.
