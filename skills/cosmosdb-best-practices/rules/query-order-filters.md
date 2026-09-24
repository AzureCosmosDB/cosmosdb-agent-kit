---
title: Let the Query Engine Order Filters
impact: MEDIUM
impactDescription: avoids ineffective predicate-order tuning and incorrect execution assumptions
tags: query, filters, optimization, performance
---

## Let the Query Engine Order Filters

The textual order of equivalent predicates in a `WHERE` clause does not determine their execution order. Cosmos DB's query engine determines which predicates are more selective and how to execute the query. Moving a selective predicate earlier in the SQL text is not a performance optimization.

**Incorrect (assuming lower RU cost solely from reordering equivalent predicates):**

```csharp
var originalQuery = @"
    SELECT * FROM c
    WHERE c.status = 'active'
    AND c.type = 'order'
    AND c.customerId = @customerId";

var reorderedQuery = @"
    SELECT * FROM c
    WHERE c.customerId = @customerId
    AND c.type = 'order'
    AND c.status = 'active'";
```

Both queries are valid and express the same filters. The mistake is claiming that `reorderedQuery` is cheaper merely because `customerId` appears first, or assigning intermediate row counts based on the clauses' textual positions.

**Correct (use readable predicates and optimize actual index usage):**

```csharp
var query = new QueryDefinition(@"
    SELECT * FROM c
    WHERE c.customerId = @customerId
    AND c.type = 'order'
    AND c.status = 'active'")
    .WithParameter("@customerId", customerId);
```

The order above is for readability, not an execution hint. To tune performance, inspect index usage and measured request charges/query metrics rather than assuming that swapping the same predicates reduces work.

**Key points:**

- Selectivity depends on the data distribution, not just the property name or type.
- Add useful filters with appropriate index support; a partition-key equality filter can narrow the query's partition scope regardless of where it appears in the `WHERE` clause.
- Preserve Boolean grouping when rewriting queries. Adding parentheses around `OR` predicates can change which documents match; it is not merely a performance rewrite.

See also: [Avoid cross-partition queries](query-avoid-cross-partition.md), [avoid full scans](query-avoid-scans.md), [combine FTS with indexed filters](fts-hybrid-queries.md).

Reference: [Index usage and filter-clause ordering](https://learn.microsoft.com/azure/cosmos-db/index-overview#composite-indexes)
