---
title: Query "latest" documents with explicit ORDER BY and TOP 1
impact: HIGH
impactDescription: prevents stale or nondeterministic "latest item" results
tags: query, order-by, top, timestamp, latest, correctness
---

## Query "latest" documents with explicit ORDER BY and TOP 1

When returning the latest item for an entity (latest reading, latest status, most recent event), always query with an explicit time field sort and `TOP 1`: `ORDER BY <timestampField> DESC`. Without explicit ordering, Cosmos DB does not guarantee result order and may return an older document.

**Incorrect (no deterministic ordering):**

```java
// ❌ No ORDER BY: can return an older document
String sql = "SELECT TOP 1 * FROM c WHERE c.deviceId = @deviceId";
SqlQuerySpec spec = new SqlQuerySpec(
    sql,
    List.of(new SqlParameter("@deviceId", deviceId))
);
```

**Correct (explicit timestamp sort + TOP 1):**


```java
// ✅ Deterministic latest item by timestamp
String sql = """
    SELECT TOP 1 * FROM c
    WHERE c.deviceId = @deviceId AND IS_DEFINED(c.timestamp)
    ORDER BY c.timestamp DESC
    """;
```

```python
# ✅ Deterministic latest item
query = """
SELECT TOP 1 * FROM c
WHERE c.userId = @uid AND IS_DEFINED(c.createdAt)
ORDER BY c.createdAt DESC
"""
```
