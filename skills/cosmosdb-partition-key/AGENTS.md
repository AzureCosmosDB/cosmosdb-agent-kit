# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Best practices for Azure Cosmos DB partition key design: high cardinality, hotspot avoidance, hierarchical keys, synthetic keys, query alignment, and partition size limits.

---

## Table of Contents

1. [Partition Key Design](#1-partition-key-design) — **CRITICAL**
   - 1.1 [Plan for 20GB Logical Partition Limit](#11-plan-for-20gb-logical-partition-limit)
   - 1.2 [Distribute Writes to Avoid Hot Partitions](#12-distribute-writes-to-avoid-hot-partitions)
   - 1.3 [Use Hierarchical Partition Keys for Flexibility](#13-use-hierarchical-partition-keys-for-flexibility)
   - 1.4 [Choose High-Cardinality Partition Keys](#14-choose-high-cardinality-partition-keys)
   - 1.5 [Choose Immutable Properties as Partition Keys](#15-choose-immutable-properties-as-partition-keys)
   - 1.6 [Respect Partition Key Value Length Limits](#16-respect-partition-key-value-length-limits)
   - 1.7 [Align Partition Key with Query Patterns](#17-align-partition-key-with-query-patterns)
   - 1.8 [Create Synthetic Partition Keys When Needed](#18-create-synthetic-partition-keys-when-needed)

---

## 1. Partition Key Design

**Impact: CRITICAL**

### 1.1 Plan for 20GB Logical Partition Limit

**Impact: HIGH** (prevents partition split failures)

## Plan for 20GB Logical Partition Limit

Each logical partition has a 20GB storage limit. Design partition keys to ensure no single partition value accumulates more than 20GB.

**Incorrect (unbounded partition growth):**

```csharp
// Anti-pattern: partition key with unbounded data accumulation
public class AuditLog
{
    public string Id { get; set; }
    public string SystemId { get; set; }  // Partition key - only 3 systems!
    public DateTime Timestamp { get; set; }
    public string Action { get; set; }
    public string Details { get; set; }
}

// Problem: Each system accumulates logs forever
// "system-a" partition will eventually hit 20GB
// Writes will fail with: PartitionKeyRangeIsFull
```

**Correct (bounded partition growth):**

```csharp
// Solution 1: Time-bucket the partition key
public class AuditLog
{
    public string Id { get; set; }
    public string SystemId { get; set; }
    public DateTime Timestamp { get; set; }
    
    // Partition by system + month
    public string PartitionKey => $"{SystemId}_{Timestamp:yyyy-MM}";
}

// Each partition holds ~1 month of data per system
// Old partitions naturally stop growing
```

```csharp
// Solution 2: Use hierarchical partition keys
var containerProperties = new ContainerProperties
{
    Id = "audit-logs",
    PartitionKeyPaths = new List<string> 
    { 
        "/systemId",
        "/yearMonth"  // Secondary level prevents 20GB limit
    }
};

public class AuditLog
{
    public string Id { get; set; }
    public string SystemId { get; set; }
    public string YearMonth { get; set; }  // "2026-01"
    public DateTime Timestamp { get; set; }
}
```

```csharp
// Monitor partition sizes
public async Task CheckPartitionSizes()
{
    var partitionKeyRanges = container.GetFeedRanges();
    
    foreach (var range in await partitionKeyRanges)
    {
        var iterator = container.GetItemQueryIterator<dynamic>(
            "SELECT * FROM c",
            requestOptions: new QueryRequestOptions { FeedRange = range });
        
        // Check size via metrics or diagnostic headers
        var response = await iterator.ReadNextAsync();
        _logger.LogInformation(
            "Partition {Range}: {Count} items, {RU} RU", 
            range, response.Count, response.RequestCharge);
    }
}

// Set up alerts before hitting limits
// Azure Monitor: PartitionKeyRangeId with high storage
```

Capacity planning:
- Estimate item count per partition key value
- Calculate average item size × item count
- Target < 10GB per partition value (50% safety margin)
- Consider time-based bucketing for growing data

Reference: [Partition key limits](https://learn.microsoft.com/azure/cosmos-db/concepts-limits#per-logical-partition)

### 1.2 Distribute Writes to Avoid Hot Partitions

**Impact: CRITICAL** (prevents throughput bottlenecks)

## Distribute Writes to Avoid Hot Partitions

Ensure writes distribute evenly across partitions. A hot partition limits throughput to that single partition's capacity.

**Incorrect (all writes hit single partition):**

```csharp
// Anti-pattern: time-based partition key with current-time writes
public class Event
{
    public string Id { get; set; }
    
    // All events for "today" go to same partition!
    public string Date { get; set; }  // ❌ "2026-01-21" - HOT!
}

// All current writes bottleneck on today's partition
// Yesterday's partition sits idle
await container.CreateItemAsync(new Event 
{ 
    Id = Guid.NewGuid().ToString(),
    Date = DateTime.UtcNow.ToString("yyyy-MM-dd")  // All writes here!
});
```

```csharp
// Anti-pattern: singleton partition key
public class Config
{
    public string Id { get; set; }
    public string PartitionKey { get; set; } = "config";  // ❌ ONE partition!
}
// Everything in single 10K RU/s max partition
```

**Correct (distributed writes):**

```csharp
// Good: write-sharding for time-series data
public class Event
{
    public string Id { get; set; }
    
    // Combine date with hash suffix for distribution
    public string PartitionKey { get; set; }  // "2026-01-21_shard3"
}

public static string CreateTimeShardedKey(DateTime timestamp, int shardCount = 10)
{
    var dateKey = timestamp.ToString("yyyy-MM-dd");
    var shard = Math.Abs(Guid.NewGuid().GetHashCode()) % shardCount;
    return $"{dateKey}_shard{shard}";
}

// Writes distribute across 10 partitions per day
await container.CreateItemAsync(new Event 
{ 
    Id = Guid.NewGuid().ToString(),
    PartitionKey = CreateTimeShardedKey(DateTime.UtcNow)
});
```

```csharp
// Good: natural distribution with entity IDs
public class Order
{
    public string Id { get; set; }
    public string CustomerId { get; set; }  // ✅ Natural distribution
    public DateTime OrderDate { get; set; }
}

// Each customer's orders in their own partition
// Writes naturally spread across many customers
```

Monitor for hot partitions:
- Check Metrics → Normalized RU Consumption
- Look for partitions consistently at 100%
- Use Azure Monitor alerts for throttling

**Partition Limits (as of current Azure Cosmos DB documentation):**
   - Physical partition throughput limit: **10,000 RU/s** per physical partition  
     See [Azure Cosmos DB partitioning – physical partitions](https://learn.microsoft.com/azure/cosmos-db/partitioning-overview#physical-partitions).
   - Logical partition size limit: **20 GB** per logical partition  
     See [Azure Cosmos DB partitioning – logical partitions](https://learn.microsoft.com/azure/cosmos-db/partitioning-overview#logical-partitions).
   - Physical partition size: **50 GB** per physical partition  
     See [Azure Cosmos DB partitioning – physical partitions](https://learn.microsoft.com/azure/cosmos-db/partitioning-overview#physical-partitions).

   > These limits can evolve over time and may vary by region/offer. Always confirm against the latest Azure Cosmos DB documentation for your account.

**Popularity Skew Warning for Hot Partitions:** Even high-cardinality keys (like `user_id`) can create hot partitions when specific values get dramatically more traffic (e.g., a viral user during peak moments).

### 1.3 Use Hierarchical Partition Keys for Flexibility

**Impact: HIGH** (overcomes 20GB limit, enables targeted queries)

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

// Must spread tenant data manually
// Queries across "big-tenant_shard1", "big-tenant_shard2" are complex
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
        "/year",       // Level 2: Year  
        "/month"       // Level 3: Month (optional)
    }
};

await database.CreateContainerAsync(containerProperties, throughput: 10000);

// Document with hierarchical key
public class Document
{
    public string Id { get; set; }
    public string TenantId { get; set; }
    public int Year { get; set; }
    public int Month { get; set; }
    public string Content { get; set; }
}

// Query targeting specific levels
// Level 1 only: scans all partitions for tenant
var tenantDocs = container.GetItemQueryIterator<Document>(
    new QueryDefinition("SELECT * FROM c WHERE c.tenantId = @tenant")
        .WithParameter("@tenant", "acme-corp"));

// Level 1+2: targets specific year partitions
var yearDocs = container.GetItemQueryIterator<Document>(
    new QueryDefinition("SELECT * FROM c WHERE c.tenantId = @tenant AND c.year = @year")
        .WithParameter("@tenant", "acme-corp")
        .WithParameter("@year", 2026),
    requestOptions: new QueryRequestOptions
    {
        PartitionKey = new PartitionKeyBuilder()
            .Add("acme-corp")
            .Add(2026)
            .Build()
    });

// Full key: single partition point read
var doc = await container.ReadItemAsync<Document>(
    docId,
    new PartitionKeyBuilder()
        .Add("acme-corp")
        .Add(2026)
        .Add(1)
        .Build());
```

**Python SDK example (hierarchical partition keys):**

```python
from azure.cosmos import PartitionKey

# Incorrect: single-level partition key for a large tenant workload
container = await database.create_container_if_not_exists(
    id="documents",
    partition_key=PartitionKey(path="/tenantId"),
)

# Correct: hierarchical partition key (broadest -> narrowest)
container = await database.create_container_if_not_exists(
    id="documents",
    partition_key=PartitionKey(
        path=["/tenantId", "/year", "/month"],
        kind="MultiHash",
    ),
)

# Point read with full partition key path values
item = await container.read_item(
    item="doc-123",
    partition_key=["acme-corp", 2026, 1],
)

# Prefix query scoped to Level 1 + Level 2
items = container.query_items(
    query="SELECT * FROM c WHERE c.tenantId = @tenant AND c.year = @year",
    parameters=[
        {"name": "@tenant", "value": "acme-corp"},
        {"name": "@year", "value": 2026},
    ],
    partition_key=["acme-corp", 2026],
)
```

**Order levels from broadest to narrowest scope.** HPK prefix queries work left-to-right — a query can efficiently target Level 1 alone, Levels 1+2, or Levels 1+2+3, but cannot efficiently target Level 3 alone without scanning all Level 1 and Level 2 combinations. Place the property that appears in the most queries at Level 1 (broadest), the next most common at Level 2, and the most granular at Level 3. This ensures the dominant access pattern always benefits from prefix-based routing.

**❌ Wrong — narrow before broad:**

```csharp
// Misordered: narrow scope before broad scope
var containerProperties = new ContainerProperties
{
    Id = "documents",
    PartitionKeyPaths = new List<string> 
    { 
        "/month",      // Level 1: Narrow (only 12 values)
        "/year",       // Level 2: Medium cardinality
        "/tenantId"    // Level 3: Broadest — but it's last!
    }
};

// Prefix queries work LEFT to RIGHT:
// ✅ Query by month only → targets 1 of 12 level-1 groups (very coarse, rarely useful)
// ✅ Query by month + year → targets specific month-year combo
// ❌ Query by tenantId ONLY → must scan ALL month/year combinations
//    because tenantId is at level 3, not queryable as a prefix
// The most common query ("get all docs for a tenant") becomes the MOST expensive
```

**✅ Right — broad to narrow:**

```csharp
// Correct: broad → narrow ordering
var containerProperties = new ContainerProperties
{
    Id = "documents",
    PartitionKeyPaths = new List<string> 
    { 
        "/tenantId",   // Level 1: Broadest — most common filter
        "/year",       // Level 2: Time-based narrowing
        "/month"       // Level 3: Finest granularity
    }
};

// Prefix queries work efficiently:
// ✅ Query by tenantId → targets all partitions for ONE tenant
// ✅ Query by tenantId + year → narrows to tenant's yearly data
// ✅ Query by tenantId + year + month → single logical partition
// The most common query ("get all docs for a tenant") is the CHEAPEST
```

Benefits of HPK:
- Each level combination creates separate logical partitions (no 20GB limit per tenant)
- Queries can target specific levels for efficiency
- Natural data organization (tenant → year → month)

Reference: [Hierarchical partition keys](https://learn.microsoft.com/en-us/azure/cosmos-db/hierarchical-partition-keys?tabs=python%2Cbicep#sdk)

### 1.4 Choose High-Cardinality Partition Keys

**Impact: CRITICAL** (enables horizontal scalability)

## Choose High-Cardinality Partition Keys

Select partition keys with many unique values to ensure even data distribution. Low-cardinality keys create hot partitions.

**Incorrect (low cardinality creates hotspots):**

```csharp
// Anti-pattern: using status as partition key
public class Order
{
    public string Id { get; set; }
    
    // Only 5-10 unique values: "pending", "processing", "shipped", "delivered", "cancelled"
    public string Status { get; set; }  // ❌ BAD partition key!
}

// Result: All "pending" orders in ONE partition
// That partition becomes a hotspot during peak ordering!
```

```csharp
// Anti-pattern: using country as partition key
public class User
{
    public string Id { get; set; }
    
    // Only ~195 countries, uneven distribution
    public string Country { get; set; }  // ❌ BAD - US/India will be hot
}
```

**Correct (high cardinality with even distribution):**

```csharp
// Good: using unique identifier as partition key
public class Order
{
    public string Id { get; set; }
    
    // Millions of unique customers = even distribution
    public string CustomerId { get; set; }  // ✅ GOOD partition key
    
    public string Status { get; set; }  // Just a regular property now
}

// Good: using tenant ID for multi-tenant apps
public class Document
{
    public string Id { get; set; }
    
    // Each tenant gets their own partition(s)
    public string TenantId { get; set; }  // ✅ GOOD - natural isolation
}

// Good: using device ID for IoT
public class Telemetry
{
    public string Id { get; set; }
    
    // Thousands/millions of devices
    public string DeviceId { get; set; }  // ✅ GOOD partition key
    
    public DateTime Timestamp { get; set; }
    public double Temperature { get; set; }
}
```

Good partition keys typically:
- Have thousands to millions of unique values
- Match your most common query patterns
- Distribute writes evenly (no single key dominates)

Reference: [Partitioning in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/partitioning-overview)

### 1.5 Choose Immutable Properties as Partition Keys

**Impact: HIGH** (prevents data integrity issues from non-atomic key changes)

## Choose Immutable Properties as Partition Keys

Cosmos DB partition keys are immutable — you cannot update a document's partition key value in place. Changing it requires deleting the original document and reinserting with the new key, a non-atomic operation that risks data loss. Prefer creation-time values that never change.

**Incorrect (mutable field as partition key):**

```csharp
// Anti-pattern: status changes throughout the document lifecycle
public class Order
{
    public string Id { get; set; }
    public string Status { get; set; }  // ❌ Partition key — but it changes!
}

// "Updating" the partition key does NOT move the document between partitions
order.Status = "shipped";
await container.ReplaceItemAsync(order, order.Id, new PartitionKey("shipped"));
```

**Correct (immutable field as partition key):**

```csharp
public class Order
{
    public string Id { get; set; }
    public string CustomerId { get; set; }  // ✅ Set at creation, never changes
    public string Status { get; set; }       // Mutable — but NOT the partition key
}

order.Status = "shipped";
await container.ReplaceItemAsync(order, order.Id, new PartitionKey(order.CustomerId));
```

**Never use as partition keys:** status fields, workflow stages, ownership/assignment fields, or any property updated during the document lifecycle.

**Safe choices:** entity identifiers (userId, tenantId, deviceId), creation-time values, or synthetic keys derived from immutable fields.

Reference: [Change partition key value](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-change-partition-key-value)

### 1.6 Respect Partition Key Value Length Limits

**Impact: HIGH** (prevents write failures from oversized keys)

## Respect Partition Key Value Length Limits

Azure Cosmos DB enforces a maximum partition key value length of **2,048 bytes** (or **101 bytes** if large partition keys are not enabled). Exceeding this limit causes write failures at runtime.

**Incorrect (risk of exceeding partition key length):**

```csharp
// Anti-pattern: concatenating many fields into a partition key
public class Document
{
    public string Id { get; set; }
    
    // Partition key built from long descriptions - DANGER!
    public string PartitionKey => $"{TenantName}_{DepartmentName}_{TeamName}_{ProjectDescription}";
    
    public string TenantName { get; set; }       // Could be very long
    public string DepartmentName { get; set; }
    public string TeamName { get; set; }
    public string ProjectDescription { get; set; } // Unbounded user input
}

// If PartitionKey exceeds 2,048 bytes:
// Microsoft.Azure.Cosmos.CosmosException: Partition key value is too large
```

**Correct (bounded partition key values):**

```csharp
// Use short, bounded identifiers for partition keys
public class Document
{
    public string Id { get; set; }
    
    // Short, deterministic IDs - always well under 2,048 bytes
    public string TenantId { get; set; }        // e.g., "t-abc123"
    public string DepartmentId { get; set; }    // e.g., "dept-42"
    
    // Partition key uses compact identifiers
    public string PartitionKey => $"{TenantId}_{DepartmentId}";
    
    // Keep long text as regular properties, not in the partition key
    public string TenantName { get; set; }
    public string DepartmentName { get; set; }
    public string ProjectDescription { get; set; }
}
```

```csharp
// If you must derive a key from long values, hash or truncate them
public class Document
{
    public string Id { get; set; }
    public string LongCategoryPath { get; set; }  // e.g., deep taxonomy
    
    // Hash long values to a fixed-length partition key
    public string PartitionKey
    {
        get
        {
            using var sha = System.Security.Cryptography.SHA256.Create();
            var hash = sha.ComputeHash(Encoding.UTF8.GetBytes(LongCategoryPath));
            return Convert.ToBase64String(hash)[..16]; // Fixed 16-char key
        }
    }
}
```

Key points:
- Default limit is **101 bytes** without large partition key feature enabled
- With large partition keys enabled, limit increases to **2,048 bytes**
- Enable large partition keys for new containers if you need longer values
- Prefer short GUIDs, IDs, or codes over human-readable strings for partition keys

Reference: [Azure Cosmos DB service quotas - Per-item limits](https://learn.microsoft.com/azure/cosmos-db/concepts-limits#per-item-limits)

### 1.7 Align Partition Key with Query Patterns

**Impact: CRITICAL** (enables single-partition queries)

## Align Partition Key with Query Patterns

Choose a partition key that supports your most frequent queries. Single-partition queries are orders of magnitude faster than cross-partition.

**Incorrect (partition key misaligned with queries):**

```csharp
// Document partitioned by category
public class Product
{
    public string Id { get; set; }
    public string Category { get; set; }  // Partition key
    public string SellerId { get; set; }
}

// But most queries are by seller!
// This forces expensive cross-partition scan
var sellerProducts = container.GetItemQueryIterator<Product>(
    new QueryDefinition("SELECT * FROM c WHERE c.sellerId = @seller")
        .WithParameter("@seller", sellerId));
// Scans ALL partitions - high RU, high latency
```

**Correct (partition key matches query patterns):**

```csharp
// Step 1: Analyze your query patterns
// - 80% of queries: "Get all products for seller X"
// - 15% of queries: "Get product by ID"
// - 5% of queries: "Get products by category"

// Step 2: Choose partition key for dominant pattern
public class Product
{
    public string Id { get; set; }
    public string SellerId { get; set; }  // Partition key - matches 80% queries!
    public string Category { get; set; }
}

// Most common query is now single-partition
var sellerProducts = container.GetItemQueryIterator<Product>(
    new QueryDefinition("SELECT * FROM c WHERE c.sellerId = @seller")
        .WithParameter("@seller", sellerId),
    requestOptions: new QueryRequestOptions 
    { 
        PartitionKey = new PartitionKey(sellerId)  // Single partition!
    });
// Fast, low RU

// For less common category queries, accept cross-partition
// Or create a secondary container partitioned by category
```

```csharp
// E-commerce example: Orders partitioned by CustomerId
public class Order
{
    public string Id { get; set; }
    public string CustomerId { get; set; }  // Partition key
    public DateTime OrderDate { get; set; }
    public string Status { get; set; }
}

// "Show my orders" - single partition, fast
// "All orders today" - cross-partition, but rare admin query

// Chat example: Messages partitioned by ConversationId
public class Message
{
    public string Id { get; set; }
    public string ConversationId { get; set; }  // Partition key
    public string SenderId { get; set; }
    public string Content { get; set; }
}

// "Get messages in conversation" - single partition, fast
```

Reference: [Choose a partition key](https://learn.microsoft.com/azure/cosmos-db/partitioning-overview#choose-a-partition-key)

### 1.8 Create Synthetic Partition Keys When Needed

**Impact: HIGH** (optimizes for multiple access patterns)

## Create Synthetic Partition Keys When Needed

When no single natural field serves as an ideal partition key, create a synthetic key by combining multiple fields.

**Incorrect (forced to choose suboptimal natural key):**

```csharp
// IoT scenario: need to query by device AND time range
public class Telemetry
{
    public string Id { get; set; }
    public string DeviceId { get; set; }  // Partition key?
    public DateTime Timestamp { get; set; }
    public double Value { get; set; }
}

// If partitioned by DeviceId alone:
// - Old data accumulates forever in same partition
// - Time-range queries still scan entire partition

// If partitioned by Timestamp alone:
// - Device queries are cross-partition
// - Hot partition on current time
```

**Correct (synthetic partition key):**

```csharp
public class Telemetry
{
    public string Id { get; set; }
    public string DeviceId { get; set; }
    public DateTime Timestamp { get; set; }
    public double Value { get; set; }
    
    // Synthetic key combining device + time bucket
    public string PartitionKey => $"{DeviceId}_{Timestamp:yyyy-MM}";
}

// Creates partitions like: "device123_2026-01", "device123_2026-02"
// Benefits:
// - Single device's data spreads across time-based partitions
// - Time-range queries can target specific partitions
// - No partition grows indefinitely

// Query device for specific month - single partition
var query = container.GetItemQueryIterator<Telemetry>(
    new QueryDefinition("SELECT * FROM c WHERE c.deviceId = @device")
        .WithParameter("@device", deviceId),
    requestOptions: new QueryRequestOptions
    {
        PartitionKey = new PartitionKey($"{deviceId}_2026-01")
    });
```

```csharp
// Multi-tenant with user-level isolation
public class UserDocument
{
    public string Id { get; set; }
    public string TenantId { get; set; }
    public string UserId { get; set; }
    
    // Synthetic key for tenant + user isolation
    public string PartitionKey => $"{TenantId}:{UserId}";
}

// Each user gets their own partition within tenant
// Query all user's docs - single partition
// Query tenant's docs - targeted cross-partition (just that tenant's users)
```

```csharp
// Order system with synthetic key
public class Order
{
    public string Id { get; set; }
    public string CustomerId { get; set; }
    public DateTime OrderDate { get; set; }
    
    // Combine customer + year for bounded partition growth
    public string PartitionKey => $"{CustomerId}_{OrderDate:yyyy}";
}
```

**Evaluate Hierarchical Partition Keys (HPK) when considering Synthetic Partition keys**:

   When suggesting synthetic partition keys as part of design, evaluate **Hierarchical Partition Keys (HPK)** as an alternative that provides efficient multi-level query boundaries without synthetic key complexity. 
   *(HPK natively supports efficient prefix-based cross-partition queries that synthetic keys cannot.)*

** Synthetic Key vs Hierarchical PK - Comparison table:**

   | Feature | Synthetic Key | Hierarchical PK |
   |---------|--------------|-----------------|
   | Query boundaries | Manual `STARTSWITH()` | Native prefix queries |
   | Key construction | Application-level string concat | Cosmos DB native |
   | Prefix queries | Inefficient (cross-partition) | Efficient (targeted) |
   
References:
- [Synthetic partition keys](https://learn.microsoft.com/azure/cosmos-db/nosql/synthetic-partition-keys)
- [Hierarchical partition keys (HPK)](https://learn.microsoft.com/azure/cosmos-db/nosql/hierarchical-partition-keys)
 
 *Additional HPK Considerations*: Evaluate HPK limitations and known issues for some SDKs, various connectors and account for Hierarchical Cardinality requirements of all levels.

---

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
