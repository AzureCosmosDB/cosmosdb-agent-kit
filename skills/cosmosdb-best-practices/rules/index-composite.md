---
title: Use Composite Indexes for ORDER BY
impact: HIGH
impactDescription: enables sorted queries, reduces RU
tags: index, composite, orderby, sorting
---

## Use Composite Indexes for ORDER BY

Create composite indexes for queries with ORDER BY on multiple properties. Without them, queries fail in production (emulator silently permits them).

**Incorrect (ORDER BY without composite index):**

```csharp
// Fails in production: "Order by query does not have a corresponding composite index"
var query = "SELECT * FROM c WHERE c.status = 'active' ORDER BY c.createdAt DESC, c.priority ASC";
```

**Correct (composite index declared):**


```json
{
    "indexingMode": "consistent",
    "compositeIndexes": [
        [
            { "path": "/status", "order": "ascending" },
            { "path": "/createdAt", "order": "descending" }
```

```csharp
// Common patterns needing composites:
// Filter + Sort: WHERE status = 'x' ORDER BY date DESC
// Multi-column sort: ORDER BY lastName ASC, firstName ASC
// Range + Sort: WHERE price >= 10 ORDER BY rating DESC
```
