# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Best practices for Azure Cosmos DB data modeling: embedding vs referencing, document size limits, schema versioning, type discriminators, JSON serialization, and denormalization strategies.

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

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
