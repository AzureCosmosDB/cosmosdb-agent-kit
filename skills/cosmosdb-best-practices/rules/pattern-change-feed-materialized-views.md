---
title: Use Change Feed for cross-partition query optimization with materialized views
impact: HIGH
impactDescription: eliminates cross-partition query overhead for admin/analytics scenarios
tags: pattern, change-feed, materialized-views, cross-partition, query-optimization, idempotency, at-least-once
---

## Use Change Feed for cross-partition query optimization with materialized views

When frequent cross-partition queries are needed (admin dashboards, lookups by non-PK attributes), use Change Feed to maintain a separate container optimized for those patterns, or use Global Secondary Index (GSI).

**Incorrect (expensive cross-partition fan-out):**

```csharp
// Fans out to ALL partitions — expensive at scale
var query = container.GetItemQueryIterator<Order>(
    "SELECT * FROM c WHERE c.status = 'Pending' ORDER BY c.createdAt DESC");
```

**Correct (materialized view via Change Feed):**


```csharp
// Source: "orders" partitioned by /customerId
// Target: "orders-by-status" partitioned by /status — single-partition queries
ChangeFeedProcessor processor = ordersContainer
    .GetChangeFeedProcessorBuilder<Order>("statusViewProcessor", async (changes, ct) =>
    {
        foreach (Order order in changes)
```

```csharp
// ❌ counter += 1 will double-count on replay
profile.TotalGamesPlayed += 1;
profile.TotalScore += score.Score;
```
