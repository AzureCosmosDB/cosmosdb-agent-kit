---
title: Composite Index Directions Must Match ORDER BY
impact: HIGH
impactDescription: prevents query failures and rejected sorts
tags: index, composite, orderby, direction, ascending, descending
---

## Composite Index Directions Must Match ORDER BY

Every composite index entry must specify sort directions that **exactly match** the `ORDER BY` clause of the queries it serves. If the directions don't match, Cosmos DB will reject the query or fall back to an expensive scan.

**Incorrect (direction mismatch — query fails):**

```python
# Composite index defined as descending
indexing_policy = {
    "compositeIndexes": [
        [{"path": "/score", "order": "descending"}]
    ]
}
```

**Correct (directions match exactly, with both orderings):**


```python
# Define BOTH directions to support ASC and DESC queries
indexing_policy = {
    "compositeIndexes": [
        [{"path": "/score", "order": "descending"}],
        [{"path": "/score", "order": "ascending"}]
    ]
```

```csharp
// Always provide both sort directions for each composite index pattern
CompositeIndexes =
{
    // For ORDER BY score DESC
    new Collection<CompositePath>
    {
```
