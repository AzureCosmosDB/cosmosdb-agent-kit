---
title: Use Hierarchical Partition Keys for Flexibility
impact: HIGH
impactDescription: overcomes 20GB limit, enables targeted queries
tags: partition, hierarchical, multi-level, flexibility
---

## Use Hierarchical Partition Keys for Flexibility

Use hierarchical partition keys (HPK) to overcome the 20GB logical partition limit and enable targeted multi-partition queries.

**Incorrect (single-level hits 20GB limit):**

```csharp
// Problem: Large tenant exceeds 20GB logical partition limit
public class Document
{
    public string Id { get; set; }
    public string TenantId { get; set; }  // Single partition key
    // Large tenants hit 20GB ceiling!
}
```

**Correct (hierarchical partition keys):**


```csharp
// Create container with hierarchical partition key
var containerProperties = new ContainerProperties
{
    Id = "documents",
    PartitionKeyPaths = new List<string> 
    { 
        "/tenantId",   // Level 1: Tenant
```

```python
from azure.cosmos import PartitionKey

# Incorrect: single-level partition key for a large tenant workload
container = await database.create_container_if_not_exists(
    id="documents",
    partition_key=PartitionKey(path="/tenantId"),
)
```

> Cross-ref: See `query-parameterize` for parameterized queries.
