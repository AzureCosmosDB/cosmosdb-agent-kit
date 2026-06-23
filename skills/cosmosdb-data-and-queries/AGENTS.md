# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Best practices for Azure Cosmos DB data design and querying: document modeling, partition key selection, indexing policy, query optimization, and data-access patterns.

---

## Table of Contents

1. [Data Modeling](#1-data-modeling) — **CRITICAL**
   - 1.1 [Keep Items Well Under 2MB Limit](#11-keep-items-well-under-2mb-limit)
   - 1.2 [Denormalize for Read-Heavy Workloads](#12-denormalize-for-read-heavy-workloads)
   - 1.3 [Embed Related Data Retrieved Together](#13-embed-related-data-retrieved-together)
   - 1.4 [Follow ID Value Length and Character Constraints](#14-follow-id-value-length-and-character-constraints)
   - 1.5 [Handle JSON serialization correctly for Cosmos DB documents](#15-handle-json-serialization-correctly-for-cosmos-db-documents)
   - 1.6 [Stay Within 128-Level Nesting Depth Limit](#16-stay-within-128-level-nesting-depth-limit)
   - 1.7 [Understand IEEE 754 Numeric Precision Limits](#17-understand-ieee-754-numeric-precision-limits)
   - 1.8 [Reference Data When Items Grow Large](#18-reference-data-when-items-grow-large)
   - 1.9 [Use ID references with transient hydration for document relationships](#19-use-id-references-with-transient-hydration-for-document-relationships)
   - 1.10 [Version Your Document Schemas](#110-version-your-document-schemas)
   - 1.11 [Use Type Discriminators for Polymorphic Data](#111-use-type-discriminators-for-polymorphic-data)
2. [Partition Key Design](#2-partition-key-design) — **CRITICAL**
   - 2.1 [Plan for 20GB Logical Partition Limit](#21-plan-for-20gb-logical-partition-limit)
   - 2.2 [Distribute Writes to Avoid Hot Partitions](#22-distribute-writes-to-avoid-hot-partitions)
   - 2.3 [Use Hierarchical Partition Keys for Flexibility](#23-use-hierarchical-partition-keys-for-flexibility)
   - 2.4 [Choose High-Cardinality Partition Keys](#24-choose-high-cardinality-partition-keys)
   - 2.5 [Choose Immutable Properties as Partition Keys](#25-choose-immutable-properties-as-partition-keys)
   - 2.6 [Respect Partition Key Value Length Limits](#26-respect-partition-key-value-length-limits)
   - 2.7 [Align Partition Key with Query Patterns](#27-align-partition-key-with-query-patterns)
   - 2.8 [Create Synthetic Partition Keys When Needed](#28-create-synthetic-partition-keys-when-needed)
3. [Indexing Strategies](#3-indexing-strategies) — **MEDIUM-HIGH**
   - 3.1 [Composite Index Directions Must Match ORDER BY](#31-composite-index-directions-must-match-order-by)
   - 3.2 [Use Composite Indexes for ORDER BY](#32-use-composite-indexes-for-order-by)
   - 3.3 [Exclude Unused Index Paths](#33-exclude-unused-index-paths)
   - 3.4 [Understand Indexing Modes](#34-understand-indexing-modes)
   - 3.5 [Use Correct Indexing Path Syntax](#35-use-correct-indexing-path-syntax)
   - 3.6 [Choose Appropriate Index Types](#36-choose-appropriate-index-types)
   - 3.7 [Add Spatial Indexes for Geo Queries](#37-add-spatial-indexes-for-geo-queries)
4. [Query Optimization](#4-query-optimization) — **HIGH**
   - 4.1 [Compute min/max/avg with one scoped aggregate query](#41-compute-min-max-avg-with-one-scoped-aggregate-query)
   - 4.2 [Minimize Cross-Partition Queries](#42-minimize-cross-partition-queries)
   - 4.3 [Avoid Full Container Scans](#43-avoid-full-container-scans)
   - 4.4 [Use DISTINCT keyword to eliminate duplicate results efficiently](#44-use-distinct-keyword-to-eliminate-duplicate-results-efficiently)
   - 4.5 [Query "latest" documents with explicit ORDER BY and TOP 1](#45-query-latest-documents-with-explicit-order-by-and-top-1)
   - 4.6 [Detect and Redirect Analytical Queries Away from Transactional Containers](#46-detect-and-redirect-analytical-queries-away-from-transactional-containers)
   - 4.7 [Order Filters by Selectivity](#47-order-filters-by-selectivity)
   - 4.8 [Use Continuation Tokens for Pagination](#48-use-continuation-tokens-for-pagination)
   - 4.9 [Use Parameterized Queries](#49-use-parameterized-queries)
   - 4.10 [Use Point Reads Instead of Queries for Known ID and Partition Key](#410-use-point-reads-instead-of-queries-for-known-id-and-partition-key)
   - 4.11 [Parameterize TOP Values Safely](#411-parameterize-top-values-safely)
   - 4.12 [Project Only Needed Fields](#412-project-only-needed-fields)
5. [Design Patterns](#5-design-patterns) — **HIGH**
   - 5.1 [Use Change Feed for cross-partition query optimization with materialized views](#51-use-change-feed-for-cross-partition-query-optimization-with-materialized-views)
   - 5.2 [Use count-based or cached rank approaches instead of full partition scans for ranking](#52-use-count-based-or-cached-rank-approaches-instead-of-full-partition-scans-for-ranking)
   - 5.3 [Use a service layer to hydrate document references before rendering](#53-use-a-service-layer-to-hydrate-document-references-before-rendering)

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

*Additional strategies to consider for denormalization*:
**Pre-computed Aggregates** :
   - Definition: When an entity is frequently read and the read response includes aggregated statistics (counts, averages, totals), store those aggregates as persistent document fields rather than computing them per-request
   - When to use:
     - The entity's read response includes derived values such as counts, sums, averages, or min/max
     - Reads significantly outnumber writes (high read-to-write ratio)
     - Computing aggregates on-demand would require COUNT/AVG/SUM queries or application-level iteration
   - Update strategy: Update aggregate fields inline at write time (within the same operation that records new data) or asynchronously via Change Feed
   - Include a `lastUpdated` timestamp field to enable staleness detection

   **Incorrect (aggregates computed on-demand):**

   ```java
   @Container(containerName = "players")
   public class PlayerProfile {
       @Id
       private String id;
       @PartitionKey
       private String playerId;
       private String displayName;
       private int bestScore;
       // No stored aggregates — totalGamesPlayed requires COUNT query,
       // averageScore requires AVG query or app-level computation per request
   }
   ```

   **Correct (pre-computed aggregates stored as fields):**

   ```java
   @Container(containerName = "players")
   public class PlayerProfile {
       @Id
       private String id;
       @PartitionKey
       private String playerId;
       private String displayName;
       private int bestScore;
       private int totalGamesPlayed;   // pre-computed, updated at write time
       private double averageScore;     // pre-computed, updated at write time
       private long lastUpdated;        // timestamp for staleness detection
   }
   ```

   ```csharp
   // Updating aggregates inline at write time
   public async Task RecordGameScore(string playerId, int score)
   {
       var profile = await container.ReadItemAsync<PlayerProfile>(
           playerId, new PartitionKey(playerId));
       var p = profile.Resource;
       p.TotalGamesPlayed += 1;
       p.BestScore = Math.Max(p.BestScore, score);
       p.AverageScore = p.TotalGamesPlayed == 1
           ? score
           : ((p.AverageScore * (p.TotalGamesPlayed - 1)) + score) / p.TotalGamesPlayed;
       p.LastUpdated = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
       await container.ReplaceItemAsync(p, p.Id, new PartitionKey(playerId));
   }
   ```

**Short-Circuit Denormalization** :
   - Definition: Duplicate *only specific fields* (not the full related document) to avoid a cross-partition lookup
   - When to use:
     - The duplicated property is mostly immutable (e.g., product name) or the app can tolerate staleness
     - The property is small (a string, not an object)
     - The access pattern would otherwise require a cross-partition read
   - Example: Copy `customerName` into Order doc to avoid looking up the Customer doc

**Workload-Driven Cost Comparison Template for Denormalization Strategy** :
   ```
   Option 1 — Denormalized:
     Read cost:  [read_RPS] × [RU_per_read] = X RU/s
     Write cost: [write_RPS] × [RU_per_write] + [update_propagation_cost] = Y RU/s
     Total: X + Y RU/s

   Option 2 — Normalized:
     Read cost:  [read_RPS] × ([RU_per_read] + [RU_for_lookup]) = X' RU/s
     Write cost: [write_RPS] × [RU_per_write] = Y' RU/s
     Total: X' + Y' RU/s

   Decision: Choose option with lower total RU/s when workload profile details available
   ```

**Cascade Delete and Update of Denormalized Documents**:

   When a source document is **deleted** or a key field used in denormalized copies is **updated**, all related derived documents in other containers must be updated or removed. Failing to cascade deletes/updates leaves orphaned or stale denormalized data, which causes queries to return ghost entries (deleted entities still appearing in listings) or outdated information (entities appearing under old field values).

   This is one of the most commonly missed patterns: developers implement the source document delete/update correctly but forget to propagate the change to all containers that hold derived documents.

   **Cascade DELETE — remove all related documents when source is deleted:**

   ```python
   # ❌ WRONG — only deletes the source document, orphans derived documents
   async def delete_player(player_id: str):
       await players_container.delete_item(item=player_id, partition_key=player_id)
       # Missing: delete from scores container
       # Missing: delete from leaderboard container
   ```

   ```python
   # ✅ CORRECT — cascade delete across all related containers
   async def delete_player(player_id: str):
       # 1. Delete the source document
       await players_container.delete_item(item=player_id, partition_key=player_id)

       # 2. Delete all related score documents (different container, same partition key)
       scores_query = "SELECT c.id FROM c WHERE c.playerId = @pid"
       async for page in scores_container.query_items(
           query=scores_query, parameters=[{"name": "@pid", "value": player_id}]
       ):
           await scores_container.delete_item(item=page["id"], partition_key=player_id)

       # 3. Delete all leaderboard entries for this player (derived documents)
       lb_query = "SELECT c.id, c.leaderboardKey FROM c WHERE c.playerId = @pid"
       async for entry in leaderboard_container.query_items(
           query=lb_query, parameters=[{"name": "@pid", "value": player_id}],
           enable_cross_partition_query=True,
       ):
           await leaderboard_container.delete_item(
               item=entry["id"], partition_key=entry["leaderboardKey"]
           )
   ```

   ```csharp
   // ✅ CORRECT — .NET cascade delete
   public async Task DeletePlayerAsync(string playerId)
   {
       // 1. Delete source
       await _playersContainer.DeleteItemAsync<Player>(playerId, new PartitionKey(playerId));

       // 2. Delete related scores
       var scoreQuery = new QueryDefinition("SELECT c.id FROM c WHERE c.playerId = @pid")
           .WithParameter("@pid", playerId);
       await foreach (var score in _scoresContainer.GetItemQueryIterator<dynamic>(
               scoreQuery, requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(playerId) }))
           await _scoresContainer.DeleteItemAsync<dynamic>(score.id, new PartitionKey(playerId));

       // 3. Delete derived leaderboard entries (enumerate all leaderboard partitions or use cross-partition query)
       var lbQuery = new QueryDefinition("SELECT c.id, c.leaderboardKey FROM c WHERE c.playerId = @pid")
           .WithParameter("@pid", playerId);
       await foreach (var entry in _leaderboardContainer.GetItemQueryIterator<dynamic>(lbQuery))
           await _leaderboardContainer.DeleteItemAsync<dynamic>(
               (string)entry.id, new PartitionKey((string)entry.leaderboardKey));
   }
   ```

   **Cascade UPDATE — re-derive documents when a partitioning field changes:**

   When an entity has a field that determines which partition its derived documents belong to (e.g., a `region` field used as the leaderboard partition key), updating that field requires:
   1. Deleting the old derived documents from the previous partition  
   2. Creating new derived documents in the new partition

   ```python
   # ❌ WRONG — updates player region but leaves stale leaderboard entry in old region
   async def update_player(player_id: str, updates: dict):
       player = await players_container.read_item(item=player_id, partition_key=player_id)
       player.update(updates)
       await players_container.replace_item(item=player_id, body=player)
       # Missing: remove leaderboard entry from old region, add to new region
   ```

   ```python
   # ✅ CORRECT — cascade update when a partition-key field changes
   async def update_player(player_id: str, updates: dict):
       player = await players_container.read_item(item=player_id, partition_key=player_id)
       old_region = player.get("region")
       player.update(updates)
       new_region = player.get("region")
       await players_container.replace_item(item=player_id, body=player)

       if "region" in updates and old_region != new_region:
           # Remove old regional leaderboard entry
           old_key = f"{old_region}_all-time"
           try:
               await leaderboard_container.delete_item(
                   item=player_id, partition_key=old_key
               )
           except Exception:
               pass  # May not exist if player had no scores

           # Re-create in new regional leaderboard if player has scores
           if player.get("bestScore", 0) > 0:
               new_key = f"{new_region}_all-time"
               new_entry = {
                   "id": player_id,
                   "leaderboardKey": new_key,
                   "playerId": player_id,
                   "displayName": player["displayName"],
                   "score": player["bestScore"],
               }
               await leaderboard_container.upsert_item(body=new_entry)
   ```

   **Key rules for cascade operations:**
   - **Every DELETE endpoint** for an entity that has denormalized copies elsewhere must also delete those copies
   - **Every UPDATE endpoint** that changes a field used in derived documents must propagate the change
   - If the updated field is a partition key of the derived container, you must delete-and-recreate (Cosmos DB does not support updating partition key values)
   - Consider listing all containers where derived data lives in a comment near each delete/update handler

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


*Consider following **Aggregate Decision Framework** for embedding vs referencing:*
1. **Access Correlation Thresholds** 
   - \>90% accessed together → Strong single-document aggregate candidate (embed)
   - 50–90% accessed together → Multi-document container aggregate candidate (same container, separate docs, shared partition key)
   - <50% accessed together → Separate containers

2. **Constraint Checks** :
   - Size: Will combined size exceed 1MB? → Force multi-document or separate containers for child documents
   - Updates: Different update frequencies? → Consider multi-document
   - Atomicity: Need transactional updates? → Favor same partition with small batched updates or distributed transactional outbox pattern

Reference: [Data modeling in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/modeling-data)

### 1.4 Follow ID Value Length and Character Constraints

**Impact: HIGH** (prevents write failures, 401 auth errors, and cross-SDK interoperability issues)

## Follow ID Value Length and Character Constraints

Azure Cosmos DB enforces a **1,023 byte** maximum for the `id` property and restricts certain characters. Using URL-reserved or path-separator characters in `id` values causes authentication failures (401) or routing errors (404) that are difficult to diagnose because they only surface on read/update/delete — not on create.

### URL-reserved characters break Cosmos DB auth signing

Cosmos DB's REST protocol computes an HMAC signature over a canonical string that includes the ResourceLink (`dbs/{db}/colls/{coll}/docs/{id}`). When the SDK sends an HTTP request whose URL embeds a URL-reserved character in the `id` segment, the HTTP transport may strip or reinterpret the URL (e.g. a `#` is a fragment delimiter per RFC 3986 and is removed before the request leaves the client). The server then recomputes the signature over the truncated ResourceLink and returns **401 Unauthorized: "The input authorization token can't serve the request"** — even though the key is correct.

The failure surfaces on `read_item`, `replace_item`, `delete_item`, and `patch_item`. It does **not** surface on `create_item` (the id is not part of the signed ResourceLink for creates — the parent collection is), so the bug often hides until the first update or read.

This is a cross-SDK issue affecting any SDK using Gateway mode. The Python SDK uses Gateway mode by default and always hits this. The .NET SDK hits the same failure in Gateway mode but not in Direct mode (Direct bypasses HTTP URI parsing). The .NET SDK's own test suite (`CosmosItemIdEncodingTestsBase.cs`, test `IdWithDisallowedCharPoundSign`) confirms 401 on read/replace/delete in Gateway mode with `#` in the id.

**Never use any of these in `id`:**

| Char | Reason |
|------|--------|
| `#` | URL fragment delimiter — HTTP client strips everything after `#` before sending; server sees truncated id, HMAC signature mismatch → 401 |
| `?` | URL query delimiter — same truncation class of failure → 401 |
| `/` `\` | Path separators — change the ResourceLink structure → 404 or 400 |

**Avoid (interoperability / encoding risk):**

| Char | Reason |
|------|--------|
| ` ` (space) | Percent-encoding inconsistency across SDKs and connectors |
| `%` | Ambiguous with percent-encoding sequences |
| Any non-ASCII | Encoded differently across clients; known issues in ADF / Spark / Kafka connectors |

**Safe synthetic-id separators:** `_`, `-`, `:`

### The `id` property is always a string

Azure Cosmos DB stores and indexes the `id` system property as a JSON string. There is no numeric `id` type.

When migrating from a relational database, keep the primary-key value but store it as a string `id` value:

| Relational key | Cosmos DB `id` |
|---------------|---------------|
| `42` | `"42"` |
| `90001` | `"90001"` |

Bind `id` to a string type in DTOs, domain models, and API contracts.

**Incorrect:**

```csharp
public record Product(int Id, string Name);
```

**Correct:**

```csharp
public record Product(string Id, string Name);
```

### SQL to NoSQL migration guidance

Do not introduce a parallel numeric copy of `id` solely for sorting or pagination.

**Incorrect:**

```sql
SELECT * FROM c
ORDER BY c.idNum
```

**Correct (for string ordering by id):**

```sql
SELECT * FROM c
ORDER BY c.id
```

If numeric ordering is required, use a dedicated business field such as `sku`, `sequenceNumber`, or another domain-specific numeric property:

```sql
SELECT * FROM c
ORDER BY c.sequenceNumber
```

Do not introduce a numeric shadow copy of `id` solely for sorting or pagination.

| Symptom | Cause |
|----------|--------|
| Could not convert `$.id` to `Int32` | DTO binds `id` to a numeric type |
| Unexpected pagination ordering | Sorting by a numeric shadow id instead of `c.id` |

**Incorrect (oversized or problematic IDs):**

```csharp
// Anti-pattern 1: ID derived from unbounded user input
public class Document
{
    // ID could exceed 1,023 bytes if title is very long
    public string Id => $"{Category}_{SubCategory}_{Title}_{Description}";
    public string Category { get; set; }
    public string SubCategory { get; set; }
    public string Title { get; set; }
    public string Description { get; set; }  // Unbounded!
}

// Anti-pattern 2: IDs containing forbidden or problematic characters
var doc = new Document
{
    Id = "files/reports\\2026/Q1",  // Contains '/' and '\' - FORBIDDEN
    Content = "..."
};
await container.CreateItemAsync(doc);
// Fails or causes routing issues

// Anti-pattern 3: Non-ASCII characters in IDs
var doc2 = new Document
{
    Id = "レポート_2026_データ",  // Non-ASCII - interoperability risk
    Content = "..."
};
// Works in some SDKs but may break in ADF, Spark, Kafka connectors
```

```python
# Anti-pattern 4: Using '#' as composite-id separator — 401 on read/update/delete
doc_id = f"best#{player_id}#{week}#{region}"
await container.upsert_item(body={"id": doc_id, ...})   # succeeds (create)
await container.read_item(item=doc_id, partition_key=pk) # 💥 401 Unauthorized
```

**Correct (safe, bounded IDs):**

```csharp
// Use GUIDs or short alphanumeric identifiers
public class Document
{
    public string Id { get; set; }
    public string Category { get; set; }
    public string Title { get; set; }
}

// Option 1: GUID-based IDs (always safe, always unique)
var doc = new Document
{
    Id = Guid.NewGuid().ToString(),  // "a1b2c3d4-e5f6-..."
    Category = "reports",
    Title = "Q1 Report"
};

// Option 2: Compact, deterministic IDs from business keys
var doc2 = new Document
{
    Id = $"report-{tenantId}-{DateTime.UtcNow:yyyyMMdd}-{sequenceNum}",
    Category = "reports",
    Title = "Q1 Report"
};

// Option 3: Base64-encode when you must derive from non-ASCII data
var rawId = "レポート_2026_データ";
var doc3 = new Document
{
    Id = Convert.ToBase64String(Encoding.UTF8.GetBytes(rawId))
            .Replace('/', '_').Replace('+', '-'),  // URL-safe Base64
    Category = "reports",
    Title = rawId  // Keep original value as a property
};
```

```python
# Correct: Use ':' or '_' or '-' as composite-id separators
doc_id = f"best:{player_id}:{week}:{region}"   # ✅ works on all operations
await container.upsert_item(body={"id": doc_id, ...})
await container.read_item(item=doc_id, partition_key=pk)  # ✅ 200 OK
```

Key constraints:
- **Max length:** 1,023 bytes
- **Forbidden characters:** `#`, `?`, `/`, and `\` are not allowed — `#` and `?` cause 401 Unauthorized on read/update/delete; `/` and `\` cause routing failures
- **Best practice:** Use only alphanumeric ASCII characters (`a-z`, `A-Z`, `0-9`, `-`, `_`) and `:` as a separator
- **Why:** URL-reserved characters break REST auth signing across all SDKs in Gateway mode; some SDK versions, Azure Data Factory, Spark connector, and Kafka connector have additional issues with non-alphanumeric IDs
- Encode non-ASCII IDs with Base64 + custom encoding if needed for interoperability

See also: `partition-synthetic-keys` for synthetic-key construction patterns.

Reference: [Azure Cosmos DB service quotas - Per-item limits](https://learn.microsoft.com/azure/cosmos-db/concepts-limits#per-item-limits) | [Access control on Cosmos DB resources](https://learn.microsoft.com/rest/api/cosmos-db/access-control-on-cosmosdb-resources)

### 1.5 Handle JSON serialization correctly for Cosmos DB documents

**Impact: HIGH** (prevents data loss, null constructor errors, and serialization failures)

## Handle JSON Serialization Correctly for Cosmos DB

Cosmos DB stores documents as JSON. Every field on an entity that must be persisted needs to be serializable. Incorrect use of `@JsonIgnore`, missing constructors, or incompatible field types (like `BigDecimal` on JDK 17+) cause silent data loss or runtime failures.

**Incorrect (common serialization mistakes):**

```java
@Container(containerName = "users")
public class User {

    @Id
    private String id;

    @PartitionKey
    private String partitionKey = "user";

    private String login;

    @JsonIgnore  // ❌ WRONG: Password will NOT be saved to Cosmos DB
    private String password;

    @JsonIgnore  // ❌ WRONG: Authorities will NOT be saved to Cosmos DB
    private Set<String> authorities = new HashSet<>();

    private BigDecimal accountBalance;  // ❌ Fails on JDK 17+ with reflection errors
}
```

**Correct (proper serialization for Cosmos DB):**

```java
@JsonIgnoreProperties(ignoreUnknown = true)  // ✅ Ignore Cosmos DB system metadata (_rid, _self, _etag, _ts, _lsn)
@Container(containerName = "users")
public class User {

    @Id
    private String id;

    @PartitionKey
    private String partitionKey = "user";

    private String login;

    // ✅ No @JsonIgnore — field is persisted to Cosmos DB
    private String password;

    // ✅ Use @JsonProperty for explicit field naming, NOT @JsonIgnore
    @JsonProperty("authorities")
    private Set<String> authorities = new HashSet<>();

    // ✅ Use Double instead of BigDecimal for JDK 17+ compatibility
    private Double accountBalance;
}
```

**Rule 1: Never `@JsonIgnore` persisted fields**

`@JsonIgnore` prevents a field from being written to Cosmos DB. This is the #1 cause of "Cannot pass null or empty values to constructor" errors after reading a document back:

```java
// ❌ Data loss: field is not stored in Cosmos
@JsonIgnore
private String password;

// ✅ Field is stored in Cosmos
private String password;

// ✅ Rename in JSON but still store
@JsonProperty("pwd")
private String password;
```

**Only use `@JsonIgnore` on transient/computed fields** that should NOT be stored in Cosmos DB (e.g., hydrated relationship objects — see `model-relationship-references`).

**Rule 2: BigDecimal fails on JDK 17+**

Java 17+ module system restricts reflection access to `BigDecimal` internal fields during Jackson serialization:

```
Unable to make field private final java.math.BigInteger
java.math.BigDecimal.intVal accessible
```

**Solutions (in order of preference):**

1. **Replace with `Double`** — sufficient for most use cases:
   ```java
   private Double amount; // Instead of BigDecimal
   ```

2. **Replace with `String`** — for high-precision requirements:
   ```java
   private String amount; // Store "1500.00"

   public BigDecimal getAmountAsBigDecimal() {
       return new BigDecimal(amount);
   }
   ```

3. **Add JVM argument** — if BigDecimal must be kept:
   ```
   --add-opens java.base/java.math=ALL-UNNAMED
   ```

**Rule 3: Provide a default constructor**

Cosmos DB deserialization requires a no-arg constructor. If you add parameterized constructors, always keep the default:

```java
@Container(containerName = "items")
public class Item {
    // ✅ Default constructor required for deserialization
    public Item() {}

    public Item(String name, Double price) {
        this.name = name;
        this.price = price;
    }
}
```

**Rule 4: Store complex objects as simple types**

For complex Cosmos DB compatibility, prefer simple types over JPA entity references:

```java
// ❌ Complex nested entity — may cause serialization issues
private Set<Authority> authorities;

// ✅ Simple string set — reliable serialization
private Set<String> authorities;
```

Convert between simple and complex types in the service layer, not in the entity.

**Rule 5: Ignore unknown properties from Cosmos DB system metadata**

Cosmos DB documents contain system metadata fields (`_rid`, `_self`, `_etag`, `_ts`, `_lsn`) that are not part of your entity model. Without handling these, Jackson throws `UnrecognizedPropertyException` when deserializing documents — during point reads, queries, and Change Feed processing:

```
com.fasterxml.jackson.databind.exc.UnrecognizedPropertyException:
  Unrecognized field "_lsn" (class PlayerProfile), not marked as ignorable
```

**Option A (recommended): Configure globally at the ObjectMapper or Spring Boot level**

This handles unknown properties for all entity classes without requiring per-class annotations:

```java
// ✅ Global ObjectMapper configuration — covers all Cosmos DB entities
ObjectMapper mapper = new ObjectMapper();
mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
```

For Spring Boot applications, add to `application.properties`:

```properties
# ✅ Spring Boot global setting
spring.jackson.deserialization.fail-on-unknown-properties=false
```

**Option B: Annotate each entity class with `@JsonIgnoreProperties(ignoreUnknown = true)`**

If global configuration is not possible, annotate every Cosmos DB entity class:

```java
// ❌ Fails on system metadata fields from Cosmos DB
@Container(containerName = "players")
public class PlayerProfile {
    @Id
    private String id;
    private String playerId;
    private int score;
}

// ✅ Ignores unknown fields — safe for all Cosmos DB reads
@JsonIgnoreProperties(ignoreUnknown = true)
@Container(containerName = "players")
public class PlayerProfile {
    @Id
    private String id;
    private String playerId;
    private int score;
}
```

⚠️ **This annotation must be on every entity class.** If you miss even one, deserialization of that entity will fail when Cosmos DB system metadata is present.

Reference: [Jackson annotations guide](https://github.com/FasterXML/jackson-annotations/wiki/Jackson-Annotations)

### 1.6 Stay Within 128-Level Nesting Depth Limit

**Impact: MEDIUM** (prevents document rejection on deeply nested structures)

## Stay Within 128-Level Nesting Depth Limit

Azure Cosmos DB allows a maximum of **128 levels** of nesting for embedded objects and arrays. While 128 is generous, recursive or auto-generated structures can exceed this limit unexpectedly.

**Incorrect (risk of exceeding nesting limit):**

```csharp
// Anti-pattern 1: Recursive tree stored as deeply nested JSON
public class TreeNode
{
    public string Id { get; set; }
    public string Name { get; set; }
    
    // Recursive children - each level adds nesting depth
    public List<TreeNode> Children { get; set; }
}

// A category hierarchy with 130+ levels will fail on write
var root = BuildDeepTree(depth: 150);  // Exceeds 128 levels!
await container.CreateItemAsync(root);
// Microsoft.Azure.Cosmos.CosmosException: Document nesting depth exceeds limit

// Anti-pattern 2: Deeply nested auto-generated JSON from ORMs
// Serializing complex object graphs without cycle detection
var entity = LoadEntityWithAllRelations();  // Lazy-loaded relations
var json = JsonSerializer.Serialize(entity);  // May create deep nesting
```

**Correct (bounded nesting depth):**

```csharp
// Solution 1: Flatten deep hierarchies using path-based approach
public class CategoryNode
{
    public string Id { get; set; }
    public string Name { get; set; }
    public string ParentId { get; set; }
    
    // Materialized path captures hierarchy without nesting
    public string Path { get; set; }  // e.g., "/root/electronics/phones/android"
    public int Depth { get; set; }
    
    // Only store immediate children IDs, not nested objects
    public List<string> ChildIds { get; set; }
}

// Each node is a flat document, hierarchy expressed via Path and ParentId
var node = new CategoryNode
{
    Id = "cat-android",
    Name = "Android",
    ParentId = "cat-phones",
    Path = "/root/electronics/phones/android",
    Depth = 3,
    ChildIds = new List<string> { "cat-samsung", "cat-pixel" }
};
```

```csharp
// Solution 2: Cap nesting depth when building recursive structures
public class TreeNode
{
    public string Id { get; set; }
    public string Name { get; set; }
    public List<TreeNode> Children { get; set; }
}

// Limit nesting at serialization time
public static TreeNode TruncateTree(TreeNode node, int maxDepth, int currentDepth = 0)
{
    if (currentDepth >= maxDepth || node.Children == null)
    {
        node.Children = null;  // Stop nesting here
        return node;
    }
    
    node.Children = node.Children
        .Select(c => TruncateTree(c, maxDepth, currentDepth + 1))
        .ToList();
    return node;
}

// Keep well under 128 - aim for practical limits like 10-20
var safeTree = TruncateTree(root, maxDepth: 20);
await container.CreateItemAsync(safeTree);
```

Key points:
- Maximum nesting depth is **128 levels** for embedded objects/arrays
- Recursive data structures (trees, graphs) are the most common cause of violations
- Prefer flat representations with references (parent IDs, materialized paths) for deep hierarchies
- If nesting is required, enforce a practical depth cap well under 128

Reference: [Azure Cosmos DB service quotas - Per-item limits](https://learn.microsoft.com/azure/cosmos-db/concepts-limits#per-item-limits)

### 1.7 Understand IEEE 754 Numeric Precision Limits

**Impact: MEDIUM** (prevents silent data loss on large or precise numbers)

## Understand IEEE 754 Numeric Precision Limits

Azure Cosmos DB stores numbers using **IEEE 754 double-precision 64-bit** format. This means integers larger than 2^53 and decimals requiring more than ~15-17 significant digits will lose precision silently.

**Incorrect (precision loss with large numbers):**

```csharp
// Anti-pattern 1: Storing large integers that exceed safe range
public class Transaction
{
    public string Id { get; set; }
    
    // 64-bit integer IDs from external systems - DANGER!
    public long ExternalTransactionId { get; set; }  // e.g., 9007199254740993
    // Values > 9,007,199,254,740,992 (2^53) lose precision
    // 9007199254740993 becomes 9007199254740992 silently!
}

// Anti-pattern 2: Financial calculations requiring exact decimal precision
public class Invoice
{
    public string Id { get; set; }
    
    // Double can't represent all decimal values exactly
    public double Amount { get; set; }  // 0.1 + 0.2 != 0.3 in IEEE 754
    public double TaxRate { get; set; }
}

// 99999999999999.99 stored as double may become 99999999999999.98
```

**Correct (preserving precision):**

```csharp
// Solution 1: Store large integers and precise decimals as strings
public class Transaction
{
    public string Id { get; set; }
    
    // Store large IDs as strings to preserve all digits
    [JsonPropertyName("externalTransactionId")]
    public string ExternalTransactionId { get; set; }  // "9007199254740993"
}

// Solution 2: Use string representation for financial amounts
public class Invoice
{
    public string Id { get; set; }
    
    // Store monetary values as strings with fixed decimal places
    [JsonPropertyName("amount")]
    public string Amount { get; set; }  // "99999999999999.99"
    
    [JsonPropertyName("taxRate")]
    public string TaxRate { get; set; }  // "0.0825"
    
    // Parse in application code for calculations
    public decimal GetAmount() => decimal.Parse(Amount);
    public decimal GetTaxRate() => decimal.Parse(TaxRate);
}
```

```csharp
// Solution 3: Store amounts as integer minor units (cents, paise, etc.)
public class Payment
{
    public string Id { get; set; }
    
    // Store $199.99 as 19999 cents - always safe as integer within 2^53
    public long AmountInCents { get; set; }
    public string Currency { get; set; }  // "USD"
    
    // Helper for display
    public decimal GetDisplayAmount() => AmountInCents / 100m;
}

var payment = new Payment
{
    Id = Guid.NewGuid().ToString(),
    AmountInCents = 19999,  // $199.99
    Currency = "USD"
};
await container.CreateItemAsync(payment);
```

Key points:
- **Safe integer range:** -2^53 to 2^53 (±9,007,199,254,740,992)
- **Significant digits:** ~15-17 decimal digits of precision
- Store large integers (snowflake IDs, blockchain hashes) as **strings**
- Store financial/monetary values as **strings** or **integer minor units** (cents)
- Numbers within the safe range (most counters, ages, quantities) are fine as-is

Reference: [Azure Cosmos DB service quotas - Per-item limits](https://learn.microsoft.com/azure/cosmos-db/concepts-limits#per-item-limits)

### 1.8 Reference Data When Items Grow Large

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

### 1.9 Use ID references with transient hydration for document relationships

**Impact: HIGH** (enables correct relationship handling without JOINs while preserving UI/API object access)

## Use ID References with Transient Hydration for Document Relationships

Cosmos DB has no cross-document JOINs. When entities need to reference each other, store relationship IDs as persistent fields and use transient (`@JsonIgnore`) properties for hydrated object access. A service layer populates the transient properties before rendering.

This pattern goes beyond basic referencing (see `model-reference-large`) by providing a **complete strategy for applications that need both document storage efficiency and runtime object graphs** (e.g., web apps with templates, REST APIs returning nested objects).

**Incorrect (JPA relationship annotations — no Cosmos equivalent):**

```java
@Entity
public class Vet {
    @Id
    private Integer id;

    @ManyToMany
    @JoinTable(name = "vet_specialties")
    private List<Specialty> specialties;  // JPA manages this relationship
}
```

**Also incorrect (embedding unbounded relationships directly):**

```java
@Container(containerName = "vets")
public class Vet {
    @Id
    private String id;

    // ❌ Stores full Specialty objects — grows unbounded, duplicates data
    private List<Specialty> specialties;
}
```

**Correct (ID references + transient hydration):**

```java
@Container(containerName = "vets")
public class Vet {

    @Id
    @GeneratedValue
    private String id;

    @PartitionKey
    private String partitionKey = "vet";

    private String firstName;
    private String lastName;

    // ✅ Persisted to Cosmos DB — stores only IDs
    private List<String> specialtyIds = new ArrayList<>();

    // ✅ Transient — NOT stored in Cosmos DB, populated by service layer
    @JsonIgnore
    private List<Specialty> specialties = new ArrayList<>();

    // Both getters needed
    public List<String> getSpecialtyIds() { return specialtyIds; }
    public List<Specialty> getSpecialties() { return specialties; }

    // Count methods should use the transient list when populated,
    // fall back to ID list
    public int getNrOfSpecialties() {
        return specialties.isEmpty() ? specialtyIds.size() : specialties.size();
    }
}
```

**When to use this pattern:**

| Scenario | Approach |
|----------|----------|
| Related data always read together, bounded size | **Embed** (see `model-embed-related`) |
| Related data read independently, unbounded | **ID reference** (this pattern) |
| UI/template needs object access to related data | **ID reference + transient hydration** (this pattern) |
| REST API returns nested objects | **ID reference + transient hydration** (this pattern) |
| Related data rarely accessed after write | **ID reference only** (no transient needed) |

**The transient hydration flow:**

1. **Entity stores** `List<String> specialtyIds` (persisted)
2. **Service layer** reads the entity, then looks up each ID to get full objects
3. **Service populates** `List<Specialty> specialties` (transient)
4. **Controller/template** accesses `vet.getSpecialties()` as if it were a normal object graph

**Important:** `@JsonIgnore` is correct here because transient properties should NOT be stored in Cosmos DB — they are populated on read by the service layer. This is the one legitimate use of `@JsonIgnore` (see `model-json-serialization` for when NOT to use it).

Reference: [Data modeling in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/modeling-data)

### 1.10 Version Your Document Schemas

**Impact: MEDIUM** (enables safe schema evolution)

## Version Your Document Schemas

Include schema version in documents to handle evolution gracefully. This enables safe migrations and backward-compatible reads.

For multi-entity or event-heavy workloads, apply this to **every persisted document type** (for example: metadata documents, events, telemetry records, and denormalized read models), not just top-level business entities.

Use a consistent field name such as `schemaVersion` (camelCase) and set it at write time so raw document checks, migrations, and mixed-version readers all work reliably.

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

### 1.11 Use Type Discriminators for Polymorphic Data

**Impact: MEDIUM** (enables efficient single-container design)

## Use Type Discriminators for Polymorphic Data

Use a single Cosmos DB container to co-locate related parent/child or different entity types when:
- similar entities are written and read together, share a natural or business partition key, require a simple transactional boundary, and do not exceed Cosmos DB partition key limits.

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

**When NOT to Use Multi-Entity Containers** :
   - Independent throughput requirements → Use separate containers
   - Different scaling patterns → Use separate containers
   - Different indexing needs → Use separate containers
   - Distinct change feed processing requirements → Use separate containers
   - Low access correlation (<20%) → Use separate containers

**Single-Container Anti-Patterns** :
   - "Everything container" → Complex filtering → Difficult analytics
   - One throughput allocation for all entity types
   - One change feed with mixed events requiring filtering
   - Difficult to maintain and onboard new developers

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

**Partition Limits (as of current Azure Cosmos DB documentation):**
   - Physical partition throughput limit: **10,000 RU/s** per physical partition  
     See [Azure Cosmos DB partitioning – physical partitions](https://learn.microsoft.com/azure/cosmos-db/partitioning-overview#physical-partitions).
   - Logical partition size limit: **20 GB** per logical partition  
     See [Azure Cosmos DB partitioning – logical partitions](https://learn.microsoft.com/azure/cosmos-db/partitioning-overview#logical-partitions).
   - Physical partition size: **50 GB** per physical partition  
     See [Azure Cosmos DB partitioning – physical partitions](https://learn.microsoft.com/azure/cosmos-db/partitioning-overview#physical-partitions).

   > These limits can evolve over time and may vary by region/offer. Always confirm against the latest Azure Cosmos DB documentation for your account.

**Popularity Skew Warning for Hot Partitions:** Even high-cardinality keys (like `user_id`) can create hot partitions when specific values get dramatically more traffic (e.g., a viral user during peak moments).

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

### 2.5 Choose Immutable Properties as Partition Keys

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

### 2.6 Respect Partition Key Value Length Limits

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

### 2.7 Align Partition Key with Query Patterns

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

### 2.8 Create Synthetic Partition Keys When Needed

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

## 3. Indexing Strategies

**Impact: MEDIUM-HIGH**

### 3.1 Composite Index Directions Must Match ORDER BY

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

### 3.2 Use Composite Indexes for ORDER BY

**Impact: HIGH** (enables sorted queries, reduces RU)

## Use Composite Indexes for ORDER BY

Create composite indexes for queries with ORDER BY on multiple properties. Without them, queries may fail or require expensive client-side sorting.

The default indexing policy indexes every property but does **not** create composite indexes. Any query that combines a `WHERE` equality filter with `ORDER BY` on a different field needs a composite index declared explicitly, or the query will either fail in production or require expensive client-side sorting.

> **Emulator warning:** The Cosmos DB emulator silently permits `ORDER BY` queries without a matching composite index and returns identical RU charges. Production containers reject the same query with *"The order by query does not have a corresponding composite index that it can be served from."* Always declare composite indexes at container-create time — do not rely on emulator success as validation.

> ⚠️ **CreateContainerIfNotExists warning:** Defining a composite index in `CreateContainerIfNotExists` (or `createIfNotExists`) only applies the indexing policy when the container is created for the first time. If the container already exists, Cosmos DB returns the existing container, silently ignores the indexing policy argument, and keeps the existing indexing policy unchanged. To update composite indexes on an existing container, read the container, update its `IndexingPolicy`, and replace the container resource using the SDK's container replace operation. Always read the container back and verify that the expected composite indexes are present.

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

### 3.3 Exclude Unused Index Paths

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

> ⚠️ **CreateContainerIfNotExists warning:** Custom indexing policies supplied to `CreateContainerIfNotExists` (or `createIfNotExists`) are applied only when the container is created. If the container already exists, the call succeeds, the indexing policy argument is ignored, and the existing indexing policy remains unchanged. To apply new included or excluded paths to an existing container, update the container's `IndexingPolicy` and replace the container resource using the SDK's container replace operation. After deployment, read the container definition back and verify that the expected included and excluded paths are present.

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

### 3.4 Understand Indexing Modes

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

### 3.5 Use Correct Indexing Path Syntax

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

### 3.6 Choose Appropriate Index Types

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

### 3.7 Add Spatial Indexes for Geo Queries

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

## 4. Query Optimization

**Impact: HIGH**

### 4.1 Compute min/max/avg with one scoped aggregate query

**Impact: HIGH** (prevents incorrect stats from partial reads or mismatched filters)

## Compute min/max/avg with one scoped aggregate query

For endpoint statistics, compute `MIN`, `MAX`, and `AVG` from the same filtered dataset in a single Cosmos DB query whenever possible. Avoid mixing values from separate queries, partial pages, or different time windows, which produces mathematically inconsistent results.

**Incorrect (client-side aggregation over partial or inconsistent data):**

```java
// ❌ Reads only first page and computes stats from incomplete data
CosmosPagedIterable<JsonNode> page = container.queryItems(
    "SELECT * FROM c WHERE c.deviceId = @deviceId",
    new CosmosQueryRequestOptions(),
    JsonNode.class
);

List<JsonNode> docs = page.stream().limit(50).toList(); // arbitrary subset
double min = docs.stream().mapToDouble(d -> d.get("temperature").asDouble()).min().orElse(0);
double max = docs.stream().mapToDouble(d -> d.get("temperature").asDouble()).max().orElse(0);
double avg = docs.stream().mapToDouble(d -> d.get("temperature").asDouble()).average().orElse(0);
```

```python
# ❌ Different filters per metric cause inconsistent results
min_q = "SELECT VALUE MIN(c.humidity) FROM c WHERE c.deviceId = @id"
max_q = "SELECT VALUE MAX(c.humidity) FROM c WHERE c.deviceId = @id AND c.timestamp > @start"
avg_q = "SELECT VALUE AVG(c.humidity) FROM c WHERE c.deviceId = @id AND c.timestamp > @start"
```

**Correct (single-pass aggregate query with consistent filters):**

```java
// ✅ One query, one filter set, consistent aggregate outputs
String sql = """
    SELECT
      MIN(c.temperature) AS minTemp,
      MAX(c.temperature) AS maxTemp,
      AVG(c.temperature) AS avgTemp,
      MIN(c.humidity) AS minHumidity,
      MAX(c.humidity) AS maxHumidity,
      AVG(c.humidity) AS avgHumidity
    FROM c
    WHERE c.deviceId = @deviceId
      AND c.timestamp >= @start
      AND c.timestamp <= @end
    """;
```

```python
# ✅ Use one scoped aggregate query
query = """
SELECT
  MIN(c.value) AS minValue,
  MAX(c.value) AS maxValue,
  AVG(c.value) AS avgValue
FROM c
WHERE c.entityId = @id AND c.timestamp >= @start AND c.timestamp <= @end
"""
```

Use a partition key aligned with the aggregation scope (for example, per-entity/per-device stats) so the query stays efficient and predictable.

Reference: [Aggregate functions in Azure Cosmos DB for NoSQL](https://learn.microsoft.com/azure/cosmos-db/nosql/query/aggregate-functions) | [Query performance tips](https://learn.microsoft.com/azure/cosmos-db/nosql/performance-tips-query-sdk)

### 4.2 Minimize Cross-Partition Queries

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

### Spring Data Cosmos — `@Query` methods bypass partition key routing

Spring Data Cosmos **does not** auto-route partition keys for `@Query`-annotated repository methods. Derived query methods (e.g., `findByTypeAndLeaderboardKey()`) are automatically scoped to the partition key, but `@Query` methods are **not** — they silently perform cross-partition scans even when the repository entity has a partition key annotation. The bug is invisible: queries return HTTP 200 with silently incorrect data (results from all partitions mixed together) and inflated RU charges.

For every `@Query` method, you must either:
1. **Add the partition key to the WHERE clause** explicitly, or
2. **Use a derived query method** instead of `@Query`

**Incorrect — `@Query` without partition key filter (silent cross-partition scan):**

```java
// ❌ Missing partition key filter — performs cross-partition scan
// Returns entries from ALL partitions mixed together (wrong data, high RU)
@Query("SELECT * FROM c WHERE c.type = @type")
List<LeaderboardEntry> findByType(@Param("type") String type);
```

**Correct — explicit partition key in `@Query` WHERE clause:**

```java
// ✅ Partition key included in WHERE clause — single-partition query
@Query("SELECT * FROM c WHERE c.type = @type AND c.leaderboardKey = @leaderboardKey")
List<LeaderboardEntry> findByTypeAndLeaderboardKey(
    @Param("type") String type,
    @Param("leaderboardKey") String leaderboardKey);
```

**Correct — derived query method (auto-routes partition key):**

```java
// ✅ Derived query method — Spring Data auto-routes to the correct partition
List<LeaderboardEntry> findByTypeAndLeaderboardKey(String type, String leaderboardKey);
```

Strategies to avoid cross-partition:
1. Include partition key in WHERE clause
2. Denormalize data to colocate in same partition
3. Create secondary containers with different partition keys for different access patterns
4. In Spring Data Cosmos, prefer derived query methods over `@Query` for automatic partition key routing

Reference: [Query patterns](https://learn.microsoft.com/azure/cosmos-db/nosql/query/getting-started)

### 4.3 Avoid Full Container Scans

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

### 4.4 Use DISTINCT keyword to eliminate duplicate results efficiently

**Impact: MEDIUM** (reduces bandwidth usage and RU consumption by eliminating duplicate results at the query engine level)

## Use DISTINCT keyword to eliminate duplicate results efficiently

**Impact: MEDIUM (reduces unnecessary data transfer and RU consumption)**

Azure Cosmos DB supports `SELECT DISTINCT` to eliminate duplicate values during query execution. Prefer using `DISTINCT` rather than retrieving all results and removing duplicates in application code, which increases network bandwidth, client-side processing, and RU consumption.

`DISTINCT` is particularly useful when returning unique property values such as categories, tags, statuses, or identifiers.

**Incorrect (client-side deduplication):**

```csharp
// Query returns duplicate category values
var query = "SELECT c.category FROM c";

var iterator = container.GetItemQueryIterator<dynamic>(query);

var categories = new HashSet<string>();

while (iterator.HasMoreResults)
{
    var response = await iterator.ReadNextAsync();

    foreach (var item in response)
    {
        categories.Add(item.category.ToString());
    }
}

// Duplicate elimination happens after all results
// have already been transferred to the client
```

**Correct (using DISTINCT in Cosmos DB):**

```csharp
// Cosmos DB removes duplicates before returning results
var query = "SELECT DISTINCT c.category FROM c";

var iterator = container.GetItemQueryIterator<dynamic>(query);

while (iterator.HasMoreResults)
{
    var response = await iterator.ReadNextAsync();

    foreach (var item in response)
    {
        Console.WriteLine(item.category);
    }
}
```

**Correct (using DISTINCT VALUE for scalar results):**

```sql
SELECT DISTINCT VALUE c.category
FROM c
```

### Additional considerations

- `DISTINCT` queries rely on indexes for efficient execution; ensure projected fields are indexed.
- `DISTINCT` queries across partitions still perform a fan-out query; prefer partition-scoped queries whenever possible to reduce RU consumption.
- Use `DISTINCT VALUE` when returning a single scalar field to simplify the result shape.

References:
- https://learn.microsoft.com/azure/cosmos-db/nosql/query/keywords#distinct

### 4.5 Query "latest" documents with explicit ORDER BY and TOP 1

**Impact: HIGH** (prevents stale or nondeterministic "latest item" results)

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

```python
# ❌ Client picks "first" item from an unordered query
query = "SELECT * FROM c WHERE c.userId = @uid"
items = list(container.query_items(
    query=query,
    parameters=[{"name": "@uid", "value": user_id}],
    enable_cross_partition_query=True
))
latest = items[0] if items else None
```

**Correct (explicit timestamp sort + TOP 1):**

```java
// ✅ Deterministic latest item by timestamp
String sql = """
    SELECT TOP 1 * FROM c
    WHERE c.deviceId = @deviceId AND IS_DEFINED(c.timestamp)
    ORDER BY c.timestamp DESC
    """;
SqlQuerySpec spec = new SqlQuerySpec(
    sql,
    List.of(new SqlParameter("@deviceId", deviceId))
);
```

```python
# ✅ Deterministic latest item
query = """
SELECT TOP 1 * FROM c
WHERE c.userId = @uid AND IS_DEFINED(c.createdAt)
ORDER BY c.createdAt DESC
"""
items = list(container.query_items(
    query=query,
    parameters=[{"name": "@uid", "value": user_id}],
    enable_cross_partition_query=True
))
latest = items[0] if items else None
```

If the query can span partitions, define the needed index policy for your filter + sort pattern (for example, a composite index when required by your query shape).

Reference: [ORDER BY in Azure Cosmos DB for NoSQL](https://learn.microsoft.com/azure/cosmos-db/nosql/query/order-by) | [TOP keyword](https://learn.microsoft.com/azure/cosmos-db/nosql/query/keywords#top)

### 4.6 Detect and Redirect Analytical Queries Away from Transactional Containers

**Impact: HIGH** (prevents RU starvation, 429 throttling cascades, and query timeouts)

## Detect and Redirect Analytical Queries Away from Transactional Containers

**Impact: HIGH (prevents RU starvation, 429 throttling cascades, and query timeouts)**

Cosmos DB's transactional store is optimized for OLTP: point reads, targeted queries within a partition, and bounded result sets. Analytical patterns — COUNT/SUM/AVG across all partitions, GROUP BY over unbounded data, or full-container scans for reporting — consume massive RU, trigger sustained 429 throttling that starves transactional operations, and can exceed the query execution timeout.

Do not run large aggregations, unbounded GROUP BY, or full-container scans against transactional Cosmos DB containers. For analytical workloads, use Azure Synapse Link with analytical store, Change Feed materialized views, or dedicated reporting containers.

Single-partition aggregations scoped to a known partition key with bounded data are acceptable — the concern is unbounded cross-partition scans.

**Correct (enable analytical store and run aggregations via Synapse Link — zero RU impact on transactional store):**

```csharp
// ✅ Enable analytical store on the container
var containerProperties = new ContainerProperties
{
    Id = "orders",
    PartitionKeyPath = "/customerId",
    AnalyticalStoreTimeToLiveInSeconds = -1  // Enable analytical store
};

// ✅ Run aggregations via Synapse Link (no RU consumed on transactional store)
// In Synapse SQL or Spark:
// SELECT region, COUNT(*) as orderCount, SUM(total) as revenue
// FROM cosmos_db.orders WHERE orderDate >= '2025-01-01' GROUP BY region
```

**Correct (pre-compute aggregates incrementally via Change Feed materialized views):**

```csharp
// ✅ Maintain real-time aggregations via Change Feed processor
public class SalesAggregate
{
    public string Id { get; set; }           // "category-electronics"
    public string PartitionKey { get; set; } // "aggregates"
    public string Category { get; set; }
    public long TotalSold { get; set; }
    public decimal AveragePrice { get; set; }
    public DateTime LastUpdated { get; set; }
}

// Dashboard reads pre-computed aggregates: 1 RU per point read
// Instead of recalculating from millions of source documents each time
```

**Correct (single-partition aggregation scoped to a known partition key is acceptable):**

```csharp
// ✅ Bounded, single-partition aggregation — acceptable cost
var query = new QueryDefinition(
    "SELECT VALUE COUNT(1) FROM c WHERE c.customerId = @cid AND c.status = 'pending'")
    .WithParameter("@cid", customerId);

var iterator = container.GetItemQueryIterator<int>(query,
    requestOptions: new QueryRequestOptions
    {
        PartitionKey = new PartitionKey(customerId)  // Scoped to ONE partition
    });
```

**Incorrect (unbounded aggregation across all partitions — fans out to every partition, massive RU):**

```csharp
// ❌ Unbounded aggregation across all partitions
var query = "SELECT c.region, COUNT(1) as orderCount, SUM(c.total) as revenue " +
            "FROM c WHERE c.orderDate >= '2025-01-01' GROUP BY c.region";

var iterator = container.GetItemQueryIterator<dynamic>(query);
// Fans out to ALL partitions, reads ALL matching documents
// At 10M orders: potentially 50,000+ RU per execution
// Blocks transactional traffic with sustained high RU consumption
```

**Incorrect (dashboard refreshing aggregations against transactional store):**

```python
# ❌ Dashboard refreshing aggregations against transactional store
def get_dashboard_metrics(self):
    queries = [
        "SELECT VALUE COUNT(1) FROM c",                           # Full scan
        "SELECT c.status, COUNT(1) FROM c GROUP BY c.status",     # Unbounded GROUP BY
        "SELECT VALUE AVG(c.responseTime) FROM c WHERE c.type = 'request'"  # Cross-partition AVG
    ]
    # Each query scans the entire container
    # Running these every 30 seconds for a dashboard = sustained throttling
```

**Incorrect (reporting query running against operational container):**

```java
// ❌ Reporting query running against operational container
@Query("SELECT c.category, SUM(c.quantity) as totalSold, AVG(c.price) as avgPrice " +
       "FROM c WHERE c.type = 'sale' GROUP BY c.category")
List<CategorySalesReport> getCategorySalesReport();
// Full cross-partition scan + aggregation — hundreds of thousands of RU
// Competes with real-time order processing for the same throughput budget
```

References:
- [Azure Synapse Link for Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/synapse-link)
- [Analytical store overview](https://learn.microsoft.com/azure/cosmos-db/analytical-store-introduction)
- [Change Feed materialized views pattern](https://learn.microsoft.com/azure/cosmos-db/nosql/change-feed-design-patterns#materialized-views)

### 4.7 Order Filters by Selectivity

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

### 4.8 Use Continuation Tokens for Pagination

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

```python
# ❌ Anti-pattern: OFFSET/LIMIT cost grows with page depth
async def get_scores_page_with_offset(container, player_id: str, page: int, page_size: int = 20):
    offset = (page - 1) * page_size
    query = (
        "SELECT * FROM c "
        "WHERE c.playerId = @playerId "
        "ORDER BY c.submittedAt DESC "
        f"OFFSET {offset} LIMIT {page_size}"
    )
    items = container.query_items(
        query=query,
        parameters=[{"name": "@playerId", "value": player_id}],
        partition_key=player_id,
    )
    return [item async for item in items]


# ✅ Preferred: continuation token pagination (stable RU per page)
async def get_scores_page(
    container,
    player_id: str,
    page_size: int = 20,
    continuation_token: str | None = None,
):
    query = (
        "SELECT * FROM c "
        "WHERE c.playerId = @playerId "
        "ORDER BY c.submittedAt DESC"
    )

    results = container.query_items(
        query=query,
        parameters=[{"name": "@playerId", "value": player_id}],
        partition_key=player_id,
        max_item_count=page_size,
    )

    pager = results.by_page(continuation_token=continuation_token)
    page = await pager.__anext__()
    items = [item async for item in page]

    return {
        "items": items,
        "continuationToken": pager.continuation_token,
    }
```

Python SDK note: Continuation tokens are supported for single-partition queries. Always set `partition_key` when using `by_page()`.

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

### ⚠️ Unbounded Query Anti-Pattern

**Fetching all results without any pagination is even worse than OFFSET/LIMIT.** This is commonly seen when developers skip pagination entirely, assuming result sets are small. At scale, unbounded queries cause:

- **Excessive RU consumption** — reading thousands of documents in one call
- **Timeouts** — queries exceeding the 5-second execution limit
- **Memory pressure** — loading all results into memory
- **Cascading failures** — high RU consumption triggers 429 throttling for other operations

```java
// ❌ Anti-pattern: No pagination — returns ALL matching documents
public List<Task> getTasksByProject(String tenantId, String projectId) {
    String query = "SELECT * FROM c WHERE c.tenantId = @tenantId " +
                   "AND c.type = 'task' AND c.projectId = @projectId";
    SqlQuerySpec spec = new SqlQuerySpec(query,
        Arrays.asList(new SqlParameter("@tenantId", tenantId),
                      new SqlParameter("@projectId", projectId)));
    // Returns ALL tasks — at 500 tasks/project this is wasteful,
    // at 50,000 tasks/project this causes timeouts
    return container.queryItems(spec, new CosmosQueryRequestOptions(), Task.class)
        .stream().collect(Collectors.toList());
}

// ✅ Correct: Return paginated results with continuation token
public PagedResult<Task> getTasksByProject(
        String tenantId, String projectId,
        int pageSize, String continuationToken) {
    String query = "SELECT * FROM c WHERE c.tenantId = @tenantId " +
                   "AND c.type = 'task' AND c.projectId = @projectId " +
                   "ORDER BY c.createdAt DESC";
    CosmosQueryRequestOptions options = new CosmosQueryRequestOptions();
    options.setMaxBufferedItemCount(pageSize);
    // Use iterableByPage for continuation token support
    CosmosPagedIterable<Task> results = container.queryItems(
        new SqlQuerySpec(query, params), options, Task.class);
    // Process first page only, return continuation token for next page
}
```

**Rule of thumb:** If a query can return more than 100 items, it **must** use pagination.

Reference: [Pagination in Azure Cosmos DB](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/query/pagination)

### 4.9 Use Parameterized Queries

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

**Rust (`azure_data_cosmos`):**

```rust
use azure_data_cosmos::Query;

// ✅ Parameterized query — safe and cacheable
let query = Query::from("SELECT * FROM c WHERE c.customerId = @customerId")
    .with_parameter("@customerId", customer_id)
    .unwrap();

// Multiple parameters
let query = Query::from(
    "SELECT * FROM c WHERE c.customerId = @cid AND c.status = @status ORDER BY c.createdAt DESC"
)
    .with_parameter("@cid", customer_id).unwrap()
    .with_parameter("@status", "active").unwrap();

// Aggregate query with parameters
let query = Query::from(
    "SELECT COUNT(1) AS totalOrders, SUM(c.total) AS totalSpent FROM c WHERE c.customerId = @cid"
)
    .with_parameter("@cid", customer_id).unwrap();
```

```rust
// ❌ Anti-pattern: String interpolation (no plan caching, injection risk)
let query = Query::from(format!(
    "SELECT * FROM c WHERE c.customerId = '{}'", customer_id
));
```

Reference: [Parameterized queries](https://learn.microsoft.com/azure/cosmos-db/nosql/query/parameterized-queries)

### 4.10 Use Point Reads Instead of Queries for Known ID and Partition Key

**Impact: HIGH** (1 RU vs ~2.5 RU per single-document lookup)

## Use Point Reads Instead of Queries for Known ID and Partition Key

When both the document `id` and partition key value are known, use a point read (`ReadItemAsync` / `read_item` / `readItem`) instead of a query. A point read costs 1 RU for a 1 KB document and bypasses the query engine entirely. An equivalent `SELECT * FROM c WHERE c.id = @id` query costs ~2.5 RU because the query engine still parses, optimizes, and executes even though the result is a single document.

**Incorrect (query when both id and partition key are known):**

```csharp
// ❌ Uses query engine when a point read would suffice
var query = new QueryDefinition("SELECT * FROM c WHERE c.id = @id")
    .WithParameter("@id", orderId);

var iterator = container.GetItemQueryIterator<Order>(query,
    requestOptions: new QueryRequestOptions
    {
        PartitionKey = new PartitionKey(customerId)
    });

var response = await iterator.ReadNextAsync();
return response.FirstOrDefault();
// Cost: ~2.5 RU for a 1 KB document (query engine overhead)
```

```python
# ❌ Query instead of point read
def get_player(self, player_id: str, game_id: str):
    query = "SELECT * FROM c WHERE c.id = @id"
    items = list(self.container.query_items(
        query=query,
        parameters=[{"name": "@id", "value": player_id}],
        partition_key=game_id
    ))
    return items[0] if items else None
    # Unnecessary query engine invocation
```

```typescript
// ❌ Query instead of point read — id and partition key both known
const { resources } = await container.items
  .query<Order>({
    query: 'SELECT * FROM c WHERE c.id = @id',
    parameters: [{ name: '@id', value: orderId }],
  }, { partitionKey: userId })
  .fetchAll();
return resources[0] ?? null;
// ~2.92 RU — goes through the query engine for a single known document
```

**Correct (point read — bypasses query engine):**

```csharp
// ✅ Point read — 1 RU for a 1 KB document, no query engine overhead
var response = await container.ReadItemAsync<Order>(
    orderId,
    new PartitionKey(customerId));
return response.Resource;
```

```python
# ✅ Point read — 1 RU, no query engine overhead
def get_player(self, player_id: str, game_id: str):
    return self.container.read_item(item=player_id, partition_key=game_id)
```

```java
// ✅ Point read in Java SDK
CosmosItemResponse<Order> response = container.readItem(
    orderId,
    new PartitionKey(customerId),
    Order.class);
return response.getItem();
```

```typescript
// ✅ Point read in Node.js — 1 RU, no query engine overhead
const { resource: order } = await container.item(orderId, userId).read<Order>();
return order ?? null;
```

```rust
// ✅ Point read in Rust (azure_data_cosmos) — 1 RU, no query engine
use azure_data_cosmos::PartitionKey;

let container = cosmos.database_client("db").container_client("orders").await;
let pk = PartitionKey::from(customer_id.to_string());
let response = container.read_item::<serde_json::Value>(pk, &order_id, None).await;
match response {
    Ok(item) => {
        let order: Order = serde_json::from_value(item.into_body()).unwrap();
        // Cost: 1 RU for a 1 KB document
    }
    Err(e) if e.http_status() == Some(azure_core::http::StatusCode::NotFound) => {
        // Document not found
    }
    Err(e) => return Err(e),
}
```

### Multiple Known Documents — ReadMany vs. Parallel Point Reads

When fetching multiple documents by known `(id, partitionKey)` pairs, you have two options:

1. **Client-side parallel point reads** — issue individual `ReadItem` calls concurrently
2. **ReadMany** — batch all `(id, partitionKey)` pairs into a single SDK call

ReadMany targets only the relevant partitions and avoids the query engine, but the performance tradeoff depends on batch size, client resources, and document size. Small batches can be slower than aggressively parallel point reads on a well-provisioned client, while larger batches tend to reduce both latency and RU cost. **Benchmark both approaches** with your actual workload before committing to one.

**⚠️ Avoid using OR/IN queries across partition keys — these fan out to all partitions regardless of how many documents you need:**

```csharp
// ❌ OR/IN clause spanning multiple partition keys — cross-partition fan-out
var query = new QueryDefinition(
    "SELECT * FROM c WHERE c.id IN (@id1, @id2, @id3)")
    .WithParameter("@id1", "order-1")
    .WithParameter("@id2", "order-2")
    .WithParameter("@id3", "order-3");
// Fans out to ALL partitions to find 3 documents — RU scales with partition count
```

**✅ ReadMany — targeted reads, no fan-out (best for larger batches; benchmark for your workload):**

```csharp
// ✅ ReadMany — targets only relevant partitions
var items = new List<(string id, PartitionKey partitionKey)>
{
    ("order-1", new PartitionKey("customer-a")),
    ("order-2", new PartitionKey("customer-b")),
    ("order-3", new PartitionKey("customer-a"))
};

var response = await container.ReadManyItemsAsync<Order>(items);
// Consistent cost — no cross-partition fan-out
```

```python
# ✅ ReadMany in Python SDK
items_to_read = [
    ("order-1", "customer-a"),
    ("order-2", "customer-b"),
    ("order-3", "customer-a")
]
results = container.read_many_items(item_identities=items_to_read)
```

**✅ Parallel point reads — alternative for small batches on well-provisioned clients:**

```csharp
// ✅ Parallel point reads — can outperform ReadMany for small batches
var tasks = new[]
{
    container.ReadItemAsync<Order>("order-1", new PartitionKey("customer-a")),
    container.ReadItemAsync<Order>("order-2", new PartitionKey("customer-b")),
    container.ReadItemAsync<Order>("order-3", new PartitionKey("customer-a"))
};

var responses = await Task.WhenAll(tasks);
```

```typescript
// ❌ OR/IN across partitions — fans out to every partition
const { resources } = await container.items.query<Order>({
  query: 'SELECT * FROM c WHERE c.id IN (@a, @b, @c)',
  parameters: [
    { name: '@a', value: 'order-1' },
    { name: '@b', value: 'order-2' },
    { name: '@c', value: 'order-3' },
  ],
}).fetchAll();

// ✅ Parallel point reads (@azure/cosmos v4 does not expose readMany;
//    use bounded-concurrency parallel reads for batched lookups)
const results = await Promise.all([
  container.item('order-1', 'user-alice').read<Order>(),
  container.item('order-2', 'user-bob').read<Order>(),
  container.item('order-3', 'user-alice').read<Order>(),
]);
return results.map(r => r.resource).filter(Boolean);
// Total RU ≈ N × 1.0; bound concurrency with a limiter for larger batches
```

### Validate parent existence with a point read before writing child records

When writing a child/event document that references a parent entity (for example, reading → device, line item → order), do a parent point read first if your API requires rejecting unknown parents. This keeps referential checks cheap and avoids orphaned documents.

```java
// ✅ Fast referential validation (1 RU point read) before write
try {
    container.readItem(deviceId, new PartitionKey(deviceId), Device.class);
} catch (CosmosException ex) {
    if (ex.getStatusCode() == 404) {
        throw new IllegalArgumentException("Unknown deviceId");
    }
    throw ex;
}
// write telemetry only after parent exists
```

```python
# ❌ No existence check: creates orphan child records
container.upsert_item({"id": event_id, "deviceId": device_id, "value": 42})
```

### When to Use Each Approach

| Scenario | Approach |
|----------|----------|
| Single document with known id and partition key | **ReadItem** (point read) |
| Multiple documents with known (id, partitionKey) pairs — large batch | **ReadMany** (benchmark to confirm) |
| Multiple documents with known (id, partitionKey) pairs — small batch | **Parallel point reads** or **ReadMany** (benchmark both) |
| Need filtering, sorting, projection, or aggregation | **Query** |
| Exact ids and partition keys are not known | **Query** |

Reference: [Point reads in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-read-item) | [ReadMany — read multiple items](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-dotnet-read-item#read-multiple-items) | [Read many items fast (Java)](https://devblogs.microsoft.com/cosmosdb/read-many-items-fast-with-the-java-sdk-for-azure-cosmos-db/)

### 4.11 Parameterize TOP Values Safely

**Impact: HIGH** (prevents incorrect query guidance and keeps parameterization secure)

## Parameterize TOP Values Safely

Cosmos DB SQL supports both literal and parameterized values for `TOP`. Prefer parameterized `TOP` values for consistency with secure query practices. Ensure the parameter value is an integer.

**Incorrect (string interpolation for TOP):**

```python
# Avoid string interpolation when parameterization works
top = int(top)
query = f"SELECT TOP {top} * FROM c ORDER BY c.score DESC"
items = container.query_items(query, enable_cross_partition_query=True)
```

```csharp
// Avoid interpolating TOP directly when parameters are available
int topN = 10;
var query = new QueryDefinition($"SELECT TOP {topN} * FROM c ORDER BY c.score DESC");
```

**Correct (parameterized TOP):**

```python
# TOP can be parameterized
query = "SELECT TOP @top * FROM c ORDER BY c.score DESC"
params = [{"name": "@top", "value": int(top)}]
items = container.query_items(query, parameters=params, enable_cross_partition_query=True)
```

```csharp
var query = new QueryDefinition("SELECT TOP @top * FROM c ORDER BY c.score DESC")
    .WithParameter("@top", 10);
```

```python
# Keep all query values parameterized, including TOP
query = "SELECT TOP @top * FROM c WHERE c.gameId = @gameId ORDER BY c.score DESC"
params = [
    {"name": "@top", "value": int(top)},
    {"name": "@gameId", "value": game_id},
]
items = container.query_items(query, parameters=params, enable_cross_partition_query=True)
```

Use a literal integer in `TOP` only when it is genuinely constant at authoring time (for example, `TOP 10`).

References:
- [Parameterized queries](https://learn.microsoft.com/azure/cosmos-db/nosql/query/parameterized-queries)
- [SQL query TOP keyword](https://learn.microsoft.com/azure/cosmos-db/nosql/query/select#top-keyword)

### 4.12 Project Only Needed Fields

**Impact: HIGH** (reduces payload size, network bandwidth, and client memory; RU savings scale with document size (negligible on small flat docs, substantial on multi-KB/MB documents and large result sets))

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

// Substantial payload-size reduction; RU savings depend on document size
// (significant on large/nested docs, negligible on small flat docs)
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

### Prefer dedicated result types for projections

When projecting fields, prefer deserializing into a dedicated DTO or record whose properties match the projected fields rather than reusing the full document model class. A dedicated result type makes the projection self-documenting, avoids confusion from null/default-valued properties that were not projected, and reduces the chance of developers reverting to `SELECT *` over time.

```csharp
// ✅ Preferred: Dedicated DTO matches projected fields exactly
public class OrderSummary
{
    public string Id { get; set; }
    public DateTime OrderDate { get; set; }
    public decimal Total { get; set; }
    public string Status { get; set; }
}

var iterator = container.GetItemQueryIterator<OrderSummary>(  // ✅ Matches projection
    new QueryDefinition(query).WithParameter("@cid", customerId));
```

```java
// ✅ Preferred: Dedicated projection record in Java
public record PlayerSummary(String id, String playerName, int score) {}

@Query("SELECT c.id, c.playerName, c.score FROM c WHERE c.leaderboardKey = @key")
List<PlayerSummary> getTopPlayers(@Param("key") String key);
```

⚠️ Deserializing projected results into the full entity type is acceptable when the entity is small, the unprojected fields are not misleading, or the surrounding framework expects that type (e.g., Spring Data repository methods, EF Core entities). In these cases, ensure the intent is clear through comments or naming so that future maintainers do not mistakenly revert to `SELECT *`.

### Node.js / TypeScript (@azure/cosmos v4)

```typescript
// ❌ Anti-pattern: SELECT * pulls every field including future additions
const bad = {
  query: 'SELECT * FROM c WHERE c.userId = @userId ORDER BY c.createdAt DESC',
  parameters: [{ name: '@userId', value: userId }],
};

// ✅ Preferred: project only the fields the caller consumes
const good = {
  query: `
    SELECT c.id, c.userId, c.status, c.total, c.createdAt
    FROM c
    WHERE c.userId = @userId
    ORDER BY c.createdAt DESC
  `,
  parameters: [{ name: '@userId', value: userId }],
};

// TypeScript: dedicated result type matches the projected fields
interface OrderSummary {
  id: string;
  userId: string;
  status: string;
  total: number;
  createdAt: string;
}
const { resources } = await container.items
  .query<OrderSummary>(good, { partitionKey: userId })
  .fetchAll();

// Single-column scalar with SELECT VALUE
const { resources: statuses } = await container.items
  .query<string>({
    query: 'SELECT VALUE c.status FROM c WHERE c.userId = @u',
    parameters: [{ name: '@u', value: userId }],
  }, { partitionKey: userId })
  .fetchAll();
```

Savings multiply with:
- Large documents (MB-sized)
- Large result sets
- High query frequency

Reference: [Project fields in queries](https://learn.microsoft.com/azure/cosmos-db/nosql/query/select)

---

## 5. Design Patterns

**Impact: HIGH**

### 5.1 Use Change Feed for cross-partition query optimization with materialized views

**Impact: HIGH** (eliminates cross-partition query overhead for admin/analytics scenarios)

## Use Change Feed for Materialized Views or Global Secondary Index

When your application requires frequent cross-partition queries (e.g., admin dashboards, analytics, frequent lookups by secondary non-PK attributes), you have two main options: use Change Feed to maintain materialized views in a separate container optimized for those query patterns, or use the new Global Secondary Index (GSI).

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

**⚠️ Change Feed delivers events at-least-once.** Your handler MUST be idempotent — processing the same event twice must produce the same result. Never use `counter += 1` or `get() + 1` patterns in Change Feed handlers, as event replay will silently double-count.

**Incorrect — non-idempotent handler (counter drift on replay):**

```java
// ❌ WRONG — at-least-once replay doubles counts
private void handleChanges(List<JsonNode> changes, ChangeFeedProcessorContext context) {
    for (JsonNode node : changes) {
        GameScore score = objectMapper.treeToValue(node, GameScore.class);
        PlayerProfile profile = playerRepository.findById(score.getPlayerId()).orElseGet(PlayerProfile::new);
        profile.setTotalGamesPlayed(profile.getTotalGamesPlayed() + 1); // NON-IDEMPOTENT
        profile.setTotalScore(profile.getTotalScore() + score.getScore()); // NON-IDEMPOTENT
        playerRepository.save(profile);
    }
}
```

```csharp
// ❌ WRONG — same problem in .NET
async Task HandleChangesAsync(IReadOnlyCollection<GameScore> changes, CancellationToken ct)
{
    foreach (var score in changes)
    {
        var profile = await GetProfileAsync(score.PlayerId);
        profile.TotalGamesPlayed += 1;  // NON-IDEMPOTENT
        profile.TotalScore += score.Score;  // NON-IDEMPOTENT
        await SaveProfileAsync(profile);
    }
}
```

**Correct — idempotent alternatives:**

Use one of these patterns to ensure safe replay:

**1. Replace pattern — write absolute values, not deltas:**

```java
// ✅ CORRECT — replace with absolute value from the event
private void handleChanges(List<JsonNode> changes, ChangeFeedProcessorContext context) {
    for (JsonNode node : changes) {
        GameScore score = objectMapper.treeToValue(node, GameScore.class);
        PlayerProfile profile = playerRepository.findById(score.getPlayerId()).orElseGet(PlayerProfile::new);
        // Idempotent: same event replayed produces same result
        profile.setHighScore(Math.max(profile.getHighScore(), score.getScore()));
        playerRepository.save(profile);
    }
}
```

**2. Conditional write — use ETags to detect duplicate processing:**

```csharp
// ✅ CORRECT — ETag prevents duplicate processing
async Task HandleChangesAsync(IReadOnlyCollection<GameScore> changes, CancellationToken ct)
{
    foreach (var score in changes)
    {
        var response = await container.ReadItemAsync<PlayerProfile>(
            score.PlayerId, new PartitionKey(score.PlayerId));
        var profile = response.Resource;
        profile.HighScore = Math.Max(profile.HighScore, score.Score);
        await container.ReplaceItemAsync(profile, profile.Id,
            new PartitionKey(profile.Id),
            new ItemRequestOptions { IfMatchEtag = response.ETag });
    }
}
```

**3. Mark-and-rebuild — flag affected records and recalculate from source of truth:**

```python
# ✅ CORRECT — mark dirty and rebuild from source data
async def handle_changes(changes):
    for change in changes:
        player_id = change["playerId"]
        # Mark the profile as needing recalculation
        await profiles_container.patch_item(
            item=player_id,
            partition_key=player_id,
            patch_operations=[
                {"op": "set", "path": "/needsRecalc", "value": True}
            ]
        )
    # Separate process recalculates from source of truth
```

| Idempotent Pattern | When to Use | Trade-off |
|--------------------|-------------|-----------|
| Replace (absolute value) | High scores, latest status, max/min values | Only works for non-cumulative data |
| Conditional write (ETag) | Any update where you can detect duplicates | Extra read + possible retry on conflict |
| Mark-and-rebuild | Counters, aggregations, cumulative totals | Higher latency, requires rebuild process |

**Key Points:**
- **Change Feed delivers at-least-once** — handlers MUST be idempotent
- Change Feed provides reliable, ordered event stream of all document changes
- Materialized views trade storage cost for query efficiency
- Updates are eventually consistent (typically <1 second delay)
- Use lease container to track processor progress (enables resume after failures)
- Never use `counter += 1`, `total += value`, or `get() + 1` patterns in Change Feed handlers
- Consider Azure Functions with Cosmos DB trigger for serverless implementation
- Consider Global Secondary Index (GSI) implementation as alternative for automatic sync between containers with different partition keys

Reference(s): 
[Change feed in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/change-feed)
[Change feed design patterns in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/change-feed-design-patterns)
[Global Secondary Indexes (GSI) in Azure Cosmos DB](https://learn.microsoft.com/en-us/azure/cosmos-db/global-secondary-indexes)

### 5.2 Use count-based or cached rank approaches instead of full partition scans for ranking

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

### 5.3 Use a service layer to hydrate document references before rendering

**Impact: HIGH** (bridges document storage with frameworks expecting object graphs, prevents empty/null relationship data)

## Use a Service Layer to Hydrate Document References

When using ID-based references between Cosmos DB documents (see `model-relationship-references`), create a service layer that populates transient relationship properties before returning entities to controllers, templates, or API responses. Never return repository results directly to the presentation layer without hydrating relationships.

**Incorrect (controller accesses repository directly — empty relationships):**

```java
@Controller
public class VetController {

    @Autowired
    private VetRepository vetRepository;

    @GetMapping("/vets")
    public String listVets(Model model) {
        // ❌ Returns vets with specialtyIds populated but specialties list empty
        List<Vet> vets = StreamSupport
            .stream(vetRepository.findAll().spliterator(), false)
            .collect(Collectors.toList());
        model.addAttribute("vets", vets);
        return "vets/vetList";
        // Template calls vet.getSpecialties() → empty list!
    }
}
```

**Correct (service layer hydrates relationships):**

```java
@Service
public class VetService {

    private final VetRepository vetRepository;
    private final SpecialtyRepository specialtyRepository;

    public VetService(VetRepository vetRepository,
                      SpecialtyRepository specialtyRepository) {
        this.vetRepository = vetRepository;
        this.specialtyRepository = specialtyRepository;
    }

    public List<Vet> findAll() {
        List<Vet> vets = StreamSupport
            .stream(vetRepository.findAll().spliterator(), false)
            .collect(Collectors.toList());
        vets.forEach(this::populateRelationships);
        return vets;
    }

    public Optional<Vet> findById(String id) {
        return vetRepository.findById(id)
            .map(vet -> {
                populateRelationships(vet);
                return vet;
            });
    }

    private void populateRelationships(Vet vet) {
        if (vet.getSpecialtyIds() != null && !vet.getSpecialtyIds().isEmpty()) {
            List<Specialty> specialties = vet.getSpecialtyIds()
                .stream()
                .map(specialtyRepository::findById)
                .filter(Optional::isPresent)
                .map(Optional::get)
                .collect(Collectors.toList());
            vet.setSpecialties(specialties);
        }
    }
}
```

**Controller uses the service:**

```java
@Controller
public class VetController {

    @Autowired
    private VetService vetService;  // ✅ Service, not repository

    @GetMapping("/vets")
    public String listVets(Model model) {
        List<Vet> vets = vetService.findAll();
        model.addAttribute("vets", vets);  // ✅ Relationships are populated
        return "vets/vetList";
    }
}
```

**When this pattern is required:**

- **Template engines** (Thymeleaf, JSP, Freemarker) that access `entity.relatedObjects`
- **REST APIs** that return nested JSON with related objects
- **Any presentation layer** that expects an object graph from the persistence layer

**Without this pattern** you will see:
- Empty lists where related objects should appear
- `Property or field 'specialties' cannot be found` errors in Thymeleaf
- `EL1008E` Spring Expression Language errors
- Null/empty data in API responses where relationships should appear

**Key rules:**

1. **Every controller method that returns entities for rendering must use the service layer** — never call repositories directly
2. **Populate ALL transient properties** used by templates or API serializers
3. **Service methods returning collections** must hydrate each entity in the list
4. **Service methods returning single entities** must hydrate before returning

**Performance consideration:** This pattern causes N+1 queries (one per reference ID). For large collections, consider batch lookups:

```java
// Batch lookup instead of N individual findById calls
private void populateRelationships(Vet vet) {
    if (vet.getSpecialtyIds() != null && !vet.getSpecialtyIds().isEmpty()) {
        // Use a single query with IN clause
        List<Specialty> specialties = specialtyRepository
            .findAllById(vet.getSpecialtyIds());
        vet.setSpecialties(specialties);
    }
}
```

For truly high-volume scenarios, consider denormalizing the data instead (see `model-denormalize-reads`) or using Change Feed to maintain materialized views (see `pattern-change-feed-materialized-views`).

Reference: [Data modeling in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/modeling-data)

---

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
