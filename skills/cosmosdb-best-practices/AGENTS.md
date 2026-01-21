# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Kit  
January 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code. Humans  
> may also find it useful, but guidance here is optimized for automation  
> and consistency by AI-assisted workflows.

---

## Abstract

Performance optimization and best practices guide for Azure Cosmos DB applications, ordered by impact. Contains rules for data modeling, partition key design, query optimization, SDK usage, indexing, throughput management, global distribution, and monitoring.

---

## Table of Contents

1. [Data Modeling](#1-data-modeling) — **CRITICAL**
   - 1.1 [Embed Related Data Retrieved Together](#11-embed-related-data-retrieved-together)
   - 1.2 [Reference Data When Items Grow Large](#12-reference-data-when-items-grow-large)
   - 1.3 [Keep Items Well Under 2MB Limit](#13-keep-items-well-under-2mb-limit)
   - 1.4 [Denormalize for Read-Heavy Workloads](#14-denormalize-for-read-heavy-workloads)
   - 1.5 [Version Your Document Schemas](#15-version-your-document-schemas)
   - 1.6 [Use Type Discriminators for Polymorphic Data](#16-use-type-discriminators-for-polymorphic-data)
2. [Partition Key Design](#2-partition-key-design) — **CRITICAL**
   - 2.1 [Choose High-Cardinality Partition Keys](#21-choose-high-cardinality-partition-keys)
   - 2.2 [Distribute Writes to Avoid Hot Partitions](#22-distribute-writes-to-avoid-hot-partitions)
   - 2.3 [Use Hierarchical Partition Keys for Flexibility](#23-use-hierarchical-partition-keys-for-flexibility)
   - 2.4 [Align Partition Key with Query Patterns](#24-align-partition-key-with-query-patterns)
   - 2.5 [Create Synthetic Partition Keys When Needed](#25-create-synthetic-partition-keys-when-needed)
   - 2.6 [Plan for 20GB Logical Partition Limit](#26-plan-for-20gb-logical-partition-limit)
3. [Query Optimization](#3-query-optimization) — **HIGH**
   - 3.1 [Minimize Cross-Partition Queries](#31-minimize-cross-partition-queries)
   - 3.2 [Project Only Needed Fields](#32-project-only-needed-fields)
   - 3.3 [Use Continuation Tokens for Pagination](#33-use-continuation-tokens-for-pagination)
   - 3.4 [Avoid Full Container Scans](#34-avoid-full-container-scans)
   - 3.5 [Use Parameterized Queries](#35-use-parameterized-queries)
   - 3.6 [Order Filters by Selectivity](#36-order-filters-by-selectivity)
4. [SDK Best Practices](#4-sdk-best-practices) — **HIGH**
   - 4.1 [Reuse CosmosClient as Singleton](#41-reuse-cosmosclient-as-singleton)
   - 4.2 [Use Async APIs for Better Throughput](#42-use-async-apis-for-better-throughput)
   - 4.3 [Handle 429 Errors with Retry-After](#43-handle-429-errors-with-retry-after)
   - 4.4 [Use Direct Connection Mode for Production](#44-use-direct-connection-mode-for-production)
   - 4.5 [Configure Preferred Regions for Availability](#45-configure-preferred-regions-for-availability)
   - 4.6 [Log Diagnostics for Troubleshooting](#46-log-diagnostics-for-troubleshooting)
5. [Indexing Strategies](#5-indexing-strategies) — **MEDIUM-HIGH**
   - 5.1 [Exclude Unused Index Paths](#51-exclude-unused-index-paths)
   - 5.2 [Use Composite Indexes for ORDER BY](#52-use-composite-indexes-for-order-by)
   - 5.3 [Add Spatial Indexes for Geo Queries](#53-add-spatial-indexes-for-geo-queries)
   - 5.4 [Choose Appropriate Index Types](#54-choose-appropriate-index-types)
   - 5.5 [Understand Indexing Modes](#55-understand-indexing-modes)
6. [Throughput & Scaling](#6-throughput--scaling) — **MEDIUM**
   - 6.1 [Use Autoscale for Variable Workloads](#61-use-autoscale-for-variable-workloads)
   - 6.2 [Right-Size Provisioned Throughput](#62-right-size-provisioned-throughput)
   - 6.3 [Consider Serverless for Dev/Test](#63-consider-serverless-for-devtest)
   - 6.4 [Understand Burst Capacity](#64-understand-burst-capacity)
   - 6.5 [Choose Container vs Database Throughput](#65-choose-container-vs-database-throughput)
7. [Global Distribution](#7-global-distribution) — **MEDIUM**
   - 7.1 [Configure Multi-Region Writes](#71-configure-multi-region-writes)
   - 7.2 [Choose Appropriate Consistency Level](#72-choose-appropriate-consistency-level)
   - 7.3 [Implement Conflict Resolution](#73-implement-conflict-resolution)
   - 7.4 [Configure Automatic Failover](#74-configure-automatic-failover)
   - 7.5 [Add Read Regions Near Users](#75-add-read-regions-near-users)
8. [Monitoring & Diagnostics](#8-monitoring--diagnostics) — **LOW-MEDIUM**
   - 8.1 [Track RU Consumption](#81-track-ru-consumption)
   - 8.2 [Monitor P99 Latency](#82-monitor-p99-latency)
   - 8.3 [Alert on Throttling (429s)](#83-alert-on-throttling-429s)
   - 8.4 [Integrate Azure Monitor](#84-integrate-azure-monitor)
   - 8.5 [Enable Diagnostic Logging](#85-enable-diagnostic-logging)

---

## 1. Data Modeling

**Impact: CRITICAL**

Proper data modeling is foundational to Cosmos DB performance. Poor modeling leads to expensive queries, excessive RU consumption, and scalability issues that are difficult to fix later.

### 1.1 Embed Related Data Retrieved Together

**Impact: CRITICAL (eliminates joins, reduces RU by 50-90%)**

Embed related data within a single document when they're always accessed together. This eliminates the need for multiple queries.

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
public class Order
{
    public string Id { get; set; }
    public string CustomerId { get; set; }
    public CustomerSummary Customer { get; set; }  // Embedded
    public List<OrderItem> Items { get; set; }     // Embedded
    public decimal Total { get; set; }
}

var order = await container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
// Single read gets everything needed
```

### 1.2 Reference Data When Items Grow Large

**Impact: CRITICAL (prevents hitting 2MB limit)**

Use document references instead of embedding when embedded data would make items too large.

**Incorrect (embedded array grows unbounded):**

```csharp
public class BlogPost
{
    public string Id { get; set; }
    public string Title { get; set; }
    public List<Comment> Comments { get; set; }  // Could grow to thousands!
}
```

**Correct (reference pattern):**

```csharp
// Separate comment documents in same partition
public class Comment
{
    public string Id { get; set; }
    public string PostId { get; set; }  // Partition key - same as post
    public string Type { get; set; } = "comment";
    public string Text { get; set; }
}
```

### 1.3 Keep Items Well Under 2MB Limit

**Impact: CRITICAL (prevents write failures)**

Store large content in Blob Storage, keep metadata in Cosmos DB.

**Incorrect:**

```csharp
public class Document
{
    public string FileContent { get; set; }  // Large base64 - DANGER!
}
```

**Correct:**

```csharp
public class Document
{
    public string Name { get; set; }
    public string BlobUri { get; set; }  // Reference to Blob Storage
}
```

### 1.4 Denormalize for Read-Heavy Workloads

**Impact: HIGH (reduces query RU by 2-10x)**

Duplicate frequently-read data to avoid expensive lookups.

**Correct:**

```csharp
public class Product
{
    public string Id { get; set; }
    public string CategoryId { get; set; }
    public string CategoryName { get; set; }  // Denormalized for display
}
```

### 1.5 Version Your Document Schemas

**Impact: MEDIUM (enables safe schema evolution)**

Include schema version for backward-compatible reads.

```csharp
public class User
{
    public string Id { get; set; }
    public int SchemaVersion { get; set; } = 2;
}
```

### 1.6 Use Type Discriminators for Polymorphic Data

**Impact: MEDIUM (enables efficient filtering)**

Include type field when storing multiple entity types in same container.

```csharp
public abstract class BaseEntity
{
    public string Id { get; set; }
    public abstract string Type { get; }
}

public class Order : BaseEntity
{
    public override string Type => "order";
}
```

---

## 2. Partition Key Design

**Impact: CRITICAL**

Partition key choice determines data distribution, query efficiency, and scalability limits.

### 2.1 Choose High-Cardinality Partition Keys

**Impact: CRITICAL (enables horizontal scalability)**

Select partition keys with many unique values.

**Incorrect:**

```csharp
public string Status { get; set; }  // Only 5-10 values - BAD!
```

**Correct:**

```csharp
public string CustomerId { get; set; }  // Millions of unique values - GOOD!
```

### 2.2 Distribute Writes to Avoid Hot Partitions

**Impact: CRITICAL (prevents throughput bottlenecks)**

Ensure writes spread evenly across partitions.

**Incorrect:**

```csharp
public string Date { get; set; }  // "2026-01-21" - all today's writes hit ONE partition!
```

**Correct:**

```csharp
public string PartitionKey => $"{Date}_shard{hash % 10}";  // Distribute across 10 partitions
```

### 2.3 Use Hierarchical Partition Keys for Flexibility

**Impact: HIGH (overcomes 20GB limit)**

Use multiple levels for large tenants.

```csharp
PartitionKeyPaths = new List<string> { "/tenantId", "/year", "/month" }
```

### 2.4 Align Partition Key with Query Patterns

**Impact: CRITICAL (enables single-partition queries)**

Choose partition key matching your most frequent queries.

### 2.5 Create Synthetic Partition Keys When Needed

**Impact: HIGH (optimizes for multiple access patterns)**

Combine fields when no single field is ideal.

```csharp
public string PartitionKey => $"{DeviceId}_{Timestamp:yyyy-MM}";
```

### 2.6 Plan for 20GB Logical Partition Limit

**Impact: HIGH (prevents partition split failures)**

Design to stay under 20GB per partition key value.

---

## 3. Query Optimization

**Impact: HIGH**

Optimized queries minimize RU consumption and latency.

### 3.1 Minimize Cross-Partition Queries

**Impact: HIGH (reduces RU by 5-100x)**

Always include partition key in WHERE clause.

```csharp
var options = new QueryRequestOptions { PartitionKey = new PartitionKey(customerId) };
```

### 3.2 Project Only Needed Fields

**Impact: HIGH (reduces RU and network by 30-80%)**

Select specific fields, not `SELECT *`.

```csharp
"SELECT c.id, c.name, c.status FROM c"
```

### 3.3 Use Continuation Tokens for Pagination

**Impact: HIGH (enables efficient large result sets)**

Never use OFFSET/LIMIT for deep pagination.

```csharp
var iterator = container.GetItemQueryIterator<T>(query, continuationToken: token);
```

### 3.4 Avoid Full Container Scans

**Impact: HIGH (prevents unbounded RU consumption)**

Ensure queries use indexes.

**Incorrect:**

```csharp
"SELECT * FROM c WHERE LOWER(c.email) = 'test@example.com'"  // Function prevents index use
```

**Correct:**

```csharp
"SELECT * FROM c WHERE c.emailLower = 'test@example.com'"  // Pre-computed, indexed
```

### 3.5 Use Parameterized Queries

**Impact: MEDIUM (improves security and caching)**

```csharp
new QueryDefinition("SELECT * FROM c WHERE c.id = @id").WithParameter("@id", id)
```

### 3.6 Order Filters by Selectivity

**Impact: MEDIUM (reduces intermediate result sets)**

Place most selective filters first.

---

## 4. SDK Best Practices

**Impact: HIGH**

Proper SDK usage ensures connection efficiency and optimal throughput.

### 4.1 Reuse CosmosClient as Singleton

**Impact: CRITICAL (prevents connection exhaustion)**

Create once, reuse throughout application lifetime.

```csharp
services.AddSingleton<CosmosClient>(sp => new CosmosClient(connectionString, options));
```

### 4.2 Use Async APIs for Better Throughput

**Impact: HIGH (improves concurrency 10-100x)**

Never use `.Result` or `.Wait()`.

```csharp
var response = await container.ReadItemAsync<Order>(id, pk);
```

### 4.3 Handle 429 Errors with Retry-After

**Impact: HIGH (prevents cascading failures)**

Configure SDK retry settings.

```csharp
MaxRetryAttemptsOnRateLimitedRequests = 9,
MaxRetryWaitTimeOnRateLimitedRequests = TimeSpan.FromSeconds(30)
```

### 4.4 Use Direct Connection Mode for Production

**Impact: HIGH (reduces latency by 30-50%)**

```csharp
ConnectionMode = ConnectionMode.Direct
```

### 4.5 Configure Preferred Regions for Availability

**Impact: HIGH (enables automatic failover)**

```csharp
ApplicationPreferredRegions = new List<string> { Regions.WestUS2, Regions.EastUS2 }
```

### 4.6 Log Diagnostics for Troubleshooting

**Impact: MEDIUM (enables root cause analysis)**

Capture diagnostics for slow or failed operations.

---

## 5. Indexing Strategies

**Impact: MEDIUM-HIGH**

Strategic indexing reduces query costs while minimizing write overhead.

### 5.1 Exclude Unused Index Paths

**Impact: HIGH (reduces write RU by 20-80%)**

```csharp
ExcludedPaths = { new ExcludedPath { Path = "/largeArray/*" } }
```

### 5.2 Use Composite Indexes for ORDER BY

**Impact: HIGH (enables sorted queries)**

```csharp
CompositeIndexes = {
    new Collection<CompositePath> {
        new CompositePath { Path = "/status" },
        new CompositePath { Path = "/createdAt", Order = Descending }
    }
}
```

### 5.3 Add Spatial Indexes for Geo Queries

**Impact: MEDIUM-HIGH (enables efficient location queries)**

```csharp
SpatialIndexes = { new SpatialPath { Path = "/location/?", SpatialTypes = { SpatialType.Point } } }
```

### 5.4 Choose Appropriate Index Types

**Impact: MEDIUM**

Range indexes (default) support equality, range, and ORDER BY.

### 5.5 Understand Indexing Modes

**Impact: MEDIUM**

- Consistent (default): Query results always current
- None: Write-only, maximum throughput

---

## 6. Throughput & Scaling

**Impact: MEDIUM**

Right-sizing throughput balances cost and performance.

### 6.1 Use Autoscale for Variable Workloads

**Impact: HIGH (handles traffic spikes)**

```csharp
ThroughputProperties.CreateAutoscaleThroughput(maxThroughput: 10000)
```

### 6.2 Right-Size Provisioned Throughput

**Impact: MEDIUM**

Monitor and adjust based on actual usage.

### 6.3 Consider Serverless for Dev/Test

**Impact: MEDIUM (pay-per-request pricing)**

No minimum commitment for low-traffic scenarios.

### 6.4 Understand Burst Capacity

**Impact: MEDIUM**

Short-term spike handling, not for sustained load.

### 6.5 Choose Container vs Database Throughput

**Impact: MEDIUM**

- Container: Guaranteed isolation
- Database: Cost efficient for many low-traffic containers

---

## 7. Global Distribution

**Impact: MEDIUM**

Multi-region configuration enables low-latency globally.

### 7.1 Configure Multi-Region Writes

**Impact: HIGH (enables local writes)**

`enableMultipleWriteLocations: true`

### 7.2 Choose Appropriate Consistency Level

**Impact: HIGH**

- Session (default): Best balance
- Strong: Financial transactions
- Eventual: Highest performance

### 7.3 Implement Conflict Resolution

**Impact: MEDIUM**

Configure Last Writer Wins or custom resolution.

### 7.4 Configure Automatic Failover

**Impact: HIGH (ensures availability)**

`enableAutomaticFailover: true`

### 7.5 Add Read Regions Near Users

**Impact: MEDIUM (reduces read latency)**

Add replicas in user-heavy geographic regions.

---

## 8. Monitoring & Diagnostics

**Impact: LOW-MEDIUM**

Proactive monitoring catches issues before they impact users.

### 8.1 Track RU Consumption

**Impact: MEDIUM**

Log `response.RequestCharge` for cost optimization.

### 8.2 Monitor P99 Latency

**Impact: MEDIUM**

Track percentiles, not just averages.

### 8.3 Alert on Throttling (429s)

**Impact: HIGH (prevents silent failures)**

Set up Azure Monitor alerts for 429 status codes.

### 8.4 Integrate Azure Monitor

**Impact: MEDIUM**

Enable diagnostic settings for comprehensive visibility.

### 8.5 Enable Diagnostic Logging

**Impact: LOW-MEDIUM**

Capture DataPlaneRequests, QueryRuntimeStatistics, PartitionKeyStatistics.

---

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
