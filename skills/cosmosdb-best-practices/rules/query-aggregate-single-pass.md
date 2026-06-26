---
title: Compute min/max/avg with one scoped aggregate query
impact: HIGH
impactDescription: prevents incorrect stats from partial reads or mismatched filters
tags: query, aggregate, min, max, avg, correctness, performance
---

## Compute min/max/avg with one scoped aggregate query

For endpoint statistics, compute `MIN`, `MAX`, and `AVG` from the same filtered dataset in a single Cosmos DB query whenever possible. Avoid mixing values from separate queries, partial pages, or different time windows, which produces mathematically inconsistent results.

**Incorrect (client-side aggregation over partial or inconsistent data):**

```java
// ❌ Reads only first page and computes stats from incomplete data
CosmosPagedIterable<JsonNode> page = container.queryItems(
    "SELECT * FROM c WHERE c.deviceId = @deviceId",
    new CosmosQueryRequestOptions(),
    JsonNode.class
);
```

**Correct (single-pass aggregate query with consistent filters):**


```java
// ✅ One query, one filter set, consistent aggregate outputs
String sql = """
    SELECT
      MIN(c.temperature) AS minTemp,
      MAX(c.temperature) AS maxTemp,
      AVG(c.temperature) AS avgTemp,
```

```python
# ✅ Use one scoped aggregate query
query = """
SELECT
  MIN(c.value) AS minValue,
  MAX(c.value) AS maxValue,
  AVG(c.value) AS avgValue
```
