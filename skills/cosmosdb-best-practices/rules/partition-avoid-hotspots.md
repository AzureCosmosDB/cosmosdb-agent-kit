---
title: Distribute Writes to Avoid Hot Partitions
impact: CRITICAL
impactDescription: prevents throughput bottlenecks
tags: partition, hot-partition, write-distribution, performance
---

## Distribute Writes to Avoid Hot Partitions

Ensure writes distribute evenly across partitions. A hot partition limits throughput to that single partition's capacity.

**Incorrect (all writes hit single partition):**

```csharp
// Anti-pattern: time-based partition key with current-time writes
public class Event
{
    public string Id { get; set; }
    
    // All events for "today" go to same partition!
```

**Correct (distributed writes):**


```csharp
// Good: write-sharding for time-series data
public class Event
{
    public string Id { get; set; }
    
    // Combine date with hash suffix for distribution
```

```csharp
// Good: natural distribution with entity IDs
public class Order
{
    public string Id { get; set; }
    public string CustomerId { get; set; }  // ✅ Natural distribution
    public DateTime OrderDate { get; set; }
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
> Cross-ref: See `partition-high-cardinality` for key selection.
