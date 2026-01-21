---
title: Exclude Unused Index Paths
impact: HIGH
impactDescription: reduces write RU by 20-80%
tags: index, exclusion, write-performance, optimization
---

## Exclude Unused Index Paths

Exclude paths from indexing that you never query. Every indexed path adds write cost with no read benefit.

**Incorrect (indexing everything):**

```csharp
// Default indexing policy indexes ALL paths
// Great for flexibility, expensive for writes
{
    "indexingMode": "consistent",
    "automatic": true,
    "includedPaths": [
        {
            "path": "/*"  // Indexes everything including unused fields
        }
    ],
    "excludedPaths": []
}

// Document with large unused fields gets indexed unnecessarily
{
    "id": "order-123",
    "customerId": "cust-1",          // Queried
    "status": "shipped",             // Queried
    "items": [...],                  // Not queried
    "internalNotes": "...",          // Not queried
    "auditLog": [...]                // Large array, never queried!
}
// Write cost includes indexing auditLog array - wasted RU
```

**Correct (selective indexing):**

```csharp
// Include only queried paths
var indexingPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,
    Automatic = true,
    
    // Only include paths you actually query
    IncludedPaths =
    {
        new IncludedPath { Path = "/customerId/?" },
        new IncludedPath { Path = "/status/?" },
        new IncludedPath { Path = "/orderDate/?" },
        new IncludedPath { Path = "/total/?" }
    },
    
    // Exclude everything else (especially large arrays)
    ExcludedPaths =
    {
        new ExcludedPath { Path = "/items/*" },         // Embedded array
        new ExcludedPath { Path = "/internalNotes/?" },
        new ExcludedPath { Path = "/auditLog/*" },      // Large array
        new ExcludedPath { Path = "/_etag/?" }          // System field
    }
};

var containerProperties = new ContainerProperties
{
    Id = "orders",
    PartitionKeyPath = "/customerId",
    IndexingPolicy = indexingPolicy
};
```

```json
// JSON equivalent indexing policy
{
    "indexingMode": "consistent",
    "automatic": true,
    "includedPaths": [
        { "path": "/customerId/?" },
        { "path": "/status/?" },
        { "path": "/orderDate/?" }
    ],
    "excludedPaths": [
        { "path": "/items/*" },
        { "path": "/auditLog/*" },
        { "path": "/*" }  // Exclude all other paths
    ]
}
```

```csharp
// Alternative: exclude all, include specific
var indexingPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,
    
    // Start with exclude all
    ExcludedPaths = { new ExcludedPath { Path = "/*" } },
    
    // Explicitly include only what you query
    IncludedPaths =
    {
        new IncludedPath { Path = "/customerId/?" },
        new IncludedPath { Path = "/orderDate/?" }
    }
};
```

Monitor and adjust:
- Review query patterns periodically
- Use Query Stats to see index utilization
- Balance write cost reduction vs query flexibility

Reference: [Indexing policies](https://learn.microsoft.com/azure/cosmos-db/index-policy)
