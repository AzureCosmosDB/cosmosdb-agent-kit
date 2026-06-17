# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Best practices for Azure Cosmos DB indexing: excluding unused paths, composite indexes, spatial indexes, index types, path syntax, and indexing modes.

---

## Table of Contents

1. [Indexing Strategies](#1-indexing-strategies) — **MEDIUM-HIGH**
   - 1.1 [Composite Index Directions Must Match ORDER BY](#11-composite-index-directions-must-match-order-by)
   - 1.2 [Use Composite Indexes for ORDER BY](#12-use-composite-indexes-for-order-by)
   - 1.3 [Exclude Unused Index Paths](#13-exclude-unused-index-paths)
   - 1.4 [Understand Indexing Modes](#14-understand-indexing-modes)
   - 1.5 [Use Correct Indexing Path Syntax](#15-use-correct-indexing-path-syntax)
   - 1.6 [Choose Appropriate Index Types](#16-choose-appropriate-index-types)
   - 1.7 [Add Spatial Indexes for Geo Queries](#17-add-spatial-indexes-for-geo-queries)

---

## 1. Indexing Strategies

**Impact: MEDIUM-HIGH**

### 1.1 Composite Index Directions Must Match ORDER BY

**Impact: HIGH** (prevents query failures and rejected sorts)

## Composite Index Directions Must Match ORDER BY

Every composite index entry must specify sort directions that **exactly match** the `ORDER BY` clause of the queries it serves. If the directions don't match, Cosmos DB will reject the query or fall back to an expensive scan.

For cross-partition `ORDER BY` queries, this is especially critical — the query **will fail** if no matching composite index exists.

**Incorrect (direction mismatch — query fails):**

```python
# Composite index defined as descending
indexing_policy = {
    "compositeIndexes": [
        [{"path": "/score", "order": "descending"}]
    ]
}

# But query uses ascending order — no matching index!
query = "SELECT * FROM c ORDER BY c.score ASC"
# Fails: "The order by query does not have a corresponding composite index"
```

```csharp
// Index covers (score DESC) only
new Collection<CompositePath>
{
    new CompositePath { Path = "/score", Order = CompositePathSortOrder.Descending }
}

// Query needs ASC — fails!
var query = "SELECT * FROM c ORDER BY c.score ASC";
```

**Correct (directions match exactly, with both orderings):**

```python
# Define BOTH directions to support ASC and DESC queries
indexing_policy = {
    "compositeIndexes": [
        [{"path": "/score", "order": "descending"}],
        [{"path": "/score", "order": "ascending"}]
    ]
}
```

```csharp
// Always provide both sort directions for each composite index pattern
CompositeIndexes =
{
    // For ORDER BY score DESC
    new Collection<CompositePath>
    {
        new CompositePath { Path = "/score", Order = CompositePathSortOrder.Descending }
    },
    // For ORDER BY score ASC
    new Collection<CompositePath>
    {
        new CompositePath { Path = "/score", Order = CompositePathSortOrder.Ascending }
    }
}
```

```python
# Multi-property example: provide paired directions
indexing_policy = {
    "compositeIndexes": [
        # For ORDER BY gameId ASC, score DESC
        [
            {"path": "/gameId", "order": "ascending"},
            {"path": "/score", "order": "descending"}
        ],
        # For ORDER BY gameId DESC, score ASC (reverse pair)
        [
            {"path": "/gameId", "order": "descending"},
            {"path": "/score", "order": "ascending"}
        ]
    ]
}
```

**Best practice: whenever you define a composite index, always include the inverse direction pair** so that both ASC and DESC queries on those paths are served.

Reference: [Composite index sort order](https://learn.microsoft.com/azure/cosmos-db/index-policy#composite-indexes)

### 1.2 Use Composite Indexes for ORDER BY

**Impact: HIGH** (enables sorted queries, reduces RU)

## Use Composite Indexes for ORDER BY

Create composite indexes for queries with ORDER BY on multiple properties. Without them, queries may fail or require expensive client-side sorting.

The default indexing policy indexes every property but does **not** create composite indexes. Any query that combines a `WHERE` equality filter with `ORDER BY` on a different field needs a composite index declared explicitly, or the query will either fail in production or require expensive client-side sorting.

> **Emulator warning:** The Cosmos DB emulator silently permits `ORDER BY` queries without a matching composite index and returns identical RU charges. Production containers reject the same query with *"The order by query does not have a corresponding composite index that it can be served from."* Always declare composite indexes at container-create time — do not rely on emulator success as validation.

**Incorrect (ORDER BY without composite index):**

```csharp
// Query with multi-property ORDER BY
var query = @"
    SELECT * FROM c 
    WHERE c.status = 'active' 
    ORDER BY c.createdAt DESC, c.priority ASC";

// Without composite index, this may:
// 1. Fail with: "Order-by item requires a corresponding composite index"
// 2. Or consume excessive RU for sorting
```

**Correct (composite index for ORDER BY):**

```csharp
// Create composite index matching the ORDER BY
var indexingPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,
    
    CompositeIndexes =
    {
        // Must match ORDER BY exactly (properties and sort order)
        new Collection<CompositePath>
        {
            new CompositePath { Path = "/createdAt", Order = CompositePathSortOrder.Descending },
            new CompositePath { Path = "/priority", Order = CompositePathSortOrder.Ascending }
        },
        
        // Add reverse order for flexibility
        new Collection<CompositePath>
        {
            new CompositePath { Path = "/createdAt", Order = CompositePathSortOrder.Ascending },
            new CompositePath { Path = "/priority", Order = CompositePathSortOrder.Descending }
        },
        
        // Common filter + sort pattern
        new Collection<CompositePath>
        {
            new CompositePath { Path = "/status", Order = CompositePathSortOrder.Ascending },
            new CompositePath { Path = "/createdAt", Order = CompositePathSortOrder.Descending }
        }
    }
};

var containerProperties = new ContainerProperties
{
    Id = "tasks",
    PartitionKeyPath = "/userId",
    IndexingPolicy = indexingPolicy
};
```

```json
// JSON indexing policy with composite indexes
{
    "indexingMode": "consistent",
    "automatic": true,
    "includedPaths": [
        { "path": "/*" }
    ],
    "compositeIndexes": [
        [
            { "path": "/status", "order": "ascending" },
            { "path": "/createdAt", "order": "descending" }
        ],
        [
            { "path": "/createdAt", "order": "descending" },
            { "path": "/priority", "order": "ascending" }
        ]
    ]
}
```

```csharp
// Common patterns that need composite indexes:

// Pattern 1: Filter + Sort
// WHERE status = 'x' ORDER BY date DESC
new Collection<CompositePath>
{
    new CompositePath { Path = "/status", Order = CompositePathSortOrder.Ascending },
    new CompositePath { Path = "/date", Order = CompositePathSortOrder.Descending }
}

// Pattern 2: Multi-column sort
// ORDER BY lastName ASC, firstName ASC
new Collection<CompositePath>
{
    new CompositePath { Path = "/lastName", Order = CompositePathSortOrder.Ascending },
    new CompositePath { Path = "/firstName", Order = CompositePathSortOrder.Ascending }
}

// Pattern 3: Range + Sort
// WHERE price >= 10 ORDER BY rating DESC
new Collection<CompositePath>
{
    new CompositePath { Path = "/price", Order = CompositePathSortOrder.Ascending },
    new CompositePath { Path = "/rating", Order = CompositePathSortOrder.Descending }
}
```

### Multi-Tenant Composite Index Patterns

In multi-tenant designs using type discriminators and hierarchical partition keys, composite indexes are **critical** for queries that filter by entity type and sort by common fields:

```json
// Multi-tenant SaaS: tasks by status, sorted by date
{
    "compositeIndexes": [
        [
            { "path": "/type", "order": "ascending" },
            { "path": "/status", "order": "ascending" },
            { "path": "/createdAt", "order": "descending" }
        ],
        [
            { "path": "/type", "order": "ascending" },
            { "path": "/assigneeId", "order": "ascending" },
            { "path": "/dueDate", "order": "ascending" }
        ],
        [
            { "path": "/type", "order": "ascending" },
            { "path": "/priority", "order": "descending" },
            { "path": "/createdAt", "order": "descending" }
        ]
    ]
}
```

```java
// Java: Composite indexes with IndexingPolicy
IndexingPolicy policy = new IndexingPolicy();

// Type + Status + Date (for: WHERE type='task' AND status='open' ORDER BY createdAt DESC)
List<CompositePath> statusSort = Arrays.asList(
    new CompositePath().setPath("/type").setOrder(CompositePathSortOrder.ASCENDING),
    new CompositePath().setPath("/status").setOrder(CompositePathSortOrder.ASCENDING),
    new CompositePath().setPath("/createdAt").setOrder(CompositePathSortOrder.DESCENDING)
);

// Type + Assignee + DueDate (for: WHERE type='task' AND assigneeId=@id ORDER BY dueDate)
List<CompositePath> assigneeSort = Arrays.asList(
    new CompositePath().setPath("/type").setOrder(CompositePathSortOrder.ASCENDING),
    new CompositePath().setPath("/assigneeId").setOrder(CompositePathSortOrder.ASCENDING),
    new CompositePath().setPath("/dueDate").setOrder(CompositePathSortOrder.ASCENDING)
);

policy.setCompositeIndexes(Arrays.asList(statusSort, assigneeSort));
```

```rust
// Rust (azure_data_cosmos): Composite indexes via JSON deserialization
// CompositeIndex types cannot be constructed directly (marked non_exhaustive),
// so use JSON deserialization instead
use azure_data_cosmos::models::{ContainerProperties, IndexingPolicy, PartitionKeyDefinition};

let indexing_policy: IndexingPolicy = serde_json::from_value(serde_json::json!({
    "automatic": true,
    "indexingMode": "consistent",
    "includedPaths": [{"path": "/*"}],
    "excludedPaths": [{"path": "/_etag/?"}],
    "compositeIndexes": [
        [
            {"path": "/status", "order": "ascending"},
            {"path": "/createdAt", "order": "descending"}
        ],
        [
            {"path": "/customerId", "order": "ascending"},
            {"path": "/createdAt", "order": "descending"}
        ]
    ]
})).expect("valid indexing policy JSON");

let properties = ContainerProperties::new(
    "orders".to_string(),
    PartitionKeyDefinition::new(vec!["/customerId".to_string()]),
)
.with_indexing_policy(indexing_policy);

// Create container with composite indexes
db_client.create_container(properties, None).await?;
```

**Why type discriminators need composite indexes:**
When a single container holds multiple entity types (tenant, user, project, task), queries always filter by `type`. Without a composite index on `(type, sortField)`, the query engine cannot efficiently sort within a single entity type. This is especially costly in containers with millions of mixed-type documents.

### Node.js / TypeScript (@azure/cosmos v4)

**Incorrect (container created with default indexing policy — no composites):**

```typescript
// ❌ No indexingPolicy → default (indexes everything, no composite)
await database.containers.createIfNotExists({
  id: 'orders',
  partitionKey: { paths: ['/userId'] },
});

// This query works on the emulator but FAILS in production:
await container.items.query({
  query: 'SELECT * FROM c WHERE c.userId = @u ORDER BY c.createdAt DESC',
  parameters: [{ name: '@u', value: userId }],
}, { partitionKey: userId }).fetchAll();
```

**Correct (composite indexes declared at container creation):**

```typescript
import { IndexingPolicy } from '@azure/cosmos';

// ✅ Declare composite indexes alongside container creation
const ordersIndexingPolicy: IndexingPolicy = {
  indexingMode: 'consistent',
  automatic: true,
  includedPaths: [{ path: '/*' }],
  excludedPaths: [{ path: '/"_etag"/?' }],
  compositeIndexes: [
    // WHERE c.userId = @u ORDER BY c.createdAt DESC
    [
      { path: '/userId', order: 'ascending' },
      { path: '/createdAt', order: 'descending' },
    ],
    // WHERE c.userId = @u AND c.status = @s ORDER BY c.createdAt DESC
    [
      { path: '/userId', order: 'ascending' },
      { path: '/status', order: 'ascending' },
      { path: '/createdAt', order: 'descending' },
    ],
  ],
};

await database.containers.createIfNotExists({
  id: 'orders',
  partitionKey: { paths: ['/userId'] },
  indexingPolicy: ordersIndexingPolicy,
});
```

**Updating an existing container's indexing policy:**

```typescript
// Replace indexing policy on an existing container
const { resource: existing } = await database.container('orders').read();
await database.container('orders').replace({
  id: 'orders',
  partitionKey: existing!.partitionKey,
  indexingPolicy: ordersIndexingPolicy,
});
// Indexing is rebuilt in the background; monitor indexTransformationProgress
```

Rules:
- Composite index order must match ORDER BY exactly
- First path can be equality filter
- Include both ASC/DESC variants for flexibility
- Maximum 8 paths per composite index
- Composite indexes consume additional write RU — declare only the composites you actually query against
- **Always** define composite indexes when using type discriminators in shared containers
- Include `/type` as the first path in multi-tenant composite indexes

Reference: [Composite indexes](https://learn.microsoft.com/azure/cosmos-db/index-policy#composite-indexes)

### 1.3 Exclude Unused Index Paths

**Impact: HIGH** (reduces write RU by 20-80%)

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

**Correct (exclude-all-first, then include back):**

```csharp
// Exclude everything, then include only what you query
var indexingPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,
    Automatic = true,
    
    // Start with exclude all — no field is indexed by default
    ExcludedPaths = { new ExcludedPath { Path = "/*" } },
    
    // Explicitly include only what you query
    IncludedPaths =
    {
        new IncludedPath { Path = "/customerId/?" },
        new IncludedPath { Path = "/status/?" },
        new IncludedPath { Path = "/orderDate/?" },
        new IncludedPath { Path = "/total/?" }
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
    "excludedPaths": [
        { "path": "/*" }
    ],
    "includedPaths": [
        { "path": "/customerId/?" },
        { "path": "/status/?" },
        { "path": "/orderDate/?" },
        { "path": "/total/?" }
    ]
}
```

⚠️ **Alternative (less optimal — indexes all paths by default):**

```csharp
// Selectively include and exclude paths
// WARNING: any new fields added to documents are auto-indexed
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
    
    // Exclude known unused paths (but new fields still auto-indexed)
    ExcludedPaths =
    {
        new ExcludedPath { Path = "/items/*" },         // Embedded array
        new ExcludedPath { Path = "/internalNotes/?" },
        new ExcludedPath { Path = "/auditLog/*" },      // Large array
        new ExcludedPath { Path = "/_etag/?" }          // System field
    }
};
```

Monitor and adjust:
- Review query patterns periodically
- Use Query Stats to see index utilization
- Balance write cost reduction vs query flexibility

Reference: [Indexing policies](https://learn.microsoft.com/azure/cosmos-db/index-policy)

### 1.4 Understand Indexing Modes

**Impact: MEDIUM** (balances write speed vs query consistency)

## Understand Indexing Modes

Choose the appropriate indexing mode based on your workload. Consistent mode ensures query results are current; None disables indexing entirely.

**Indexing modes explained:**

```csharp
// CONSISTENT MODE (Default - recommended for most cases)
// Indexes are updated synchronously with writes
// Queries always see latest data
var consistentPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,  // Default
    Automatic = true
};

// Benefits:
// - Query results are always up-to-date
// - Strong consistency between writes and reads
// Tradeoffs:
// - Write latency includes index update time
```

```csharp
// NONE MODE (Write-only containers)
// No automatic indexing - fastest writes
// Only point reads work (by id + partition key)
var nonePolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.None,
    Automatic = false
};

// Use cases:
// - Pure key-value store (only point reads)
// - High-volume write ingestion
// - Time-series data queried via external system (Synapse Link)
```

**Correct (choosing mode based on workload):**

```csharp
// Typical transactional workload - use Consistent
var ordersPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,
    Automatic = true,
    IncludedPaths = { new IncludedPath { Path = "/*" } }
};

var ordersContainer = new ContainerProperties
{
    Id = "orders",
    PartitionKeyPath = "/customerId",
    IndexingPolicy = ordersPolicy
};
// Queries immediately see new orders
```

```csharp
// High-volume telemetry ingestion - consider None
var telemetryPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.None,  // Maximum write throughput
    Automatic = false
};

var telemetryContainer = new ContainerProperties
{
    Id = "telemetry",
    PartitionKeyPath = "/deviceId",
    IndexingPolicy = telemetryPolicy,
    
    // Enable analytical store for querying via Synapse
    AnalyticalStorageTimeToLiveInSeconds = -1
};

// Point reads still work
var reading = await container.ReadItemAsync<Telemetry>(
    readingId, new PartitionKey(deviceId));

// Complex queries via Synapse Link (analytical store)
// No indexing overhead on transactional writes
```

```csharp
// Selective indexing - best of both worlds
var hybridPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,
    Automatic = true,
    
    // Only index fields you query
    IncludedPaths =
    {
        new IncludedPath { Path = "/customerId/?" },
        new IncludedPath { Path = "/orderDate/?" }
    },
    ExcludedPaths =
    {
        new ExcludedPath { Path = "/*" }  // Exclude everything else
    }
};
// Fast writes (minimal indexing) + efficient queries (on indexed paths)
```

Decision guide:
- **Consistent**: Default, transactional workloads, need queries
- **None**: Write-only, pure key-value, using Synapse Link for analytics

Note: Lazy mode was deprecated - use Consistent instead.

Reference: [Indexing modes](https://learn.microsoft.com/azure/cosmos-db/index-policy#indexing-mode)

### 1.5 Use Correct Indexing Path Syntax

**Impact: HIGH** (prevents container creation failures from invalid paths)

## Use Correct Indexing Path Syntax

Cosmos DB indexing paths use specific notation for scalars, arrays, and wildcards. Using the wrong notation causes container creation to fail with a BadRequest error.

**Three valid path notations:**

| Notation | Meaning | Example |
|----------|---------|---------|
| `/?` | Scalar value (string or number) | `/price/?` |
| `/[]` | Array element traversal | `/items/[]/name/?` |
| `/*` | **Terminal** wildcard — everything below this node | `/metadata/*` |

**Incorrect (using `*` for array traversal):**

```json
// ❌ WRONG — * cannot be used mid-path for array traversal
// This causes: "The indexing path could not be accepted, failed near position ..."
{
    "excludedPaths": [
        { "path": "/lineItems/*/productSnapshot/?" },
        { "path": "/orders/*/items/?" }
    ]
}
```

**Correct (using `[]` for array traversal):**

```json
// ✅ CORRECT — use [] to traverse array elements
{
    "excludedPaths": [
        { "path": "/lineItems/[]/productSnapshot/?" },
        { "path": "/orders/[]/items/?" }
    ]
}
```

**Correct (terminal `*` wildcard for subtree):**

```json
// ✅ CORRECT — * at the END of a path matches everything below
{
    "includedPaths": [
        { "path": "/*" }
    ],
    "excludedPaths": [
        { "path": "/metadata/*" },
        { "path": "/auditLog/*" },
        { "path": "/\"_etag\"/?" }
    ]
}
```

**Common patterns:**

```json
{
    "includedPaths": [
        { "path": "/*" }
    ],
    "excludedPaths": [
        { "path": "/\"_etag\"/?" },
        { "path": "/largeBlob/*" },
        { "path": "/items/[]/internalNotes/?" },
        { "path": "/events/[]/payload/*" }
    ]
}
```

**Key rules:**

- `/?` terminates a path to a scalar value — use for leaf properties
- `/[]` traverses into array elements — use when the parent is an array and you need to reach nested properties
- `/*` is a terminal wildcard — it means "all descendants" and must be the LAST segment in the path
- **NEVER** use `*` in the middle of a path (e.g., `/items/*/name/?` is INVALID)
- For composite indexes, paths do NOT use `/?` or `/*` — they have an implicit `/?` at the end. Use `/[]` for array traversal in composite paths (e.g., `/children/[]/age`)

Reference: [Indexing policy path syntax](https://learn.microsoft.com/azure/cosmos-db/index-policy#include-exclude-paths)

### 1.6 Choose Appropriate Index Types

**Impact: MEDIUM** (optimizes query performance)

## Choose Appropriate Index Types

Understand when to use different index types. Range indexes support equality, range, and ORDER BY; Hash indexes are deprecated.

**Understanding index types:**

```csharp
// Range Index (DEFAULT - recommended for most cases)
// Supports: =, >, <, >=, <=, !=, ORDER BY, JOINs
// Index entries: ["a"], ["a", "b"], ["a", "b", "c"]...
{
    "includedPaths": [
        {
            "path": "/price/?",
            "indexes": [
                {
                    "kind": "Range",  // Default, most flexible
                    "dataType": "Number",
                    "precision": -1   // -1 = maximum precision
                },
                {
                    "kind": "Range",
                    "dataType": "String",
                    "precision": -1
                }
            ]
        }
    ]
}
```

**Correct (modern indexing approach):**

```csharp
// Modern Cosmos DB automatically uses optimal index types
// You typically just specify paths, not index kinds
var indexingPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,
    Automatic = true,
    
    // Just specify paths - Cosmos DB handles index types
    IncludedPaths =
    {
        new IncludedPath { Path = "/category/?" },    // Equality queries
        new IncludedPath { Path = "/price/?" },       // Range queries
        new IncludedPath { Path = "/createdAt/?" },   // ORDER BY
        new IncludedPath { Path = "/tags/*" }         // Array elements
    },
    
    ExcludedPaths =
    {
        new ExcludedPath { Path = "/description/?" },  // Large text, not queried
        new ExcludedPath { Path = "/metadata/*" }      // Nested object, not queried
    }
};
```

```csharp
// For special query patterns, add composite or spatial indexes

var indexingPolicy = new IndexingPolicy
{
    // Standard range indexes (automatic)
    IncludedPaths =
    {
        new IncludedPath { Path = "/*" }  // Index everything by default
    },
    
    // Composite indexes for multi-property ORDER BY
    CompositeIndexes =
    {
        new Collection<CompositePath>
        {
            new CompositePath { Path = "/category", Order = CompositePathSortOrder.Ascending },
            new CompositePath { Path = "/price", Order = CompositePathSortOrder.Descending }
        }
    },
    
    // Spatial indexes for geo queries
    SpatialIndexes =
    {
        new SpatialPath
        {
            Path = "/location/?",
            SpatialTypes = { SpatialType.Point }
        }
    }
};
```

```json
// JSON policy showing all index types
{
    "indexingMode": "consistent",
    "automatic": true,
    "includedPaths": [
        { "path": "/*" }
    ],
    "excludedPaths": [
        { "path": "/largeContent/?" }
    ],
    "compositeIndexes": [
        [
            { "path": "/status", "order": "ascending" },
            { "path": "/createdAt", "order": "descending" }
        ]
    ],
    "spatialIndexes": [
        {
            "path": "/location/?",
            "types": ["Point"]
        }
    ]
}
```

Index type summary:
- **Range (default)**: Equality, range, ORDER BY - use for everything
- **Composite**: Multi-property ORDER BY, filter+sort
- **Spatial**: Geographic/geometric queries
- **Hash**: DEPRECATED - don't use

Reference: [Index types](https://learn.microsoft.com/azure/cosmos-db/index-overview)

### 1.7 Add Spatial Indexes for Geo Queries

**Impact: MEDIUM-HIGH** (enables efficient location queries)

## Add Spatial Indexes for Geo Queries

Create spatial indexes for properties that store geographic data when you need to perform proximity or geometry queries.

**Incorrect (geo queries without spatial index):**

```csharp
// Document with location
{
    "id": "store-1",
    "name": "Downtown Store",
    "location": {
        "type": "Point",
        "coordinates": [-122.4194, 37.7749]  // [longitude, latitude]
    }
}

// Query without spatial index - expensive full scan!
var query = @"
    SELECT * FROM c 
    WHERE ST_DISTANCE(c.location, {'type':'Point','coordinates':[-122.4,37.7]}) < 5000";
```

**Correct (spatial index for location queries):**

```csharp
// Create indexing policy with spatial index
var indexingPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,
    
    // Include path with spatial index
    SpatialIndexes =
    {
        new SpatialPath
        {
            Path = "/location/?",
            SpatialTypes =
            {
                SpatialType.Point
            }
        }
    }
};

// If you have multiple geometry types
var indexingPolicyMulti = new IndexingPolicy
{
    SpatialIndexes =
    {
        // Store locations as points
        new SpatialPath
        {
            Path = "/location/?",
            SpatialTypes = { SpatialType.Point }
        },
        // Delivery zones as polygons
        new SpatialPath
        {
            Path = "/deliveryArea/?",
            SpatialTypes = { SpatialType.Polygon }
        }
    }
};
```

```json
// JSON indexing policy with spatial index
{
    "indexingMode": "consistent",
    "spatialIndexes": [
        {
            "path": "/location/?",
            "types": ["Point"]
        },
        {
            "path": "/boundaries/?",
            "types": ["Polygon"]
        }
    ]
}
```

```csharp
// Efficient spatial queries with index

// Find stores within 5km of user
var nearbyQuery = @"
    SELECT c.name, c.address, 
           ST_DISTANCE(c.location, @userLocation) AS distanceMeters
    FROM c 
    WHERE ST_DISTANCE(c.location, @userLocation) < 5000
    ORDER BY ST_DISTANCE(c.location, @userLocation)";

var userLocation = new
{
    type = "Point",
    coordinates = new[] { -122.4194, 37.7749 }
};

var stores = await container.GetItemQueryIterator<Store>(
    new QueryDefinition(nearbyQuery)
        .WithParameter("@userLocation", userLocation)
).ReadNextAsync();

// Check if point is within polygon (delivery zone)
var withinQuery = @"
    SELECT * FROM c 
    WHERE ST_WITHIN(@orderLocation, c.deliveryArea)";

// Find intersecting regions
var intersectQuery = @"
    SELECT * FROM c 
    WHERE ST_INTERSECTS(c.boundaries, @searchArea)";
```

Supported spatial functions:
- `ST_DISTANCE` - Distance between geometries
- `ST_WITHIN` - Point within polygon
- `ST_INTERSECTS` - Geometries intersect
- `ST_ISVALID` - Validate GeoJSON
- `ST_ISVALIDDETAILED` - Validation with details

Reference: [Geospatial queries](https://learn.microsoft.com/azure/cosmos-db/nosql/query/geospatial)

---

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
