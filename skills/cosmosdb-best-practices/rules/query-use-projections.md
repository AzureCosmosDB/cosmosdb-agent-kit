---
title: Project Only Needed Fields
impact: HIGH
impactDescription: reduces payload size, network bandwidth, and client memory; RU savings scale with document size (negligible on small flat docs, substantial on multi-KB/MB documents and large result sets)
tags: query, projection, performance, bandwidth
---

## Project Only Needed Fields

Select only the fields you need rather than returning entire documents. Reduces both RU consumption and network bandwidth.

**Incorrect (selecting entire document):**

```csharp
// Selecting everything when you only need a few fields
var query = "SELECT * FROM c WHERE c.customerId = @customerId";

// Returns all fields including:
// - Large text content
var orders = await container.GetItemQueryIterator<Order>(
    new QueryDefinition(query).WithParameter("@customerId", customerId),
```

**Correct (projecting specific fields):**


```csharp
// Project only what's needed
var query = @"
    SELECT 
        c.id,
        c.orderDate,
        c.total,
        c.status
```

```csharp
// For nested objects, project specific paths
var query = @"
    SELECT 
        c.id,
        c.customer.name AS customerName,
        c.items[0].productName AS firstProduct,
        ARRAY_LENGTH(c.items) AS itemCount
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
> Cross-ref: See `query-parameterize` for parameterized queries.
