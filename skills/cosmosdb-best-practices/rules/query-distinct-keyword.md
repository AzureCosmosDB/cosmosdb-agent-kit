---
title: Use DISTINCT keyword to eliminate duplicate results efficiently
impact: MEDIUM
impactDescription: reduces bandwidth usage and RU consumption by eliminating duplicate results at the query engine level
tags: query, distinct, performance, optimization
---

## Use DISTINCT keyword to eliminate duplicate results efficiently

**Impact: MEDIUM (reduces unnecessary data transfer and RU consumption)**

Azure Cosmos DB supports `SELECT DISTINCT` to eliminate duplicate values during query execution. Prefer using `DISTINCT` rather than retrieving all results and removing duplicates in application code, which increases network bandwidth, client-side processing, and RU consumption.

**Incorrect (client-side deduplication):**

```csharp
// Query returns duplicate category values
var query = "SELECT c.category FROM c";

var iterator = container.GetItemQueryIterator<dynamic>(query);

var categories = new HashSet<string>();
```

**Correct (using DISTINCT in Cosmos DB):**


```csharp
// Cosmos DB removes duplicates before returning results
var query = "SELECT DISTINCT c.category FROM c";

var iterator = container.GetItemQueryIterator<dynamic>(query);

while (iterator.HasMoreResults)
```

```sql
SELECT DISTINCT VALUE c.category
FROM c
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
