---
name: cosmosdb-query-optimization
description: |
  Azure Cosmos DB query optimization best practices: point reads, projections,
  pagination with continuation tokens, parameterized queries, filter ordering,
  cross-partition query avoidance, and analytical query detection.
  USE FOR: Cosmos DB queries, point reads vs queries, SELECT projections,
  continuation tokens, parameterized queries, avoid cross-partition, avoid scans,
  filter selectivity, TOP literal, ORDER BY, latest by timestamp, OLAP detection,
  aggregate queries, DISTINCT keyword.
  DO NOT USE FOR: indexing (use cosmosdb-indexing), data modeling (use cosmosdb-data-modeling),
  SDK client code (use cosmosdb-sdk).

license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.0.0"
---

# Azure Cosmos DB Query Optimization

Best practices for writing efficient queries against Azure Cosmos DB.

## When to Apply

Reference these guidelines when:
- Writing or optimizing Cosmos DB queries
- Implementing pagination
- Choosing between point reads and queries
- Reducing RU consumption on read operations
- Handling aggregations and sorting

## Rules

- [query-point-reads](rules/query-point-reads.md) - Use point reads when id and partition key are known
- [query-aggregate-single-pass](rules/query-aggregate-single-pass.md) - Compute min/max/avg with one scoped aggregate query
- [query-avoid-cross-partition](rules/query-avoid-cross-partition.md) - Minimize cross-partition queries
- [query-use-projections](rules/query-use-projections.md) - Project only needed fields
- [query-pagination](rules/query-pagination.md) - Use continuation tokens for pagination
- [query-avoid-scans](rules/query-avoid-scans.md) - Avoid full container scans
- [query-parameterize](rules/query-parameterize.md) - Use parameterized queries
- [query-order-filters](rules/query-order-filters.md) - Order filters by selectivity
- [query-top-literal](rules/query-top-literal.md) - Use literal integers for TOP
- [query-latest-by-timestamp](rules/query-latest-by-timestamp.md) - Query latest documents with ORDER BY and TOP 1
- [query-olap-detection](rules/query-olap-detection.md) - Detect and redirect analytical queries
- [query-distinct-keyword](rules/query-distinct-keyword.md) - Use DISTINCT keyword correctly

## Full Compiled Document

For all rules expanded: [AGENTS.md](AGENTS.md)
