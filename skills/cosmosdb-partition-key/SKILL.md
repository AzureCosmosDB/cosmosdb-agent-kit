---
name: cosmosdb-partition-key
description: |
  Azure Cosmos DB partition key design best practices: high cardinality,
  hotspot avoidance, hierarchical partition keys, synthetic keys, query pattern
  alignment, immutability, and logical partition size limits.
  USE FOR: Cosmos DB partition key choice, high cardinality, avoid hot partitions,
  hierarchical partition keys, synthetic partition keys, query pattern alignment,
  partition key length, immutable partition key, 20GB logical partition limit.
  DO NOT USE FOR: data modeling (use cosmosdb-data-modeling), query optimization
  (use cosmosdb-query-optimization), throughput (use cosmosdb-throughput).

license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.0.0"
---

# Azure Cosmos DB Partition Key Design

Best practices for choosing and designing partition keys in Azure Cosmos DB.

## When to Apply

Reference these guidelines when:
- Choosing a partition key for a new container
- Evaluating partition key cardinality
- Designing for even write distribution
- Using hierarchical partition keys
- Planning for logical partition size limits

## Rules

- [partition-high-cardinality](rules/partition-high-cardinality.md) - Choose high-cardinality partition keys
- [partition-avoid-hotspots](rules/partition-avoid-hotspots.md) - Distribute writes evenly
- [partition-hierarchical](rules/partition-hierarchical.md) - Use hierarchical partition keys for flexibility
- [partition-query-patterns](rules/partition-query-patterns.md) - Align partition key with query patterns
- [partition-synthetic-keys](rules/partition-synthetic-keys.md) - Create synthetic keys when needed
- [partition-key-length](rules/partition-key-length.md) - Respect partition key value length limits
- [partition-immutable-key](rules/partition-immutable-key.md) - Choose immutable properties as partition keys
- [partition-20gb-limit](rules/partition-20gb-limit.md) - Plan for 20GB logical partition limit

## Full Compiled Document

For all rules expanded: [AGENTS.md](AGENTS.md)
