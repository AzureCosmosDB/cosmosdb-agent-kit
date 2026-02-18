# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
January 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Performance optimization and best practices guide for Azure Cosmos DB applications, ordered by impact. Contains rules for data modeling, partition key design, query optimization, SDK usage, indexing, throughput management, global distribution, and monitoring.

---

## Table of Contents

1. [Data Modeling](#1-data-modeling) — **CRITICAL**
   - 1.1 [Keep Items Well Under 2MB Limit](#11-keep-items-well-under-2mb-limit)
   - 1.2 [Denormalize for Read-Heavy Workloads](#12-denormalize-for-read-heavy-workloads)
   - 1.3 [Embed Related Data Retrieved Together](#13-embed-related-data-retrieved-together)
   - 1.4 [Reference Data When Items Grow Large](#14-reference-data-when-items-grow-large)
   - 1.5 [Version Your Document Schemas](#15-version-your-document-schemas)
   - 1.6 [Use Type Discriminators for Polymorphic Data](#16-use-type-discriminators-for-polymorphic-data)
2. [Partition Key Design](#2-partition-key-design) — **CRITICAL**
   - 2.1 [Plan for 20GB Logical Partition Limit](#21-plan-for-20gb-logical-partition-limit)
   - 2.2 [Distribute Writes to Avoid Hot Partitions](#22-distribute-writes-to-avoid-hot-partitions)
   - 2.3 [Use Hierarchical Partition Keys for Flexibility](#23-use-hierarchical-partition-keys-for-flexibility)
   - 2.4 [Choose High-Cardinality Partition Keys](#24-choose-high-cardinality-partition-keys)
   - 2.5 [Align Partition Key with Query Patterns](#25-align-partition-key-with-query-patterns)
   - 2.6 [Create Synthetic Partition Keys When Needed](#26-create-synthetic-partition-keys-when-needed)
3. [Query Optimization](#3-query-optimization) — **HIGH**
   - 3.1 [Minimize Cross-Partition Queries](#31-minimize-cross-partition-queries)
   - 3.2 [Avoid Full Container Scans](#32-avoid-full-container-scans)
   - 3.3 [Order Filters by Selectivity](#33-order-filters-by-selectivity)
   - 3.4 [Use Continuation Tokens for Pagination](#34-use-continuation-tokens-for-pagination)
   - 3.5 [Use Parameterized Queries](#35-use-parameterized-queries)
   - 3.6 [Project Only Needed Fields](#36-project-only-needed-fields)
4. [SDK Best Practices](#4-sdk-best-practices) — **HIGH**
   - 4.1 [Use Async APIs for Better Throughput](#41-use-async-apis-for-better-throughput)
   - 4.2 [Configure Threshold-Based Availability Strategy (Hedging)](#42-configure-threshold-based-availability-strategy-hedging-)
   - 4.3 [Configure Partition-Level Circuit Breaker](#43-configure-partition-level-circuit-breaker)
   - 4.4 [Use Direct Connection Mode for Production](#44-use-direct-connection-mode-for-production)
   - 4.5 [Log Diagnostics for Troubleshooting](#45-log-diagnostics-for-troubleshooting)
   - 4.6 [Configure SSL and connection mode for Cosmos DB Emulator](#46-configure-ssl-and-connection-mode-for-cosmos-db-emulator)
   - 4.7 [Use ETags for optimistic concurrency on read-modify-write operations](#47-use-etags-for-optimistic-concurrency-on-read-modify-write-operations)
   - 4.8 [Configure Excluded Regions for Dynamic Failover](#48-configure-excluded-regions-for-dynamic-failover)
   - 4.9 [Enable content response on write operations in Java SDK](#49-enable-content-response-on-write-operations-in-java-sdk)
   - 4.10 [Spring Boot and Java version compatibility for Cosmos DB SDK](#410-spring-boot-and-java-version-compatibility-for-cosmos-db-sdk)
   - 4.11 [Configure local development environment to avoid cloud connection conflicts](#411-configure-local-development-environment-to-avoid-cloud-connection-conflicts)
   - 4.12 [Explicitly reference Newtonsoft.Json package](#412-explicitly-reference-newtonsoft-json-package)
   - 4.13 [Configure Preferred Regions for Availability](#413-configure-preferred-regions-for-availability)
   - 4.14 [Handle 429 Errors with Retry-After](#414-handle-429-errors-with-retry-after)
   - 4.15 [Use consistent enum serialization between Cosmos SDK and application layer](#415-use-consistent-enum-serialization-between-cosmos-sdk-and-application-layer)
   - 4.16 [Reuse CosmosClient as Singleton](#416-reuse-cosmosclient-as-singleton)
5. [Indexing Strategies](#5-indexing-strategies) — **MEDIUM-HIGH**
   - 5.1 [Use Composite Indexes for ORDER BY](#51-use-composite-indexes-for-order-by)
   - 5.2 [Exclude Unused Index Paths](#52-exclude-unused-index-paths)
   - 5.3 [Understand Indexing Modes](#53-understand-indexing-modes)
   - 5.4 [Choose Appropriate Index Types](#54-choose-appropriate-index-types)
   - 5.5 [Add Spatial Indexes for Geo Queries](#55-add-spatial-indexes-for-geo-queries)
6. [Throughput & Scaling](#6-throughput-scaling) — **MEDIUM**
   - 6.1 [Use Autoscale for Variable Workloads](#61-use-autoscale-for-variable-workloads)
   - 6.2 [Understand Burst Capacity](#62-understand-burst-capacity)
   - 6.3 [Choose Container vs Database Throughput](#63-choose-container-vs-database-throughput)
   - 6.4 [Right-Size Provisioned Throughput](#64-right-size-provisioned-throughput)
   - 6.5 [Consider Serverless for Dev/Test](#65-consider-serverless-for-dev-test)
7. [Global Distribution](#7-global-distribution) — **MEDIUM**
   - 7.1 [Implement Conflict Resolution](#71-implement-conflict-resolution)
   - 7.2 [Choose Appropriate Consistency Level](#72-choose-appropriate-consistency-level)
   - 7.3 [Configure Automatic Failover](#73-configure-automatic-failover)
   - 7.4 [Configure Multi-Region Writes](#74-configure-multi-region-writes)
   - 7.5 [Add Read Regions Near Users](#75-add-read-regions-near-users)
   - 7.6 [Configure Zone Redundancy for High Availability](#76-configure-zone-redundancy-for-high-availability)
8. [Monitoring & Diagnostics](#8-monitoring-diagnostics) — **LOW-MEDIUM**
   - 8.1 [Integrate Azure Monitor](#81-integrate-azure-monitor)
   - 8.2 [Enable Diagnostic Logging](#82-enable-diagnostic-logging)
   - 8.3 [Monitor P99 Latency](#83-monitor-p99-latency)
   - 8.4 [Track RU Consumption](#84-track-ru-consumption)
   - 8.5 [Alert on Throttling (429s)](#85-alert-on-throttling-429s-)
9. [Design Patterns](#9-design-patterns) — **HIGH**
   - 9.1 [Use Change Feed for cross-partition query optimization with materialized views](#91-use-change-feed-for-cross-partition-query-optimization-with-materialized-views)
   - 9.2 [Use count-based or cached rank approaches instead of full partition scans for ranking](#92-use-count-based-or-cached-rank-approaches-instead-of-full-partition-scans-for-ranking)

---

## 1. Data Modeling

**Impact: CRITICAL**

### 1.1 Keep Items Well Under 2MB Limit

**Impact: CRITICAL** (prevents write failures)

## Keep Items Well Under 2MB Limit

Azure Cosmos DB enforces a 2MB maximum item size. Design documents to stay well under this limit to avoid runtime failures.

**Incorrect (risk of hitting limit):**

```csharp
// Anti-pattern: storing large binary data in documents
public class Document
{
    public string Id { get; set; }
    public string Name { get; set; }
    
    // Large base64-encoded file content - DANGER!
    public string FileContent { get; set; }  // Could be megabytes
    
    // Or large arrays that grow
    public List<AuditEntry> AuditLog { get; set; }  // Unbounded
}

// This will fail when content exceeds 2MB
await container.CreateItemAsync(doc);
// Microsoft.Azure.Cosmos.CosmosException: Request Entity Too Large
```

**Correct (bounded document size):**

```csharp
// Store metadata in Cosmos DB, large content in Blob Storage
public class Document
{
    public string Id { get; set; }
    public string Name { get; set; }
    public long FileSizeBytes { get; set; }
    public string ContentType { get; set; }
    
    // Reference to blob storage instead of inline content
    public string BlobUri { get; set; }
    
    // Keep only recent/relevant audit entries
    public List<AuditEntry> RecentAuditEntries { get; set; }  // Max 10-20 items
}

// Large content goes to Blob Storage
await blobClient.UploadAsync(largeFileStream);
var doc = new Document
{
    Id = Guid.NewGuid().ToString(),
    Name = "large-file.pdf",
    BlobUri = blobClient.Uri.ToString()
};
await container.CreateItemAsync(doc);
```

Size monitoring:

```csharp
// Check item size before writing
var json = JsonSerializer.Serialize(item);
var sizeBytes = Encoding.UTF8.GetByteCount(json);
if (sizeBytes > 1_500_000) // 1.5MB warning threshold
{
    _logger.LogWarning("Item approaching size limit: {SizeKB}KB", sizeBytes / 1024);
}
```

Reference: [Azure Cosmos DB service quotas](https://learn.microsoft.com/azure/cosmos-db/concepts-limits)

### 1.2 Denormalize for Read-Heavy Workloads

**Impact: HIGH** (reduces query RU by 2-10x)

## Denormalize for Read-Heavy Workloads

In read-heavy workloads, denormalize frequently-queried data to avoid expensive lookups. Accept write overhead for faster reads.

**Incorrect (normalized requires multiple queries):**

```csharp
// Displaying product list with category names
public class Product
{
    public string Id { get; set; }
    public string Name { get; set; }
    public string CategoryId { get; set; }  // Just the ID
    public decimal Price { get; set; }
}

// To display "Product Name - Category Name" requires JOIN-like pattern:
var products = await GetProductsAsync();
foreach (var product in products)
{
    // N+1 query problem!
    var category = await container.ReadItemAsync<Category>(
        product.CategoryId, new PartitionKey(product.CategoryId));
    product.CategoryName = category.Name;
}
// 1 + N queries = terrible performance
```

**Correct (denormalized for read efficiency):**

```csharp
public class Product
{
    public string Id { get; set; }
    public string Name { get; set; }
    public string CategoryId { get; set; }
    
    // Denormalized category info for display
    public string CategoryName { get; set; }
    public string CategorySlug { get; set; }
    
    public decimal Price { get; set; }
}

// Single query returns everything needed for display
var query = "SELECT c.id, c.name, c.categoryName, c.price FROM c WHERE c.type = 'product'";
var products = await container.GetItemQueryIterator<Product>(query).ReadNextAsync();
// No additional queries needed!

// When category changes, update products using Change Feed
public async Task HandleCategoryChange(Category category)
{
    var query = $"SELECT * FROM c WHERE c.categoryId = '{category.Id}'";
    await foreach (var product in container.GetItemQueryIterator<Product>(query))
    {
        product.CategoryName = category.Name;
        await container.UpsertItemAsync(product);
    }
}
```

Denormalize when:
- Read-to-write ratio is high (10:1 or more)
- Denormalized data changes infrequently
- Query patterns benefit from co-located data

Reference: [Denormalization patterns](https://learn.microsoft.com/azure/cosmos-db/nosql/modeling-data#denormalization)

### 1.3 Embed Related Data Retrieved Together

**Impact: CRITICAL** (eliminates joins, reduces RU by 50-90%)

## Embed Related Data Retrieved Together

Embed related data within a single document when they're always accessed together. This eliminates the need for multiple queries (Cosmos DB has no JOINs across documents).

**Incorrect (requires multiple queries):**

```csharp
// Separate documents require multiple round-trips
var order = await container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
var customer = await container.ReadItemAsync<Customer>(order.CustomerId, new PartitionKey(order.CustomerId));
var items = await container.GetItemQueryIterator<OrderItem>(
    $"SELECT * FROM c WHERE c.orderId = '{orderId}'").ReadNextAsync();

// 3 separate queries = 3x latency + 3x RU cost
```

**Correct (single read operation):**

```csharp
// Embedded document - single query retrieves everything
public class Order
{
    public string Id { get; set; }
    public string CustomerId { get; set; }
    
    // Embedded customer summary (not full customer document)
    public CustomerSummary Customer { get; set; }
    
    // Embedded order items
    public List<OrderItem> Items { get; set; }
    
    public decimal Total { get; set; }
    public DateTime OrderDate { get; set; }
}

// Single read gets everything needed
var order = await container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
// 1 query = lowest latency + minimal RU
```

Embed when:
- Data is read together frequently
- Embedded data changes infrequently
- Embedded data is bounded in size

Reference: [Data modeling in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/modeling-data)

### 1.4 Reference Data When Items Grow Large

**Impact: CRITICAL** (prevents hitting 2MB limit)

## Reference Data When Items Grow Large

Use document references instead of embedding when embedded data would make items too large, or when embedded data changes independently.

**Incorrect (embedded array grows unbounded):**

```csharp
// Anti-pattern: blog post with all comments embedded
public class BlogPost
{
    public string Id { get; set; }
    public string Title { get; set; }
    public string Content { get; set; }
    
    // This array can grow forever - will eventually hit 2MB limit!
    public List<Comment> Comments { get; set; } // Could be thousands
}

// Eventually fails when document exceeds 2MB
await container.UpsertItemAsync(blogPost);
// RequestEntityTooLarge exception
```

**Correct (reference pattern for unbounded relationships):**

```csharp
// Blog post document (bounded size)
public class BlogPost
{
    public string Id { get; set; }
    public string PostId { get; set; }  // Partition key
    public string Type { get; set; } = "post";
    public string Title { get; set; }
    public string Content { get; set; }
    public int CommentCount { get; set; }  // Denormalized count
}

// Separate comment documents (same partition for efficient queries)
public class Comment
{
    public string Id { get; set; }
    public string PostId { get; set; }  // Partition key - same as post
    public string Type { get; set; } = "comment";
    public string AuthorId { get; set; }
    public string Text { get; set; }
    public DateTime CreatedAt { get; set; }
}

// Query comments within same partition - efficient!
var comments = container.GetItemQueryIterator<Comment>(
    new QueryDefinition("SELECT * FROM c WHERE c.postId = @postId AND c.type = 'comment' ORDER BY c.createdAt DESC")
        .WithParameter("@postId", postId),
    requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(postId) }
);
```

Use references when:
- Embedded data is unbounded (arrays that grow)
- Embedded data changes frequently/independently
- You need to query embedded data separately

Reference: [Model document data](https://learn.microsoft.com/azure/cosmos-db/nosql/modeling-data#referencing-data)

### 1.5 Version Your Document Schemas

**Impact: MEDIUM** (enables safe schema evolution)

## Version Your Document Schemas

Include schema version in documents to handle evolution gracefully. This enables safe migrations and backward-compatible reads.

**Incorrect (no version tracking):**

```csharp
// Original schema
public class UserV1
{
    public string Id { get; set; }
    public string Name { get; set; }  // Later split into FirstName + LastName
    public string Address { get; set; }  // Later becomes Address object
}

// After schema change, old documents break deserialization
public class User
{
    public string Id { get; set; }
    public string FirstName { get; set; }  // Null for old docs!
    public string LastName { get; set; }   // Null for old docs!
    public Address Address { get; set; }   // Deserialization fails!
}
```

**Correct (versioned documents):**

```csharp
public abstract class UserBase
{
    public string Id { get; set; }
    public int SchemaVersion { get; set; }
}

public class UserV1 : UserBase
{
    public string Name { get; set; }
    public string Address { get; set; }
}

public class UserV2 : UserBase
{
    public string FirstName { get; set; }
    public string LastName { get; set; }
    public AddressV2 Address { get; set; }
}

// Read with version handling
public async Task<User> GetUserAsync(string id, string partitionKey)
{
    var response = await container.ReadItemStreamAsync(id, new PartitionKey(partitionKey));
    using var doc = await JsonDocument.ParseAsync(response.Content);
    var version = doc.RootElement.GetProperty("schemaVersion").GetInt32();
    
    return version switch
    {
        1 => MigrateV1ToV2(JsonSerializer.Deserialize<UserV1>(doc)),
        2 => JsonSerializer.Deserialize<UserV2>(doc),
        _ => throw new NotSupportedException($"Unknown schema version: {version}")
    };
}

// Background migration using Change Feed
public async Task MigrateUserDocuments()
{
    var changeFeed = container.GetChangeFeedProcessorBuilder<UserV1>("migration", HandleChanges)
        .WithInstanceName("migrator")
        .WithStartTime(DateTime.MinValue.ToUniversalTime())
        .Build();
    await changeFeed.StartAsync();
}
```

Always increment version when:
- Adding required fields
- Changing field types
- Restructuring nested objects

Reference: [Schema evolution in Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/modeling-data)

### 1.6 Use Type Discriminators for Polymorphic Data

**Impact: MEDIUM** (enables efficient single-container design)

## Use Type Discriminators for Polymorphic Data

When storing multiple entity types in the same container, include a type discriminator field for efficient filtering and deserialization.

**Incorrect (no type discrimination):**

```csharp
// Multiple types in same container without clear identification
public class Order { public string Id { get; set; } /* ... */ }
public class Customer { public string Id { get; set; } /* ... */ }
public class Product { public string Id { get; set; } /* ... */ }

// How do you query just orders? Full scan!
var allItems = await container.GetItemQueryIterator<dynamic>("SELECT * FROM c").ReadNextAsync();
var orders = allItems.Where(x => x.orderDate != null);  // Brittle, inefficient
```

**Correct (explicit type discriminator):**

```csharp
// Base class with type discriminator
public abstract class BaseEntity
{
    [JsonPropertyName("id")]
    public string Id { get; set; }
    
    [JsonPropertyName("type")]
    public abstract string Type { get; }
    
    [JsonPropertyName("partitionKey")]
    public string PartitionKey { get; set; }
}

public class Order : BaseEntity
{
    public override string Type => "order";
    public DateTime OrderDate { get; set; }
    public List<OrderItem> Items { get; set; }
}

public class Customer : BaseEntity
{
    public override string Type => "customer";
    public string Email { get; set; }
    public string Name { get; set; }
}

public class Product : BaseEntity
{
    public override string Type => "product";
    public string Name { get; set; }
    public decimal Price { get; set; }
}

// Efficient queries by type - uses index!
var ordersQuery = new QueryDefinition(
    "SELECT * FROM c WHERE c.type = @type AND c.partitionKey = @pk")
    .WithParameter("@type", "order")
    .WithParameter("@pk", customerId);

// Polymorphic deserialization
public static BaseEntity DeserializeEntity(JsonDocument doc)
{
    var type = doc.RootElement.GetProperty("type").GetString();
    return type switch
    {
        "order" => doc.Deserialize<Order>(),
        "customer" => doc.Deserialize<Customer>(),
        "product" => doc.Deserialize<Product>(),
        _ => throw new InvalidOperationException($"Unknown type: {type}")
    };
}
```

Benefits:
- Efficient filtering with indexed `type` field
- Clear deserialization logic
- Self-documenting data structure

Reference: [Model data in Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/modeling-data)

---

## 2. Partition Key Design

**Impact: CRITICAL**

### 2.1 Plan for 20GB Logical Partition Limit

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

### 2.2 Distribute Writes to Avoid Hot Partitions

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

Reference: [Design for partition hot-spotting](https://learn.microsoft.com/azure/cosmos-db/nosql/modeling-data#design-for-partition-key-hot-spots)

### 2.3 Use Hierarchical Partition Keys for Flexibility

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

Benefits of HPK:
- Each level combination creates separate logical partitions (no 20GB limit per tenant)
- Queries can target specific levels for efficiency
- Natural data organization (tenant → year → month)

Reference: [Hierarchical partition keys](https://learn.microsoft.com/azure/cosmos-db/hierarchical-partition-keys)

### 2.4 Choose High-Cardinality Partition Keys

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

### 2.5 Align Partition Key with Query Patterns

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

### 2.6 Create Synthetic Partition Keys When Needed

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

Reference: [Synthetic partition keys](https://learn.microsoft.com/azure/cosmos-db/nosql/synthetic-partition-keys)

---

## 3. Query Optimization

**Impact: HIGH**

### 3.1 Minimize Cross-Partition Queries

**Impact: HIGH** (reduces RU by 5-100x)

## Minimize Cross-Partition Queries

Always include partition key in queries when possible. Cross-partition queries fan out to all partitions, consuming RU proportional to partition count.

**Incorrect (cross-partition fan-out):**

```csharp
// Missing partition key - scans ALL partitions
var query = new QueryDefinition("SELECT * FROM c WHERE c.status = @status")
    .WithParameter("@status", "active");

var iterator = container.GetItemQueryIterator<Order>(query);
// If you have 100 physical partitions, this runs 100 queries!
// RU cost = single partition cost × number of partitions
```

**Correct (single-partition query):**

```csharp
// Include partition key for single-partition query
var query = new QueryDefinition(
    "SELECT * FROM c WHERE c.customerId = @customerId AND c.status = @status")
    .WithParameter("@customerId", customerId)
    .WithParameter("@status", "active");

var iterator = container.GetItemQueryIterator<Order>(
    query,
    requestOptions: new QueryRequestOptions
    {
        PartitionKey = new PartitionKey(customerId)  // Single partition!
    });
// Runs against ONE partition only
// Dramatically lower RU and latency
```

```csharp
// When cross-partition is unavoidable, optimize parallelism
var query = new QueryDefinition("SELECT * FROM c WHERE c.status = @status")
    .WithParameter("@status", "active");

var options = new QueryRequestOptions
{
    MaxConcurrency = -1,  // Maximum parallelism
    MaxBufferedItemCount = 100,  // Buffer for smoother streaming
    MaxItemCount = 100  // Items per page
};

var iterator = container.GetItemQueryIterator<Order>(query, requestOptions: options);

// Stream results efficiently
await foreach (var item in iterator)
{
    ProcessItem(item);
}
```

```csharp
// Use GetItemLinqQueryable with partition key
var results = container.GetItemLinqQueryable<Order>(
    requestOptions: new QueryRequestOptions 
    { 
        PartitionKey = new PartitionKey(customerId) 
    })
    .Where(o => o.Status == "active")
    .ToFeedIterator();
```

Strategies to avoid cross-partition:
1. Include partition key in WHERE clause
2. Denormalize data to colocate in same partition
3. Create secondary containers with different partition keys for different access patterns

Reference: [Query patterns](https://learn.microsoft.com/azure/cosmos-db/nosql/query/getting-started)

### 3.2 Avoid Full Container Scans

**Impact: HIGH** (prevents unbounded RU consumption)

## Avoid Full Container Scans

Ensure queries can use indexes to filter data. Queries that can't use indexes scan entire partitions or containers.

**Incorrect (queries that cause scans):**

```csharp
// Functions on properties prevent index usage
var query = "SELECT * FROM c WHERE LOWER(c.email) = 'john@example.com'";
// Full scan! Index stores 'John@example.com', not lowercased

// CONTAINS without index
var query2 = "SELECT * FROM c WHERE CONTAINS(c.description, 'azure')";
// No full-text index = full scan

// NOT operations
var query3 = "SELECT * FROM c WHERE NOT c.status = 'completed'";
// Often causes scan (depends on index configuration)

// Type checking
var query4 = "SELECT * FROM c WHERE IS_STRING(c.name)";
// Schema checking = full scan

// OR with different properties (in some cases)
var query5 = "SELECT * FROM c WHERE c.firstName = 'John' OR c.lastName = 'Smith'";
// May scan if indexes can't be combined efficiently
```

**Correct (index-friendly queries):**

```csharp
// Store normalized data to avoid functions
public class User
{
    public string Email { get; set; }
    public string EmailLower { get; set; }  // Pre-computed lowercase
}

var query = "SELECT * FROM c WHERE c.emailLower = 'john@example.com'";
// Uses index directly!

// Use range operators that leverage indexes
var query2 = @"
    SELECT * FROM c 
    WHERE c.createdAt >= @start 
    AND c.createdAt < @end";
// Range index on createdAt

// Prefer equality and range over NOT
var query3 = @"
    SELECT * FROM c 
    WHERE c.status IN ('pending', 'processing', 'shipped')";
// Instead of NOT = 'completed'

// Use StartsWith for prefix matching (uses index)
var query4 = "SELECT * FROM c WHERE STARTSWITH(c.name, 'John')";
// Uses range index on name

// Split OR into UNION if needed for large datasets
// Or ensure composite indexes cover both paths
```

```csharp
// Check if query uses index with query metrics
var options = new QueryRequestOptions
{
    PopulateIndexMetrics = true,
    PartitionKey = new PartitionKey(partitionKey)
};

var iterator = container.GetItemQueryIterator<Product>(query, requestOptions: options);
var response = await iterator.ReadNextAsync();

// Check index metrics in diagnostics
Console.WriteLine($"Index Hit: {response.Diagnostics}");
// Look for "IndexLookupTime" vs "ScanTime"
```

Reference: [Query optimization](https://learn.microsoft.com/azure/cosmos-db/nosql/query-metrics)

### 3.3 Order Filters by Selectivity

**Impact: MEDIUM** (reduces intermediate result sets)

## Order Filters by Selectivity

Place most selective filters first in WHERE clauses. The query engine processes filters left-to-right, so selective filters early reduce data scanned.

**Incorrect (least selective filter first):**

```csharp
// Status has low selectivity (few unique values)
// Filters 1M items to 300K, then to 100
var query = @"
    SELECT * FROM c 
    WHERE c.status = 'active'        -- 30% of items match
    AND c.type = 'order'             -- 10% of items match
    AND c.customerId = @customerId"; -- 0.01% match (highly selective)

// Processes: 1M → 300K → 100K → 100
// More intermediate processing than necessary
```

**Correct (most selective filter first):**

```csharp
// CustomerId is highly selective (unique per customer)
var query = @"
    SELECT * FROM c 
    WHERE c.customerId = @customerId  -- 0.01% match (filter first!)
    AND c.type = 'order'              -- Then narrow by type
    AND c.status = 'active'";         -- Finally by status

// Processes: 1M → 1K → 100 → 100
// Much less intermediate data
```

```csharp
// Selectivity guidelines (from most to least selective):
// 1. Unique identifiers: id, customerId, orderId (highest)
// 2. Foreign keys with many values: productId, userId
// 3. Timestamps (range queries): createdAt, modifiedAt
// 4. Categories with many values: categoryId, departmentId
// 5. Status fields: status, state (low selectivity)
// 6. Boolean flags: isActive, isDeleted (lowest - only 2 values)

// Example: Combining timestamp with status
var query = @"
    SELECT * FROM c 
    WHERE c.customerId = @customerId
    AND c.orderDate >= @startDate
    AND c.orderDate < @endDate
    AND c.status = 'completed'";

// Even better with composite index
```

```csharp
// Use BETWEEN with high selectivity values
var query = @"
    SELECT * FROM c 
    WHERE c.orderId >= @startId AND c.orderId <= @endId  -- Very selective range
    AND c.status = 'active'";

// For OR clauses, check if rewriting helps
// Less efficient:
var query1 = "SELECT * FROM c WHERE c.status = 'a' OR c.status = 'b' AND c.customerId = @id";
// Better (explicit grouping):
var query2 = "SELECT * FROM c WHERE (c.status = 'a' OR c.status = 'b') AND c.customerId = @id";
// Best (if possible, use IN):
var query3 = "SELECT * FROM c WHERE c.status IN ('a', 'b') AND c.customerId = @id";
```

Reference: [Query optimization tips](https://learn.microsoft.com/azure/cosmos-db/nosql/performance-tips-query-sdk)

### 3.4 Use Continuation Tokens for Pagination

**Impact: HIGH** (enables efficient large result sets)

## Use Continuation Tokens for Pagination

Use continuation tokens to paginate through large result sets efficiently. **Never use OFFSET/LIMIT for deep pagination** — it is a common anti-pattern with severe performance implications.

### ⚠️ OFFSET/LIMIT Anti-Pattern

**OFFSET/LIMIT is one of the most common and costly Cosmos DB anti-patterns.** The RU cost of OFFSET scales linearly with the offset value because Cosmos DB must read and discard all skipped documents:

| Page | OFFSET | Documents Scanned | Documents Returned | Relative RU Cost |
|------|--------|-------------------|--------------------|------------------|
| 1 | 0 | 100 | 100 | 1x |
| 10 | 900 | 1,000 | 100 | 10x |
| 100 | 9,900 | 10,000 | 100 | 100x |
| 1,000 | 99,900 | 100,000 | 100 | 1,000x |

This pattern is especially dangerous in **leaderboard** and **feed** scenarios where users page through large result sets.

Use OFFSET/LIMIT only when:
- The total result set is small (< 1,000 items)
- You need random access to a specific page (rare)
- Deep pagination is impossible (e.g., top 100 only)

**Incorrect (OFFSET/LIMIT for pagination):**

```csharp
// ❌ Anti-pattern: OFFSET increases cost linearly with page number
public async Task<List<Product>> GetProductsPage(int page, int pageSize)
{
    // Page 1: Skip 0, Page 100: Skip 9900
    var offset = (page - 1) * pageSize;
    
    // OFFSET must scan and discard all previous items!
    var query = $"SELECT * FROM c ORDER BY c.name OFFSET {offset} LIMIT {pageSize}";
    
    var results = await container.GetItemQueryIterator<Product>(query).ReadNextAsync();
    return results.ToList();
    
    // Page 1: Scans 100 items
    // Page 100: Scans 10,000 items, returns 100
    // RU cost grows linearly with page depth!
}
```

**Correct (continuation token pagination):**

```csharp
public class PagedResult<T>
{
    public List<T> Items { get; set; }
    public string ContinuationToken { get; set; }
    public bool HasMore => !string.IsNullOrEmpty(ContinuationToken);
}

public async Task<PagedResult<Product>> GetProductsPage(
    int pageSize, 
    string continuationToken = null)
{
    var query = new QueryDefinition("SELECT * FROM c ORDER BY c.name");
    
    var options = new QueryRequestOptions
    {
        MaxItemCount = pageSize  // Items per page
    };
    
    var iterator = container.GetItemQueryIterator<Product>(
        query,
        continuationToken: continuationToken,  // Resume from last position
        requestOptions: options);
    
    var response = await iterator.ReadNextAsync();
    
    return new PagedResult<Product>
    {
        Items = response.ToList(),
        ContinuationToken = response.ContinuationToken  // For next page
    };
    
    // Every page costs the same RU regardless of depth!
}

// Usage in API
[HttpGet("products")]
public async Task<IActionResult> GetProducts(
    [FromQuery] int pageSize = 20,
    [FromQuery] string continuationToken = null)
{
    // Decode token if passed as query param (URL-safe encoding)
    var token = continuationToken != null 
        ? Encoding.UTF8.GetString(Convert.FromBase64String(continuationToken))
        : null;
    
    var result = await GetProductsPage(pageSize, token);
    
    // Encode token for URL safety
    var nextToken = result.ContinuationToken != null
        ? Convert.ToBase64String(Encoding.UTF8.GetBytes(result.ContinuationToken))
        : null;
    
    return Ok(new { result.Items, NextPage = nextToken });
}
```

```csharp
// Streaming through all results
public async IAsyncEnumerable<Product> GetAllProducts()
{
    string continuationToken = null;
    
    do
    {
        var page = await GetProductsPage(100, continuationToken);
        
        foreach (var product in page.Items)
        {
            yield return product;
        }
        
        continuationToken = page.ContinuationToken;
    }
    while (continuationToken != null);
}
```

Reference: [Pagination in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/query/pagination)

### 3.5 Use Parameterized Queries

**Impact: MEDIUM** (improves security and query plan caching)

## Use Parameterized Queries

Always use parameterized queries instead of string concatenation. This prevents injection attacks and enables query plan caching.

**Incorrect (string concatenation):**

```csharp
// SQL injection vulnerability!
public async Task<User> GetUser(string userId)
{
    // NEVER DO THIS - vulnerable to injection
    var query = $"SELECT * FROM c WHERE c.userId = '{userId}'";
    
    // Attacker input: "' OR '1'='1"
    // Results in: SELECT * FROM c WHERE c.userId = '' OR '1'='1'
    // Returns ALL users!
    
    var iterator = container.GetItemQueryIterator<User>(query);
    return (await iterator.ReadNextAsync()).FirstOrDefault();
}

// Also prevents query plan caching
// Each unique query string = new compilation
var query1 = "SELECT * FROM c WHERE c.userId = 'user1'";
var query2 = "SELECT * FROM c WHERE c.userId = 'user2'";
// Two different query plans compiled!
```

**Correct (parameterized queries):**

```csharp
public async Task<User> GetUser(string userId)
{
    var query = new QueryDefinition("SELECT * FROM c WHERE c.userId = @userId")
        .WithParameter("@userId", userId);
    
    // Injection attempt becomes literal string comparison
    // Attacker input "' OR '1'='1" just searches for that literal value
    
    var iterator = container.GetItemQueryIterator<User>(query);
    return (await iterator.ReadNextAsync()).FirstOrDefault();
}

// Query plan is cached and reused
var query1 = new QueryDefinition("SELECT * FROM c WHERE c.userId = @userId")
    .WithParameter("@userId", "user1");
var query2 = new QueryDefinition("SELECT * FROM c WHERE c.userId = @userId")
    .WithParameter("@userId", "user2");
// Same query plan reused!
```

```csharp
// Multiple parameters
var query = new QueryDefinition(@"
    SELECT * FROM c 
    WHERE c.customerId = @customerId 
    AND c.status = @status
    AND c.orderDate >= @startDate")
    .WithParameter("@customerId", customerId)
    .WithParameter("@status", "active")
    .WithParameter("@startDate", startDate);

// Array parameter for IN clauses
var statuses = new[] { "pending", "processing", "shipped" };
var query2 = new QueryDefinition(
    "SELECT * FROM c WHERE ARRAY_CONTAINS(@statuses, c.status)")
    .WithParameter("@statuses", statuses);
```

```csharp
// LINQ (automatically parameterized)
var results = container.GetItemLinqQueryable<Order>()
    .Where(o => o.CustomerId == customerId && o.Status == status)
    .ToFeedIterator();
// SDK handles parameterization automatically
```

Benefits:
- Security: Prevents SQL injection
- Performance: Query plan caching and reuse
- Maintainability: Cleaner, type-safe code

Reference: [Parameterized queries](https://learn.microsoft.com/azure/cosmos-db/nosql/query/parameterized-queries)

### 3.6 Project Only Needed Fields

**Impact: HIGH** (reduces RU and network by 30-80%)

## Project Only Needed Fields

Select only the fields you need rather than returning entire documents. Reduces both RU consumption and network bandwidth.

**Incorrect (selecting entire document):**

```csharp
// Selecting everything when you only need a few fields
var query = "SELECT * FROM c WHERE c.customerId = @customerId";

// Returns all fields including:
// - Large text content
// - Arrays with hundreds of items
// - Fields you'll never use
var orders = await container.GetItemQueryIterator<Order>(
    new QueryDefinition(query).WithParameter("@customerId", customerId),
    requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(customerId) }
).ReadNextAsync();

// UI only shows: orderId, orderDate, total
// But you transferred and deserialized everything!
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
    FROM c 
    WHERE c.customerId = @customerId";

public class OrderSummary
{
    public string Id { get; set; }
    public DateTime OrderDate { get; set; }
    public decimal Total { get; set; }
    public string Status { get; set; }
}

var orders = await container.GetItemQueryIterator<OrderSummary>(
    new QueryDefinition(query).WithParameter("@customerId", customerId),
    requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(customerId) }
).ReadNextAsync();

// 70% less data transferred, proportionally lower RU
```

```csharp
// For nested objects, project specific paths
var query = @"
    SELECT 
        c.id,
        c.customer.name AS customerName,
        c.items[0].productName AS firstProduct,
        ARRAY_LENGTH(c.items) AS itemCount
    FROM c";

// Even more efficient: VALUE for single field
var query2 = "SELECT VALUE c.email FROM c WHERE c.type = 'customer'";
var emails = await container.GetItemQueryIterator<string>(query2).ReadNextAsync();
```

```csharp
// LINQ projection
var orderSummaries = container.GetItemLinqQueryable<Order>(
    requestOptions: new QueryRequestOptions 
    { 
        PartitionKey = new PartitionKey(customerId) 
    })
    .Where(o => o.CustomerId == customerId)
    .Select(o => new OrderSummary
    {
        Id = o.Id,
        OrderDate = o.OrderDate,
        Total = o.Total,
        Status = o.Status
    })
    .ToFeedIterator();
```

Savings multiply with:
- Large documents (MB-sized)
- Large result sets
- High query frequency

Reference: [Project fields in queries](https://learn.microsoft.com/azure/cosmos-db/nosql/query/select)

---

## 4. SDK Best Practices

**Impact: HIGH**

### 4.1 Use Async APIs for Better Throughput

**Impact: HIGH** (improves concurrency 10-100x)

## Use Async APIs for Better Throughput

Always use async/await patterns for Cosmos DB operations. Synchronous calls block threads and severely limit throughput under load.

**Incorrect (blocking synchronous calls):**

```csharp
// Anti-pattern: Blocking async code
public Order GetOrder(string orderId, string customerId)
{
    // .Result blocks the calling thread!
    var response = _container.ReadItemAsync<Order>(
        orderId, 
        new PartitionKey(customerId)).Result;
    
    return response.Resource;
}

// Or using .Wait()
public void UpdateOrder(Order order)
{
    _container.UpsertItemAsync(order, new PartitionKey(order.CustomerId)).Wait();
}

// Problems:
// - Thread pool exhaustion under load
// - Potential deadlocks in ASP.NET
// - Cannot scale to handle concurrent requests
// - 100 concurrent requests = 100 blocked threads
```

**Correct (fully async):**

```csharp
public async Task<Order> GetOrderAsync(string orderId, string customerId)
{
    var response = await _container.ReadItemAsync<Order>(
        orderId, 
        new PartitionKey(customerId));
    
    return response.Resource;
}

public async Task UpdateOrderAsync(Order order)
{
    await _container.UpsertItemAsync(order, new PartitionKey(order.CustomerId));
}

// Async all the way up the call stack
public async Task<IActionResult> GetOrder(string id, string customerId)
{
    var order = await _orderRepository.GetOrderAsync(id, customerId);
    return Ok(order);
}
```

```csharp
// Concurrent operations with Task.WhenAll
public async Task<OrderWithItems> GetOrderWithItemsAsync(string orderId, string customerId)
{
    // Start both operations concurrently
    var orderTask = _container.ReadItemAsync<Order>(
        orderId, new PartitionKey(customerId));
    
    var itemsTask = _container.GetItemQueryIterator<OrderItem>(
        new QueryDefinition("SELECT * FROM c WHERE c.orderId = @orderId")
            .WithParameter("@orderId", orderId),
        requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(customerId) }
    ).ReadNextAsync();
    
    // Wait for both to complete
    await Task.WhenAll(orderTask, itemsTask);
    
    return new OrderWithItems
    {
        Order = orderTask.Result.Resource,
        Items = itemsTask.Result.ToList()
    };
    // Total time ≈ max(order time, items time) instead of sum
}
```

```csharp
// Bulk operations with async streaming
public async Task<int> ImportProductsAsync(IAsyncEnumerable<Product> products)
{
    var count = 0;
    var tasks = new List<Task>();
    
    await foreach (var product in products)
    {
        tasks.Add(_container.UpsertItemAsync(product, new PartitionKey(product.CategoryId)));
        count++;
        
        // Limit concurrent operations to avoid overwhelming the client
        if (tasks.Count >= 100)
        {
            await Task.WhenAll(tasks);
            tasks.Clear();
        }
    }
    
    await Task.WhenAll(tasks);  // Complete remaining
    return count;
}
```

Reference: [Async programming best practices](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet#use-async-methods)

### 4.2 Configure Threshold-Based Availability Strategy (Hedging)

**Impact: HIGH** (reduces tail latency by 90%+, eliminates regional outage impact)

## Configure Threshold-Based Availability Strategy (Hedging)

The threshold-based availability strategy (hedging) improves tail latency and availability by sending parallel read requests to secondary regions when the primary region is slow. This approach drastically reduces the impact of regional outages or high-latency conditions.

**Incorrect (no availability strategy):**

```csharp
// Without availability strategy, slow regions cause high latency for all users
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationPreferredRegions = new List<string> { "East US", "East US 2", "West US" }
});

// If East US is experiencing high latency (e.g., 2 seconds):
// - ALL requests wait the full 2 seconds
// - No automatic failover to faster regions for reads
// - Tail latency spikes affect user experience
var response = await container.ReadItemAsync<Order>(id, partitionKey);
```

**Correct (.NET SDK - availability strategy with hedging):**

```csharp
// Configure threshold-based availability strategy
CosmosClient client = new CosmosClientBuilder("connection string")
    .WithApplicationPreferredRegions(
        new List<string> { "East US", "East US 2", "West US" })
    .WithAvailabilityStrategy(
        AvailabilityStrategy.CrossRegionHedgingStrategy(
            threshold: TimeSpan.FromMilliseconds(500),    // Wait 500ms before hedging
            thresholdStep: TimeSpan.FromMilliseconds(100) // Additional 100ms between regions
        ))
    .Build();

// How it works:
// T1: Request sent to East US (primary)
// T1 + 500ms: If no response, parallel request to East US 2
// T1 + 600ms: If no response, parallel request to West US
// First response wins, others are cancelled
```

```csharp
// Alternative: Configure via CosmosClientOptions
CosmosClientOptions options = new CosmosClientOptions()
{
    AvailabilityStrategy = AvailabilityStrategy.CrossRegionHedgingStrategy(
        threshold: TimeSpan.FromMilliseconds(500),
        thresholdStep: TimeSpan.FromMilliseconds(100)
    ),
    ApplicationPreferredRegions = new List<string> { "East US", "East US 2", "West US" }
};

CosmosClient client = new CosmosClient(
    accountEndpoint: "account endpoint",
    authKeyOrResourceToken: "auth key",
    clientOptions: options);
```

**Correct (Java SDK - threshold-based availability strategy):**

```java
// Proactive Connection Management (warm up connections to failover regions)
CosmosContainerIdentity containerIdentity = new CosmosContainerIdentity("sample_db", "sample_container");
int proactiveConnectionRegionsCount = 2;
Duration aggressiveWarmupDuration = Duration.ofSeconds(1);

CosmosAsyncClient client = new CosmosClientBuilder()
    .endpoint("<account URL>")
    .key("<account key>")
    .endpointDiscoveryEnabled(true)
    .preferredRegions(Arrays.asList("East US", "East US 2", "West US"))
    // Warm up connections to secondary regions for faster failover
    .openConnectionsAndInitCaches(
        new CosmosContainerProactiveInitConfigBuilder(Arrays.asList(containerIdentity))
            .setProactiveConnectionRegionsCount(proactiveConnectionRegionsCount)
            .setAggressiveWarmupDuration(aggressiveWarmupDuration)
            .build())
    .directMode()
    .buildAsyncClient();

// Configure threshold-based availability strategy per request
int threshold = 500;
int thresholdStep = 100;

CosmosEndToEndOperationLatencyPolicyConfig config = 
    new CosmosEndToEndOperationLatencyPolicyConfigBuilder(Duration.ofSeconds(3))
        .availabilityStrategy(new ThresholdBasedAvailabilityStrategy(
            Duration.ofMillis(threshold), 
            Duration.ofMillis(thresholdStep)))
        .build();

CosmosItemRequestOptions options = new CosmosItemRequestOptions();
options.setCosmosEndToEndOperationLatencyPolicyConfig(config);

// Read with hedging enabled
container.readItem("id", new PartitionKey("pk"), options, JsonNode.class).block();

// Writes can benefit too with multi-region write accounts + non-idempotent retry
options.setNonIdempotentWriteRetryPolicy(true, true);
container.createItem(item, new PartitionKey("pk"), options).block();
```

**Trade-offs:**

| Aspect | Benefit | Cost |
|--------|---------|------|
| Latency | 90%+ reduction in tail latency | Extra parallel requests |
| Availability | Preempts regional outages | Increased RU consumption during thresholds |
| Complexity | SDK handles automatically | Configuration tuning required |

**Best Practices:**

1. **Tune threshold based on your P50 latency** - Set threshold slightly above your normal P50 to avoid unnecessary hedging
2. **Use with multi-region accounts** - Requires at least 2 regions configured
3. **Monitor RU consumption** - Track extra RUs during hedging periods
4. **Combine with circuit breaker** - Use both strategies for maximum resilience

Reference: [Performance tips - .NET SDK High Availability](https://learn.microsoft.com/en-us/azure/cosmos-db/performance-tips-dotnet-sdk-v3#high-availability)
Reference: [Performance tips - Java SDK High Availability](https://learn.microsoft.com/en-us/azure/cosmos-db/performance-tips-java-sdk-v4#high-availability)

### 4.3 Configure Partition-Level Circuit Breaker

**Impact: HIGH** (prevents cascading failures, improves write availability)

## Configure Partition-Level Circuit Breaker

The partition-level circuit breaker (PPCB) enhances availability by tracking unhealthy physical partitions and routing requests away from them. This prevents cascading failures when specific partitions experience issues.

**Incorrect (no circuit breaker, cascading failures):**

```csharp
// Without circuit breaker:
// - Requests to unhealthy partitions keep failing
// - Retry storms amplify the problem
// - Application experiences cascading failures
// - No automatic recovery when partition heals

var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationPreferredRegions = new List<string> { "East US", "East US 2" }
});

// If partition P1 in East US is unhealthy:
// - Every request to P1 fails with timeout/503
// - Retries make it worse
// - No automatic failover to East US 2 for that partition
```

**Correct (.NET SDK - partition-level circuit breaker):**

```csharp
// Enable via environment variables (.NET SDK)
// Set these before creating the CosmosClient

// Enable the circuit breaker feature
Environment.SetEnvironmentVariable("AZURE_COSMOS_CIRCUIT_BREAKER_ENABLED", "true");

// Configure thresholds for reads
Environment.SetEnvironmentVariable(
    "AZURE_COSMOS_PPCB_CONSECUTIVE_FAILURE_COUNT_FOR_READS", "10");

// Configure thresholds for writes
Environment.SetEnvironmentVariable(
    "AZURE_COSMOS_PPCB_CONSECUTIVE_FAILURE_COUNT_FOR_WRITES", "5");

// Time before re-evaluating partition health
Environment.SetEnvironmentVariable(
    "AZURE_COSMOS_PPCB_ALLOWED_PARTITION_UNAVAILABILITY_DURATION_IN_SECONDS", "5");

// Background health check interval
Environment.SetEnvironmentVariable(
    "AZURE_COSMOS_PPCB_STALE_PARTITION_UNAVAILABILITY_REFRESH_INTERVAL_IN_SECONDS", "60");

var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationPreferredRegions = new List<string> { "East US", "East US 2", "West US" }
});

// Now if partition P1 in East US fails 5+ writes:
// 1. Circuit breaker marks P1 as "Unavailable" in East US
// 2. Requests to P1 automatically route to East US 2
// 3. Background thread monitors P1 for recovery
// 4. When P1 heals, circuit closes and East US serves P1 again
```

**Correct (Java SDK - partition-level circuit breaker):**

```java
// Enable via system properties (Java SDK)
// Requires SDK version 4.63.0+

System.setProperty(
    "COSMOS.PARTITION_LEVEL_CIRCUIT_BREAKER_CONFIG",
    "{\"isPartitionLevelCircuitBreakerEnabled\": true, " +
    "\"circuitBreakerType\": \"CONSECUTIVE_EXCEPTION_COUNT_BASED\"," +
    "\"consecutiveExceptionCountToleratedForReads\": 10," +
    "\"consecutiveExceptionCountToleratedForWrites\": 5}");

// Configure background health check interval
System.setProperty(
    "COSMOS.STALE_PARTITION_UNAVAILABILITY_REFRESH_INTERVAL_IN_SECONDS", "60");

// Configure how long a partition can remain unavailable before retry
System.setProperty(
    "COSMOS.ALLOWED_PARTITION_UNAVAILABILITY_DURATION_IN_SECONDS", "30");

CosmosAsyncClient client = new CosmosClientBuilder()
    .endpoint("<endpoint>")
    .key("<key>")
    .preferredRegions(Arrays.asList("East US", "East US 2", "West US"))
    .buildAsyncClient();
```

**Correct (Python SDK - partition-level circuit breaker):**

```python
import os
from azure.cosmos import CosmosClient

# Enable via environment variables (Python SDK)
# Requires SDK version 4.14.0+

os.environ["AZURE_COSMOS_ENABLE_CIRCUIT_BREAKER"] = "true"
os.environ["AZURE_COSMOS_CONSECUTIVE_ERROR_COUNT_TOLERATED_FOR_READ"] = "10"
os.environ["AZURE_COSMOS_CONSECUTIVE_ERROR_COUNT_TOLERATED_FOR_WRITE"] = "5"
os.environ["AZURE_COSMOS_FAILURE_PERCENTAGE_TOLERATED"] = "90"

client = CosmosClient(
    url=HOST,
    credential=MASTER_KEY,
    preferred_locations=['East US', 'East US 2', 'West US']
)

# Circuit breaker state machine:
# Healthy → (failures) → Unhealthy Tentative → (more failures) → Unhealthy
# Unhealthy → (backoff) → Healthy Tentative → (probe success) → Healthy
# Unhealthy → (backoff) → Healthy Tentative → (probe fails) → Unhealthy
```

**How Circuit Breaker Works:**

```
                    ┌─────────────────────────────────────┐
                    │           HEALTHY                   │
                    │   (Normal operation)                │
                    └────────────┬────────────────────────┘
                                 │ Consecutive failures > threshold
                                 ▼
                    ┌─────────────────────────────────────┐
                    │     UNHEALTHY TENTATIVE             │
                    │ (Short-circuit for 1 minute)        │
                    └────────────┬────────────────────────┘
                                 │ More failures OR timeout
                                 ▼
                    ┌─────────────────────────────────────┐
                    │         UNHEALTHY                   │
                    │ (Route to other regions)            │
                    └────────────┬────────────────────────┘
                                 │ Backoff period expires
                                 ▼
                    ┌─────────────────────────────────────┐
                    │      HEALTHY TENTATIVE              │
                    │  (Test probe requests)              │
                    └────────────┬───────────┬────────────┘
                     Success     │           │ Failure
                                 ▼           ▼
                    ┌────────────┐  ┌────────────────────┐
                    │  HEALTHY   │  │    UNHEALTHY       │
                    └────────────┘  └────────────────────┘
```

**Important Requirements:**

| SDK | Minimum Version | Account Type |
|-----|-----------------|--------------|
| .NET | 3.37.0+ | Multi-region (single or multi-write) |
| Java | 4.63.0+ | Multi-region write accounts only |
| Python | 4.14.0+ | Multi-region (single or multi-write) |

**Trade-offs vs Availability Strategy:**

| Feature | Circuit Breaker | Availability Strategy |
|---------|-----------------|----------------------|
| Extra RU cost | None | Yes (parallel requests) |
| Latency reduction | After failures occur | Proactive (threshold-based) |
| Best for | Write-heavy workloads | Read-heavy workloads |
| Initial failures | Some requests fail first | Hedged immediately |

**Best Practice: Combine Both Strategies**

```csharp
// Use BOTH for maximum resilience
Environment.SetEnvironmentVariable("AZURE_COSMOS_CIRCUIT_BREAKER_ENABLED", "true");

var client = new CosmosClientBuilder("connection string")
    .WithApplicationPreferredRegions(new List<string> { "East US", "East US 2", "West US" })
    .WithAvailabilityStrategy(
        AvailabilityStrategy.CrossRegionHedgingStrategy(
            threshold: TimeSpan.FromMilliseconds(500),
            thresholdStep: TimeSpan.FromMilliseconds(100)))
    .Build();

// Circuit breaker handles sustained partition failures
// Availability strategy handles latency spikes
```

Reference: [Performance tips - .NET SDK Circuit Breaker](https://learn.microsoft.com/en-us/azure/cosmos-db/performance-tips-dotnet-sdk-v3#partition-level-circuit-breaker)
Reference: [Performance tips - Java SDK Circuit Breaker](https://learn.microsoft.com/en-us/azure/cosmos-db/performance-tips-java-sdk-v4#partition-level-circuit-breaker)
Reference: [Performance tips - Python SDK Circuit Breaker](https://learn.microsoft.com/en-gb/azure/cosmos-db/performance-tips-python-sdk#partition-level-circuit-breaker)

### 4.4 Use Direct Connection Mode for Production

**Impact: HIGH** (reduces latency by 30-50%)

## Use Direct Connection Mode for Production

Use Direct connection mode for production workloads. Gateway mode adds an extra network hop and is only needed for firewall-restricted environments.

**Incorrect (defaulting to Gateway mode):**

```csharp
// Gateway mode adds extra hop through Azure gateway
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ConnectionMode = ConnectionMode.Gateway  // Extra network hop!
});

// Request path:
// Client → Azure Gateway → Cosmos DB partition
// Extra latency: 2-10ms per request
```

**Correct (Direct mode for production):**

```csharp
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    // Direct mode connects straight to backend partitions
    ConnectionMode = ConnectionMode.Direct,
    
    // Protocol.Tcp for best performance (default in Direct mode)
    // Uses persistent connections
    
    // Configure connection limits for high throughput
    MaxRequestsPerTcpConnection = 30,
    MaxTcpConnectionsPerEndpoint = 65535,
    
    // Idle connection timeout
    IdleTcpConnectionTimeout = TimeSpan.FromMinutes(10),
    
    // Enable connection recovery
    EnableTcpConnectionEndpointRediscovery = true
});

// Request path:
// Client → Cosmos DB partition directly
// Lower latency, higher throughput
```

```csharp
// When to use Gateway mode (exceptions):
var gatewayClient = new CosmosClient(connectionString, new CosmosClientOptions
{
    // Use Gateway when:
    // 1. Corporate firewall blocks TCP port range 10000-20000
    // 2. Running in Azure Functions Consumption plan (sometimes)
    // 3. Kubernetes with restrictive network policies
    ConnectionMode = ConnectionMode.Gateway
});
```

```csharp
// Complete production configuration
var productionClient = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationName = "MyProductionApp",
    ConnectionMode = ConnectionMode.Direct,
    
    // Retry configuration
    MaxRetryAttemptsOnRateLimitedRequests = 9,
    MaxRetryWaitTimeOnRateLimitedRequests = TimeSpan.FromSeconds(30),
    
    // Connection management
    MaxRequestsPerTcpConnection = 30,
    MaxTcpConnectionsPerEndpoint = 65535,
    PortReuseMode = PortReuseMode.PrivatePortPool,
    
    // Serialization (optional optimization)
    SerializerOptions = new CosmosSerializationOptions
    {
        PropertyNamingPolicy = CosmosPropertyNamingPolicy.CamelCase,
        IgnoreNullValues = true
    },
    
    // Consistency (if different from account default)
    ConsistencyLevel = ConsistencyLevel.Session
});
```

Required firewall ports for Direct mode:
- TCP 443 (control plane)
- TCP 10000-20000 (data plane)

Reference: [Direct vs Gateway connection modes](https://learn.microsoft.com/azure/cosmos-db/nosql/sdk-connection-modes)

### 4.5 Log Diagnostics for Troubleshooting

**Impact: MEDIUM** (enables root cause analysis)

## Log Diagnostics for Troubleshooting

Capture and log diagnostics from Cosmos DB responses, especially for slow or failed operations. Diagnostics contain crucial information for troubleshooting.

**Incorrect (ignoring diagnostics):**

```csharp
public async Task<Order> GetOrder(string orderId, string customerId)
{
    try
    {
        var response = await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
        return response.Resource;
    }
    catch (CosmosException ex)
    {
        // Only logging the message loses critical debugging info!
        _logger.LogError("Failed to read order: {Message}", ex.Message);
        throw;
    }
}
```

**Correct (logging diagnostics):**

```csharp
public async Task<Order> GetOrder(string orderId, string customerId)
{
    var response = await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
    
    // Log diagnostics for slow operations
    if (response.Diagnostics.GetClientElapsedTime() > TimeSpan.FromMilliseconds(100))
    {
        _logger.LogWarning(
            "Slow Cosmos DB read: {ElapsedMs}ms, RU: {RU}, Diagnostics: {Diagnostics}",
            response.Diagnostics.GetClientElapsedTime().TotalMilliseconds,
            response.RequestCharge,
            response.Diagnostics.ToString());
    }
    
    return response.Resource;
}

// For all operations - track RU consumption
public async Task<T> ExecuteWithDiagnostics<T>(
    Func<Task<ItemResponse<T>>> operation,
    string operationName)
{
    var stopwatch = Stopwatch.StartNew();
    
    try
    {
        var response = await operation();
        stopwatch.Stop();
        
        // Always log RU for cost tracking
        _logger.LogDebug(
            "{Operation} completed: {ElapsedMs}ms, {RU} RU",
            operationName,
            stopwatch.ElapsedMilliseconds,
            response.RequestCharge);
        
        // Log full diagnostics if slow or high RU
        if (stopwatch.ElapsedMilliseconds > 100 || response.RequestCharge > 10)
        {
            _logger.LogInformation(
                "{Operation} diagnostics: {Diagnostics}",
                operationName,
                response.Diagnostics.ToString());
        }
        
        return response.Resource;
    }
    catch (CosmosException ex)
    {
        // CRITICAL: Always log diagnostics on failure!
        _logger.LogError(ex,
            "{Operation} failed: Status={Status}, RU={RU}, RetryAfter={RetryAfter}, Diagnostics={Diagnostics}",
            operationName,
            ex.StatusCode,
            ex.RequestCharge,
            ex.RetryAfter,
            ex.Diagnostics?.ToString());
        throw;
    }
}
```

```csharp
// Query diagnostics with query metrics
var queryOptions = new QueryRequestOptions
{
    PopulateIndexMetrics = true,  // Index usage info
    MaxItemCount = 100
};

var iterator = _container.GetItemQueryIterator<Order>(query, requestOptions: queryOptions);
var response = await iterator.ReadNextAsync();

_logger.LogInformation(
    "Query completed: {ItemCount} items, {RU} RU, IndexMetrics: {IndexMetrics}",
    response.Count,
    response.RequestCharge,
    response.IndexMetrics);
// IndexMetrics shows which indexes were used/not used
```

Key diagnostic fields:
- `GetClientElapsedTime()`: Total client-side time
- `RequestCharge`: RU consumed
- Server response time, regions contacted
- Retry information
- Connection information

Reference: [Capture diagnostics](https://learn.microsoft.com/azure/cosmos-db/nosql/troubleshoot-dotnet-sdk)

### 4.6 Configure SSL and connection mode for Cosmos DB Emulator

**Impact: MEDIUM** (enables local development with all SDKs)

## Configure SSL and Connection Mode for Cosmos DB Emulator

The Azure Cosmos DB Emulator uses a self-signed SSL certificate that requires special handling. Additionally, **all SDKs should use Gateway connection mode with the emulator** - Direct mode has known issues with the emulator's SSL certificate handling.

### General Guidance (All SDKs)

| Setting | Emulator | Production |
|---------|----------|------------|
| Connection Mode | **Gateway** (required) | Direct (recommended) |
| SSL Validation | Disable or import cert | Normal validation |
| Endpoint | `https://localhost:8081` | Your account URL |
| Key | Well-known emulator key | Your account key |

**Well-known emulator key:** `C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==`

---

### .NET SDK

```csharp
var options = new CosmosClientOptions
{
    ConnectionMode = ConnectionMode.Gateway,  // Required for emulator
    HttpClientFactory = () => new HttpClient(
        new HttpClientHandler
        {
            // Accept self-signed certificate from emulator
            ServerCertificateCustomValidationCallback = 
                HttpClientHandler.DangerousAcceptAnyServerCertificateValidator
        })
};

var client = new CosmosClient(
    "https://localhost:8081",
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
    options
);
```

---

### Python SDK

```python
from azure.cosmos import CosmosClient
import urllib3

# Suppress SSL warnings for local development only
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Python SDK uses Gateway mode by default
client = CosmosClient(
    url="https://localhost:8081",
    credential="C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
    connection_verify=False  # Disable SSL verification for emulator
)
```

---

### Node.js SDK

```javascript
const { CosmosClient } = require("@azure/cosmos");

// Disable SSL verification for emulator (development only!)
process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

const client = new CosmosClient({
    endpoint: "https://localhost:8081",
    key: "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
    connectionPolicy: {
        connectionMode: "Gateway"  // Recommended for emulator
    }
});
```

---

### Java SDK (Detailed)

When using the Azure Cosmos DB Emulator with the Java SDK, you must import the emulator's self-signed SSL certificate into the JDK truststore and use Gateway connection mode. Direct mode has persistent SSL issues with the emulator.

**Problem (SSL handshake failures):**

```java
// Without certificate import, you'll see errors like:
// javax.net.ssl.SSLHandshakeException: PKIX path building failed
// sun.security.provider.certpath.SunCertPathBuilderException: 
//   unable to find valid certification path to requested target

// Direct mode fails even after certificate import:
CosmosClientBuilder builder = new CosmosClientBuilder()
    .endpoint("https://localhost:8081")
    .key("...")
    .directMode();  // Will fail with SSL errors!
```

**Solution - Step 1: Export the emulator certificate:**

```powershell
# The emulator stores its certificate at this path (Windows):
# %LOCALAPPDATA%\CosmosDBEmulator\emulator-cert.cer

# Or export from Windows Certificate Manager:
# certmgr.msc → Personal → Certificates → DocumentDbEmulatorCertificate
# Right-click → All Tasks → Export → DER encoded binary X.509 (.CER)
```

**Solution - Step 2: Import certificate into JDK truststore:**

```powershell
# Find your JDK path first:
# java -XshowSettings:properties -version 2>&1 | Select-String "java.home"

# Import the certificate (run as Administrator):
keytool -importcert `
    -alias cosmosemulator `
    -file "C:\Users\<username>\AppData\Local\CosmosDBEmulator\emulator-cert.cer" `
    -keystore "C:\Program Files\Eclipse Adoptium\jdk-17.0.10.7-hotspot\lib\security\cacerts" `
    -storepass changeit `
    -noprompt

# For other JDK distributions, the cacerts location varies:
# - Oracle JDK: $JAVA_HOME/lib/security/cacerts
# - Eclipse Adoptium: $JAVA_HOME/lib/security/cacerts
# - Amazon Corretto: $JAVA_HOME/lib/security/cacerts
```

**Solution - Step 3: Use Gateway mode with the emulator:**

```java
// Gateway mode works reliably with the emulator after certificate import
CosmosClientBuilder builder = new CosmosClientBuilder()
    .endpoint("https://localhost:8081")
    .key("C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==")
    .gatewayMode()  // Required for emulator!
    .consistencyLevel(ConsistencyLevel.SESSION);

CosmosClient client = builder.buildClient();
```

```yaml
# Spring Boot application.properties for emulator:
azure:
  cosmos:
    endpoint: https://localhost:8081
    key: C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
    database: your-database
    # Note: Spring Data Cosmos uses Gateway mode by default
```

**Alternative - Custom truststore (no admin required):**

If you cannot modify the JDK's `cacerts` (requires administrator access), create a custom truststore instead:

```powershell
# Step 1: Copy JDK's default cacerts to a local custom truststore
$jdkCacerts = "$env:JAVA_HOME\lib\security\cacerts"
Copy-Item $jdkCacerts -Destination .\custom-cacerts

# Step 2: Extract the emulator's SSL certificate
$tcpClient = New-Object System.Net.Sockets.TcpClient("localhost", 8081)
$sslStream = New-Object System.Net.Security.SslStream($tcpClient.GetStream(), $false, {$true})
$sslStream.AuthenticateAsClient("localhost")
$cert = $sslStream.RemoteCertificate
[System.IO.File]::WriteAllBytes("emulator-cert.cer", $cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert))
$sslStream.Close(); $tcpClient.Close()

# Step 3: Import into custom truststore
keytool -importcert -alias cosmosemulator -file emulator-cert.cer `
    -keystore custom-cacerts -storepass changeit -noprompt
```

```powershell
# Step 4: Run your app with the custom truststore
java "-Djavax.net.ssl.trustStore=custom-cacerts" `
     "-Djavax.net.ssl.trustStorePassword=changeit" `
     -jar your-app.jar
```

**⚠️ `COSMOS.EMULATOR_SSL_TRUST_ALL` does NOT work with Java/Netty:**

```java
// WARNING: This property does NOT work with the Java Cosmos SDK!
// The Java SDK uses Netty with OpenSSL, which bypasses Java's SSLContext entirely.
// Setting this property has no effect — SSL handshake will still fail.
System.setProperty("COSMOS.EMULATOR_SSL_TRUST_ALL", "true");  // INEFFECTIVE!

// Also ineffective as a JVM argument:
// -DCOSMOS.EMULATOR_SSL_TRUST_ALL=true  // DOES NOT WORK

// Instead, use one of these approaches:
// 1. Import the emulator certificate into the JDK truststore (Step 2 above)
// 2. Use a custom truststore with -Djavax.net.ssl.trustStore (recommended)
```

**Key Points:**
- Direct connection mode does not work reliably with the emulator even after certificate import
- Gateway mode is required for local development with the Java SDK and emulator
- **`COSMOS.EMULATOR_SSL_TRUST_ALL` does NOT work** — the Java SDK uses Netty/OpenSSL which ignores Java SSL system properties. You must import the emulator certificate into a JDK or custom truststore
- The custom truststore approach avoids needing administrator access
- The emulator's well-known key is: `C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==`
- For production, switch back to Direct mode and use your actual Cosmos DB endpoint

Reference: [Use the Azure Cosmos DB Emulator for local development](https://learn.microsoft.com/azure/cosmos-db/emulator)

### 4.7 Use ETags for optimistic concurrency on read-modify-write operations

**Impact: HIGH** (prevents lost updates in concurrent write scenarios)

## Use ETags for Optimistic Concurrency

When performing read-modify-write operations (read a document, update a field, write it back), always use ETags to prevent lost updates from concurrent writes. Without ETags, the last writer silently overwrites changes from other operations.

**Problem: Lost updates without ETag checks**

```csharp
// Anti-pattern: Read-modify-write without concurrency control
// If two requests run concurrently, one update is silently lost
public async Task UpdatePlayerStatsAsync(string playerId, int newScore)
{
    // Thread A reads player (bestScore: 100)
    var response = await _container.ReadItemAsync<Player>(
        playerId, new PartitionKey(playerId));
    var player = response.Resource;

    // Thread B also reads player (bestScore: 100)
    // Thread B updates bestScore to 200 and writes

    // Thread A updates bestScore to 150 and writes
    // Thread A's write OVERWRITES Thread B's update!
    player.BestScore = Math.Max(player.BestScore, newScore);
    player.TotalGamesPlayed++;
    player.TotalScore += newScore;
    player.AverageScore = player.TotalScore / player.TotalGamesPlayed;

    await _container.UpsertItemAsync(player,  // Overwrites without checking!
        new PartitionKey(playerId));
}
```

**Solution: ETag-based optimistic concurrency with retry**

```csharp
// Correct: Use ETag to detect concurrent modifications and retry
public async Task UpdatePlayerStatsAsync(string playerId, int newScore)
{
    const int maxRetries = 3;

    for (int attempt = 0; attempt < maxRetries; attempt++)
    {
        try
        {
            // Read current state (includes ETag in response headers)
            var response = await _container.ReadItemAsync<Player>(
                playerId, new PartitionKey(playerId));
            var player = response.Resource;
            var etag = response.ETag;  // Capture the ETag

            // Modify the document
            player.BestScore = Math.Max(player.BestScore, newScore);
            player.TotalGamesPlayed++;
            player.TotalScore += newScore;
            player.AverageScore = player.TotalScore / player.TotalGamesPlayed;
            player.LastPlayedAt = DateTime.UtcNow;

            // Write with ETag condition — fails if document changed since read
            await _container.UpsertItemAsync(player,
                new PartitionKey(playerId),
                new ItemRequestOptions
                {
                    IfMatchEtag = etag  // Only succeeds if ETag matches
                });

            return; // Success
        }
        catch (CosmosException ex) when (ex.StatusCode == System.Net.HttpStatusCode.PreconditionFailed)
        {
            // HTTP 412: Document was modified by another request
            // Retry by re-reading the latest version
            if (attempt == maxRetries - 1)
            {
                throw new InvalidOperationException(
                    $"Failed to update player {playerId} after {maxRetries} attempts due to concurrent modifications.", ex);
            }
            // Loop back to re-read and retry
        }
    }
}
```

**Java equivalent:**

```java
// Java SDK: Use ETag with ifMatchETag option
CosmosItemResponse<Player> response = container.readItem(
    playerId, new PartitionKey(playerId), Player.class);
Player player = response.getItem();
String etag = response.getETag();

// Modify player...

CosmosItemRequestOptions options = new CosmosItemRequestOptions();
options.setIfMatchETag(etag);  // Conditional write

try {
    container.upsertItem(player, new PartitionKey(playerId), options);
} catch (CosmosException ex) {
    if (ex.getStatusCode() == 412) {
        // Retry: document was modified concurrently
    }
}
```

**Python equivalent:**

```python
# Python SDK: Use ETag with match_condition
response = container.read_item(item=player_id, partition_key=player_id)
etag = response.get('_etag')

# Modify response...

container.upsert_item(
    body=response,
    match_condition=etag,      # If-Match header
    etag=etag
)
# Raises CosmosHttpResponseError with status_code=412 on conflict
```

**When to use ETags:**
- **Always use** for read-modify-write patterns (counters, aggregates, status updates)
- **Always use** when multiple users/services can modify the same document
- **Skip** for append-only operations (new document creation with unique IDs)
- **Skip** for idempotent overwrites where last-writer-wins is acceptable

**Key Points:**
- Every Cosmos DB document has a system-managed `_etag` property that changes on every write
- Pass `IfMatchEtag` (or `setIfMatchETag` in Java) to get HTTP 412 on conflicts
- Always implement retry logic (typically 3 attempts) for ETag conflicts
- ETag checks add no extra RU cost — it's a header comparison, not an additional read
- For high-contention scenarios (thousands of concurrent updates to same document), consider a different data model (e.g., append scores as separate documents, aggregate periodically)

Reference: [Optimistic concurrency control in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/database-transactions-optimistic-concurrency#optimistic-concurrency-control)

### 4.8 Configure Excluded Regions for Dynamic Failover

**Impact: MEDIUM** (enables dynamic routing control without code changes)

## Configure Excluded Regions for Dynamic Failover

The excluded regions feature enables fine-grained control over request routing by excluding specific regions on a per-request or client basis. This allows dynamic failover without code changes or restarts.

**Incorrect (static region configuration):**

```csharp
// Static configuration requires restart to change routing
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationPreferredRegions = new List<string> { "East US", "West US" }
});

// If East US has issues but isn't fully down:
// - Circuit breaker thresholds may not trigger
// - Manual intervention required
// - Code changes or restart needed to route away
```

**Correct (.NET SDK - excluded regions):**

```csharp
// Configure excluded regions at request level (.NET SDK 3.37.0+)
CosmosClientOptions options = new CosmosClientOptions()
{
    ApplicationPreferredRegions = new List<string> { "West US", "Central US", "East US" }
};

CosmosClient client = new CosmosClient(connectionString, options);
Container container = client.GetDatabase("myDb").GetContainer("myContainer");

// Normal request - uses West US first
await container.ReadItemAsync<dynamic>("item", new PartitionKey("pk"));

// Exclude regions dynamically - bypasses preferred order
await container.ReadItemAsync<dynamic>(
    "item",
    new PartitionKey("pk"),
    new ItemRequestOptions
    {
        ExcludeRegions = new List<string> { "West US", "Central US" }
    });
// This request goes directly to East US
```

```csharp
// Handle rate limiting by routing to alternate regions
ItemResponse<Order> response;
try
{
    response = await container.ReadItemAsync<Order>("id", partitionKey);
}
catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.TooManyRequests)
{
    // Retry in a different region
    response = await container.ReadItemAsync<Order>(
        "id",
        partitionKey,
        new ItemRequestOptions
        {
            ExcludeRegions = new List<string> { "East US" }  // Exclude throttled region
        });
}
```

**Correct (Java SDK - excluded regions):**

```java
// Configure excluded regions with AtomicReference for dynamic updates
CosmosExcludedRegions excludedRegions = new CosmosExcludedRegions(Set.of("East US"));
AtomicReference<CosmosExcludedRegions> excludedRegionsRef = new AtomicReference<>(excludedRegions);

CosmosAsyncClient client = new CosmosClientBuilder()
    .endpoint("<endpoint>")
    .key("<key>")
    .preferredRegions(List.of("West US", "East US"))
    .excludedRegionsSupplier(excludedRegionsRef::get)  // Dynamic supplier
    .buildAsyncClient();

// Update excluded regions without restart
excludedRegionsRef.set(new CosmosExcludedRegions(Set.of("West US")));

// Request-level override
CosmosItemRequestOptions options = new CosmosItemRequestOptions()
    .setExcludedRegions(List.of("East US"));
container.readItem("id", new PartitionKey("pk"), options, JsonNode.class).block();
```

**Correct (Python SDK - excluded regions):**

```python
from azure.cosmos import CosmosClient

# Configure at client level (Python SDK 4.14.0+)
preferred_locations = ['West US 3', 'West US', 'East US 2']
excluded_locations_on_client = ['West US 3', 'West US']

client = CosmosClient(
    url=HOST,
    credential=MASTER_KEY,
    preferred_locations=preferred_locations,
    excluded_locations=excluded_locations_on_client
)

# Request-level override takes highest priority
item = container.read_item(
    item=created_item['id'],
    partition_key=created_item['pk'],
    excluded_locations=['West US 3']  # Override client settings
)
```

**Use Cases:**

| Scenario | Solution |
|----------|----------|
| Region experiencing high latency | Exclude temporarily via request options |
| Rate limiting in specific region | Route to regions with available throughput |
| Planned maintenance | Pre-exclude region before maintenance window |
| Consistency vs availability trade-off | Exclude all but primary for consistent reads |

**Fine-Tuning Consistency vs Availability:**

```csharp
// Steady state: Prioritize consistency (exclude all but primary)
var steadyStateOptions = new ItemRequestOptions
{
    ExcludeRegions = new List<string> { "East US 2", "West US" }  // Only East US (primary)
};

// Outage mode: Prioritize availability (allow cross-region)
var outageOptions = new ItemRequestOptions
{
    ExcludeRegions = new List<string>()  // Empty - use all regions
};
```

Reference: [Performance tips - .NET SDK Excluded Regions](https://learn.microsoft.com/en-us/azure/cosmos-db/performance-tips-dotnet-sdk-v3#excluded-regions)
Reference: [Performance tips - Java SDK Excluded Regions](https://learn.microsoft.com/en-us/azure/cosmos-db/performance-tips-java-sdk-v4#excluded-regions)

### 4.9 Enable content response on write operations in Java SDK

**Impact: MEDIUM** (ensures created/updated documents are returned from write operations)

## Enable Content Response on Write Operations (Java)

By default, the Java Cosmos DB SDK does **not** return the document content after create/upsert operations. The response contains only metadata (headers, diagnostics) but the `getItem()` method returns null. You must explicitly enable content response if you need the created document.

**Problem - createItem returns null:**

```java
// Default behavior - item is null!
CosmosItemResponse<Order> response = container.createItem(order);
Order createdOrder = response.getItem();  // ❌ Returns null!

// This also affects upsertItem
CosmosItemResponse<Order> response = container.upsertItem(order);
Order upsertedOrder = response.getItem();  // ❌ Returns null!
```

**Solution - Enable contentResponseOnWriteEnabled:**

```java
// Option 1: Set at client level (applies to all operations)
CosmosClient client = new CosmosClientBuilder()
    .endpoint(endpoint)
    .key(key)
    .contentResponseOnWriteEnabled(true)  // Enable for all writes
    .buildClient();

// Now createItem returns the document
CosmosItemResponse<Order> response = container.createItem(order);
Order createdOrder = response.getItem();  // ✅ Returns the created document
```

```java
// Option 2: Set per-request (more granular control)
CosmosItemRequestOptions options = new CosmosItemRequestOptions();
options.setContentResponseOnWriteEnabled(true);

CosmosItemResponse<Order> response = container.createItem(
    order, 
    new PartitionKey(order.getCustomerId()),
    options
);
Order createdOrder = response.getItem();  // ✅ Returns the created document
```

**Async client:**

```java
// With CosmosAsyncClient
CosmosAsyncClient asyncClient = new CosmosClientBuilder()
    .endpoint(endpoint)
    .key(key)
    .contentResponseOnWriteEnabled(true)
    .buildAsyncClient();

// Or per-request
CosmosItemRequestOptions options = new CosmosItemRequestOptions();
options.setContentResponseOnWriteEnabled(true);

container.createItem(order, new PartitionKey(customerId), options)
    .map(response -> response.getItem())  // ✅ Now has the document
    .subscribe(createdOrder -> {
        System.out.println("Created: " + createdOrder.getId());
    });
```

**Spring Data Cosmos:**

```java
// Spring Data Cosmos handles this automatically
// The repository methods return the saved entity

@Repository
public interface OrderRepository extends CosmosRepository<Order, String> {
    // save() returns the saved entity automatically
}

// Usage
Order savedOrder = orderRepository.save(newOrder);  // ✅ Returns saved document
```

**When NOT to enable content response:**

If you don't need the created document (fire-and-forget writes), leave it disabled to save bandwidth:

```java
// High-throughput ingestion - don't need response content
CosmosItemRequestOptions options = new CosmosItemRequestOptions();
options.setContentResponseOnWriteEnabled(false);  // Default, saves bandwidth

for (Order order : ordersToInsert) {
    container.createItem(order, new PartitionKey(order.getCustomerId()), options);
    // Just need to know it succeeded, don't need the document back
}
```

**RU cost consideration:**

Enabling content response does NOT increase RU cost - the document is already fetched server-side for the write operation. It only affects the response payload size over the network.

**Key Points:**
- Java SDK returns null by default for created/upserted items
- Enable `contentResponseOnWriteEnabled(true)` to get documents back
- Can be set at client level (all operations) or per-request
- Spring Data Cosmos handles this automatically
- Disable for high-throughput scenarios where response content is not needed

Reference: [Azure Cosmos DB Java SDK best practices](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-java)

### 4.10 Spring Boot and Java version compatibility for Cosmos DB SDK

**Impact: CRITICAL** (Prevents build failures due to version incompatibility between Spring Boot and Java)

## Spring Boot and Java Version Requirements

The Azure Cosmos DB Java SDK works with various Spring Boot versions, but each Spring Boot version has **strict Java version requirements** that must be met for the project to build successfully.

**Problem:**

Developers may encounter build failures with cryptic error messages when the Java version doesn't match Spring Boot requirements:

```
[ERROR] bad class file...has wrong version 61.0, should be 55.0
[ERROR] release version 17 not supported
```

These errors occur when:
- Spring Boot 3.x is used with Java 11 or lower
- The JAVA_HOME environment variable points to an incompatible Java version
- Maven/Gradle is configured to use a different Java version than expected

**Solution:**

Always match your Java version to your Spring Boot requirements:

### Version Compatibility Matrix

| Spring Boot Version | Minimum Java | Recommended Java | Azure Cosmos SDK | Notes |
|---------------------|--------------|------------------|------------------|-------|
| **3.2.x** | 17 | 17 or 21 | 4.52.0+ | **Requires Java 17+** (non-negotiable) |
| **3.1.x** | 17 | 17 or 21 | 4.52.0+ | **Requires Java 17+** (non-negotiable) |
| **3.0.x** | 17 | 17 | 4.52.0+ | **Requires Java 17+** (non-negotiable) |
| **2.7.x** | 8 | 11 or 17 | 4.52.0+ | Long-term support, uses `javax.*` |

### pom.xml Configuration

For **Spring Boot 3.x** (requires Java 17+):

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.1</version>
</parent>

<properties>
    <java.version>17</java.version>
    <maven.compiler.source>17</maven.compiler.source>
    <maven.compiler.target>17</maven.compiler.target>
    <azure.cosmos.version>4.52.0</azure.cosmos.version>
</properties>

<dependencies>
    <dependency>
        <groupId>com.azure</groupId>
        <artifactId>azure-cosmos</artifactId>
        <version>${azure.cosmos.version}</version>
    </dependency>
</dependencies>
```

For **Spring Boot 2.7.x** (compatible with Java 8, 11, or 17):

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>2.7.18</version>
</parent>

<properties>
    <java.version>11</java.version>  <!-- or 17 -->
    <azure.cosmos.version>4.52.0</azure.cosmos.version>
</properties>
```

### Verify Your Environment

Before building, ensure your Java version matches your Spring Boot requirements:

```bash
# Check Java version
java -version

# Check Maven is using the correct Java version
mvn -version

# Set JAVA_HOME if needed (Windows PowerShell)
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.10.7-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

# Set JAVA_HOME if needed (macOS/Linux)
export JAVA_HOME=/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home
export PATH=$JAVA_HOME/bin:$PATH
```

### Key Differences Between Spring Boot 2.x and 3.x

| Aspect | Spring Boot 2.7.x | Spring Boot 3.x |
|--------|-------------------|-----------------|
| Minimum Java | Java 8 | **Java 17** |
| Package namespace | `javax.*` | `jakarta.*` |
| Azure Cosmos SDK | 4.52.0+ | 4.52.0+ |
| Migration effort | N/A | High (package renames) |

**Key Points:**

- **Spring Boot 3.x is NOT compatible with Java 11 or lower** - the build will fail immediately
- Always set `JAVA_HOME` to point to the correct Java version before building
- Use explicit `maven.compiler.source` and `maven.compiler.target` properties to avoid ambiguity
- Spring Boot 3.x requires migrating from `javax.*` to `jakarta.*` packages (breaking change)
- The Azure Cosmos DB Java SDK (4.52.0+) works with both Spring Boot 2.7.x and 3.x

**Common Pitfalls:**

1. **Multiple Java versions installed**: System may default to older Java version
   - Solution: Explicitly set `JAVA_HOME` before building

2. **IDE using different Java than terminal**: IntelliJ/Eclipse may use project JDK settings
   - Solution: Configure IDE project SDK to match Spring Boot requirements

3. **Docker/CI environments**: Base image Java version may not match
   - Solution: Use `eclipse-temurin:17-jdk` or `amazoncorretto:17` for Spring Boot 3.x

**References:**

- [Spring Boot 3.x System Requirements](https://docs.spring.io/spring-boot/docs/current/reference/html/getting-started.html#getting-started.system-requirements)
- [Spring Boot 2.7.x System Requirements](https://docs.spring.io/spring-boot/docs/2.7.x/reference/html/getting-started.html#getting-started-system-requirements)
- [Azure Cosmos DB Java SDK](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/sdk-java-v4)

### 4.11 Configure local development environment to avoid cloud connection conflicts

**Impact: MEDIUM** (prevents accidental connections to production instead of emulator)

## Configure Local Development Environment Properly

When developing locally with the Cosmos DB Emulator, system-level environment variables pointing to Azure cloud accounts can override your local configuration, causing unexpected connections to production resources instead of the emulator.

**Problem - System environment variables override local config:**

```python
# Your .env file (local config)
COSMOS_ENDPOINT=https://localhost:8081
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==

# But system environment has (from Azure CLI or other tools):
# COSMOS_ENDPOINT=https://my-prod-account.documents.azure.com:443/

# Default dotenv loading does NOT override existing env vars!
from dotenv import load_dotenv
load_dotenv()  # ❌ System COSMOS_ENDPOINT wins - connects to production!
```

**Solution - Force override of environment variables:**

**Python:**

```python
from dotenv import load_dotenv
import os

# Force .env values to override system environment variables
load_dotenv(override=True)  # ✅ .env values take precedence

# Or use explicit defaults for emulator
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "https://localhost:8081")
COSMOS_KEY = os.getenv(
    "COSMOS_KEY", 
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
)
```

**Node.js:**

```javascript
// dotenv also has override option
require('dotenv').config({ override: true });

// Or with explicit defaults
const endpoint = process.env.COSMOS_ENDPOINT || 'https://localhost:8081';
const key = process.env.COSMOS_KEY || 
    'C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==';
```

**.NET:**

```csharp
// appsettings.Development.json takes precedence over appsettings.json
// in Development environment

// appsettings.Development.json
{
  "CosmosDb": {
    "Endpoint": "https://localhost:8081",
    "Key": "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
  }
}

// Program.cs - Environment-specific config loaded automatically
var builder = WebApplication.CreateBuilder(args);
// Configuration precedence: appsettings.{Environment}.json > appsettings.json > env vars
```

```csharp
// Or use explicit emulator detection
public static class CosmosConfig
{
    public static bool IsEmulator(string endpoint) => 
        endpoint.Contains("localhost") || endpoint.Contains("127.0.0.1");
    
    public static CosmosClientOptions GetClientOptions(string endpoint)
    {
        var options = new CosmosClientOptions();
        
        if (IsEmulator(endpoint))
        {
            options.ConnectionMode = ConnectionMode.Gateway;  // Required for emulator
            options.HttpClientFactory = () => new HttpClient(
                new HttpClientHandler
                {
                    ServerCertificateCustomValidationCallback = 
                        HttpClientHandler.DangerousAcceptAnyServerCertificateValidator
                });
        }
        else
        {
            options.ConnectionMode = ConnectionMode.Direct;  // Production
        }
        
        return options;
    }
}
```

**Java (Spring Boot):**

```yaml
# application.yml - Profile-specific configuration
spring:
  profiles:
    active: local  # Set via SPRING_PROFILES_ACTIVE env var

---
# application-local.yml (local development profile)
azure:
  cosmos:
    endpoint: https://localhost:8081
    key: C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==

---
# application-prod.yml (production profile)
azure:
  cosmos:
    endpoint: ${COSMOS_ENDPOINT}  # From environment
    key: ${COSMOS_KEY}  # From Key Vault ideally
```

**Best practices for local development:**

1. **Use profile/environment-specific configuration files**
   - `.env.local`, `appsettings.Development.json`, `application-local.yml`

2. **Log the endpoint at startup (without the key!)**
   ```python
   print(f"Connecting to Cosmos DB at: {COSMOS_ENDPOINT}")
   # Never log the key!
   ```

3. **Validate you're connecting to emulator**
   ```python
   if "localhost" not in COSMOS_ENDPOINT and "127.0.0.1" not in COSMOS_ENDPOINT:
       print("⚠️ WARNING: Not connecting to local emulator!")
       print(f"Endpoint: {COSMOS_ENDPOINT}")
   ```

4. **Use different database names for dev/prod**
   ```python
   DATABASE_NAME = os.getenv("COSMOS_DATABASE", "dev-database")
   # Production uses: prod-ecommerce
   # Local uses: dev-database (default)
   ```

5. **Clear conflicting system environment variables**
   ```powershell
   # PowerShell - temporarily clear for this session
   $env:COSMOS_ENDPOINT = $null
   $env:COSMOS_KEY = $null
   
   # Or unset permanently
   [Environment]::SetEnvironmentVariable("COSMOS_ENDPOINT", $null, "User")
   ```

**Key Points:**
- System environment variables take precedence over .env files by default
- Use `load_dotenv(override=True)` in Python to force local config
- Use environment/profile-specific configuration files
- Log the endpoint (not the key!) at startup to verify correct connection
- The emulator uses a well-known key - don't use this in production!

Reference: [Azure Cosmos DB Emulator](https://learn.microsoft.com/azure/cosmos-db/emulator)

### 4.12 Explicitly reference Newtonsoft.Json package

**Impact: MEDIUM** (Prevents build failures and security vulnerabilities from missing or outdated Newtonsoft.Json dependency)

## Explicitly reference Newtonsoft.Json package

The Azure Cosmos DB .NET SDK requires an explicit reference to `Newtonsoft.Json` version 13.0.3 or higher. This dependency is not managed automatically - you must add it directly to your project.

**Problem (build fails without explicit reference):**

```csharp
// Your .csproj only references Cosmos DB SDK
<ItemGroup>
  <PackageReference Include="Microsoft.Azure.Cosmos" Version="3.47.0" />
  <!-- Missing Newtonsoft.Json reference! -->
</ItemGroup>

// Build error:
// error: The Newtonsoft.Json package must be explicitly referenced with version >= 10.0.2.
// Please add a reference to Newtonsoft.Json or set the 
// 'AzureCosmosDisableNewtonsoftJsonCheck' property to 'true' to bypass this check.
```

**Solution (add explicit Newtonsoft.Json reference):**

```xml
<!-- Standard .csproj projects -->
<ItemGroup>
  <PackageReference Include="Microsoft.Azure.Cosmos" Version="3.47.0" />
  <PackageReference Include="Newtonsoft.Json" Version="13.0.4" />
</ItemGroup>
```

**For projects using Central Package Management:**

```xml
<!-- Directory.Packages.props -->
<Project>
  <ItemGroup>
    <PackageVersion Include="Microsoft.Azure.Cosmos" Version="3.47.0" />
    <PackageVersion Include="Newtonsoft.Json" Version="13.0.4" />
  </ItemGroup>
</Project>
```

**Key Points:**

- **Always use version 13.0.3 or higher** - Never use 10.x despite technical compatibility, as it has known security vulnerabilities
- **Required even with System.Text.Json** - The dependency is needed even when using `CosmosClientOptions.UseSystemTextJsonSerializerWithOptions`, because the SDK's internal operations still use Newtonsoft.Json for system types
- **Build check is intentional** - The Cosmos DB SDK includes build targets that explicitly check for this dependency to prevent issues
- **Pin the version explicitly** - Don't rely on transitive dependency resolution
- **SDK compiles against 10.x internally** - But recommends 13.0.3+ to avoid security issues and conflicts

**Version Compatibility:**

| Cosmos DB SDK Version | Minimum Secure Newtonsoft.Json | Recommended |
|-----------------------|--------------------------------|-------------|
| 3.47.0+ | 13.0.3 | 13.0.4 |
| 3.54.0+ | 13.0.4 | 13.0.4 |

**Special Cases:**

**For library projects** (not applications):

If you're building a reusable library and want to defer the Newtonsoft.Json dependency to your library's consumers, you can bypass the build check:

```xml
<PropertyGroup>
  <AzureCosmosDisableNewtonsoftJsonCheck>true</AzureCosmosDisableNewtonsoftJsonCheck>
</PropertyGroup>
```

⚠️ **Warning**: Only use this bypass for libraries. For applications, always add the explicit reference.

**Troubleshooting version conflicts:**

If you see package downgrade errors:

```
error NU1109: Detected package downgrade: Newtonsoft.Json from 13.0.4 to 13.0.3
```

Solution:
1. Check which packages need which versions:
   ```bash
   dotnet list package --include-transitive | findstr Newtonsoft.Json
   ```
2. Update to the highest required version in your central package management or csproj
3. Clean and rebuild:
   ```bash
   dotnet clean && dotnet restore && dotnet build
   ```

**Why This Matters:**

- **Prevents build failures** - The SDK will fail the build if Newtonsoft.Json is missing
- **Security** - Version 10.x has known vulnerabilities that should be avoided
- **Compatibility** - Ensures consistent behavior across different environments
- **Future-proofing** - Explicit references prevent surprises when transitive dependencies change

Reference: [Managing Newtonsoft.Json Dependencies](https://learn.microsoft.com/en-us/azure/cosmos-db/performance-tips-dotnet-sdk-v3?tabs=trace-net-core#managing-newtonsoftjson-dependencies)

### 4.13 Configure Preferred Regions for Availability

**Impact: HIGH** (enables automatic failover, reduces latency)

## Configure Preferred Regions for Availability

Configure preferred regions in priority order for multi-region deployments. The SDK automatically routes to available regions during outages.

**Incorrect (no region configuration):**

```csharp
// No region preference - SDK uses account's default write region
var client = new CosmosClient(connectionString);

// Problems:
// - May route to distant region (high latency)
// - No automatic failover if region goes down
// - Unpredictable behavior during partial outages
```

**Correct (explicit region configuration):**

```csharp
// Configure preferred regions in order of preference
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationName = "MyApp",
    
    // SDK tries regions in order until one succeeds
    ApplicationPreferredRegions = new List<string>
    {
        Regions.WestUS2,      // Primary (closest to users)
        Regions.EastUS2,      // Secondary (nearby)
        Regions.WestEurope    // Tertiary (disaster recovery)
    }
});

// SDK automatically:
// 1. Connects to first available region in list
// 2. Fails over to next region if current becomes unavailable
// 3. Fails back when preferred region recovers
```

```csharp
// Dynamic region based on deployment
public static CosmosClient CreateClient(string connectionString, string deploymentRegion)
{
    var preferredRegions = deploymentRegion switch
    {
        "westus" => new List<string> { Regions.WestUS2, Regions.EastUS2, Regions.WestEurope },
        "eastus" => new List<string> { Regions.EastUS2, Regions.WestUS2, Regions.WestEurope },
        "europe" => new List<string> { Regions.WestEurope, Regions.NorthEurope, Regions.EastUS2 },
        _ => new List<string> { Regions.WestUS2 }
    };
    
    return new CosmosClient(connectionString, new CosmosClientOptions
    {
        ApplicationPreferredRegions = preferredRegions
    });
}
```

```csharp
// For multi-region writes, enable endpoint discovery
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationPreferredRegions = new List<string>
    {
        Regions.WestUS2,
        Regions.EastUS2
    },
    
    // Enable endpoint discovery for multi-region accounts
    EnableTcpConnectionEndpointRediscovery = true,
    
    // For multi-region writes, writes can go to any region
    // SDK handles routing automatically
});
```

```csharp
// Verify region routing in diagnostics
var response = await container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
var diagnostics = response.Diagnostics.ToString();
_logger.LogDebug("Request region info: {Diagnostics}", diagnostics);
// Check contacted regions, failovers in diagnostics
```

Best practices:
- List closest region first
- Include at least 2 regions for redundancy
- Match regions with your account's replicated regions
- Use Azure region constants (Regions.WestUS2) for correctness

Reference: [Configure preferred regions](https://learn.microsoft.com/azure/cosmos-db/nosql/tutorial-global-distribution)

### 4.14 Handle 429 Errors with Retry-After

**Impact: HIGH** (prevents cascading failures)

## Handle 429 Errors with Retry-After

Properly handle rate limiting (HTTP 429) responses by respecting the Retry-After header. The SDK handles this automatically, but configuration and logging are important.

**Incorrect (ignoring or mishandling throttling):**

```csharp
// Anti-pattern: Retrying immediately without backoff
public async Task<Order> GetOrderWithBadRetry(string orderId, string customerId)
{
    while (true)
    {
        try
        {
            return await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
        }
        catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.TooManyRequests)
        {
            // WRONG: Immediate retry makes throttling worse!
            continue;
        }
    }
}

// Anti-pattern: Failing immediately on throttling
public async Task<Order> GetOrderWithNoRetry(string orderId, string customerId)
{
    try
    {
        return await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
    }
    catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.TooManyRequests)
    {
        // WRONG: Failing on transient error
        throw new ApplicationException("Database unavailable");
    }
}
```

**Correct (leverage SDK's built-in retry):**

```csharp
// Configure client with appropriate retry settings
var cosmosClient = new CosmosClient(connectionString, new CosmosClientOptions
{
    // SDK automatically retries 429s up to this many times
    MaxRetryAttemptsOnRateLimitedRequests = 9,
    
    // Maximum total wait time for retries
    MaxRetryWaitTimeOnRateLimitedRequests = TimeSpan.FromSeconds(30),
    
    // Enable automatic retry (on by default)
    EnableTcpConnectionEndpointRediscovery = true
});

// SDK handles 429 automatically with exponential backoff
// respecting the Retry-After header from service
public async Task<Order> GetOrderAsync(string orderId, string customerId)
{
    // No manual retry logic needed!
    return await _container.ReadItemAsync<Order>(
        orderId, 
        new PartitionKey(customerId));
}
```

```csharp
// Log throttling for monitoring and capacity planning
public async Task<Order> GetOrderWithDiagnostics(string orderId, string customerId)
{
    try
    {
        var response = await _container.ReadItemAsync<Order>(
            orderId, 
            new PartitionKey(customerId));
        
        // Log RU consumption for capacity planning
        _logger.LogDebug("Read order {OrderId}: {RU} RU", orderId, response.RequestCharge);
        
        return response.Resource;
    }
    catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.TooManyRequests)
    {
        // This only fires if ALL retries exhausted
        _logger.LogWarning(
            "Throttled after all retries. RetryAfter: {RetryAfter}, Diagnostics: {Diagnostics}",
            ex.RetryAfter,
            ex.Diagnostics);
        
        throw;  // Let it bubble up - caller should handle
    }
}
```

```csharp
// For bulk operations, use Bulk API with built-in throttling management
var bulkOptions = new CosmosClientOptions
{
    AllowBulkExecution = true,
    MaxRetryAttemptsOnRateLimitedRequests = 9,
    MaxRetryWaitTimeOnRateLimitedRequests = TimeSpan.FromSeconds(60)
};

var bulkClient = new CosmosClient(connectionString, bulkOptions);

// Bulk upsert handles throttling automatically
var tasks = items.Select(item => 
    container.UpsertItemAsync(item, new PartitionKey(item.PartitionKey)));
await Task.WhenAll(tasks);
```

Reference: [Handle rate limiting](https://learn.microsoft.com/azure/cosmos-db/nosql/troubleshoot-request-rate-too-large)

### 4.15 Use consistent enum serialization between Cosmos SDK and application layer

**Impact: critical** (undefined)

# Use Consistent Enum Serialization

## Problem

The Cosmos DB SDK's default serializer stores enums as **integers**, but many application frameworks (ASP.NET Core, Spring Boot) serialize enums as **strings** in API responses. This mismatch causes queries to fail silently - returning empty results when filtering by enum values.

## Example Bug

```csharp
// Model with enum
public class Order
{
    public OrderStatus Status { get; set; }  // Stored as integer: 1
}

// Query looks for string - FINDS NOTHING!
var query = new QueryDefinition("SELECT * FROM c WHERE c.status = @status")
    .WithParameter("@status", "Shipped");  // ❌ Wrong - Cosmos has integer 1
```

## Solution

### Option 1: Configure Cosmos SDK to use string serialization (Recommended)

**.NET - Use System.Text.Json with string enums:**
```csharp
var clientOptions = new CosmosClientOptions
{
    Serializer = new CosmosSystemTextJsonSerializer(new JsonSerializerOptions
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        Converters = { new JsonStringEnumConverter() }
    })
};
var client = new CosmosClient(endpoint, key, clientOptions);
```

**Java - Use Jackson with string enums:**
```java
ObjectMapper mapper = new ObjectMapper();
mapper.configure(SerializationFeature.WRITE_ENUMS_USING_TO_STRING, true);
mapper.configure(DeserializationFeature.READ_ENUMS_USING_TO_STRING, true);

CosmosClientBuilder builder = new CosmosClientBuilder()
    .endpoint(endpoint)
    .key(key)
    .customSerializer(new JacksonJsonSerializer(mapper));
```

**Python - Enums serialize as strings by default with proper setup:**
```python
from enum import Enum

class OrderStatus(str, Enum):  # Inherit from str for JSON serialization
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
```

### Option 2: Query using integer values

If you can't change the serializer, query with the integer value:

```csharp
// Query with integer value
var query = new QueryDefinition("SELECT * FROM c WHERE c.status = @status")
    .WithParameter("@status", (int)OrderStatus.Shipped);  // ✅ Matches stored data
```

### Option 3: Store status as string explicitly

```csharp
public class Order
{
    // Store as string, not enum
    public string Status { get; set; } = "Pending";
}
```

## Best Practice

**Always verify serialization consistency** by:
1. Creating a test document
2. Reading it back via the SDK
3. Querying it with a filter
4. Checking the raw JSON in Data Explorer

## Warning Signs

- Queries return empty results but you know matching documents exist
- Point reads work but filtered queries don't
- API returns different enum format than stored in Cosmos DB

### 4.16 Reuse CosmosClient as Singleton

**Impact: CRITICAL** (prevents connection exhaustion)

## Reuse CosmosClient as Singleton

Create CosmosClient once and reuse it throughout the application lifetime. Creating multiple clients exhausts connections and wastes resources.

**Incorrect (creating new client per request):**

```csharp
// Anti-pattern: New client per operation
public class OrderRepository
{
    public async Task<Order> GetOrder(string orderId, string customerId)
    {
        // WRONG: Creates new client every call!
        using var cosmosClient = new CosmosClient(connectionString);
        var container = cosmosClient.GetContainer("db", "orders");
        return await container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
    }
    // Client disposed = connection closed
    // Next call = new connection = TCP handshake + TLS negotiation
}

// Results in:
// - Connection exhaustion under load
// - High latency (connection setup per request)
// - Memory leaks (connection pool not reused)
// - Eventually: SocketException or timeout errors
```

**Correct (singleton client):**

```csharp
// Register as singleton in DI
public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddCosmosDb(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddSingleton<CosmosClient>(sp =>
        {
            var connectionString = configuration["CosmosDb:ConnectionString"];
            
            return new CosmosClient(connectionString, new CosmosClientOptions
            {
                ApplicationName = "MyApp",
                ConnectionMode = ConnectionMode.Direct,
                MaxRetryAttemptsOnRateLimitedRequests = 9,
                MaxRetryWaitTimeOnRateLimitedRequests = TimeSpan.FromSeconds(30)
            });
        });
        
        services.AddSingleton<IOrderRepository, OrderRepository>();
        
        return services;
    }
}

// Repository uses injected singleton client
public class OrderRepository : IOrderRepository
{
    private readonly Container _container;
    
    public OrderRepository(CosmosClient cosmosClient)
    {
        _container = cosmosClient.GetContainer("db", "orders");
    }
    
    public async Task<Order> GetOrder(string orderId, string customerId)
    {
        return await _container.ReadItemAsync<Order>(
            orderId, 
            new PartitionKey(customerId));
    }
}
```

```csharp
// For Azure Functions (using static initialization)
public static class CosmosDbFunction
{
    private static readonly Lazy<CosmosClient> _lazyClient = new(() =>
    {
        var connectionString = Environment.GetEnvironmentVariable("CosmosDbConnection");
        return new CosmosClient(connectionString);
    });
    
    private static CosmosClient Client => _lazyClient.Value;
    
    [FunctionName("GetOrder")]
    public static async Task<IActionResult> GetOrder(
        [HttpTrigger(AuthorizationLevel.Function, "get")] HttpRequest req)
    {
        var container = Client.GetContainer("db", "orders");
        // Client reused across all function invocations
    }
}
```

```csharp
// Graceful shutdown (optional but recommended)
public class CosmosDbHostedService : IHostedService
{
    private readonly CosmosClient _client;
    
    public CosmosDbHostedService(CosmosClient client) => _client = client;
    
    public Task StartAsync(CancellationToken cancellationToken) => Task.CompletedTask;
    
    public async Task StopAsync(CancellationToken cancellationToken)
    {
        _client.Dispose();
    }
}
```

Reference: [CosmosClient best practices](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)

---

## 5. Indexing Strategies

**Impact: MEDIUM-HIGH**

### 5.1 Use Composite Indexes for ORDER BY

**Impact: HIGH** (enables sorted queries, reduces RU)

## Use Composite Indexes for ORDER BY

Create composite indexes for queries with ORDER BY on multiple properties. Without them, queries may fail or require expensive client-side sorting.

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

Rules:
- Composite index order must match ORDER BY exactly
- First path can be equality filter
- Include both ASC/DESC variants for flexibility
- Maximum 8 paths per composite index

Reference: [Composite indexes](https://learn.microsoft.com/azure/cosmos-db/index-policy#composite-indexes)

### 5.2 Exclude Unused Index Paths

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

### 5.3 Understand Indexing Modes

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

### 5.4 Choose Appropriate Index Types

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

### 5.5 Add Spatial Indexes for Geo Queries

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

## 6. Throughput & Scaling

**Impact: MEDIUM**

### 6.1 Use Autoscale for Variable Workloads

**Impact: HIGH** (handles traffic spikes, optimizes cost)

## Use Autoscale for Variable Workloads

Use autoscale throughput for workloads with variable or unpredictable traffic patterns. It automatically scales between 10% and 100% of max RU/s.

**Incorrect (fixed throughput for variable workload):**

```csharp
// Fixed provisioned throughput
var containerProperties = new ContainerProperties
{
    Id = "orders",
    PartitionKeyPath = "/customerId"
};

await database.CreateContainerAsync(
    containerProperties,
    throughput: 10000);  // Fixed 10,000 RU/s always

// Problems:
// - Peak hours: 10K RU/s isn't enough → throttling
// - Off-peak: 10K RU/s is wasted → paying for unused capacity
// - Black Friday: Can't handle 50x spike → massive throttling
```

**Correct (autoscale for variable workloads):**

```csharp
// Autoscale with max 10,000 RU/s
var containerProperties = new ContainerProperties
{
    Id = "orders",
    PartitionKeyPath = "/customerId"
};

await database.CreateContainerAsync(
    containerProperties,
    throughputProperties: ThroughputProperties.CreateAutoscaleThroughput(
        maxThroughput: 10000));  // Scales 1,000-10,000 RU/s

// Benefits:
// - Quiet period: Scales down to 1,000 RU/s (10% of max)
// - Busy period: Scales up to 10,000 RU/s automatically
// - No throttling during traffic spikes
// - Pay only for what you use (within autoscale range)
```

```csharp
// Check current autoscale settings
var throughputResponse = await container.ReadThroughputAsync(new RequestOptions());
var autoscaleSettings = throughputResponse.Resource.AutoscaleMaxThroughput;
Console.WriteLine($"Autoscale max: {autoscaleSettings} RU/s");
Console.WriteLine($"Current: {throughputResponse.Resource.Throughput} RU/s");
```

```csharp
// Modify autoscale max throughput
await container.ReplaceThroughputAsync(
    ThroughputProperties.CreateAutoscaleThroughput(maxThroughput: 20000));
// Now scales between 2,000-20,000 RU/s
```

Cost comparison example:
- Fixed 10,000 RU/s: ~$584/month (always)
- Autoscale 10,000 max: $58-$584/month (based on usage)
- If average utilization is 30%, autoscale saves ~70%!

When to use autoscale:
- Variable traffic (peak hours, batch jobs)
- Unpredictable workloads
- Development/test environments
- New applications (unknown traffic patterns)

When to use fixed:
- Steady, predictable workloads (utilization > 66%)
- Cost-sensitive workloads with known patterns

Reference: [Autoscale throughput](https://learn.microsoft.com/azure/cosmos-db/provision-throughput-autoscale)

### 6.2 Understand Burst Capacity

**Impact: MEDIUM** (handles short traffic spikes)

## Understand Burst Capacity

Cosmos DB provides burst capacity to handle short traffic spikes above provisioned throughput. Understand how it works to avoid unexpected throttling.

**How burst capacity works:**

```csharp
// Cosmos DB accumulates unused RU/s into a burst bucket
// Maximum burst: 300 seconds worth of provisioned throughput

// Example: 1,000 RU/s provisioned
// - If you use 500 RU/s average, unused 500 RU/s accumulates
// - Maximum burst bucket: 1,000 × 300 = 300,000 RU
// - Allows short spike up to ~1,500 RU/s until bucket depletes

// Visual representation:
// Time:    | Steady | Light | BURST | Steady |
// Usage:   | 1000   | 500   | 2000  | 1000   |
// Burst:   | 0      | +500  | -1000 | 0      |
//          |--------|-------|-------|--------|
// Result:  | OK     | OK    | OK*   | OK     |
// * Uses accumulated burst capacity
```

**Incorrect (relying on burst for sustained load):**

```csharp
// Provisioned 1,000 RU/s but regularly need 1,500 RU/s
var container = await database.CreateContainerAsync(props, throughput: 1000);

// Hoping burst will cover:
// - Hour 1: Burst bucket fills from overnight
// - Hour 2-3: Burst bucket depletes
// - Hour 4+: Throttling (429s) begins!

// Result: Temporary success followed by degraded performance
```

**Correct (provision for actual sustained needs):**

```csharp
// Option 1: Provision for peak sustained load
await database.CreateContainerAsync(props, throughput: 1500);

// Option 2: Use autoscale for variable loads
await database.CreateContainerAsync(
    props,
    throughputProperties: ThroughputProperties.CreateAutoscaleThroughput(
        maxThroughput: 2000));  // Scales 200-2000 RU/s

// Burst is for:
// - Momentary spikes (seconds to a few minutes)
// - NOT for sustained elevated load
```

```csharp
// Monitor burst usage
// Azure Monitor metric: "Normalized RU Consumption"
// - > 100% means using burst capacity
// - Sustained > 100% will lead to throttling

// Detect burst usage in code
var response = await container.ReadItemAsync<Order>(id, pk);
// Check if operation used more than provisioned share
// (Diagnostics contain server-side timing and capacity info)
```

Best practices:
- Use burst for absorbing unexpected short spikes
- Don't rely on burst for regular operation
- Monitor "Normalized RU Consumption" metric
- If regularly > 90%, consider scaling up or using autoscale
- Burst capacity is per partition - hot partitions may throttle even with burst available

Reference: [Burst capacity](https://learn.microsoft.com/azure/cosmos-db/concepts-limits#throughput-limits)

### 6.3 Choose Container vs Database Throughput

**Impact: MEDIUM** (optimizes cost and isolation)

## Choose Container vs Database Throughput

Decide between container-level (dedicated) and database-level (shared) throughput based on workload isolation needs and cost optimization.

**Container-level throughput (dedicated):**

```csharp
// Each container has dedicated RU/s
var ordersContainer = await database.CreateContainerAsync(
    new ContainerProperties("orders", "/customerId"),
    throughput: 10000);  // Dedicated 10,000 RU/s

var productsContainer = await database.CreateContainerAsync(
    new ContainerProperties("products", "/categoryId"),
    throughput: 2000);  // Dedicated 2,000 RU/s

// Benefits:
// - Guaranteed throughput per container
// - No "noisy neighbor" effect
// - Predictable performance

// Use when:
// - Critical workloads needing guaranteed throughput
// - Containers with very different usage patterns
// - High-throughput containers (> 10,000 RU/s)
```

**Database-level throughput (shared):**

```csharp
// Database shares throughput across containers
var database = await cosmosClient.CreateDatabaseAsync(
    "my-database",
    throughput: 10000);  // 10,000 RU/s shared across all containers

var ordersContainer = await database.CreateContainerAsync(
    new ContainerProperties("orders", "/customerId"));
    // No throughput specified - uses database shared pool

var productsContainer = await database.CreateContainerAsync(
    new ContainerProperties("products", "/categoryId"));
    // Also uses shared pool

var logsContainer = await database.CreateContainerAsync(
    new ContainerProperties("logs", "/date"));
    // Also uses shared pool

// Benefits:
// - Cost efficient for many low-traffic containers
// - Throughput flows to wherever it's needed
// - Minimum 400 RU/s total (vs 400 per container)

// Use when:
// - Many containers with varying/low traffic
// - Containers accessed at different times
// - Cost optimization is priority
```

**Hybrid approach:**

```csharp
// Shared database for most containers
var database = await cosmosClient.CreateDatabaseAsync(
    "my-database",
    throughput: 5000);  // 5,000 RU/s shared

// Dedicated throughput for critical/high-volume container
var ordersContainer = await database.CreateContainerAsync(
    new ContainerProperties("orders", "/customerId"),
    throughput: 10000);  // Dedicated 10,000 RU/s - NOT shared!

// Other containers share database throughput
var productsContainer = await database.CreateContainerAsync(
    new ContainerProperties("products", "/categoryId"));  // Shared
var usersContainer = await database.CreateContainerAsync(
    new ContainerProperties("users", "/userId"));  // Shared
```

Decision matrix:
| Scenario | Recommendation |
|----------|---------------|
| Few containers, predictable load | Container-level |
| Many containers, variable load | Database-level |
| Mixed critical + low-traffic | Hybrid |
| Multi-tenant isolation | Container-level per tenant |
| Development/testing | Database-level (cost saving) |

Reference: [Throughput on containers vs databases](https://learn.microsoft.com/azure/cosmos-db/set-throughput)

### 6.4 Right-Size Provisioned Throughput

**Impact: MEDIUM** (balances performance and cost)

## Right-Size Provisioned Throughput

Provision throughput based on actual workload needs. Over-provisioning wastes money; under-provisioning causes throttling.

**Incorrect (arbitrary throughput):**

```csharp
// Guessing throughput without analysis
await database.CreateContainerAsync(containerProperties, throughput: 10000);
// "10,000 sounds like a good number"

// Results in:
// - Over-provisioned: Wasting money if actual need is 2,000 RU/s
// - Under-provisioned: Throttling if actual need is 15,000 RU/s
```

**Correct (data-driven provisioning):**

```csharp
// Step 1: Calculate RU requirements

// Point read (by id + partition key): ~1 RU for 1KB item
// Point write: ~5 RU for 1KB item  
// Query: 2.5-10+ RU depending on complexity

// Example calculation:
// - 100 reads/sec × 1 RU = 100 RU/s
// - 50 writes/sec × 5 RU = 250 RU/s
// - 20 queries/sec × 10 RU = 200 RU/s
// - Total: 550 RU/s baseline
// - Add 2x buffer for spikes: 1,100 RU/s
// - Round to minimum: 1,000 RU/s (minimum for manual)

await database.CreateContainerAsync(containerProperties, throughput: 1000);
```

```csharp
// Step 2: Monitor and adjust

// Check RU consumption in code
var response = await container.ReadItemAsync<Order>(id, new PartitionKey(pk));
Console.WriteLine($"Read consumed: {response.RequestCharge} RU");

var queryResponse = await container.GetItemQueryIterator<Order>(query).ReadNextAsync();
Console.WriteLine($"Query consumed: {queryResponse.RequestCharge} RU");

// Monitor via Azure Monitor metrics:
// - Total Request Units: actual consumption
// - Normalized RU Consumption: % of provisioned used
// - 429 Throttling: indicates under-provisioned
```

```csharp
// Step 3: Adjust based on metrics
public async Task AdjustThroughputAsync(Container container)
{
    // Get current throughput
    var current = await container.ReadThroughputAsync();
    
    // Check metrics (would come from Azure Monitor in production)
    var avgUtilization = await GetAverageRUUtilization(container);
    
    if (avgUtilization > 80)
    {
        // Scale up to reduce throttling risk
        var newThroughput = (int)(current.Resource.Throughput * 1.5);
        await container.ReplaceThroughputAsync(newThroughput);
        _logger.LogInformation("Scaled up to {RU} RU/s", newThroughput);
    }
    else if (avgUtilization < 20)
    {
        // Scale down to save cost
        var newThroughput = Math.Max(400, (int)(current.Resource.Throughput * 0.5));
        await container.ReplaceThroughputAsync(newThroughput);
        _logger.LogInformation("Scaled down to {RU} RU/s", newThroughput);
    }
}
```

Throughput guidance:
- Start low, monitor, and adjust
- Target 60-70% average utilization for fixed throughput
- Use autoscale for unpredictable workloads
- Monitor for 429s (throttling indicator)
- Scale before known traffic events (sales, launches)

Reference: [Estimate RU/s](https://learn.microsoft.com/azure/cosmos-db/estimate-ru-with-capacity-planner)

### 6.5 Consider Serverless for Dev/Test

**Impact: MEDIUM** (pay-per-request pricing)

## Consider Serverless for Dev/Test

Use serverless accounts for development, testing, and low-traffic workloads. Pay only for actual RU consumption with no minimum commitment.

**Incorrect (provisioned for low traffic):**

```csharp
// Development environment with provisioned throughput
// Minimum 400 RU/s × 24 hours × 30 days = always-on cost
await database.CreateContainerAsync(containerProperties, throughput: 400);

// Problems:
// - Dev environment sits idle 90% of time
// - Still paying for 400 RU/s continuously
// - Multiple dev containers = multiplied waste
```

**Correct (serverless for low/sporadic traffic):**

```csharp
// Create serverless account (at account level, not container)
// No throughput specification - purely consumption-based

// Container creation in serverless account (no throughput parameter)
var containerProperties = new ContainerProperties
{
    Id = "orders",
    PartitionKeyPath = "/customerId"
};

await database.CreateContainerIfNotExistsAsync(containerProperties);
// No throughput = serverless mode

// Cost: Only pay for RUs consumed
// - Idle: $0
// - Light usage: pennies per day
// - Burst: pay for actual consumption
```

```csharp
// Serverless is set at account level, not container
// ARM template for serverless account
{
    "type": "Microsoft.DocumentDB/databaseAccounts",
    "apiVersion": "2021-10-15",
    "name": "my-serverless-account",
    "properties": {
        "databaseAccountOfferType": "Standard",
        "capabilities": [
            {
                "name": "EnableServerless"  // Serverless mode
            }
        ],
        "locations": [
            {
                "locationName": "West US 2"
            }
        ]
    }
}
```

When to use serverless:
- Development and test environments
- Proof of concepts and prototypes
- Low traffic applications (< 5,000 RU/s sustained)
- Sporadic workloads (nightly batch jobs)
- Variable traffic with low baseline

When NOT to use serverless:
- Production with sustained high traffic
- Applications requiring > 5,000 RU/s
- Multi-region deployments (not supported)
- Workloads needing guaranteed throughput

```csharp
// Serverless limitations to be aware of
// - Maximum 5,000 RU/s per container
// - Single region only
// - No dedicated gateway
// - No analytical store (Synapse Link)

// Cost comparison:
// Provisioned 400 RU/s: ~$23/month (always)
// Serverless with 1M RU/month: ~$0.25/month
// Break-even: ~30M RU/month
```

Reference: [Serverless in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/serverless)

---

## 7. Global Distribution

**Impact: MEDIUM**

### 7.1 Implement Conflict Resolution

**Impact: MEDIUM** (ensures data integrity in multi-region)

## Implement Conflict Resolution

Configure appropriate conflict resolution policies for multi-region write scenarios. Without proper handling, data can be lost.

**Understanding conflicts:**

```csharp
// Conflicts occur when same document is written in multiple regions
// before replication completes

// Region A: Update order status to "shipped"
// Region B: Update order status to "cancelled" (same time)
// Both writes succeed locally, then conflict during replication
```

**Incorrect (ignoring conflicts):**

```csharp
// Using default LWW with _ts but not understanding implications
// Later timestamp wins - but "later" may be wrong server

// Server A clock: 10:00:00.100 → "shipped"
// Server B clock: 10:00:00.050 → "cancelled"
// Result: "shipped" wins even though B's write may be logically later
```

**Correct (explicit conflict resolution):**

```csharp
// Option 1: Last Writer Wins with logical clock (recommended)
var containerProperties = new ContainerProperties
{
    Id = "orders",
    PartitionKeyPath = "/customerId",
    ConflictResolutionPolicy = new ConflictResolutionPolicy
    {
        Mode = ConflictResolutionMode.LastWriterWins,
        ResolutionPath = "/version"  // Use application-managed version
    }
};

// Document with version counter
public class Order
{
    public string Id { get; set; }
    public string CustomerId { get; set; }
    public string Status { get; set; }
    public long Version { get; set; }  // Increment on each update
}

// Update with version increment
public async Task UpdateOrderStatus(Order order, string newStatus)
{
    order.Status = newStatus;
    order.Version++;  // Higher version always wins
    await container.UpsertItemAsync(order, new PartitionKey(order.CustomerId));
}
```

```csharp
// Option 2: Stored procedure for custom resolution
var containerWithCustom = new ContainerProperties
{
    Id = "inventory",
    PartitionKeyPath = "/productId",
    ConflictResolutionPolicy = new ConflictResolutionPolicy
    {
        Mode = ConflictResolutionMode.Custom,
        ResolutionProcedure = "dbs/mydb/colls/inventory/sprocs/resolveConflict"
    }
};

// Stored procedure for custom logic
// Example: For inventory, take the LOWER value (conservative)
const string resolveConflictSproc = @"
function resolveConflict(incomingItem, existingItem, isTombstone, conflictingItems) {
    if (isTombstone) {
        // Delete wins
        return existingItem;
    }
    
    // For inventory: lower quantity wins (conservative)
    if (existingItem.quantity < incomingItem.quantity) {
        return existingItem;
    }
    return incomingItem;
}";
```

```csharp
// Option 3: Read and resolve conflicts manually (async)
// Conflicts written to conflicts feed when no automatic resolution

var conflictsFeed = container.Conflicts.GetConflictQueryIterator<dynamic>();

while (conflictsFeed.HasMoreResults)
{
    var conflicts = await conflictsFeed.ReadNextAsync();
    foreach (var conflict in conflicts)
    {
        // Read conflicting versions
        var conflictContent = await container.Conflicts.ReadCurrentAsync<Order>(
            conflict, new PartitionKey(conflict.PartitionKey));
        
        // Apply custom resolution logic
        var resolvedOrder = ResolveOrderConflict(conflictContent.Resource);
        
        // Write resolved version
        await container.UpsertItemAsync(resolvedOrder);
        
        // Delete conflict record
        await container.Conflicts.DeleteAsync(conflict, new PartitionKey(conflict.PartitionKey));
    }
}
```

Best practices:
- Use LWW with application-controlled version for simple cases
- Use stored procedures when business logic determines winner
- Monitor conflicts feed if using Custom mode
- Design to minimize conflicts (partition by user, idempotent operations)

Reference: [Conflict resolution](https://learn.microsoft.com/azure/cosmos-db/conflict-resolution-policies)

### 7.2 Choose Appropriate Consistency Level

**Impact: HIGH** (balances latency, availability, consistency)

## Choose Appropriate Consistency Level

Select the consistency level that matches your application's requirements. Each level has different tradeoffs for latency, availability, and consistency.

**Consistency levels (strongest to weakest):**

```csharp
// STRONG - Linearizable reads
// Reads always see most recent committed write
// Highest latency, lowest availability in multi-region
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ConsistencyLevel = ConsistencyLevel.Strong
});
// Use: Financial transactions, inventory management
// Tradeoff: Higher latency, reduced availability during regional outage

// BOUNDED STALENESS - Reads lag behind writes by bounded amount
// "Reads at least this fresh" guarantee
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ConsistencyLevel = ConsistencyLevel.BoundedStaleness
});
// Use: Stock tickers, leaderboards (where slight delay is OK)
// Tradeoff: May read slightly old data, better performance than Strong

// SESSION (DEFAULT) - Monotonic reads within session
// Client always sees its own writes
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ConsistencyLevel = ConsistencyLevel.Session
});
// Use: Most applications - user sees their changes
// Best balance of consistency and performance

// CONSISTENT PREFIX - Reads never see out-of-order writes
// Guarantees ordering but may lag behind
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ConsistencyLevel = ConsistencyLevel.ConsistentPrefix
});
// Use: Event sourcing, activity feeds
// Tradeoff: May read stale data, but always in order

// EVENTUAL - Weakest, highest performance
// No ordering guarantees, eventually converges
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ConsistencyLevel = ConsistencyLevel.Eventual
});
// Use: View counts, likes, non-critical telemetry
// Best performance, lowest cost
```

**Correct (choosing based on requirements):**

```csharp
// Example: E-commerce platform

// Orders container - Strong or Session
// User must see their order immediately after placing
var ordersClient = new CosmosClient(connectionString, new CosmosClientOptions
{
    ConsistencyLevel = ConsistencyLevel.Session  // Recommended
});

// Product catalog - Eventual or Consistent Prefix
// Slight delay in inventory updates is acceptable
var catalogClient = new CosmosClient(connectionString, new CosmosClientOptions
{
    ConsistencyLevel = ConsistencyLevel.Eventual
});

// Analytics/metrics - Eventual
// Historical data doesn't need immediate consistency
var analyticsClient = new CosmosClient(connectionString, new CosmosClientOptions
{
    ConsistencyLevel = ConsistencyLevel.Eventual
});
```

```csharp
// Session consistency with session token (most common pattern)
// SDK handles session tokens automatically within a client instance

// For scenarios where you need to share session across requests:
var response = await container.CreateItemAsync(order);
var sessionToken = response.Headers["x-ms-session-token"];

// Later request can use same session for read-your-writes
var readOptions = new ItemRequestOptions
{
    SessionToken = sessionToken
};
var order = await container.ReadItemAsync<Order>(id, pk, readOptions);
```

RU cost comparison (relative to Strong):
- Strong: 2x RU for reads (waits for quorum)
- Bounded Staleness: 2x RU for reads
- Session: 1x RU (default)
- Consistent Prefix: 1x RU
- Eventual: 1x RU

Reference: [Consistency levels](https://learn.microsoft.com/azure/cosmos-db/consistency-levels)

### 7.3 Configure Automatic Failover

**Impact: HIGH** (ensures availability during outages)

## Configure Automatic Failover

Enable automatic failover for high availability. Without it, regional outages require manual intervention.

**Incorrect (no failover configuration):**

```csharp
// Multi-region account without automatic failover
// If primary region goes down:
// - Manual intervention required
// - Downtime until you notice and trigger failover
// - MTTR (Mean Time To Recovery) = hours potentially

// ARM template without failover
{
    "properties": {
        "enableAutomaticFailover": false,  // DEFAULT - dangerous!
        "locations": [
            { "locationName": "West US 2", "failoverPriority": 0 },
            { "locationName": "East US 2", "failoverPriority": 1 }
        ]
    }
}
```

**Correct (automatic failover enabled):**

```csharp
// ARM template with automatic failover
{
    "type": "Microsoft.DocumentDB/databaseAccounts",
    "apiVersion": "2021-10-15",
    "name": "my-cosmos-account",
    "properties": {
        "enableAutomaticFailover": true,  // Enable automatic failover!
        
        // Define failover priority order
        "locations": [
            { 
                "locationName": "West US 2", 
                "failoverPriority": 0,  // Primary
                "isZoneRedundant": true  // Zone redundancy for HA
            },
            { 
                "locationName": "East US 2", 
                "failoverPriority": 1   // First failover target
            },
            { 
                "locationName": "West Europe", 
                "failoverPriority": 2   // Second failover target
            }
        ]
    }
}
```

```csharp
// Configure SDK to handle failovers gracefully
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationName = "MyApp",
    
    // SDK will automatically discover new endpoints after failover
    EnableTcpConnectionEndpointRediscovery = true,
    
    // Preferred regions in priority order
    ApplicationPreferredRegions = new List<string>
    {
        Regions.WestUS2,     // Primary
        Regions.EastUS2,     // Failover 1
        Regions.WestEurope   // Failover 2
    },
    
    // Connection will retry and discover new primary
    MaxRetryAttemptsOnRateLimitedRequests = 9,
    MaxRetryWaitTimeOnRateLimitedRequests = TimeSpan.FromSeconds(30)
});

// SDK handles failover transparently - your code doesn't change
await container.CreateItemAsync(order, new PartitionKey(order.CustomerId));
// If West US 2 is down, SDK automatically routes to East US 2
```

```csharp
// Monitor failover status
var accountProperties = await client.ReadAccountAsync();

Console.WriteLine($"Write regions: {string.Join(", ", 
    accountProperties.WritableRegions.Select(r => r.Name))}");
Console.WriteLine($"Read regions: {string.Join(", ", 
    accountProperties.ReadableRegions.Select(r => r.Name))}");

// Set up Azure Monitor alerts for:
// - Region failover events
// - Replication lag metrics
// - Availability metrics
```

```csharp
// Test failover (non-production)
// Azure CLI command to trigger manual failover
// az cosmosdb failover-priority-change \
//   --name mycosmosdb \
//   --resource-group myrg \
//   --failover-policies "East US 2"=0 "West US 2"=1

// Monitor your application behavior during failover test
// Expect: brief increase in latency, no data loss
```

Automatic failover behavior:
- Triggered after region unresponsive for ~1 minute
- Promotes next region in priority order
- SDK automatically reconnects to new primary
- No data loss with synchronous replication

Reference: [Automatic failover](https://learn.microsoft.com/azure/cosmos-db/high-availability)

### 7.4 Configure Multi-Region Writes

**Impact: HIGH** (enables local writes, high availability)

## Configure Multi-Region Writes

Enable multi-region writes for globally distributed applications. Allows writes to any region with automatic conflict resolution.

**Incorrect (single write region):**

```csharp
// Default: Single write region
// All writes must travel to one region
// Users in Asia writing to US region: 200-300ms latency

// No multi-region write configuration
var client = new CosmosClient(connectionString);

// Write from Asia still goes to US (write region)
await container.CreateItemAsync(order);  // 200ms+ latency for Asian users
```

**Correct (multi-region writes enabled):**

```csharp
// Step 1: Enable multi-region writes on account (Azure Portal or ARM)
{
    "type": "Microsoft.DocumentDB/databaseAccounts",
    "properties": {
        "enableMultipleWriteLocations": true,  // Enable multi-region writes
        "locations": [
            { "locationName": "West US 2", "failoverPriority": 0 },
            { "locationName": "East Asia", "failoverPriority": 1 },
            { "locationName": "West Europe", "failoverPriority": 2 }
        ]
    }
}

// Step 2: Configure SDK to write locally
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    // SDK automatically routes to nearest region
    ApplicationPreferredRegions = new List<string>
    {
        Regions.EastAsia,    // First choice (if deployed in Asia)
        Regions.WestUS2,
        Regions.WestEurope
    }
});

// Write goes to nearest region (East Asia for Asian users)
await container.CreateItemAsync(order);  // <10ms latency locally!
```

```csharp
// Step 3: Handle conflicts (Last Writer Wins is default)
// For custom conflict resolution, configure container

// Last Writer Wins (LWW) - Default
// Uses _ts (timestamp) to determine winner
var containerWithLWW = new ContainerProperties
{
    Id = "orders",
    PartitionKeyPath = "/customerId",
    ConflictResolutionPolicy = new ConflictResolutionPolicy
    {
        Mode = ConflictResolutionMode.LastWriterWins,
        ResolutionPath = "/_ts"  // Higher timestamp wins
    }
};

// Custom resolution path (e.g., version number)
var containerWithCustomLWW = new ContainerProperties
{
    Id = "products",
    PartitionKeyPath = "/categoryId",
    ConflictResolutionPolicy = new ConflictResolutionPolicy
    {
        Mode = ConflictResolutionMode.LastWriterWins,
        ResolutionPath = "/version"  // Higher version wins
    }
};
```

```csharp
// Verify multi-region write is working
var accountProperties = await client.ReadAccountAsync();
Console.WriteLine($"Multi-region writes: {accountProperties.EnableMultipleWriteLocations}");
Console.WriteLine($"Write regions: {string.Join(", ", 
    accountProperties.WritableRegions.Select(r => r.Name))}");
```

Benefits:
- Local write latency (< 10ms vs 200ms+)
- Higher write availability (any region can accept writes)
- Better disaster recovery

Considerations:
- Higher cost (replication in both directions)
- Requires conflict resolution strategy
- Some operations have restrictions (stored procedures)

Reference: [Multi-region writes](https://learn.microsoft.com/azure/cosmos-db/multi-region-writes)

### 7.5 Add Read Regions Near Users

**Impact: MEDIUM** (reduces read latency globally)

## Add Read Regions Near Users

Add read regions in geographic locations close to your users. Reads can be served from any region, reducing latency for global users.

**Incorrect (single region for global users):**

```csharp
// Only one region configured
// Users from all locations read from single region
// Asia users → 200ms+ latency to US region
// Europe users → 100ms+ latency to US region

{
    "properties": {
        "locations": [
            { "locationName": "West US 2", "failoverPriority": 0 }
        ]
    }
}
```

**Correct (read regions near user populations):**

```csharp
// Add read replicas near major user bases
{
    "type": "Microsoft.DocumentDB/databaseAccounts",
    "properties": {
        "locations": [
            // Primary write region
            { 
                "locationName": "West US 2", 
                "failoverPriority": 0 
            },
            // Read replica for European users
            { 
                "locationName": "West Europe", 
                "failoverPriority": 1 
            },
            // Read replica for Asian users
            { 
                "locationName": "Southeast Asia", 
                "failoverPriority": 2 
            },
            // Read replica for Australian users
            { 
                "locationName": "Australia East", 
                "failoverPriority": 3 
            }
        ]
    }
}
```

```csharp
// Configure SDK for region-local reads
// Deployed in Europe - prioritize European region
var europeClient = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationPreferredRegions = new List<string>
    {
        Regions.WestEurope,      // Nearest region first
        Regions.NorthEurope,     // Backup within Europe
        Regions.WestUS2          // Primary (for writes)
    }
});

// Deployed in Asia - prioritize Asian region
var asiaClient = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationPreferredRegions = new List<string>
    {
        Regions.SoutheastAsia,   // Nearest region first
        Regions.EastAsia,        // Backup within Asia
        Regions.WestUS2          // Primary (for writes)
    }
});
```

```csharp
// Dynamic region selection based on deployment
public static CosmosClient CreateRegionalClient(string connectionString)
{
    var deploymentRegion = Environment.GetEnvironmentVariable("AZURE_REGION") 
        ?? "westus2";
    
    var preferredRegions = deploymentRegion.ToLower() switch
    {
        "westeurope" or "northeurope" => new List<string>
        {
            Regions.WestEurope, Regions.NorthEurope, Regions.WestUS2
        },
        "southeastasia" or "eastasia" => new List<string>
        {
            Regions.SoutheastAsia, Regions.EastAsia, Regions.WestUS2
        },
        "australiaeast" => new List<string>
        {
            Regions.AustraliaEast, Regions.SoutheastAsia, Regions.WestUS2
        },
        _ => new List<string>
        {
            Regions.WestUS2, Regions.EastUS2
        }
    };
    
    return new CosmosClient(connectionString, new CosmosClientOptions
    {
        ApplicationPreferredRegions = preferredRegions
    });
}
```

```csharp
// Verify reads are going to correct region
var response = await container.ReadItemAsync<Order>(orderId, pk);
// Check diagnostics for contacted region
var diagnostics = response.Diagnostics.ToString();
_logger.LogDebug("Request served from: {Diagnostics}", diagnostics);
// Look for "Contacted Region" in diagnostics
```

Cost considerations:
- Each read replica adds cost (~same as primary)
- Calculate: User latency improvement × request volume vs. replica cost
- Start with regions serving most users, add more based on metrics

Reference: [Global distribution](https://learn.microsoft.com/azure/cosmos-db/distribute-data-globally)

### 7.6 Configure Zone Redundancy for High Availability

**Impact: HIGH** (eliminates availability zone failures, increases SLA to 99.995%)

## Configure Zone Redundancy for High Availability

Enable zone redundancy to protect against availability zone failures. Zone-redundant accounts distribute replicas across multiple availability zones within a region.

**Incorrect (no zone redundancy):**

```json
// Single-region account without zone redundancy
// If an availability zone fails:
// - Potential data loss
// - Availability loss until recovery
// - SLA: 99.99%
{
    "type": "Microsoft.DocumentDB/databaseAccounts",
    "properties": {
        "locations": [
            {
                "locationName": "East US",
                "failoverPriority": 0,
                "isZoneRedundant": false  // DEFAULT - no zone protection!
            }
        ]
    }
}
```

**Correct (zone redundancy enabled):**

```json
// ARM template with zone redundancy
{
    "type": "Microsoft.DocumentDB/databaseAccounts",
    "apiVersion": "2023-04-15",
    "name": "my-cosmos-account",
    "properties": {
        "locations": [
            {
                "locationName": "East US",
                "failoverPriority": 0,
                "isZoneRedundant": true  // Enable zone redundancy!
            },
            {
                "locationName": "West US",
                "failoverPriority": 1,
                "isZoneRedundant": true  // Enable in secondary too
            }
        ]
    }
}
```

```bicep
// Bicep template with zone redundancy
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: 'my-cosmos-account'
  location: 'East US'
  properties: {
    locations: [
      {
        locationName: 'East US'
        failoverPriority: 0
        isZoneRedundant: true  // Replicas spread across 3 AZs
      }
      {
        locationName: 'West US'
        failoverPriority: 1
        isZoneRedundant: true
      }
    ]
    enableAutomaticFailover: true
  }
}
```

**SLA Improvements with Zone Redundancy:**

| Configuration | Write SLA | Read SLA | Zone Failure | Regional Failure |
|--------------|-----------|----------|--------------|------------------|
| Single region, no ZR | 99.99% | 99.99% | Data/availability loss | Data/availability loss |
| Single region + ZR | 99.995% | 99.995% | No loss | Data/availability loss |
| Multi-region, no ZR | 99.99% | 99.999% | Data/availability loss | Dependent on consistency |
| Multi-region + ZR | 99.995% | 99.999% | No loss | Dependent on consistency |
| Multi-region writes + ZR | 99.999% | 99.999% | No loss | No loss (with conflicts) |

**Cost Considerations:**

- Zone redundancy adds **25% premium** to provisioned throughput
- Premium is **waived** for:
  - Multi-region write accounts
  - Autoscale collections
- Adding a region adds ~100% to existing bill

**When to Enable Zone Redundancy:**

1. **Always for single-region accounts** - Primary protection against AZ failures
2. **Write regions in multi-region accounts** - Protects write availability
3. **Production workloads** - Required for high SLA guarantees

**Regions Supporting Zone Redundancy:**

Check current availability: [Azure regions with availability zones](https://learn.microsoft.com/en-us/azure/reliability/availability-zones-service-support)

Reference: [High availability in Azure Cosmos DB](https://learn.microsoft.com/en-us/azure/reliability/reliability-cosmos-db-nosql#availability-zone-support)

---

## 8. Monitoring & Diagnostics

**Impact: LOW-MEDIUM**

### 8.1 Integrate Azure Monitor

**Impact: MEDIUM** (enables comprehensive observability)

## Integrate Azure Monitor

Enable Azure Monitor integration for comprehensive visibility into Cosmos DB performance, availability, and cost metrics.

**Incorrect (no monitoring integration):**

```csharp
// Flying blind - no visibility into:
// - RU consumption trends
// - Latency patterns
// - Throttling events
// - Availability issues
// - Cost attribution

// Application runs but you only know about problems from user complaints
```

**Correct (Azure Monitor integration):**

```csharp
// Step 1: Enable diagnostic settings (Azure Portal, CLI, or ARM)
{
    "type": "Microsoft.DocumentDB/databaseAccounts/providers/diagnosticSettings",
    "properties": {
        "logs": [
            {
                "category": "DataPlaneRequests",
                "enabled": true,
                "retentionPolicy": { "enabled": true, "days": 30 }
            },
            {
                "category": "QueryRuntimeStatistics",
                "enabled": true
            },
            {
                "category": "PartitionKeyStatistics",
                "enabled": true
            },
            {
                "category": "PartitionKeyRUConsumption",
                "enabled": true
            }
        ],
        "metrics": [
            {
                "category": "Requests",
                "enabled": true
            }
        ],
        "workspaceId": "/subscriptions/.../workspaces/my-workspace"
    }
}
```

```csharp
// Step 2: Key metrics to monitor in Azure Monitor

// a) Normalized RU Consumption (% of provisioned used)
// Alert if > 90% sustained - indicates need to scale

// b) Total Requests by Status Code
// Alert on 429s (throttling) and 5xx (errors)

// c) Server Side Latency
// Track P50, P99 for performance baselines

// d) Data Usage
// Monitor storage growth

// e) Availability
// Alert on availability drops below 99.99%
```

```csharp
// Step 3: Application Insights integration
public static class CosmosDbTelemetry
{
    public static void ConfigureWithAppInsights(
        CosmosClientOptions options, 
        TelemetryClient telemetry)
    {
        // Track all operations as dependencies
        options.CosmosClientTelemetryOptions = new CosmosClientTelemetryOptions
        {
            DisableDistributedTracing = false  // Enable distributed tracing
        };
        
        // Custom handler for detailed telemetry
        options.CustomHandlers.Add(new AppInsightsHandler(telemetry));
    }
}

public class AppInsightsHandler : RequestHandler
{
    private readonly TelemetryClient _telemetry;
    
    public override async Task<ResponseMessage> SendAsync(
        RequestMessage request, 
        CancellationToken cancellationToken)
    {
        using var operation = _telemetry.StartOperation<DependencyTelemetry>(
            "CosmosDB", 
            request.RequestUri.ToString());
        
        operation.Telemetry.Type = "Azure DocumentDB";
        operation.Telemetry.Target = request.RequestUri.Host;
        
        var response = await base.SendAsync(request, cancellationToken);
        
        operation.Telemetry.Success = response.IsSuccessStatusCode;
        operation.Telemetry.ResultCode = ((int)response.StatusCode).ToString();
        operation.Telemetry.Properties["RU"] = response.Headers.RequestCharge.ToString();
        
        return response;
    }
}
```

```kusto
// Useful Log Analytics queries

// RU consumption by operation
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| summarize TotalRU = sum(requestCharge_s), 
            AvgRU = avg(requestCharge_s),
            Count = count()
    by OperationName
| order by TotalRU desc

// Slow queries
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| where duration_s > 100  // > 100ms
| project TimeGenerated, OperationName, duration_s, 
          requestCharge_s, partitionKey_s, querytext_s

// Storage growth trend
AzureMetrics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| where MetricName == "DataUsage"
| summarize StorageGB = max(Total) / 1073741824 by bin(TimeGenerated, 1d)
| order by TimeGenerated
```

Essential alerts to configure:
1. Throttling (429s) > 0
2. Normalized RU > 90% for 5 min
3. Availability < 99.99%
4. P99 latency > threshold
5. Storage approaching limits

Reference: [Monitor Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/monitor)

### 8.2 Enable Diagnostic Logging

**Impact: LOW-MEDIUM** (enables troubleshooting)

## Enable Diagnostic Logging

Enable diagnostic logging to capture detailed operation data for troubleshooting. Essential for root cause analysis of production issues.

**Incorrect (no diagnostic logging):**

```csharp
// When issues occur, you have no data to investigate
// "Why is this query slow?"
// "Why did we get throttled yesterday at 3am?"
// "Which operations are using the most RU?"
// No answers without logging!
```

**Correct (comprehensive diagnostic logging):**

```csharp
// Azure diagnostic settings for detailed logs
// Enable via Azure Portal > Cosmos DB > Diagnostic settings

// Categories to enable:
// 1. DataPlaneRequests - All CRUD operations
// 2. QueryRuntimeStatistics - Query execution details
// 3. PartitionKeyStatistics - Partition key distribution
// 4. PartitionKeyRUConsumption - RU by partition
// 5. ControlPlaneRequests - Management operations

// ARM template for diagnostic settings
{
    "type": "Microsoft.Insights/diagnosticSettings",
    "name": "cosmos-diagnostics",
    "properties": {
        "logs": [
            { "category": "DataPlaneRequests", "enabled": true },
            { "category": "QueryRuntimeStatistics", "enabled": true },
            { "category": "PartitionKeyStatistics", "enabled": true },
            { "category": "PartitionKeyRUConsumption", "enabled": true },
            { "category": "ControlPlaneRequests", "enabled": true }
        ],
        "logAnalyticsDestinationType": "Dedicated",
        "workspaceId": "[resourceId('Microsoft.OperationalInsights/workspaces', 'my-workspace')]"
    }
}
```

```csharp
// Application-level diagnostic logging
public class DiagnosticLoggingRepository
{
    private readonly Container _container;
    private readonly ILogger _logger;
    
    public async Task<T> ExecuteWithDiagnostics<T>(
        string operationName,
        Func<Task<Response<T>>> operation)
    {
        var correlationId = Activity.Current?.Id ?? Guid.NewGuid().ToString();
        
        try
        {
            var response = await operation();
            
            // Always log basic info
            _logger.LogDebug(
                "[{CorrelationId}] {Operation}: {RU} RU, {LatencyMs}ms, Status: {Status}",
                correlationId,
                operationName,
                response.RequestCharge,
                response.Diagnostics.GetClientElapsedTime().TotalMilliseconds,
                "Success");
            
            // Log full diagnostics for slow operations
            if (response.Diagnostics.GetClientElapsedTime() > TimeSpan.FromMilliseconds(100))
            {
                _logger.LogWarning(
                    "[{CorrelationId}] Slow {Operation}: {Diagnostics}",
                    correlationId,
                    operationName,
                    response.Diagnostics.ToString());
            }
            
            return response.Resource;
        }
        catch (CosmosException ex)
        {
            _logger.LogError(ex,
                "[{CorrelationId}] {Operation} failed: Status={Status}, SubStatus={SubStatus}, " +
                "RU={RU}, RetryAfter={RetryAfter}, ActivityId={ActivityId}, Diagnostics={Diagnostics}",
                correlationId,
                operationName,
                ex.StatusCode,
                ex.SubStatusCode,
                ex.RequestCharge,
                ex.RetryAfter,
                ex.ActivityId,
                ex.Diagnostics?.ToString());
            
            throw;
        }
    }
}
```

```csharp
// Query-specific diagnostics
public async Task<List<T>> ExecuteQueryWithDiagnostics<T>(
    string queryName,
    QueryDefinition query,
    QueryRequestOptions options = null)
{
    options ??= new QueryRequestOptions();
    options.PopulateIndexMetrics = true;  // Get index usage info
    
    var results = new List<T>();
    var totalRU = 0.0;
    var pageCount = 0;
    
    var iterator = _container.GetItemQueryIterator<T>(query, requestOptions: options);
    
    while (iterator.HasMoreResults)
    {
        var response = await iterator.ReadNextAsync();
        results.AddRange(response);
        totalRU += response.RequestCharge;
        pageCount++;
        
        // Log index metrics (helps identify missing indexes)
        if (!string.IsNullOrEmpty(response.IndexMetrics))
        {
            _logger.LogDebug(
                "Query '{QueryName}' page {Page} index metrics: {IndexMetrics}",
                queryName, pageCount, response.IndexMetrics);
        }
    }
    
    _logger.LogInformation(
        "Query '{QueryName}': {Count} results, {TotalRU} RU, {Pages} pages",
        queryName, results.Count, totalRU, pageCount);
    
    return results;
}
```

Key diagnostic data to capture:
- Operation name and duration
- RU consumption
- Partition key (for hot partition analysis)
- Full diagnostics for errors/slow operations
- Index metrics for queries
- ActivityId (for Azure support)

Reference: [Diagnostic logging](https://learn.microsoft.com/azure/cosmos-db/monitor-resource-logs)

### 8.3 Monitor P99 Latency

**Impact: MEDIUM** (identifies performance issues)

## Monitor P99 Latency

Track P99 (99th percentile) latency to identify performance outliers. Average latency hides tail latency issues that affect user experience.

**Incorrect (only tracking average latency):**

```csharp
// Average latency looks good: 5ms
// But P99 could be 500ms - 1% of users have terrible experience!

public async Task<Order> GetOrder(string orderId, string customerId)
{
    var sw = Stopwatch.StartNew();
    var result = await _container.ReadItemAsync<Order>(orderId, pk);
    sw.Stop();
    
    // Only tracking average is misleading
    _metrics.TrackAverage("CosmosDB.Latency", sw.ElapsedMilliseconds);
    // Average: 5ms (hides that some requests take 500ms)
    
    return result.Resource;
}
```

**Correct (tracking latency distribution):**

```csharp
public async Task<Order> GetOrder(string orderId, string customerId)
{
    var sw = Stopwatch.StartNew();
    var response = await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
    sw.Stop();
    
    var clientLatency = sw.ElapsedMilliseconds;
    var serverLatency = response.Diagnostics.GetClientElapsedTime().TotalMilliseconds;
    
    // Track as histogram (enables percentile calculations)
    _metrics.TrackHistogram("CosmosDB.Latency.Client", clientLatency);
    _metrics.TrackHistogram("CosmosDB.Latency.Server", serverLatency);
    
    // Alert on slow requests
    if (clientLatency > 100)  // 100ms threshold
    {
        _logger.LogWarning(
            "Slow Cosmos DB read: {LatencyMs}ms, Diagnostics: {Diagnostics}",
            clientLatency,
            response.Diagnostics.ToString());
    }
    
    return response.Resource;
}
```

```csharp
// Track percentiles with Application Insights
public class LatencyTracker
{
    private readonly TelemetryClient _telemetry;
    private readonly ConcurrentBag<double> _recentLatencies = new();
    private readonly Timer _reportTimer;
    
    public LatencyTracker(TelemetryClient telemetry)
    {
        _telemetry = telemetry;
        _reportTimer = new Timer(ReportPercentiles, null, 
            TimeSpan.FromMinutes(1), TimeSpan.FromMinutes(1));
    }
    
    public void RecordLatency(double latencyMs)
    {
        _recentLatencies.Add(latencyMs);
    }
    
    private void ReportPercentiles(object state)
    {
        var latencies = _recentLatencies.ToArray();
        _recentLatencies.Clear();
        
        if (latencies.Length == 0) return;
        
        Array.Sort(latencies);
        
        var p50 = GetPercentile(latencies, 50);
        var p90 = GetPercentile(latencies, 90);
        var p99 = GetPercentile(latencies, 99);
        
        _telemetry.TrackMetric("CosmosDB.Latency.P50", p50);
        _telemetry.TrackMetric("CosmosDB.Latency.P90", p90);
        _telemetry.TrackMetric("CosmosDB.Latency.P99", p99);
        
        // Alert if P99 exceeds threshold
        if (p99 > 100)
        {
            _telemetry.TrackEvent("HighP99Latency", 
                new Dictionary<string, string> { { "P99", p99.ToString() } });
        }
    }
    
    private static double GetPercentile(double[] sorted, int percentile)
    {
        var index = (int)Math.Ceiling(percentile / 100.0 * sorted.Length) - 1;
        return sorted[Math.Max(0, index)];
    }
}
```

```csharp
// Azure Monitor / Log Analytics query for P99
// Query to get latency percentiles
/*
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| where TimeGenerated > ago(1h)
| summarize 
    P50 = percentile(duration_s, 50),
    P90 = percentile(duration_s, 90),
    P99 = percentile(duration_s, 99),
    Max = max(duration_s)
    by bin(TimeGenerated, 5m), OperationName
| order by TimeGenerated desc
*/
```

What P99 latency reveals:
- Network issues (high client vs server latency gap)
- Hot partitions (certain keys slow)
- Query efficiency problems
- Cross-partition query overhead
- Regional routing issues

Target latencies:
- Point reads: P99 < 10ms (same region)
- Queries: P99 < 50ms (depends on complexity)
- Cross-region: Add ~RTT to target

Reference: [Monitor latency](https://learn.microsoft.com/azure/cosmos-db/monitor-server-side-latency)

### 8.4 Track RU Consumption

**Impact: MEDIUM** (enables cost optimization)

## Track RU Consumption

Monitor Request Unit (RU) consumption to optimize costs and identify inefficient operations. Every operation has an RU cost.

**Incorrect (ignoring RU consumption):**

```csharp
// Operations without tracking cost
public async Task<Order> GetOrder(string orderId, string customerId)
{
    // No visibility into cost
    return await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
    // Is this costing 1 RU or 100 RU? Unknown!
}
```

**Correct (tracking RU at operation level):**

```csharp
public async Task<Order> GetOrder(string orderId, string customerId)
{
    var response = await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
    
    // Log RU consumption
    _logger.LogDebug(
        "Read order {OrderId}: {RU} RU, {Latency}ms",
        orderId,
        response.RequestCharge,
        response.Diagnostics.GetClientElapsedTime().TotalMilliseconds);
    
    // Track in metrics/telemetry
    _telemetry.TrackMetric("CosmosDB.ReadItem.RU", response.RequestCharge, 
        new Dictionary<string, string> 
        { 
            { "Operation", "ReadItem" },
            { "Container", "orders" }
        });
    
    return response.Resource;
}
```

```csharp
// Track RU for queries (can be high!)
public async Task<List<Order>> GetCustomerOrders(string customerId)
{
    var query = new QueryDefinition("SELECT * FROM c WHERE c.status = @status")
        .WithParameter("@status", "active");
    
    var totalRU = 0.0;
    var results = new List<Order>();
    
    var iterator = _container.GetItemQueryIterator<Order>(
        query,
        requestOptions: new QueryRequestOptions 
        { 
            PartitionKey = new PartitionKey(customerId),
            PopulateIndexMetrics = true  // Also get index metrics
        });
    
    while (iterator.HasMoreResults)
    {
        var response = await iterator.ReadNextAsync();
        results.AddRange(response);
        totalRU += response.RequestCharge;
        
        // Log per-page RU
        _logger.LogDebug(
            "Query page: {Count} items, {RU} RU, Index: {IndexMetrics}",
            response.Count,
            response.RequestCharge,
            response.IndexMetrics);
    }
    
    // Log total query cost
    _logger.LogInformation(
        "GetCustomerOrders: {Total} items, {TotalRU} total RU",
        results.Count,
        totalRU);
    
    // Alert on expensive queries
    if (totalRU > 100)
    {
        _logger.LogWarning(
            "Expensive query detected: {TotalRU} RU for {Count} items",
            totalRU, results.Count);
    }
    
    return results;
}
```

```csharp
// Middleware to track all operations
public class CosmosDbMetricsHandler : RequestHandler
{
    private readonly IMetricTracker _metrics;
    
    public override async Task<ResponseMessage> SendAsync(
        RequestMessage request, 
        CancellationToken cancellationToken)
    {
        var sw = Stopwatch.StartNew();
        var response = await base.SendAsync(request, cancellationToken);
        sw.Stop();
        
        _metrics.TrackDependency(
            "CosmosDB",
            request.RequestUri.ToString(),
            sw.Elapsed,
            response.IsSuccessStatusCode,
            new Dictionary<string, string>
            {
                { "RU", response.Headers.RequestCharge.ToString() },
                { "StatusCode", response.StatusCode.ToString() }
            });
        
        return response;
    }
}

// Register handler
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    CustomHandlers = { new CosmosDbMetricsHandler(_metrics) }
});
```

Azure Monitor queries for RU analysis:
```kusto
// Top expensive operations
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| summarize TotalRU = sum(requestCharge_s) by OperationName
| order by TotalRU desc

// RU per partition key (detect hot partitions)
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| summarize TotalRU = sum(requestCharge_s) by partitionKey_s
| order by TotalRU desc
```

Reference: [Monitor RU/s](https://learn.microsoft.com/azure/cosmos-db/monitor-request-unit-usage)

### 8.5 Alert on Throttling (429s)

**Impact: HIGH** (prevents silent failures)

## Alert on Throttling (429s)

Set up alerts for HTTP 429 (Request Rate Too Large) errors. Throttling indicates your application is exceeding provisioned throughput.

**Incorrect (ignoring throttling):**

```csharp
// SDK retries silently, application seems "slow" but no alerts
public async Task<Order> GetOrder(string orderId, string customerId)
{
    // SDK retries 429s automatically (up to 9 times by default)
    // But you have no visibility into this happening!
    return await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
    // Users experience slow responses, you see nothing in logs
}
```

**Correct (tracking and alerting on throttling):**

```csharp
// Option 1: Track via exception handling
public async Task<Order> GetOrder(string orderId, string customerId)
{
    try
    {
        var response = await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
        return response.Resource;
    }
    catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.TooManyRequests)
    {
        // This fires only after ALL retries exhausted
        _logger.LogError(
            "Throttled after max retries! RetryAfter: {RetryAfter}s, Diagnostics: {Diagnostics}",
            ex.RetryAfter?.TotalSeconds,
            ex.Diagnostics?.ToString());
        
        _metrics.IncrementCounter("CosmosDB.ThrottledRequests");
        throw;
    }
}

// Option 2: Custom handler to track all 429s (even those retried)
public class ThrottlingTracker : RequestHandler
{
    private readonly ILogger _logger;
    private readonly IMetricTracker _metrics;
    
    public override async Task<ResponseMessage> SendAsync(
        RequestMessage request, 
        CancellationToken cancellationToken)
    {
        var response = await base.SendAsync(request, cancellationToken);
        
        if (response.StatusCode == HttpStatusCode.TooManyRequests)
        {
            _logger.LogWarning(
                "429 Throttled: {Uri}, RetryAfter: {RetryAfter}",
                request.RequestUri,
                response.Headers.RetryAfter);
            
            _metrics.IncrementCounter("CosmosDB.429.Total");
        }
        
        return response;
    }
}

// Register handler
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    CustomHandlers = { new ThrottlingTracker(_logger, _metrics) }
});
```

```csharp
// Azure Monitor alert rule for throttling
// Create alert in Azure Portal or via ARM:
{
    "type": "Microsoft.Insights/metricAlerts",
    "properties": {
        "criteria": {
            "odata.type": "Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria",
            "allOf": [
                {
                    "name": "TotalRequests429",
                    "metricName": "TotalRequests",
                    "dimensions": [
                        {
                            "name": "StatusCode",
                            "operator": "Include",
                            "values": ["429"]
                        }
                    ],
                    "operator": "GreaterThan",
                    "threshold": 0,
                    "timeAggregation": "Total"
                }
            ]
        },
        "actions": [
            {
                "actionGroupId": "/subscriptions/.../actionGroups/ops-team"
            }
        ],
        "severity": 2,
        "windowSize": "PT5M",
        "evaluationFrequency": "PT1M"
    }
}
```

```kusto
// Log Analytics query for throttling analysis
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| where statusCode_s == "429"
| summarize ThrottledCount = count() by 
    bin(TimeGenerated, 5m),
    partitionKeyRangeId_s,
    OperationName
| order by TimeGenerated desc

// Identify which partition keys are throttling
AzureDiagnostics
| where statusCode_s == "429"
| summarize Count = count() by partitionKey_s
| order by Count desc
| take 10
```

Response to throttling:
1. **Immediate**: SDK retries automatically
2. **Short-term**: Scale up throughput (manual or autoscale)
3. **Long-term**: 
   - Optimize queries to use less RU
   - Review partition key for hot partitions
   - Consider autoscale for variable workloads

Reference: [Monitor throttling](https://learn.microsoft.com/azure/cosmos-db/monitor-normalized-request-units)

---

## 9. Design Patterns

**Impact: HIGH**

### 9.1 Use Change Feed for cross-partition query optimization with materialized views

**Impact: HIGH** (eliminates cross-partition query overhead for admin/analytics scenarios)

## Use Change Feed for Materialized Views

When your application requires frequent cross-partition queries (e.g., admin dashboards, analytics), consider using Change Feed to maintain materialized views in a separate container optimized for those query patterns.

**Problem: Cross-partition queries are expensive**

```csharp
// This query fans out to ALL partitions - expensive at scale!
// Container partitioned by /customerId
var query = container.GetItemQueryIterator<Order>(
    "SELECT * FROM c WHERE c.status = 'Pending' ORDER BY c.createdAt DESC"
);
// With 100,000 customers = 100,000+ physical partitions queried
```

Cross-partition queries:
- Consume RUs from every partition (high cost)
- Have higher latency (parallel fan-out)
- Don't scale well as data grows

**Solution: Materialized view with Change Feed**

Create a second container optimized for your admin queries:

```
Container 1: "orders" (partitioned by /customerId)
├── Efficient for: customer order history, point reads
└── Pattern: Single-partition queries

Container 2: "orders-by-status" (partitioned by /status)  
├── Efficient for: admin status queries
├── Pattern: Single-partition queries within status
└── Populated by: Change Feed processor
```

**Implementation - .NET:**

```csharp
// Change Feed processor to sync materialized view
Container leaseContainer = database.GetContainer("leases");
Container ordersContainer = database.GetContainer("orders");
Container ordersByStatusContainer = database.GetContainer("orders-by-status");

ChangeFeedProcessor processor = ordersContainer
    .GetChangeFeedProcessorBuilder<Order>("statusViewProcessor", HandleChangesAsync)
    .WithInstanceName("instance-1")
    .WithLeaseContainer(leaseContainer)
    .WithStartFromBeginning()
    .Build();

async Task HandleChangesAsync(
    IReadOnlyCollection<Order> changes, 
    CancellationToken cancellationToken)
{
    foreach (Order order in changes)
    {
        // Create/update the materialized view document
        var statusView = new OrderStatusView
        {
            Id = order.Id,
            CustomerId = order.CustomerId,
            Status = order.Status,  // This becomes the partition key
            CreatedAt = order.CreatedAt,
            Total = order.Total
        };
        
        await ordersByStatusContainer.UpsertItemAsync(
            statusView,
            new PartitionKey(order.Status.ToString()),
            cancellationToken: cancellationToken
        );
    }
}

await processor.StartAsync();
```

**Implementation - Java:**

```java
// Change Feed processor with Spring Boot
@Component
public class OrderStatusViewProcessor {
    
    @Autowired
    private CosmosAsyncContainer ordersByStatusContainer;
    
    public void startProcessor(CosmosAsyncContainer ordersContainer, 
                               CosmosAsyncContainer leaseContainer) {
        
        ChangeFeedProcessor processor = new ChangeFeedProcessorBuilder<Order>()
            .hostName("processor-1")
            .feedContainer(ordersContainer)
            .leaseContainer(leaseContainer)
            .handleChanges(this::handleChanges)
            .buildChangeFeedProcessor();
            
        processor.start().block();
    }
    
    private void handleChanges(List<Order> changes, ChangeFeedProcessorContext context) {
        for (Order order : changes) {
            OrderStatusView view = new OrderStatusView(
                order.getId(),
                order.getCustomerId(), 
                order.getStatus(),
                order.getCreatedAt(),
                order.getTotal()
            );
            
            ordersByStatusContainer.upsertItem(
                view,
                new PartitionKey(order.getStatus().getValue()),
                new CosmosItemRequestOptions()
            ).block();
        }
    }
}
```

**Implementation - Python:**

```python
from azure.cosmos import CosmosClient
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
import asyncio

async def process_change_feed():
    """Process changes and update materialized view"""
    
    async with AsyncCosmosClient(endpoint, credential=key) as client:
        orders_container = client.get_database_client(db).get_container_client("orders")
        status_container = client.get_database_client(db).get_container_client("orders-by-status")
        
        # Read change feed
        async for changes in orders_container.query_items_change_feed():
            for order in changes:
                # Upsert to materialized view
                status_view = {
                    "id": order["id"],
                    "customerId": order["customerId"],
                    "status": order["status"],  # Partition key in target container
                    "createdAt": order["createdAt"],
                    "total": order["total"]
                }
                
                await status_container.upsert_item(
                    body=status_view,
                    partition_key=order["status"]
                )
```

**Query the materialized view (single-partition!):**

```csharp
// Now this is a single-partition query - fast and cheap!
var query = ordersByStatusContainer.GetItemQueryIterator<OrderStatusView>(
    new QueryDefinition("SELECT * FROM c WHERE c.status = @status ORDER BY c.createdAt DESC")
        .WithParameter("@status", "Pending"),
    requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey("Pending") }
);
```

**When to use this pattern:**

| Use Materialized Views When | Stick with Cross-Partition When |
|-----------------------------|---------------------------------|
| High-frequency admin queries | Rare/occasional admin queries |
| Large dataset (100K+ docs) | Small dataset (<10K docs) |
| Query latency is critical | Latency is acceptable |
| Consistent query patterns | Ad-hoc query patterns |

**Trade-offs:**

| Benefit | Cost |
|---------|------|
| Fast single-partition queries | Additional storage (duplicated data) |
| Predictable latency | Change Feed processor complexity |
| Better scalability | Eventual consistency (slight delay) |
| Lower RU cost per query | RU cost for writes to both containers |

**Key Points:**
- Change Feed provides reliable, ordered event stream of all document changes
- Materialized views trade storage cost for query efficiency
- Updates are eventually consistent (typically <1 second delay)
- Use lease container to track processor progress (enables resume after failures)
- Consider Azure Functions with Cosmos DB trigger for serverless implementation

Reference: [Change feed in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/change-feed)

### 9.2 Use count-based or cached rank approaches instead of full partition scans for ranking

**Impact: HIGH** (reduces rank lookups from O(N) partition scans to O(1) or O(log N) operations)

## Efficient Ranking in Cosmos DB

When implementing leaderboards or rankings, avoid scanning an entire partition to determine a single player's rank. Full partition scans for rank lookups are an anti-pattern that becomes unsustainable at scale.

**Problem: Full partition scan to find rank**

```csharp
// Anti-pattern: Reads ALL entries in a partition to find one player's rank
// At 500K players, this consumes thousands of RU and takes seconds
public async Task<int> GetPlayerRankAsync(string leaderboardKey, string playerId)
{
    var query = new QueryDefinition(
        "SELECT c.playerId, c.bestScore FROM c WHERE c.type = @type ORDER BY c.bestScore DESC"
    ).WithParameter("@type", "leaderboardEntry");

    var allEntries = new List<LeaderboardEntry>();
    using var iterator = _container.GetItemQueryIterator<LeaderboardEntry>(
        query, requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(leaderboardKey) });

    while (iterator.HasMoreResults)
    {
        var response = await iterator.ReadNextAsync();
        allEntries.AddRange(response); // Loading ALL entries into memory!
    }

    // O(N) scan to find player
    return allEntries.FindIndex(e => e.PlayerId == playerId) + 1;
}
```

This approach:
- Reads every document in the partition (potentially 500K+ documents)
- Consumes thousands of RU per request
- Has multi-second latency
- Loads all entries into memory

**Solution 1: COUNT-based rank query (simplest)**

```csharp
// Count players with higher scores to determine rank
// Single query, ~3-5 RU regardless of partition size
public async Task<int> GetPlayerRankAsync(string leaderboardKey, string playerId, int playerScore)
{
    var countQuery = new QueryDefinition(
        "SELECT VALUE COUNT(1) FROM c WHERE c.type = @type AND c.bestScore > @score"
    )
    .WithParameter("@type", "leaderboardEntry")
    .WithParameter("@score", playerScore);

    using var iterator = _container.GetItemQueryIterator<int>(
        countQuery, requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(leaderboardKey) });

    var response = await iterator.ReadNextAsync();
    return response.Resource.FirstOrDefault() + 1; // Rank = count of players above + 1
}
```

**Solution 2: Cached rank offsets with Change Feed**

For extremely high-volume leaderboard reads, pre-compute and cache rank data:

```csharp
// Maintain a rank cache that is periodically updated
// Leaderboard entry includes pre-computed rank
public class RankedLeaderboardEntry
{
    [JsonPropertyName("id")]
    public string Id { get; set; }  // playerId

    [JsonPropertyName("leaderboardKey")]
    public string LeaderboardKey { get; set; }

    [JsonPropertyName("rank")]
    public int Rank { get; set; }  // Pre-computed rank

    [JsonPropertyName("bestScore")]
    public int BestScore { get; set; }

    [JsonPropertyName("displayName")]
    public string DisplayName { get; set; }
}

// Change Feed processor periodically recomputes ranks
// Run on a schedule (e.g., every 30 seconds) for near-real-time rankings
public async Task RecomputeRanksAsync(string leaderboardKey)
{
    var query = new QueryDefinition(
        "SELECT c.id, c.playerId, c.bestScore, c.displayName FROM c " +
        "WHERE c.type = @type ORDER BY c.bestScore DESC"
    ).WithParameter("@type", "leaderboardEntry");

    int rank = 0;
    using var iterator = _container.GetItemQueryIterator<LeaderboardEntry>(
        query, requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(leaderboardKey) });

    while (iterator.HasMoreResults)
    {
        var batch = await iterator.ReadNextAsync();
        foreach (var entry in batch)
        {
            rank++;
            entry.Rank = rank;
            await _container.UpsertItemAsync(entry,
                new PartitionKey(leaderboardKey));
        }
    }
}

// Then rank lookup is a simple point read: O(1), 1 RU
public async Task<int> GetPlayerRankAsync(string leaderboardKey, string playerId)
{
    var response = await _container.ReadItemAsync<RankedLeaderboardEntry>(
        playerId, new PartitionKey(leaderboardKey));
    return response.Resource.Rank;
}
```

**Solution 3: Approximate ranking with score buckets**

For leaderboards where approximate rank is acceptable:

```csharp
// Maintain score distribution buckets for O(1) approximate ranking
// Partition key: /leaderboardKey, id: "bucket-{range}"
public class ScoreBucket
{
    [JsonPropertyName("id")]
    public string Id { get; set; }  // e.g., "bucket-9000-10000"

    [JsonPropertyName("leaderboardKey")]
    public string LeaderboardKey { get; set; }

    [JsonPropertyName("minScore")]
    public int MinScore { get; set; }

    [JsonPropertyName("maxScore")]
    public int MaxScore { get; set; }

    [JsonPropertyName("playerCount")]
    public int PlayerCount { get; set; }
}

// Approximate rank = sum of players in all higher buckets + position within bucket
```

**Key Points:**
- **Never scan an entire partition** to find a single item's rank — this is O(N) and doesn't scale
- **COUNT queries** are the simplest solution and work well for moderate scale (< 1M entries)
- **Pre-computed ranks** via Change Feed are best for high-volume reads with eventual consistency tolerance
- **Score buckets** provide O(1) approximate ranking for very large datasets
- Consider the trade-off: exact real-time rank (more RU) vs. slightly stale rank (less RU)
- For "nearby players ±10", combine a COUNT query with a TOP 21 query centered on the player's score

Reference: [Cosmos DB query optimization](https://learn.microsoft.com/azure/cosmos-db/nosql/query/getting-started)

---

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
