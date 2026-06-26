# Azure Cosmos DB Best Practices

**Version 1.1.0**  
CosmosDB Agent Kit  
January 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Performance optimization and best practices guide for Azure Cosmos DB applications, ordered by impact. Contains rules for data modeling, partition key design, query optimization, SDK usage, indexing, throughput management, global distribution, monitoring, developer tooling, and vector search.

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
3. [Query Optimization](#3-query-optimization) — **HIGH**
   - 3.1 [Compute min/max/avg with one scoped aggregate query](#31-compute-min-max-avg-with-one-scoped-aggregate-query)
   - 3.2 [Minimize Cross-Partition Queries](#32-minimize-cross-partition-queries)
   - 3.3 [Avoid Full Container Scans](#33-avoid-full-container-scans)
   - 3.4 [Use DISTINCT keyword to eliminate duplicate results efficiently](#34-use-distinct-keyword-to-eliminate-duplicate-results-efficiently)
   - 3.5 [Query "latest" documents with explicit ORDER BY and TOP 1](#35-query-latest-documents-with-explicit-order-by-and-top-1)
   - 3.6 [Detect and Redirect Analytical Queries Away from Transactional Containers](#36-detect-and-redirect-analytical-queries-away-from-transactional-containers)
   - 3.7 [Order Filters by Selectivity](#37-order-filters-by-selectivity)
   - 3.8 [Use Continuation Tokens for Pagination](#38-use-continuation-tokens-for-pagination)
   - 3.9 [Use Parameterized Queries](#39-use-parameterized-queries)
   - 3.10 [Use Point Reads Instead of Queries for Known ID and Partition Key](#310-use-point-reads-instead-of-queries-for-known-id-and-partition-key)
   - 3.11 [Parameterize TOP Values Safely](#311-parameterize-top-values-safely)
   - 3.12 [Project Only Needed Fields](#312-project-only-needed-fields)
4. [SDK Best Practices](#4-sdk-best-practices) — **HIGH**
   - 4.1 [Use Async APIs for Better Throughput](#41-use-async-apis-for-better-throughput)
   - 4.2 [Configure Threshold-Based Availability Strategy (Hedging)](#42-configure-threshold-based-availability-strategy-hedging-)
   - 4.3 [Configure Partition-Level Circuit Breaker](#43-configure-partition-level-circuit-breaker)
   - 4.4 [Use IfNoneMatchETag("*") for conditional creates to prevent duplicates](#44-use-ifnonematchetag-for-conditional-creates-to-prevent-duplicates)
   - 4.5 [Use Direct Connection Mode for Production](#45-use-direct-connection-mode-for-production)
   - 4.6 [Guard against empty continuation tokens before calling byPage](#46-guard-against-empty-continuation-tokens-before-calling-bypage)
   - 4.7 [Log Diagnostics for Troubleshooting](#47-log-diagnostics-for-troubleshooting)
   - 4.8 [Use Microsoft.Azure.Cosmos package, not abandoned Azure.Cosmos](#48-use-microsoft-azure-cosmos-package-not-abandoned-azure-cosmos)
   - 4.9 [Avoid Microsoft.Azure.Cosmos namespace collisions with domain models](#49-avoid-microsoft-azure-cosmos-namespace-collisions-with-domain-models)
   - 4.10 [Configure SSL and connection mode for Cosmos DB Emulator](#410-configure-ssl-and-connection-mode-for-cosmos-db-emulator)
   - 4.11 [Use ETags for optimistic concurrency on read-modify-write operations](#411-use-etags-for-optimistic-concurrency-on-read-modify-write-operations)
   - 4.12 [Configure Excluded Regions for Dynamic Failover](#412-configure-excluded-regions-for-dynamic-failover)
   - 4.13 [Use current Go Cosmos DB SDK versions and explicit partition-key metadata](#413-use-current-go-cosmos-db-sdk-versions-and-explicit-partition-key-metadata)
   - 4.14 [Unwrap CosmosItemResponse and enable content response in Java SDK](#414-unwrap-cosmositemresponse-and-enable-content-response-in-java-sdk)
   - 4.15 [Use dependent @Bean methods for Cosmos DB initialization in Spring Boot](#415-use-dependent-bean-methods-for-cosmos-db-initialization-in-spring-boot)
   - 4.16 [Spring Boot and Java version compatibility for Cosmos DB SDK](#416-spring-boot-and-java-version-compatibility-for-cosmos-db-sdk)
   - 4.17 [Initialize Async Cosmos DB Container Before CosmosDBSaver](#417-initialize-async-cosmos-db-container-before-cosmosdbsaver)
   - 4.18 [Use CosmosDBSaver for LangGraph Checkpointing](#418-use-cosmosdbsaver-for-langgraph-checkpointing)
   - 4.19 [Use AzureCosmosDBNoSQLChatMessageHistory for Persistent Conversations in JS/TS](#419-use-azurecosmosdbnosqlchatmessagehistory-for-persistent-conversations-in-js-ts)
   - 4.20 [Configure Azure OpenAI Embedding Deployment Name for JS/TS LangChain](#420-configure-azure-openai-embedding-deployment-name-for-js-ts-langchain)
   - 4.21 [Prevent Filter Injection in JS/TS LangChain Vector Store Queries](#421-prevent-filter-injection-in-js-ts-langchain-vector-store-queries)
   - 4.22 [Configure Full-Text Prerequisites Before JS/TS LangChain Hybrid Search](#422-configure-full-text-prerequisites-before-js-ts-langchain-hybrid-search)
   - 4.23 [Use Managed Identity for JS/TS LangChain Cosmos DB Integration](#423-use-managed-identity-for-js-ts-langchain-cosmos-db-integration)
   - 4.24 [Choose the Correct Search Type for JS/TS LangChain Vector Store](#424-choose-the-correct-search-type-for-js-ts-langchain-vector-store)
   - 4.25 [Use AzureCosmosDBNoSQLSemanticCache for LLM Cost Reduction in JS/TS](#425-use-azurecosmosdbnosqlsemanticcache-for-llm-cost-reduction-in-js-ts)
   - 4.26 [Correctly Initialize AzureCosmosDBNoSQLVectorStore in JavaScript/TypeScript](#426-correctly-initialize-azurecosmosdbnosqlvectorstore-in-javascript-typescript)
   - 4.27 [Use Persistent MCP Client Sessions for Multi-Agent Applications](#427-use-persistent-mcp-client-sessions-for-multi-agent-applications)
   - 4.28 [Handle MCP ToolMessage Content Format Variations](#428-handle-mcp-toolmessage-content-format-variations)
   - 4.29 [Filter MCP Tools by Name Prefix for Agent Assignment](#429-filter-mcp-tools-by-name-prefix-for-agent-assignment)
   - 4.30 [Configure local development environment to avoid cloud connection conflicts](#430-configure-local-development-environment-to-avoid-cloud-connection-conflicts)
   - 4.31 [Explicitly reference Newtonsoft.Json package](#431-explicitly-reference-newtonsoft-json-package)
   - 4.32 [Use the Patch API for atomic counter increments](#432-use-the-patch-api-for-atomic-counter-increments)
   - 4.33 [Configure Preferred Regions for Availability](#433-configure-preferred-regions-for-availability)
   - 4.34 [Include aiohttp When Using Python Async SDK](#434-include-aiohttp-when-using-python-async-sdk)
   - 4.35 [Never share a single CosmosItemRequestOptions instance across multiple createItem calls](#435-never-share-a-single-cosmositemrequestoptions-instance-across-multiple-createitem-calls)
   - 4.36 [Handle 429 Errors with Retry-After](#436-handle-429-errors-with-retry-after)
   - 4.37 [Use consistent enum serialization between Cosmos SDK and application layer](#437-use-consistent-enum-serialization-between-cosmos-sdk-and-application-layer)
   - 4.38 [Reuse CosmosClient as Singleton](#438-reuse-cosmosclient-as-singleton)
   - 4.39 [Annotate entities for Spring Data Cosmos with @Container, @PartitionKey, and String IDs](#439-annotate-entities-for-spring-data-cosmos-with-container-partitionkey-and-string-ids)
   - 4.40 [Use CosmosRepository correctly and handle Iterable return types](#440-use-cosmosrepository-correctly-and-handle-iterable-return-types)
5. [Indexing Strategies](#5-indexing-strategies) — **MEDIUM-HIGH**
   - 5.1 [Composite Index Directions Must Match ORDER BY](#51-composite-index-directions-must-match-order-by)
   - 5.2 [Use Composite Indexes for ORDER BY](#52-use-composite-indexes-for-order-by)
   - 5.3 [Exclude Unused Index Paths](#53-exclude-unused-index-paths)
   - 5.4 [Understand Indexing Modes](#54-understand-indexing-modes)
   - 5.5 [Use Correct Indexing Path Syntax](#55-use-correct-indexing-path-syntax)
   - 5.6 [Choose Appropriate Index Types](#56-choose-appropriate-index-types)
   - 5.7 [Add Spatial Indexes for Geo Queries](#57-add-spatial-indexes-for-geo-queries)
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
   - 9.1 [Use Point Reads for AI-Grounding and RAG Retrieval When ID Is Known](#91-use-point-reads-for-ai-grounding-and-rag-retrieval-when-id-is-known)
   - 9.2 [Use Background Tasks for Non-Blocking Chat History Storage](#92-use-background-tasks-for-non-blocking-chat-history-storage)
   - 9.3 [Use Change Feed for cross-partition query optimization with materialized views](#93-use-change-feed-for-cross-partition-query-optimization-with-materialized-views)
   - 9.4 [Use count-based or cached rank approaches instead of full partition scans for ranking](#94-use-count-based-or-cached-rank-approaches-instead-of-full-partition-scans-for-ranking)
   - 9.5 [Tag AI Messages with Agent Name for API Response Attribution](#95-tag-ai-messages-with-agent-name-for-api-response-attribution)
   - 9.6 [Persist Active Agent in Cosmos DB for Deterministic Routing](#96-persist-active-agent-in-cosmos-db-for-deterministic-routing)
   - 9.7 [Wrap Cosmos DB Sync Calls in asyncio.to_thread for LangGraph Routing Functions](#97-wrap-cosmos-db-sync-calls-in-asyncio-to-thread-for-langgraph-routing-functions)
   - 9.8 [Use asyncio.to_thread for Active Agent Writes in LangGraph Node Functions](#98-use-asyncio-to-thread-for-active-agent-writes-in-langgraph-node-functions)
   - 9.9 [Store Chat History Separately from LangGraph Checkpoints](#99-store-chat-history-separately-from-langgraph-checkpoints)
   - 9.10 [Initialize LangGraph Agents in FastAPI Startup with Retry](#910-initialize-langgraph-agents-in-fastapi-startup-with-retry)
   - 9.11 [Use LangGraph Interrupt for Human-in-the-Loop Confirmation](#911-use-langgraph-interrupt-for-human-in-the-loop-confirmation)
   - 9.12 [Use StateGraph with Conditional Edges for Multi-Agent Routing](#912-use-stategraph-with-conditional-edges-for-multi-agent-routing)
   - 9.13 [Resume LangGraph from Checkpoint After Interrupt](#913-resume-langgraph-from-checkpoint-after-interrupt)
   - 9.14 [Use a service layer to hydrate document references before rendering](#914-use-a-service-layer-to-hydrate-document-references-before-rendering)
10. [Developer Tooling](#10-developer-tooling) — **MEDIUM**
   - 10.1 [Use Azure Cosmos DB Emulator for local development and testing](#101-use-azure-cosmos-db-emulator-for-local-development-and-testing)
   - 10.2 [Use Azure Cosmos DB VS Code extension for routine inspection and management](#102-use-azure-cosmos-db-vs-code-extension-for-routine-inspection-and-management)
11. [Vector Search](#11-vector-search) — **HIGH**
   - 11.1 [Use VectorDistance for Similarity Search](#111-use-vectordistance-for-similarity-search)
   - 11.2 [Define Vector Embedding Policy](#112-define-vector-embedding-policy)
   - 11.3 [Enable Vector Search Feature on Account](#113-enable-vector-search-feature-on-account)
   - 11.4 [Configure Vector Indexes in Indexing Policy](#114-configure-vector-indexes-in-indexing-policy)
   - 11.5 [Normalize Embeddings for Cosine Similarity](#115-normalize-embeddings-for-cosine-similarity)
   - 11.6 [Implement Repository Pattern for Vector Search](#116-implement-repository-pattern-for-vector-search)
12. [Full-Text Search](#12-full-text-search) — **HIGH**
   - 12.1 [Add Full-Text Index in the Indexing Policy](#121-add-full-text-index-in-the-indexing-policy)
   - 12.2 [Define Full-Text Policy on the Container](#122-define-full-text-policy-on-the-container)
   - 12.3 [Enable Full-Text Search Capability on Account](#123-enable-full-text-search-capability-on-account)
   - 12.4 [Combine FTS predicates with range or equality filters for hybrid queries](#124-combine-fts-predicates-with-range-or-equality-filters-for-hybrid-queries)
   - 12.5 [Use FullTextContains for keyword matching on indexed text fields](#125-use-fulltextcontains-for-keyword-matching-on-indexed-text-fields)
   - 12.6 [Use FullTextScore with ORDER BY RANK for BM25 relevance ranking](#126-use-fulltextscore-with-order-by-rank-for-bm25-relevance-ranking)
13. [Security](#13-security) — **HIGH**
   - 13.1 [Enable Continuous Backup for Point-in-Time Restore](#131-enable-continuous-backup-for-point-in-time-restore)
   - 13.2 [Disable Local Authentication (Keys)](#132-disable-local-authentication-keys-)
   - 13.3 [Use Managed Identity with DefaultAzureCredential](#133-use-managed-identity-with-defaultazurecredential)
   - 13.4 [Restrict Network Access](#134-restrict-network-access)
   - 13.5 [Assign Minimum RBAC Roles with Narrow Scope](#135-assign-minimum-rbac-roles-with-narrow-scope)

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
    
```

**Correct (bounded document size):**


```csharp
// Store metadata in Cosmos DB, large content in Blob Storage
public class Document
{
    public string Id { get; set; }
    public string Name { get; set; }
    public long FileSizeBytes { get; set; }
```

```csharp
// Check item size before writing
var json = JsonSerializer.Serialize(item);
var sizeBytes = Encoding.UTF8.GetByteCount(json);
if (sizeBytes > 1_500_000) // 1.5MB warning threshold
{
    _logger.LogWarning("Item approaching size limit: {SizeKB}KB", sizeBytes / 1024);
```

### 1.2 Denormalize for Read-Heavy Workloads

**Impact: HIGH** (reduces query RU by 2-10x)

## Denormalize for Read-Heavy Workloads

In read-heavy workloads, duplicate frequently-queried data to avoid expensive lookups. Accept write overhead for faster reads.

**Incorrect (normalized requires multiple queries):**

```csharp
// N+1 query problem — separate lookup per product for category name
foreach (var product in products)
{
    var category = await container.ReadItemAsync<Category>(
        product.CategoryId, new PartitionKey(product.CategoryId));
    product.CategoryName = category.Name;
```

**Correct (denormalized for read efficiency):**


```csharp
public class Product
{
    public string Id { get; set; }
    public string Name { get; set; }
    public string CategoryId { get; set; }
    public string CategoryName { get; set; }  // Denormalized
```

```python
# Cascade delete — remove all related documents
async def delete_player(player_id: str):
    await players_container.delete_item(item=player_id, partition_key=player_id)
    # Delete from scores container
    async for page in scores_container.query_items(
        query="SELECT c.id FROM c WHERE c.playerId = @pid",
```

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

```

**Correct (single read operation):**


```csharp
// Embedded document - single query retrieves everything
public class Order
{
    public string Id { get; set; }
    public string CustomerId { get; set; }
    
```

### 1.4 Follow ID Value Length and Character Constraints

**Impact: HIGH** (prevents write failures, 401 auth errors, and cross-SDK interoperability issues)

## Follow ID Value Length and Character Constraints

Max `id` length: 1,023 bytes. URL-reserved characters in `id` cause 401 auth errors or 404 routing failures on read/update/delete (not create — the bug hides until first read).

**Incorrect (problematic IDs):**

```python
# ❌ '#' causes 401 on read/update/delete (HTTP fragment delimiter)
doc_id = f"best#{player_id}#{week}#{region}"
await container.upsert_item(body={"id": doc_id, ...})    # succeeds
await container.read_item(item=doc_id, partition_key=pk)  # 💥 401
```

**Correct (safe, bounded IDs):**


```python
# ✅ Use ':' or '_' or '-' as separators
doc_id = f"best:{player_id}:{week}:{region}"
await container.read_item(item=doc_id, partition_key=pk)  # ✅ 200 OK
```

```csharp
// ✅ GUID or bounded deterministic ID
Id = Guid.NewGuid().ToString();
Id = $"report-{tenantId}-{DateTime.UtcNow:yyyyMMdd}-{seq}";
// ✅ Base64 for non-ASCII sources
Id = Convert.ToBase64String(Encoding.UTF8.GetBytes(rawId)).Replace('/', '_').Replace('+', '-');
```

### 1.5 Handle JSON serialization correctly for Cosmos DB documents

**Impact: HIGH** (prevents data loss, null constructor errors, and serialization failures)

## Handle JSON serialization correctly for Cosmos DB documents

Cosmos DB stores documents as JSON. Every field on an entity that must be persisted needs to be serializable.

**Incorrect (common serialization mistakes):**

```java
@Container(containerName = "users")
public class User {

    @Id
    private String id;

    @PartitionKey
```

**Correct (proper serialization for Cosmos DB):**


```java
@JsonIgnoreProperties(ignoreUnknown = true)  // ✅ Ignore Cosmos DB system metadata (_rid, _self, _etag, _ts, _lsn)
@Container(containerName = "users")
public class User {

    @Id
    private String id;

```

```java
// ❌ Data loss: field is not stored in Cosmos
@JsonIgnore
private String password;

// ✅ Field is stored in Cosmos
private String password;

```

> Cross-ref: See `query-parameterize` for parameterized queries.

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
    
```

**Correct (bounded nesting depth):**


```csharp
// Solution 1: Flatten deep hierarchies using path-based approach
public class CategoryNode
{
    public string Id { get; set; }
    public string Name { get; set; }
    public string ParentId { get; set; }
```

```csharp
// Solution 2: Cap nesting depth when building recursive structures
public class TreeNode
{
    public string Id { get; set; }
    public string Name { get; set; }
    public List<TreeNode> Children { get; set; }
```

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
```

**Correct (preserving precision):**


```csharp
// Solution 1: Store large integers and precise decimals as strings
public class Transaction
{
    public string Id { get; set; }
    
    // Store large IDs as strings to preserve all digits
```

```csharp
// Solution 3: Store amounts as integer minor units (cents, paise, etc.)
public class Payment
{
    public string Id { get; set; }
    
    // Store $199.99 as 19999 cents - always safe as integer within 2^53
```

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
```

**Correct (reference pattern for unbounded relationships):**


```csharp
// Blog post document (bounded size)
public class BlogPost
{
    public string Id { get; set; }
    public string PostId { get; set; }  // Partition key
    public string Type { get; set; } = "post";
```

> Cross-ref: See `query-parameterize` for parameterized queries.

### 1.9 Use ID references with transient hydration for document relationships

**Impact: HIGH** (enables correct relationship handling without JOINs while preserving UI/API object access)

## Use ID references with transient hydration for document relationships

Cosmos DB has no cross-document JOINs. When entities need to reference each other, store relationship IDs as persistent fields and use transient (`@JsonIgnore`) properties for hydrated object access.

**Incorrect (JPA relationship annotations — no Cosmos equivalent):**

```java
@Entity
public class Vet {
    @Id
    private Integer id;

    @ManyToMany
```

**Correct (ID references + transient hydration):**


```java
@Container(containerName = "vets")
public class Vet {

    @Id
    @GeneratedValue
    private String id;
```

### 1.10 Version Your Document Schemas

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
```

**Correct (versioned documents):**


```csharp
public abstract class UserBase
{
    public string Id { get; set; }
    public int SchemaVersion { get; set; }
}

```

### 1.11 Use Type Discriminators for Polymorphic Data

**Impact: MEDIUM** (enables efficient single-container design)

## Use Type Discriminators for Polymorphic Data

Use a single Cosmos DB container to co-locate related parent/child or different entity types when:
- similar entities are written and read together, share a natural or business partition key, require a simple transactional boundary, and do not exceed Cosmos DB partition key limits. When storing multiple entity types in the same container, include a type discriminator field for efficient filtering and deserialization.

**Incorrect (no type discrimination):**

```csharp
// Multiple types in same container without clear identification
public class Order { public string Id { get; set; } /* ... */ }
public class Customer { public string Id { get; set; } /* ... */ }
public class Product { public string Id { get; set; } /* ... */ }

// How do you query just orders? Full scan!
```

**Correct (explicit type discriminator):**


```csharp
// Base class with type discriminator
public abstract class BaseEntity
{
    [JsonPropertyName("id")]
    public string Id { get; set; }
    
```

> Cross-ref: See `query-parameterize` for parameterized queries.

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
```

**Correct (bounded partition growth):**


```csharp
// Solution 1: Time-bucket the partition key
public class AuditLog
{
    public string Id { get; set; }
    public string SystemId { get; set; }
    public DateTime Timestamp { get; set; }
```

```csharp
// Solution 2: Use hierarchical partition keys
var containerProperties = new ContainerProperties
{
    Id = "audit-logs",
    PartitionKeyPaths = new List<string> 
    { 
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.

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
```

**Correct (distributed writes):**


```csharp
// Good: write-sharding for time-series data
public class Event
{
    public string Id { get; set; }
    
    // Combine date with hash suffix for distribution
```

```csharp
// Good: natural distribution with entity IDs
public class Order
{
    public string Id { get; set; }
    public string CustomerId { get; set; }  // ✅ Natural distribution
    public DateTime OrderDate { get; set; }
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
> Cross-ref: See `partition-high-cardinality` for key selection.

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
```

**Correct (high cardinality with even distribution):**


```csharp
// Good: using unique identifier as partition key
public class Order
{
    public string Id { get; set; }
    
    // Millions of unique customers = even distribution
```

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
```

**Correct (bounded partition key values):**


```csharp
// Use short, bounded identifiers for partition keys
public class Document
{
    public string Id { get; set; }
    
    // Short, deterministic IDs - always well under 2,048 bytes
```

```csharp
// If you must derive a key from long values, hash or truncate them
public class Document
{
    public string Id { get; set; }
    public string LongCategoryPath { get; set; }  // e.g., deep taxonomy
    
```

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
```

**Correct (partition key matches query patterns):**


```csharp
// Step 1: Analyze your query patterns
// - 80% of queries: "Get all products for seller X"

// Step 2: Choose partition key for dominant pattern
public class Product
{
```

```csharp
// E-commerce example: Orders partitioned by CustomerId
public class Order
{
    public string Id { get; set; }
    public string CustomerId { get; set; }  // Partition key
    public DateTime OrderDate { get; set; }
```

> Cross-ref: See `query-parameterize` for parameterized queries.

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
```

**Correct (synthetic partition key):**


```csharp
public class Telemetry
{
    public string Id { get; set; }
    public string DeviceId { get; set; }
    public DateTime Timestamp { get; set; }
    public double Value { get; set; }
```

```csharp
// Multi-tenant with user-level isolation
public class UserDocument
{
    public string Id { get; set; }
    public string TenantId { get; set; }
    public string UserId { get; set; }
```

> Cross-ref: See `query-parameterize` for parameterized queries.

---

## 3. Query Optimization

**Impact: HIGH**

### 3.1 Compute min/max/avg with one scoped aggregate query

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
```

**Correct (single-pass aggregate query with consistent filters):**


```java
// ✅ One query, one filter set, consistent aggregate outputs
String sql = """
    SELECT
      MIN(c.temperature) AS minTemp,
      MAX(c.temperature) AS maxTemp,
      AVG(c.temperature) AS avgTemp,
```

```python
# ✅ Use one scoped aggregate query
query = """
SELECT
  MIN(c.value) AS minValue,
  MAX(c.value) AS maxValue,
  AVG(c.value) AS avgValue
```

### 3.2 Minimize Cross-Partition Queries

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
```

```csharp
// When cross-partition is unavoidable, optimize parallelism
var query = new QueryDefinition("SELECT * FROM c WHERE c.status = @status")
    .WithParameter("@status", "active");

var options = new QueryRequestOptions
{
    MaxConcurrency = -1,  // Maximum parallelism
```

> Cross-ref: See `query-parameterize` for parameterized queries.

### 3.3 Avoid Full Container Scans

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
```

**Correct (index-friendly queries):**


```csharp
// Store normalized data to avoid functions
public class User
{
    public string Email { get; set; }
    public string EmailLower { get; set; }  // Pre-computed lowercase
}
```

```csharp
// Check if query uses index with query metrics
var options = new QueryRequestOptions
{
    PopulateIndexMetrics = true,
    PartitionKey = new PartitionKey(partitionKey)
};
```

> Cross-ref: See `sdk-diagnostics` for capturing diagnostics.

### 3.4 Use DISTINCT keyword to eliminate duplicate results efficiently

**Impact: MEDIUM** (reduces bandwidth usage and RU consumption by eliminating duplicate results at the query engine level)

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

### 3.5 Query "latest" documents with explicit ORDER BY and TOP 1

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

**Correct (explicit timestamp sort + TOP 1):**


```java
// ✅ Deterministic latest item by timestamp
String sql = """
    SELECT TOP 1 * FROM c
    WHERE c.deviceId = @deviceId AND IS_DEFINED(c.timestamp)
    ORDER BY c.timestamp DESC
    """;
```

```python
# ✅ Deterministic latest item
query = """
SELECT TOP 1 * FROM c
WHERE c.userId = @uid AND IS_DEFINED(c.createdAt)
ORDER BY c.createdAt DESC
"""
```

### 3.6 Detect and Redirect Analytical Queries Away from Transactional Containers

**Impact: HIGH** (prevents RU starvation, 429 throttling cascades, and query timeouts)

## Detect and Redirect Analytical Queries Away from Transactional Containers

**Impact: HIGH (prevents RU starvation, 429 throttling cascades, and query timeouts)**

Cosmos DB's transactional store is optimized for OLTP: point reads, targeted queries within a partition, and bounded result sets. Analytical patterns — COUNT/SUM/AVG across all partitions, GROUP BY over unbounded data, or full-container scans for reporting — consume massive RU, trigger sustained 429 throttling that starves transactional operations, and can exceed the query execution timeout.

**Incorrect (unbounded aggregation across all partitions — fans out to every partition, massive RU):**

```csharp
// ❌ Unbounded aggregation across all partitions
var query = "SELECT c.region, COUNT(1) as orderCount, SUM(c.total) as revenue " +
            "FROM c WHERE c.orderDate >= '2025-01-01' GROUP BY c.region";

var iterator = container.GetItemQueryIterator<dynamic>(query);
// Fans out to ALL partitions, reads ALL matching documents
// At 10M orders: potentially 50,000+ RU per execution
```

**Correct (enable analytical store and run aggregations via Synapse Link — zero RU impact on transactional store):**


```csharp
// ✅ Enable analytical store on the container
var containerProperties = new ContainerProperties
{
    Id = "orders",
    PartitionKeyPath = "/customerId",
    AnalyticalStoreTimeToLiveInSeconds = -1  // Enable analytical store
};
```

```csharp
// ✅ Maintain real-time aggregations via Change Feed processor
public class SalesAggregate
{
    public string Id { get; set; }           // "category-electronics"
    public string PartitionKey { get; set; } // "aggregates"
    public string Category { get; set; }
    public long TotalSold { get; set; }
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
> Cross-ref: See `query-parameterize` for parameterized queries.

### 3.7 Order Filters by Selectivity

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
```

**Correct (most selective filter first):**


```csharp
// CustomerId is highly selective (unique per customer)
var query = @"
    SELECT * FROM c 
    WHERE c.customerId = @customerId  -- 0.01% match (filter first!)
    AND c.type = 'order'              -- Then narrow by type
    AND c.status = 'active'";         -- Finally by status
```

```csharp
// Selectivity guidelines (from most to least selective):
// 1. Unique identifiers: id, customerId, orderId (highest)

// Example: Combining timestamp with status
var query = @"
    SELECT * FROM c 
```

### 3.8 Use Continuation Tokens for Pagination

**Impact: HIGH** (enables efficient large result sets)

## Use Continuation Tokens for Pagination

Never use OFFSET/LIMIT for deep pagination — RU cost scales linearly with offset (page 100 scans 10,000 docs to return 100). Use continuation tokens instead (constant RU per page).

**Incorrect (OFFSET/LIMIT — cost grows with depth):**

```csharp
// ❌ Page 100: scans 10,000 items, returns 100. RU grows linearly!
var query = $"SELECT * FROM c ORDER BY c.name OFFSET {offset} LIMIT {pageSize}";
```

**Correct (continuation token — constant cost per page):**


```csharp
public async Task<PagedResult<Product>> GetProductsPage(int pageSize, string continuationToken = null)
{
    var query = new QueryDefinition("SELECT * FROM c ORDER BY c.name");
    var iterator = container.GetItemQueryIterator<Product>(query,
        continuationToken: continuationToken,
        requestOptions: new QueryRequestOptions { MaxItemCount = pageSize });
```

```python
# ✅ Continuation token pagination — stable RU per page
results = container.query_items(
    query=query, parameters=params,
    partition_key=player_id, max_item_count=page_size)
pager = results.by_page(continuation_token=continuation_token)
page = await pager.__anext__()
```

### 3.9 Use Parameterized Queries

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
    
```

**Correct (parameterized queries):**


```csharp
public async Task<User> GetUser(string userId)
{
    var query = new QueryDefinition("SELECT * FROM c WHERE c.userId = @userId")
        .WithParameter("@userId", userId);
    
    // Injection attempt becomes literal string comparison
```

```csharp
// Multiple parameters
var query = new QueryDefinition(@"
    SELECT * FROM c 
    WHERE c.customerId = @customerId 
    AND c.status = @status
    AND c.orderDate >= @startDate")
```

### 3.10 Use Point Reads Instead of Queries for Known ID and Partition Key

**Impact: HIGH** (1 RU vs ~2.5 RU per single-document lookup)

## Use Point Reads Instead of Queries for Known ID and Partition Key

When both `id` and partition key are known, use a point read instead of a query. Point read = 1 RU for 1 KB; equivalent query = ~2.5 RU (query engine overhead).

**Incorrect (query when point read suffices):**

```csharp
// ❌ Query engine invoked for a single known document
var query = new QueryDefinition("SELECT * FROM c WHERE c.id = @id")
    .WithParameter("@id", orderId);
var iterator = container.GetItemQueryIterator<Order>(query,
    requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(customerId) });
```

**Correct (point read — bypasses query engine):**


```csharp
// ✅ 1 RU, no query engine overhead
var response = await container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
```

```python
# ✅ Point read
container.read_item(item=player_id, partition_key=game_id)
```

> Cross-ref: See `query-parameterize` for parameterized queries.

### 3.11 Parameterize TOP Values Safely

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

### 3.12 Project Only Needed Fields

**Impact: HIGH** (reduces payload size, network bandwidth, and client memory; RU savings scale with document size (negligible on small flat docs, substantial on multi-KB/MB documents and large result sets))

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
```

**Correct (fully async):**


```csharp
public async Task<Order> GetOrderAsync(string orderId, string customerId)
{
    var response = await _container.ReadItemAsync<Order>(
        orderId, 
        new PartitionKey(customerId));
    
```

```csharp
// Concurrent operations with Task.WhenAll
public async Task<OrderWithItems> GetOrderWithItemsAsync(string orderId, string customerId)
{
    // Start both operations concurrently
    var orderTask = _container.ReadItemAsync<Order>(
        orderId, new PartitionKey(customerId));
```

> Cross-ref: See `query-parameterize` for parameterized queries.

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
```

```csharp
// Alternative: Configure via CosmosClientOptions
CosmosClientOptions options = new CosmosClientOptions()
{
    AvailabilityStrategy = AvailabilityStrategy.CrossRegionHedgingStrategy(
        threshold: TimeSpan.FromMilliseconds(500),
        thresholdStep: TimeSpan.FromMilliseconds(100)
    ),
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.

### 4.3 Configure Partition-Level Circuit Breaker

**Impact: HIGH** (prevents cascading failures, improves write availability)

## Configure Partition-Level Circuit Breaker

The partition-level circuit breaker (PPCB) tracks unhealthy partitions and routes requests away from them, preventing cascading failures.

**Incorrect (no circuit breaker — cascading failures):**

```csharp
// Without circuit breaker: requests to unhealthy partitions keep failing,
// retry storms amplify the problem, no automatic failover per-partition
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationPreferredRegions = new List<string> { "East US", "East US 2" }
});
```

**Correct (circuit breaker enabled):**


```csharp
// .NET — enable via environment variables before creating client
Environment.SetEnvironmentVariable("AZURE_COSMOS_CIRCUIT_BREAKER_ENABLED", "true");
Environment.SetEnvironmentVariable("AZURE_COSMOS_PPCB_CONSECUTIVE_FAILURE_COUNT_FOR_WRITES", "5");
Environment.SetEnvironmentVariable("AZURE_COSMOS_PPCB_CONSECUTIVE_FAILURE_COUNT_FOR_READS", "10");

var client = new CosmosClient(connectionString, new CosmosClientOptions
```

```java
// Java (4.63.0+) — system property
System.setProperty("COSMOS.PARTITION_LEVEL_CIRCUIT_BREAKER_CONFIG",
    "{\"isPartitionLevelCircuitBreakerEnabled\": true, " +
    "\"circuitBreakerType\": \"CONSECUTIVE_EXCEPTION_COUNT_BASED\"," +
    "\"consecutiveExceptionCountToleratedForWrites\": 5}");
```

### 4.4 Use IfNoneMatchETag("*") for conditional creates to prevent duplicates

**Impact: HIGH** (prevents duplicate documents on concurrent or retried creates without a prior read)

## Use IfNoneMatchETag("*") for conditional creates to prevent duplicates

**Impact: HIGH (prevents duplicate documents on concurrent or retried creates without a prior read)**

When creating a document that must be unique (e.g., user credentials keyed by email), pass `IfNoneMatchETag("*")` on the `createItem` options. Cosmos DB rejects the write with HTTP 409 Conflict if a document with the same `id` in the same partition already exists, making duplicate detection atomic and free of an extra read.

**Incorrect (upsert silently overwrites existing records):**

```java
// ❌ upsertItem overwrites an existing user-credentials document silently
// A duplicate email gets no error — the old credentials are lost
container.upsertItem(credentialsDto, new PartitionKey(email), null).block();
```

**Correct (conditional create — 409 on duplicate):**


```java
// ✅ createItem with IfNoneMatchETag("*") rejects if the document already exists
CosmosItemRequestOptions options = new CosmosItemRequestOptions()
    .setIfNoneMatchETag("*");  // Reject if any document exists with this id+PK

try {
    credentialsContainer
```

```java
// ✅ Reactive chain
credentialsContainer
    .createItem(credentialsDto, new PartitionKey(email),
        new CosmosItemRequestOptions().setIfNoneMatchETag("*"))
    .onErrorMap(CosmosException.class, ex ->
        ex.getStatusCode() == 409
```

### 4.5 Use Direct Connection Mode for Production

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

```

**Correct (Direct mode for production):**


```csharp
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    // Direct mode connects straight to backend partitions
    ConnectionMode = ConnectionMode.Direct,
    
    // Protocol.Tcp for best performance (default in Direct mode)
```

```csharp
// When to use Gateway mode (exceptions):
var gatewayClient = new CosmosClient(connectionString, new CosmosClientOptions
{
    // Use Gateway when:
    // 1. Corporate firewall blocks TCP port range 10000-20000
    ConnectionMode = ConnectionMode.Gateway
```

### 4.6 Guard against empty continuation tokens before calling byPage

**Impact: HIGH** (empty string token causes runtime "INVALID JSON in continuation token" error; null is the correct sentinel for first-page requests)

## Guard against empty continuation tokens before calling byPage

**Impact: HIGH (empty string token causes runtime `INVALID JSON in continuation token` error; `null` is the correct sentinel for first-page requests)**

When integrating Cosmos DB pagination with frameworks that use empty strings as default values for "no token" (e.g., gRPC/proto3, where string fields default to `""`), passing `""` to `byPage(continuationToken, pageSize)` triggers a server-side parse error. The correct sentinel for "no paging state" is `null`.

**Incorrect (empty string passed as continuation token):**

```java
// ❌ gRPC/proto3: string fields default to "" — NOT null
String pagingState = request.getPagingState();  // returns "" on first call

// Passing "" to byPage causes:
// CosmosException: INVALID JSON in continuation token
return container.queryItems(querySpec, opts, Video.class)
```

**Correct (null-guard before passing to byPage):**


```java
// ✅ Convert empty string to null before passing as continuation token
String raw = request.getPagingState();     // "" on first call, token on subsequent calls
String continuationToken = (raw == null || raw.isEmpty()) ? null : raw;

return container.queryItems(querySpec, opts, Video.class)
    .byPage(continuationToken, pageSize)   // ✅ null = first page, token = continuation
```

```java
// ✅ Or with Optional pattern
Optional<String> pageState = Optional.ofNullable(
    raw == null || raw.isEmpty() ? null : raw);

return container.queryItems(querySpec, opts, Video.class)
    .byPage(pageState.orElse(null), pageSize)
```

### 4.7 Log Diagnostics for Troubleshooting

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
```

**Correct (logging diagnostics):**


```csharp
public async Task<Order> GetOrder(string orderId, string customerId)
{
    var response = await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
    
    // Log diagnostics for slow operations
    if (response.Diagnostics.GetClientElapsedTime() > TimeSpan.FromMilliseconds(100))
    {
```

```csharp
// Query diagnostics with query metrics
var queryOptions = new QueryRequestOptions
{
    PopulateIndexMetrics = true,  // Index usage info
    MaxItemCount = 100
};

```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
> Cross-ref: See `sdk-429-retry` for retry/throttle handling.

### 4.8 Use Microsoft.Azure.Cosmos package, not abandoned Azure.Cosmos

**Impact: HIGH** (Prevents build failures from referencing non-existent package versions)

## Use Microsoft.Azure.Cosmos package, not abandoned Azure.Cosmos

The canonical .NET SDK for Azure Cosmos DB is **`Microsoft.Azure.Cosmos`** (v3.x, currently GA). Never reference the **`Azure.Cosmos`** package — it was an abandoned v4-preview experiment that only shipped three preview versions (`4.0.0-preview` through `4.0.0-preview3`) and has no stable release. Referencing `Azure.Cosmos` with a 3.x version number will fail with **NU1103** because no such version exists.

**Incorrect (wrong package id — causes build failure):**

```xml
<ItemGroup>
  <!-- WRONG: Azure.Cosmos has no 3.x release. Only abandoned 4.0.0-preview exists. -->
  <PackageReference Include="Azure.Cosmos" Version="3.47.2" />
</ItemGroup>
```

```
error NU1103: Unable to find a stable package Azure.Cosmos with version (>= 3.47.2)
```

**Correct (canonical GA package):**

```xml
<ItemGroup>
  <PackageReference Include="Microsoft.Azure.Cosmos" Version="3.47.0" />
</ItemGroup>
```

**Key Points:**

- **Always use `Microsoft.Azure.Cosmos`** — this is the only supported, GA Cosmos DB .NET SDK
- **`Azure.Cosmos` is abandoned** — the v4 rewrite built on `Azure.Core` was never released as stable
- **No 3.x versions of `Azure.Cosmos` exist** — only `4.0.0-preview`, `4.0.0-preview2`, and `4.0.0-preview3`
- **Do not confuse package ids** — `Microsoft.Azure.Cosmos` 3.x is GA; `Azure.Cosmos` 4.x-preview is dead
- **Applies to all .NET project types** — ASP.NET Core, Azure Functions, class libraries, console apps

Reference: [Microsoft.Azure.Cosmos NuGet package](https://www.nuget.org/packages/Microsoft.Azure.Cosmos)

### 4.9 Avoid Microsoft.Azure.Cosmos namespace collisions with domain models

**Impact: HIGH** (prevents CS0104 build-breaking ambiguous reference errors)

## Avoid Microsoft.Azure.Cosmos namespace collisions with domain models

The `Microsoft.Azure.Cosmos` namespace exports top-level types including `User`, `Database`, `Container`, `Conflict`, `Trigger`, and `Permission`. When an application defines a domain entity by the same name and both namespaces are imported with unqualified `using` directives in the same file, every reference to the shared name becomes ambiguous and the build fails with **CS0104**.

**Incorrect (ambiguous reference — CS0104):**

```csharp
using ECommerce.Core.Models;      // defines User
using Microsoft.Azure.Cosmos;     // also defines User

public class UserRepository
{
    private readonly Container _container;
```

**Correct (alias the SDK import):**


```csharp
using Cosmos = Microsoft.Azure.Cosmos;
using ECommerce.Core.Models;      // defines User — no collision

public class UserRepository
{
    private readonly Cosmos.Container _container;
```

```csharp
using ECommerce.Core.Models;

public class UserRepository
{
    private readonly Microsoft.Azure.Cosmos.Container _container;

```

### 4.10 Configure SSL and connection mode for Cosmos DB Emulator

**Impact: MEDIUM** (enables local development with all SDKs)

## Configure SSL and connection mode for Cosmos DB Emulator

The emulator uses a self-signed certificate requiring special handling. **All SDKs must use Gateway mode** — Direct mode has known SSL issues with the emulator.

**Incorrect (Direct mode with emulator):**

```java
// Direct mode fails with SSL errors even after cert import
CosmosClientBuilder builder = new CosmosClientBuilder()
    .endpoint("https://localhost:8081")
    .key("...")
    .directMode();  // WRONG: SSL handshake will fail
```

**Correct (Gateway mode, per-SDK SSL handling):**


```csharp
// .NET — Gateway + accept self-signed cert
var client = new CosmosClient("https://localhost:8081", emulatorKey, new CosmosClientOptions
{
    ConnectionMode = ConnectionMode.Gateway,
    HttpClientFactory = () => new HttpClient(new HttpClientHandler
    {
```

```python
# Python — Gateway by default, disable SSL verification
client = CosmosClient(
    url="https://localhost:8081", credential=emulator_key,
    connection_verify=False  # Disable SSL for emulator only
)
```

### 4.11 Use ETags for optimistic concurrency on read-modify-write operations

**Impact: HIGH** (prevents lost updates in concurrent write scenarios)

## Use ETags for optimistic concurrency on read-modify-write operations

For read-modify-write operations, use ETags to prevent lost updates. Without them, the last writer silently overwrites concurrent changes.

**Incorrect (no concurrency control — lost updates):**

```csharp
// Two concurrent requests both read bestScore: 100
// Thread A writes 150, Thread B writes 200
var response = await _container.ReadItemAsync<Player>(playerId, new PartitionKey(playerId));
var player = response.Resource;
player.BestScore = Math.Max(player.BestScore, newScore);
await _container.UpsertItemAsync(player, new PartitionKey(playerId)); // No ETag check!
```

**Correct (ETag-based optimistic concurrency with retry):**


```csharp
for (int attempt = 0; attempt < 3; attempt++)
{
    var response = await _container.ReadItemAsync<Player>(playerId, new PartitionKey(playerId));
    var player = response.Resource;
    var etag = response.ETag;

```

```python
# Python — use MatchConditions enum (NOT a string)
from azure.core import MatchConditions

response = container.read_item(item=player_id, partition_key=player_id)
etag = response.get('_etag')
# ... modify response ...
```

### 4.12 Configure Excluded Regions for Dynamic Failover

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
```

**Correct (.NET SDK - excluded regions):**


```csharp
// Configure excluded regions at request level (.NET SDK 3.37.0+)
CosmosClientOptions options = new CosmosClientOptions()
{
    ApplicationPreferredRegions = new List<string> { "West US", "Central US", "East US" }
};

CosmosClient client = new CosmosClient(connectionString, options);
```

```csharp
// Handle rate limiting by routing to alternate regions
ItemResponse<Order> response;
try
{
    response = await container.ReadItemAsync<Order>("id", partitionKey);
}
catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.TooManyRequests)
```

> Cross-ref: See `sdk-429-retry` for retry/throttle handling.

### 4.13 Use current Go Cosmos DB SDK versions and explicit partition-key metadata

**Impact: HIGH** (prevents cross-SDK partition-key metadata incompatibilities)

## Use current Go Cosmos DB SDK versions and explicit partition-key metadata

When creating Azure Cosmos DB containers from Go with `github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos`, avoid stale SDK pins such as `v1.0.0`. The primary fix is **upgrading the SDK**: `azcosmos v1.0.0` serializes a `Paths`-only `PartitionKeyDefinition` as `{"paths":["/h3Cell"]}` — omitting `kind` entirely — whereas `v1.3.0` serializes `{"kind":"Hash","paths":["/h3Cell"]}`.

**Incorrect (stale SDK pin — serializes without `kind`):**

```

```

**Correct (current SDK — serializes `kind:"Hash"`; explicit `Kind` is defensive best practice):**


```

```

### 4.14 Unwrap CosmosItemResponse and enable content response in Java SDK

**Impact: MEDIUM** (prevents type errors from missing getItem() on reads and null content on writes)

## Unwrap CosmosItemResponse and enable content response in Java SDK

All Java SDK operations (`readItem`, `createItem`, `upsertItem`, `replaceItem`) return `CosmosItemResponse<T>`, not `T` directly. Call `.getItem()` to extract the entity.

**Incorrect (treating response as entity):**

```java
// ❌ Compilation error — readItem returns CosmosItemResponse<Player>, not Player
Player player = container.readItem(playerId, new PartitionKey(playerId), Player.class);
```

**Correct (unwrap with getItem):**


```java
// ✅ Unwrap the response
CosmosItemResponse<Player> response = container.readItem(
    playerId, new PartitionKey(playerId), Player.class);
Player player = response.getItem();

// ✅ Async — map to extract entity
```

```java
// ❌ getItem() returns null without contentResponseOnWriteEnabled
CosmosItemResponse<Order> response = container.createItem(order);
response.getItem();  // null!

// ✅ Enable at client level
CosmosClient client = new CosmosClientBuilder()
```

### 4.15 Use dependent @Bean methods for Cosmos DB initialization in Spring Boot

**Impact: HIGH** (prevents circular dependency, startup failures, class name collisions, and compile errors)

## Use dependent @Bean methods for Cosmos DB initialization in Spring Boot

Use dependent `@Bean` methods with parameter injection instead of `@PostConstruct`. Calling a `@Bean` method from `@PostConstruct` creates a circular dependency crash.

**Incorrect (@PostConstruct calling @Bean — circular dependency):**

```java
@Configuration
public class CosmosDbConfig {
    @Bean
    public CosmosClient cosmosClient() { return new CosmosClientBuilder()...; }

    @PostConstruct  // ❌ Calls cosmosClient() which is a @Bean — circular!
```

**Correct (dependent @Bean chain):**


```java
@Configuration
public class CosmosDbConfig {
    @Value("${azure.cosmos.endpoint}") private String endpoint;
    @Value("${azure.cosmos.key}") private String key;
    @Value("${azure.cosmos.database}") private String databaseName;

```

```java
@Configuration
@EnableCosmosRepositories
public class CosmosDbConfig extends AbstractCosmosConfiguration {
    @Bean  // ✅ Not @Override — declare as a bean
    public CosmosClientBuilder cosmosClientBuilder() {
        return new CosmosClientBuilder().endpoint(endpoint).key(key)
```

### 4.16 Spring Boot and Java version compatibility for Cosmos DB SDK

**Impact: CRITICAL** (Prevents build failures due to version incompatibility between Spring Boot and Java)

## Spring Boot and Java version compatibility for Cosmos DB SDK

## Spring Boot and Java Version Requirements

The Azure Cosmos DB Java SDK works with various Spring Boot versions, but each Spring Boot version has **strict Java version requirements** that must be met for the project to build successfully.

**Incorrect:**

```
[ERROR] bad class file...has wrong version 61.0, should be 55.0
[ERROR] release version 17 not supported
```

**Correct:**


```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.1</version>
</parent>

<properties>
    <java.version>17</java.version>
```

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>2.7.18</version>
</parent>

<properties>
    <java.version>11</java.version>  <!-- or 17 -->
```

### 4.17 Initialize Async Cosmos DB Container Before CosmosDBSaver

**Impact: HIGH** (prevents credential and event-loop errors in async applications)

## Initialize Async Cosmos DB Container Before CosmosDBSaver

**Impact: HIGH (prevents credential and event-loop errors in async applications)**

When using `CosmosDBSaver` with the async Cosmos DB SDK, the container client must be created within an active async context (e.g., inside an `async def` function). Creating it at module level causes event-loop errors because the async credential and client require a running loop.

**Incorrect (module-level initialization — event loop not running):**

```python
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from langchain_azure_cosmosdb import CosmosDBSaver

# BAD: No event loop running at module import time
credential = AsyncDefaultAzureCredential()
```

**Correct (initialize in async startup function):**


```python
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from langchain_azure_cosmosdb import CosmosDBSaver
from langgraph.graph import StateGraph, MessagesState

builder = StateGraph(MessagesState)
```

### 4.18 Use CosmosDBSaver for LangGraph Checkpointing

**Impact: HIGH** (enables persistent multi-turn conversation state across restarts)

## Use CosmosDBSaver for LangGraph Checkpointing

**Impact: HIGH (enables persistent multi-turn conversation state across restarts)**

When building LangGraph agents that require multi-turn conversation persistence, use `CosmosDBSaver` from `langchain-azure-cosmosdb` as the checkpointer. This stores graph state in Cosmos DB, enabling conversations to survive process restarts and scale across multiple instances.

**Incorrect (using in-memory checkpointer — state lost on restart):**

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState

builder = StateGraph(MessagesState)
# ... add nodes and edges ...

```

**Correct (async container client with CosmosDBSaver):**


```python
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from langchain_azure_cosmosdb import CosmosDBSaver
from langgraph.graph import StateGraph, MessagesState

builder = StateGraph(MessagesState)
```

### 4.19 Use AzureCosmosDBNoSQLChatMessageHistory for Persistent Conversations in JS/TS

**Impact: HIGH** (enables persistent multi-turn conversations that survive restarts and scale horizontally)

## Use AzureCosmosDBNoSQLChatMessageHistory for Persistent Conversations in JS/TS

**Impact: HIGH (enables persistent multi-turn conversations that survive restarts and scale horizontally)**

When building conversational AI applications with LangChain.js, use `AzureCosmosDBNoSQLChatMessageHistory` to persist chat messages in Cosmos DB. This ensures conversations survive process restarts, enables horizontal scaling across multiple instances, and provides a queryable audit trail.

**Incorrect (in-memory history — lost on restart, no horizontal scaling):**

```typescript
import { ChatMessageHistory } from "langchain/memory";

// BAD: Messages lost when process restarts or user hits different instance
const history = new ChatMessageHistory();
await history.addUserMessage("Hello");
await history.addAIMessage("Hi there!");
```

**Correct (persistent chat history with proper session isolation):**


```typescript
import { AzureCosmosDBNoSQLChatMessageHistory } from "@langchain/azure-cosmosdb";
import { DefaultAzureCredential } from "@azure/identity";
import { RunnableWithMessageHistory } from "@langchain/core/runnables";
import { ChatOpenAI } from "@langchain/openai";

const credential = new DefaultAzureCredential();
```

### 4.20 Configure Azure OpenAI Embedding Deployment Name for JS/TS LangChain

**Impact: MEDIUM** (incorrect deployment name causes 404 errors or uses wrong model)

## Configure Azure OpenAI Embedding Deployment Name for JS/TS LangChain

**Impact: MEDIUM (incorrect deployment name causes 404 errors or uses wrong model)**

When using `AzureOpenAIEmbeddings` with `@langchain/openai` in JavaScript/TypeScript, you must specify the Azure OpenAI **deployment name** (the name you chose when deploying the model in Azure AI Studio or via CLI) — not the bare model name. Azure OpenAI uses deployment names to route requests, and these can differ from the underlying model name.

**Incorrect (using bare model name or wrong property):**

```typescript
import { AzureOpenAIEmbeddings } from "@langchain/openai";

// BAD: "model" property is for OpenAI API, not Azure OpenAI
const embeddings = new AzureOpenAIEmbeddings({
  model: "text-embedding-3-small",  // Wrong property for Azure
});
```

**Correct (explicit deployment name and API version):**


```typescript
import { AzureOpenAIEmbeddings } from "@langchain/openai";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "my-embedding-deployment", // Your actual deployment name
  azureOpenAIApiVersion: "2024-06-01",
  // Endpoint and key from environment variables:
```

```typescript
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const credential = new DefaultAzureCredential();

const embeddings = new AzureOpenAIEmbeddings({
```

### 4.21 Prevent Filter Injection in JS/TS LangChain Vector Store Queries

**Impact: CRITICAL** (prevents NoSQL injection attacks that can exfiltrate or corrupt data)

## Prevent Filter Injection in JS/TS LangChain Vector Store Queries

**Impact: CRITICAL (prevents NoSQL injection attacks that can exfiltrate or corrupt data)**

When passing filter clauses to `AzureCosmosDBNoSQLVectorStore` similarity searches, **never** concatenate user input directly into the filter string. Cosmos DB NoSQL queries support parameterized queries with `@param` placeholders — always use these to safely inject user-provided values.

**Incorrect (string concatenation — SQL injection vulnerability):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

async function searchByCategory(store: AzureCosmosDBNoSQLVectorStore, userInput: string) {
  // CRITICAL VULNERABILITY: User can inject arbitrary SQL predicates
  // e.g., userInput = "electronics' OR c.secret != '"
  const results = await store.similaritySearch("find products", 10, {
```

**Correct (parameterized queries with @param placeholders):**


```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

async function searchByCategory(store: AzureCosmosDBNoSQLVectorStore, userInput: string) {
  // SAFE: Parameters are escaped by the SDK — no injection possible
  const results = await store.similaritySearch("find products", 10, {
    filter: "c.category = @category",
```

> Cross-ref: See `query-parameterize` for parameterized queries.

### 4.22 Configure Full-Text Prerequisites Before JS/TS LangChain Hybrid Search

**Impact: HIGH** (full-text and hybrid queries fail at runtime without container-level configuration)

## Configure Full-Text Prerequisites Before JS/TS LangChain Hybrid Search

**Impact: HIGH (full-text and hybrid queries fail at runtime without container-level configuration)**

Before using `FullTextSearch`, `Hybrid`, or `HybridScoreThreshold` search types with `AzureCosmosDBNoSQLVectorStore` in JavaScript/TypeScript, you must configure three things on your Cosmos DB container: (1) enable the full-text search capability on the account, (2) define a `fullTextPolicy` specifying which properties to index and their language, and (3) add `fullTextIndexes` entries to the indexing policy. Without all three, queries will fail with opaque errors.

**Incorrect (attempting hybrid search on unconfigured container):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

// Container created with only vector embedding policy — no full-text config
const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
```

**Correct (container configured with full-text policy and indexes):**


```json
{
  "containerProperties": {
    "id": "docs",
    "partitionKey": { "paths": ["/tenantId"], "kind": "Hash" },
    "fullTextPolicy": {
      "defaultLanguage": "en-US",
```

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
```

### 4.23 Use Managed Identity for JS/TS LangChain Cosmos DB Integration

**Impact: CRITICAL** (zero-secret authentication eliminates credential leakage risk)

## Use Managed Identity for JS/TS LangChain Cosmos DB Integration

**Impact: CRITICAL (zero-secret authentication eliminates credential leakage risk)**

In production JavaScript/TypeScript applications using `@langchain/azure-cosmosdb`, always authenticate with `DefaultAzureCredential` from `@azure/identity` instead of connection strings. Connection strings contain master keys that grant full access — if leaked, they compromise the entire account.

**Incorrect (connection string in production):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
});
```

**Correct (endpoint + DefaultAzureCredential):**


```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
```

```bash
az cosmosdb sql role assignment create \
  --account-name myaccount \
  --resource-group myrg \
  --role-definition-id 00000000-0000-0000-0000-000000000002 \
  --principal-id <managed-identity-object-id> \
  --scope "/"
```

### 4.24 Choose the Correct Search Type for JS/TS LangChain Vector Store

**Impact: HIGH** (selecting wrong search type returns irrelevant results or causes errors)

## Choose the Correct Search Type for JS/TS LangChain Vector Store

**Impact: HIGH (selecting wrong search type returns irrelevant results or causes errors)**

The `@langchain/azure-cosmosdb` package supports multiple search types via `AzureCosmosDBNoSQLVectorStore`. Choose the appropriate type based on your retrieval needs.

**Incorrect (using hybrid search without full-text configuration):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
  databaseName: "mydb",
```

**Correct (vector search — no special container config needed):**


```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
  databaseName: "mydb",
```

```typescript
// Container must have fullTextPolicy and fullTextIndexes configured FIRST
const results = await store.similaritySearch("keyword and semantic query", 10, {
  searchType: "Hybrid",
});
```

### 4.25 Use AzureCosmosDBNoSQLSemanticCache for LLM Cost Reduction in JS/TS

**Impact: MEDIUM** (reduces LLM API costs and latency by caching semantically similar queries)

## Use AzureCosmosDBNoSQLSemanticCache for LLM Cost Reduction in JS/TS

**Impact: MEDIUM (reduces LLM API costs and latency by caching semantically similar queries)**

When building LLM-powered applications with LangChain.js, use `AzureCosmosDBNoSQLSemanticCache` to cache LLM responses in Cosmos DB. Unlike exact-match caches, semantic cache uses vector similarity to return cached responses for queries that are semantically similar (not just identical).

**Incorrect (no caching — every request hits the LLM):**

```typescript
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  azureOpenAIApiDeploymentName: "gpt-4o",
});

```

**Correct (semantic cache with Cosmos DB):**


```typescript
import { AzureCosmosDBNoSQLSemanticCache } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings, ChatOpenAI } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const credential = new DefaultAzureCredential();

```

### 4.26 Correctly Initialize AzureCosmosDBNoSQLVectorStore in JavaScript/TypeScript

**Impact: HIGH** (prevents runtime connection failures and misconfigured vector stores)

## Correctly Initialize AzureCosmosDBNoSQLVectorStore

Initialize `AzureCosmosDBNoSQLVectorStore` with an embedding model instance and either a connection string (dev) or endpoint + `DefaultAzureCredential` (prod). Database/container must exist when using RBAC.

**Incorrect (missing embedding model, relying on auto-create with RBAC):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

// ❌ No embedding model — store cannot generate vectors
const store = new AzureCosmosDBNoSQLVectorStore({
  connectionString: process.env.COSMOS_CONNECTION_STRING,
  databaseName: "mydb",
  containerName: "vectors",
  // Missing: embedding model!
});
```

**Correct (embedding model + proper initialization):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

// ✅ Development — connection string
const store = new AzureCosmosDBNoSQLVectorStore(
  new AzureOpenAIEmbeddings({ azureOpenAIApiDeploymentName: "text-embedding-ada-002" }),
  {
    connectionString: process.env.COSMOS_CONNECTION_STRING,
    databaseName: "mydb",
    containerName: "vectors",
  }
);

// ✅ Production — RBAC with DefaultAzureCredential (database must pre-exist)
const prodStore = new AzureCosmosDBNoSQLVectorStore(
  new AzureOpenAIEmbeddings({ azureOpenAIApiDeploymentName: "text-embedding-ada-002" }),
  {
    endpoint: process.env.COSMOS_ENDPOINT,
    credential: new DefaultAzureCredential(),
    databaseName: "mydb",
    containerName: "vectors",
  }
);

await store.initialize(); // Required before first use
```

**Key points:**
- Always pass embedding model as first argument
- Call `await store.initialize()` before first operation
- With RBAC, pre-create database/container (SDK won't auto-create)
- Connection string for local dev, DefaultAzureCredential for production

### 4.27 Use Persistent MCP Client Sessions for Multi-Agent Applications

**Impact: HIGH** (prevents session initialization overhead and connection churn)

## Use Persistent MCP Client Sessions for Multi-Agent Applications

**Impact: HIGH (prevents session initialization overhead and connection churn)**

When using `MultiServerMCPClient` with LangGraph agents, avoid creating a new client instance per request. MCP sessions involve transport negotiation, tool discovery, and server handshakes.

**Incorrect (new client per request — high overhead, applies to all versions):**

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

async def handle_request(user_input):
    # BAD: Creates a new client (and underlying sessions) for every single request
    client = MultiServerMCPClient({
        "my_server": {"transport": "streamable_http", "url": "http://localhost:8080/mcp"}
```

**Correct (>= 0.2.0 — single client instance, get_tools() manages sessions internally):**


```python
from langchain_mcp_adapters.client import MultiServerMCPClient

_mcp_client: MultiServerMCPClient | None = None

async def setup_mcp():
    """Call once during application startup."""
```

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

_mcp_client = None
_session_context = None
_persistent_session = None
```

### 4.28 Handle MCP ToolMessage Content Format Variations

**Impact: HIGH** (prevents JSON parse failures from langchain-mcp-adapters >= 0.2.0)

## Handle MCP ToolMessage Content Format Variations

**Impact: HIGH (prevents JSON parse failures from langchain-mcp-adapters >= 0.2.0)**

Starting with `langchain-mcp-adapters` 0.2.0, `ToolMessage.content` changed from a plain JSON string to a list of content blocks (e.g., `[{"type": "text", "text": "..."}]`). Any code that parses `ToolMessage.content` must handle both formats to remain compatible across versions and avoid `json.JSONDecodeError` or `TypeError`.

**Incorrect (assumes content is always a string):**

```python
import json
from langchain_core.messages import ToolMessage

def extract_routing_info(message: ToolMessage):
    # BAD: Fails when content is a list (langchain-mcp-adapters >= 0.2.0)
    data = json.loads(message.content)
    return data.get("goto")
```

Error with newer adapter versions:
```
TypeError: the JSON object must be str, bytes or bytearray, not list
```

**Correct (handles both string and list formats):**

```python
import json
from langchain_core.messages import ToolMessage

def extract_routing_info(message: ToolMessage):
    content = message.content

    # Handle list-of-blocks format (langchain-mcp-adapters >= 0.2.0)
    if isinstance(content, list):
        text_parts = [block["text"] for block in content if block.get("type") == "text"]
        content = text_parts[0] if text_parts else ""

    # Now content is a plain string — safe to parse
    data = json.loads(content)
    return data.get("goto")
```

**When this matters:** Any time you inspect tool call results programmatically — for example, to extract routing decisions, parse structured responses, or implement conditional logic based on tool outputs.

Reference: [langchain-mcp-adapters changelog](https://github.com/langchain-ai/langchain-mcp-adapters)

### 4.29 Filter MCP Tools by Name Prefix for Agent Assignment

**Impact: MEDIUM** (reduces agent confusion and improves routing accuracy)

## Filter MCP Tools by Name Prefix for Agent Assignment

**Impact: MEDIUM (reduces agent confusion and improves routing accuracy)**

When a single MCP server exposes tools for multiple domains, assign each LangGraph agent only the subset of tools it needs. Use a name-prefix convention on the server side (e.g., `get_transaction_history`, `get_offer_information`, `transfer_to_sales_agent`) and filter client-side by prefix.

**Incorrect (all agents receive all tools):**

```python
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

all_tools = await load_mcp_tools(session)

# BAD: Every agent sees every tool — leads to wrong tool calls
```

**Correct (filter tools by prefix per agent):**


```python
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

all_tools = await load_mcp_tools(session)

def filter_tools_by_prefix(tools, prefixes):
```

### 4.30 Configure local development environment to avoid cloud connection conflicts

**Impact: MEDIUM** (prevents accidental connections to production instead of emulator)

## Configure local development environment to avoid cloud connection conflicts

## Configure Local Development Environment Properly

When developing locally with the Cosmos DB Emulator, system-level environment variables pointing to Azure cloud accounts can override your local configuration, causing unexpected connections to production resources instead of the emulator.

**Incorrect:**

```python
# Your .env file (local config)
COSMOS_ENDPOINT=https://localhost:8081
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==

# But system environment has (from Azure CLI or other tools):
# COSMOS_ENDPOINT=https://my-prod-account.documents.azure.com:443/

```

**Correct:**


```python
from dotenv import load_dotenv
import os

# Force .env values to override system environment variables
load_dotenv(override=True)  # ✅ .env values take precedence

# Or use explicit defaults for emulator
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "https://localhost:8081")
```

```javascript
// dotenv also has override option
require('dotenv').config({ override: true });

// Or with explicit defaults
const endpoint = process.env.COSMOS_ENDPOINT || 'https://localhost:8081';
const key = process.env.COSMOS_KEY || 
    'C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==';
```

### 4.31 Explicitly reference Newtonsoft.Json package

**Impact: HIGH** (Prevents build failures and security vulnerabilities from missing or outdated Newtonsoft.Json dependency)

## Explicitly reference Newtonsoft.Json package

## Explicitly reference Newtonsoft.Json package

When creating any .NET project that references `Microsoft.Azure.Cosmos` (version 3.43.0 or later), your `.csproj` **MUST** include an explicit `PackageReference` for `Newtonsoft.Json` (version 13.0.3 or higher). Without this reference the project will not build.

**Incorrect:**

```csharp
// Your .csproj only references Cosmos DB SDK
<ItemGroup>
  <PackageReference Include="Microsoft.Azure.Cosmos" Version="3.47.0" />
  <!-- Missing Newtonsoft.Json reference! -->
</ItemGroup>

// Build error:
```

**Correct:**


```xml
<!-- Standard .csproj projects -->
<ItemGroup>
  <PackageReference Include="Microsoft.Azure.Cosmos" Version="3.47.0" />
  <PackageReference Include="Newtonsoft.Json" Version="13.0.4" />
</ItemGroup>
```

```xml
<!-- Directory.Packages.props -->
<Project>
  <ItemGroup>
    <PackageVersion Include="Microsoft.Azure.Cosmos" Version="3.47.0" />
    <PackageVersion Include="Newtonsoft.Json" Version="13.0.4" />
  </ItemGroup>
</Project>
```

### 4.32 Use the Patch API for atomic counter increments

**Impact: HIGH** (eliminates read-modify-write for counters; reduces RU cost and eliminates concurrency conflicts)

## Use the Patch API for atomic counter increments

**Impact: HIGH (eliminates read-modify-write for counters; reduces RU cost and eliminates concurrency conflicts)**

For fields that act as counters (view counts, rating totals, like counts), `patchItem` with `CosmosPatchOperations.incr()` performs a server-side atomic increment without a prior read. This is cheaper (no read RU), faster, and free of the ETag conflict/retry cycle.

**Incorrect (read-modify-write for counters):**

```java
// ❌ Read-modify-write: 1 read RU + 1 write RU, subject to ETag conflicts at scale
CosmosItemResponse<Video> resp = container.readItem(videoId,
    new PartitionKey(videoId), Video.class).block();
Video video = resp.getItem();
video.setViews(video.getViews() + 1);
container.upsertItem(video, new PartitionKey(videoId), null).block();
```

**Correct (Patch API — server-side atomic increment):**


```java
// ✅ Atomic increment — no read required, no ETag conflict possible
CosmosPatchOperations ops = CosmosPatchOperations.create()
    .increment("/views", 1);      // Atomic add, server-side

container.patchItem(
    videoId,
```

```java
// ✅ Patch multiple counters in one round-trip (e.g., rate-video: two fields)
CosmosPatchOperations ratingOps = CosmosPatchOperations.create()
    .increment("/ratingsCount", 1)
    .increment("/ratingsTotal", ratingValue);

videosContainer.patchItem(
```

### 4.33 Configure Preferred Regions for Availability

**Impact: HIGH** (enables automatic failover, reduces latency)

## Configure Preferred Regions for Availability

Configure preferred regions in priority order for multi-region deployments. The SDK automatically routes to available regions during outages.

**Incorrect (no region configuration):**

```csharp
// No region preference - SDK uses account's default write region
var client = new CosmosClient(connectionString);

// Problems:
// - May route to distant region (high latency)
```

**Correct (explicit region configuration):**


```csharp
// Configure preferred regions in order of preference
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationName = "MyApp",
    
    // SDK tries regions in order until one succeeds
```

```csharp
// Dynamic region based on deployment
public static CosmosClient CreateClient(string connectionString, string deploymentRegion)
{
    var preferredRegions = deploymentRegion switch
    {
        "westus" => new List<string> { Regions.WestUS2, Regions.EastUS2, Regions.WestEurope },
```

> Cross-ref: See `sdk-diagnostics` for capturing diagnostics.

### 4.34 Include aiohttp When Using Python Async SDK

**Impact: HIGH** (prevents application startup failure)

## Include aiohttp When Using Python Async SDK

When using the Azure Cosmos DB Python SDK's async client (`azure.cosmos.aio`), you **must** explicitly install `aiohttp` as a dependency. The `azure-cosmos` package does not automatically install `aiohttp` — it is an optional dependency required only for async operations.

**Incorrect (missing aiohttp — application will crash on startup):**

```txt
# requirements.txt
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
azure-cosmos>=4.6.0
```

```python
# main.py — this import will fail at runtime without aiohttp
from azure.cosmos.aio import CosmosClient
```

Error: `ModuleNotFoundError: No module named 'aiohttp'`

**Correct (aiohttp explicitly listed):**

```txt
# requirements.txt
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
azure-cosmos>=4.6.0
aiohttp>=3.9.0
```

```python
# main.py — works correctly with aiohttp installed
from azure.cosmos.aio import CosmosClient
```

**Alternative — use the sync client if async is not needed:**

```python
# No aiohttp required for synchronous usage
from azure.cosmos import CosmosClient
```

Reference: [Azure Cosmos DB Python SDK](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/sdk-python)

### 4.35 Never share a single CosmosItemRequestOptions instance across multiple createItem calls

**Impact: HIGH** (causes wrong partition key to be sent, producing silent data corruption or 400/404 errors)

## Never share a single CosmosItemRequestOptions instance across multiple createItem calls

**Impact: HIGH (causes wrong partition key to be sent, producing silent data corruption or 400/404 errors)**

`CosmosItemRequestOptions` is a mutable object. The SDK may mutate the options object internally during request preparation (e.g., stamping the resolved partition key).

**Incorrect (shared mutable options — second call sends wrong partition key):**

```java
// ❌ Anti-pattern: one options instance reused for two different createItem calls
CosmosItemRequestOptions options = new CosmosItemRequestOptions()
    .setIfNoneMatchETag("*");

// First call: writes UserCredentials with PK = email
credentialsContainer.createItem(credentials, new PartitionKey(email), options).block();
```

**Correct (separate instance per call):**


```java
// ✅ Each createItem gets its own fresh options instance
CosmosItemRequestOptions credsOptions = new CosmosItemRequestOptions()
    .setIfNoneMatchETag("*");
CosmosItemRequestOptions userOptions = new CosmosItemRequestOptions()
    .setIfNoneMatchETag("*");

```

```java
// ✅ Or construct inline to make sharing structurally impossible
credentialsContainer.createItem(
    credentials, new PartitionKey(email),
    new CosmosItemRequestOptions().setIfNoneMatchETag("*")).block();

usersContainer.createItem(
```

### 4.36 Handle 429 Errors with Retry-After

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
```

**Correct (leverage SDK's built-in retry):**


```csharp
// Configure client with appropriate retry settings
var cosmosClient = new CosmosClient(connectionString, new CosmosClientOptions
{
    // SDK automatically retries 429s up to this many times
    MaxRetryAttemptsOnRateLimitedRequests = 9,
    
```

```csharp
// Log throttling for monitoring and capacity planning
public async Task<Order> GetOrderWithDiagnostics(string orderId, string customerId)
{
    try
    {
        var response = await _container.ReadItemAsync<Order>(
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
> Cross-ref: See `sdk-diagnostics` for capturing diagnostics.
> Cross-ref: See `sdk-429-retry` for retry/throttle handling.

### 4.37 Use consistent enum serialization between Cosmos SDK and application layer

**Impact: CRITICAL** (mismatched enum storage causes queries to silently return empty results)

## Use Consistent Enum Serialization

Cosmos DB SDK default stores enums as integers, but many frameworks (ASP.NET Core, Spring Boot) serialize as strings. This mismatch causes queries to silently return empty results.

**Incorrect (default integer storage — queries fail silently):**

```csharp
// Stored as {"status": 1} but queried with "Active" → no results
public enum OrderStatus { Pending, Active, Completed }
public class Order { public OrderStatus Status { get; set; } }
// SELECT * FROM c WHERE c.status = "Active" → 0 results (stored as 1)
```

**Correct (explicit string serialization):**

```csharp
// .NET — System.Text.Json
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum OrderStatus { Pending, Active, Completed }

// Or configure globally on CosmosClient
var options = new CosmosClientOptions {
    SerializerOptions = new CosmosSerializationOptions {
        PropertyNamingPolicy = CosmosPropertyNamingPolicy.CamelCase
    }
};
// Use [JsonConverter(typeof(JsonStringEnumConverter))] on each enum
```

```java
// Java — Jackson annotation
@JsonFormat(shape = JsonFormat.Shape.STRING)
public enum OrderStatus { PENDING, ACTIVE, COMPLETED }
```

**Key rule:** Pick one (string or integer) and use it everywhere — SDK, queries, and API layer. String is safer for readability and cross-system compatibility.

Reference: See `query-parameterize` for parameterized queries.

### 4.38 Reuse CosmosClient as Singleton

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
```

```csharp
// For Azure Functions (using static initialization)
public static class CosmosDbFunction
{
    private static readonly Lazy<CosmosClient> _lazyClient = new(() =>
    {
        var connectionString = Environment.GetEnvironmentVariable("CosmosDbConnection");
        return new CosmosClient(connectionString);
```

### 4.39 Annotate entities for Spring Data Cosmos with @Container, @PartitionKey, and String IDs

**Impact: CRITICAL** (prevents startup failures and data access errors in Spring Data Cosmos applications)

## Annotate entities for Spring Data Cosmos with @Container, @PartitionKey, and String IDs

Spring Data Cosmos requires specific annotations on entity classes. JPA annotations (`@Entity`, `@Table`, `@Column`, `@JoinColumn`) are not recognized.

**Incorrect (JPA annotations — not recognized by Cosmos):**

```java
import jakarta.persistence.*;

@Entity
@Table(name = "owners")
public class Owner {

    @Id
```

**Correct (Spring Data Cosmos annotations):**


```java
import com.azure.spring.data.cosmos.core.mapping.Container;
import com.azure.spring.data.cosmos.core.mapping.PartitionKey;
import com.azure.spring.data.cosmos.core.mapping.GeneratedValue;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import org.springframework.data.annotation.Id;

@JsonIgnoreProperties(ignoreUnknown = true)
```

```java
// Wrong: Integer IDs don't work with CosmosRepository<Entity, String>
   private Integer id;

   // Correct: Always use String IDs
   @Id
   @GeneratedValue
   private String id;
```

### 4.40 Use CosmosRepository correctly and handle Iterable return types

**Impact: HIGH** (prevents ClassCastException and query failures in Spring Data Cosmos repositories)

## Use CosmosRepository correctly and handle Iterable return types

`CosmosRepository` differs from `JpaRepository` in return types, pagination support, and query method conventions. Common pitfalls include casting `Iterable` to `List` directly and using JPA-style pagination.

**Incorrect (JPA repository patterns that fail with Cosmos):**

```java
// JpaRepository extends PagingAndSortingRepository — Cosmos does not
public interface OwnerRepository extends JpaRepository<Owner, Integer> {
    Page<Owner> findByLastNameStartingWith(String lastName, Pageable pageable);
    List<PetType> findPetTypes();
}
```

**Correct (CosmosRepository patterns):**


```java
import com.azure.spring.data.cosmos.repository.CosmosRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface OwnerRepository extends CosmosRepository<Owner, String> {
    List<Owner> findByLastNameStartingWith(String lastName); // No Pageable
```

```java
// WRONG — ClassCastException: BlockingIterable cannot be cast to java.util.List
default List<Entity> findAllSorted() {
    return (List<Entity>) this.findAll();
}

// CORRECT — Use StreamSupport to convert
```

---

## 5. Indexing Strategies

**Impact: MEDIUM-HIGH**

### 5.1 Composite Index Directions Must Match ORDER BY

**Impact: HIGH** (prevents query failures and rejected sorts)

## Composite Index Directions Must Match ORDER BY

Every composite index entry must specify sort directions that **exactly match** the `ORDER BY` clause of the queries it serves. If the directions don't match, Cosmos DB will reject the query or fall back to an expensive scan.

**Incorrect (direction mismatch — query fails):**

```python
# Composite index defined as descending
indexing_policy = {
    "compositeIndexes": [
        [{"path": "/score", "order": "descending"}]
    ]
}
```

**Correct (directions match exactly, with both orderings):**


```python
# Define BOTH directions to support ASC and DESC queries
indexing_policy = {
    "compositeIndexes": [
        [{"path": "/score", "order": "descending"}],
        [{"path": "/score", "order": "ascending"}]
    ]
```

```csharp
// Always provide both sort directions for each composite index pattern
CompositeIndexes =
{
    // For ORDER BY score DESC
    new Collection<CompositePath>
    {
```

### 5.2 Use Composite Indexes for ORDER BY

**Impact: HIGH** (enables sorted queries, reduces RU)

## Use Composite Indexes for ORDER BY

Create composite indexes for queries with ORDER BY on multiple properties. Without them, queries fail in production (emulator silently permits them).

**Incorrect (ORDER BY without composite index):**

```csharp
// Fails in production: "Order by query does not have a corresponding composite index"
var query = "SELECT * FROM c WHERE c.status = 'active' ORDER BY c.createdAt DESC, c.priority ASC";
```

**Correct (composite index declared):**


```json
{
    "indexingMode": "consistent",
    "compositeIndexes": [
        [
            { "path": "/status", "order": "ascending" },
            { "path": "/createdAt", "order": "descending" }
```

```csharp
// Common patterns needing composites:
// Filter + Sort: WHERE status = 'x' ORDER BY date DESC
// Multi-column sort: ORDER BY lastName ASC, firstName ASC
// Range + Sort: WHERE price >= 10 ORDER BY rating DESC
```

### 5.3 Exclude Unused Index Paths

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
```

**Correct (exclude-all-first, then include back):**


```csharp
// Exclude everything, then include only what you query
var indexingPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,
    Automatic = true,
    
    // Start with exclude all — no field is indexed by default
```

```json
// JSON equivalent indexing policy
{
    "indexingMode": "consistent",
    "automatic": true,
    "excludedPaths": [
        { "path": "/*" }
    ],
```

### 5.4 Understand Indexing Modes

**Impact: MEDIUM** (balances write speed vs query consistency)

## Understand Indexing Modes

## Understand Indexing Modes

Choose the appropriate indexing mode based on your workload. Consistent mode ensures query results are current; None disables indexing entirely.

**Incorrect:**

```csharp
// CONSISTENT MODE (Default - recommended for most cases)
// Indexes are updated synchronously with writes
var consistentPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,  // Default
    Automatic = true
};
```

**Correct:**


```csharp
// Typical transactional workload - use Consistent
var ordersPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,
    Automatic = true,
    IncludedPaths = { new IncludedPath { Path = "/*" } }
};

```

```csharp
// High-volume telemetry ingestion - consider None
var telemetryPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.None,  // Maximum write throughput
    Automatic = false
};

var telemetryContainer = new ContainerProperties
```

### 5.5 Use Correct Indexing Path Syntax

**Impact: HIGH** (prevents container creation failures from invalid paths)

## Use Correct Indexing Path Syntax

Cosmos DB indexing paths use specific notation for scalars, arrays, and wildcards. Using the wrong notation causes container creation to fail with a BadRequest error.

**Incorrect (using `*` for array traversal):**

```json
// ❌ WRONG — * cannot be used mid-path for array traversal
// This causes: "The indexing path could not be accepted, failed near position ..."
{
    "excludedPaths": [
        { "path": "/lineItems/*/productSnapshot/?" },
        { "path": "/orders/*/items/?" }
```

**Correct (using `[]` for array traversal):**


```json
// ✅ CORRECT — use [] to traverse array elements
{
    "excludedPaths": [
        { "path": "/lineItems/[]/productSnapshot/?" },
        { "path": "/orders/[]/items/?" }
    ]
```

```json
// ✅ CORRECT — * at the END of a path matches everything below
{
    "includedPaths": [
        { "path": "/*" }
    ],
    "excludedPaths": [
```

### 5.6 Choose Appropriate Index Types

**Impact: MEDIUM** (optimizes query performance)

## Choose Appropriate Index Types

## Choose Appropriate Index Types

Understand when to use different index types. Range indexes support equality, range, and ORDER BY; Hash indexes are deprecated.

**Incorrect:**

```csharp
// Range Index (DEFAULT - recommended for most cases)
// Supports: =, >, <, >=, <=, !=, ORDER BY, JOINs
{
    "includedPaths": [
        {
            "path": "/price/?",
            "indexes": [
```

**Correct:**


```csharp
// Modern Cosmos DB automatically uses optimal index types
// You typically just specify paths, not index kinds
var indexingPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,
    Automatic = true,
    
    // Just specify paths - Cosmos DB handles index types
```

```csharp
// For special query patterns, add composite or spatial indexes

var indexingPolicy = new IndexingPolicy
{
    // Standard range indexes (automatic)
    IncludedPaths =
    {
        new IncludedPath { Path = "/*" }  // Index everything by default
```

### 5.7 Add Spatial Indexes for Geo Queries

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
```

**Correct (spatial index for location queries):**


```csharp
// Create indexing policy with spatial index
var indexingPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,
    
    // Include path with spatial index
```

```json
// JSON indexing policy with spatial index
{
    "indexingMode": "consistent",
    "spatialIndexes": [
        {
            "path": "/location/?",
```

> Cross-ref: See `query-parameterize` for parameterized queries.

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
```

**Correct (autoscale for variable workloads):**


```csharp
// Autoscale with max 10,000 RU/s
var containerProperties = new ContainerProperties
{
    Id = "orders",
    PartitionKeyPath = "/customerId"
};
```

```csharp
// Check current autoscale settings
var throughputResponse = await container.ReadThroughputAsync(new RequestOptions());
var autoscaleSettings = throughputResponse.Resource.AutoscaleMaxThroughput;
Console.WriteLine($"Autoscale max: {autoscaleSettings} RU/s");
Console.WriteLine($"Current: {throughputResponse.Resource.Throughput} RU/s");
```

### 6.2 Understand Burst Capacity

**Impact: MEDIUM** (handles short traffic spikes)

## Understand Burst Capacity

Cosmos DB provides burst capacity to handle short traffic spikes above provisioned throughput. Understand how it works to avoid unexpected throttling.

**Incorrect (relying on burst for sustained load):**

```csharp
// Provisioned 1,000 RU/s but regularly need 1,500 RU/s
var container = await database.CreateContainerAsync(props, throughput: 1000);

// Hoping burst will cover:
// - Hour 1: Burst bucket fills from overnight

```

**Correct (provision for actual sustained needs):**


```csharp
// Option 1: Provision for peak sustained load
await database.CreateContainerAsync(props, throughput: 1500);

// Option 2: Use autoscale for variable loads
await database.CreateContainerAsync(
    props,
```

```csharp
// Monitor burst usage
// Azure Monitor metric: "Normalized RU Consumption"

// Detect burst usage in code
var response = await container.ReadItemAsync<Order>(id, pk);
// Check if operation used more than provisioned share
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.

### 6.3 Choose Container vs Database Throughput

**Impact: MEDIUM** (optimizes cost and isolation)

## Choose Container vs Database Throughput

Decide between container-level (dedicated) and database-level (shared) throughput based on workload isolation needs and cost optimization.

**Incorrect (one-size-fits-all allocation):**

```csharp
// Anti-pattern: dedicated throughput for every container including low-traffic ones
var logsContainer = await database.CreateContainerAsync(
    new ContainerProperties("logs", "/date"),
    throughput: 400);  // Paying minimum 400 RU/s for rarely-used container
// 20 low-traffic containers × 400 RU/s = 8,000 RU/s wasted
```

**Correct (choose based on workload):**

```csharp
// Database-level: share RU across low-traffic containers
var database = await cosmosClient.CreateDatabaseAsync("my-db", throughput: 5000);

// Container-level: dedicate RU for critical/high-volume containers
var ordersContainer = await database.CreateContainerAsync(
    new ContainerProperties("orders", "/customerId"),
    throughput: 10000);  // Dedicated, not shared

// Other containers share database throughput pool
var productsContainer = await database.CreateContainerAsync(
    new ContainerProperties("products", "/categoryId"));  // Shared
```

**Decision guide:** Container-level for critical/predictable workloads or tenant isolation. Database-level for many low-traffic containers or dev/test. Hybrid for mixed scenarios.

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
```

**Correct (data-driven provisioning):**


```csharp
// Step 1: Calculate RU requirements

// Point read (by id + partition key): ~1 RU for 1KB item
// Point write: ~5 RU for 1KB item  

// Example calculation:
```

```csharp
// Step 2: Monitor and adjust

// Check RU consumption in code
var response = await container.ReadItemAsync<Order>(id, new PartitionKey(pk));
Console.WriteLine($"Read consumed: {response.RequestCharge} RU");

```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.

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
```

**Correct (serverless for low/sporadic traffic):**


```csharp
// Create serverless account (at account level, not container)
// No throughput specification - purely consumption-based

// Container creation in serverless account (no throughput parameter)
var containerProperties = new ContainerProperties
{
```

```csharp
// Serverless is set at account level, not container
// ARM template for serverless account
{
    "type": "Microsoft.DocumentDB/databaseAccounts",
    "apiVersion": "2021-10-15",
    "name": "my-serverless-account",
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.

---

## 7. Global Distribution

**Impact: MEDIUM**

### 7.1 Implement Conflict Resolution

**Impact: MEDIUM** (ensures data integrity in multi-region)

## Implement Conflict Resolution

Configure appropriate conflict resolution policies for multi-region write scenarios. Without proper handling, data can be lost.

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
```

```csharp
// Option 2: Stored procedure for custom resolution
var containerWithCustom = new ContainerProperties
{
    Id = "inventory",
    PartitionKeyPath = "/productId",
    ConflictResolutionPolicy = new ConflictResolutionPolicy
    {
```

### 7.2 Choose Appropriate Consistency Level

**Impact: HIGH** (balances latency, availability, consistency)

## Choose Appropriate Consistency Level

## Choose Appropriate Consistency Level

Select the consistency level that matches your application's requirements. Each level has different tradeoffs for latency, availability, and consistency.

**Incorrect:**

```csharp
// STRONG - Linearizable reads
// Reads always see most recent committed write
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ConsistencyLevel = ConsistencyLevel.Strong
});
// Use: Financial transactions, inventory management
```

**Correct:**


```csharp
// Example: E-commerce platform

// Orders container - Strong or Session
// User must see their order immediately after placing
var ordersClient = new CosmosClient(connectionString, new CosmosClientOptions
{
    ConsistencyLevel = ConsistencyLevel.Session  // Recommended
});
```

```csharp
// Session consistency with session token (most common pattern)
// SDK handles session tokens automatically within a client instance

// For scenarios where you need to share session across requests:
var response = await container.CreateItemAsync(order);
var sessionToken = response.Headers["x-ms-session-token"];

// Later request can use same session for read-your-writes
```

### 7.3 Configure Automatic Failover

**Impact: HIGH** (ensures availability during outages)

## Configure Automatic Failover

Enable automatic failover for high availability. Without it, regional outages require manual intervention.

**Incorrect (no failover configuration):**

```csharp
// Multi-region account without automatic failover
// If primary region goes down:

// ARM template without failover
{
    "properties": {
```

**Correct (automatic failover enabled):**


```csharp
// ARM template with automatic failover
{
    "type": "Microsoft.DocumentDB/databaseAccounts",
    "apiVersion": "2021-10-15",
    "name": "my-cosmos-account",
    "properties": {
```

```csharp
// Configure SDK to handle failovers gracefully
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationName = "MyApp",
    
    // SDK will automatically discover new endpoints after failover
```

### 7.4 Configure Multi-Region Writes

**Impact: HIGH** (enables local writes, high availability)

## Configure Multi-Region Writes

Enable multi-region writes for globally distributed applications. Allows writes to any region with automatic conflict resolution.

**Incorrect (single write region):**

```csharp
// Default: Single write region
// All writes must travel to one region

// No multi-region write configuration
var client = new CosmosClient(connectionString);

```

**Correct (multi-region writes enabled):**


```csharp
// Step 1: Enable multi-region writes on account (Azure Portal or ARM)
{
    "type": "Microsoft.DocumentDB/databaseAccounts",
    "properties": {
        "enableMultipleWriteLocations": true,  // Enable multi-region writes
        "locations": [
```

```csharp
// Step 3: Handle conflicts (Last Writer Wins is default)
// For custom conflict resolution, configure container

// Last Writer Wins (LWW) - Default
// Uses _ts (timestamp) to determine winner
var containerWithLWW = new ContainerProperties
```

### 7.5 Add Read Regions Near Users

**Impact: MEDIUM** (reduces read latency globally)

## Add Read Regions Near Users

Add read regions in geographic locations close to your users. Reads can be served from any region, reducing latency for global users.

**Incorrect (single region for global users):**

```csharp
// Only one region configured
// Users from all locations read from single region

{
    "properties": {
        "locations": [
```

**Correct (read regions near user populations):**


```csharp
// Add read replicas near major user bases
{
    "type": "Microsoft.DocumentDB/databaseAccounts",
    "properties": {
        "locations": [
            // Primary write region
```

```csharp
// Configure SDK for region-local reads
// Deployed in Europe - prioritize European region
var europeClient = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationPreferredRegions = new List<string>
    {
```

> Cross-ref: See `sdk-diagnostics` for capturing diagnostics.

### 7.6 Configure Zone Redundancy for High Availability

**Impact: HIGH** (eliminates availability zone failures, increases SLA to 99.995%)

## Configure Zone Redundancy for High Availability

Enable zone redundancy to protect against availability zone failures. Zone-redundant accounts distribute replicas across multiple availability zones within a region.

**Incorrect (no zone redundancy):**

```json
// Single-region account without zone redundancy
// If an availability zone fails:
{
    "type": "Microsoft.DocumentDB/databaseAccounts",
    "properties": {
        "locations": [
```

**Correct (zone redundancy enabled):**


```json
// ARM template with zone redundancy
{
    "type": "Microsoft.DocumentDB/databaseAccounts",
    "apiVersion": "2023-04-15",
    "name": "my-cosmos-account",
    "properties": {
```

```bicep
// Bicep template with zone redundancy
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: 'my-cosmos-account'
  location: 'East US'
  properties: {
    locations: [
```

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
```

```csharp
// Step 2: Key metrics to monitor in Azure Monitor

// a) Normalized RU Consumption (% of provisioned used)
// Alert if > 90% sustained - indicates need to scale

// b) Total Requests by Status Code
// Alert on 429s (throttling) and 5xx (errors)
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.

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

// ARM template for diagnostic settings
```

```csharp
// Application-level diagnostic logging
public class DiagnosticLoggingRepository
{
    private readonly Container _container;
    private readonly ILogger _logger;
    
    public async Task<T> ExecuteWithDiagnostics<T>(
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
> Cross-ref: See `sdk-diagnostics` for capturing diagnostics.

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
```

**Correct (tracking latency distribution):**


```csharp
public async Task<Order> GetOrder(string orderId, string customerId)
{
    var sw = Stopwatch.StartNew();
    var response = await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
    sw.Stop();
    
    var clientLatency = sw.ElapsedMilliseconds;
```

```csharp
// Track percentiles with Application Insights
public class LatencyTracker
{
    private readonly TelemetryClient _telemetry;
    private readonly ConcurrentBag<double> _recentLatencies = new();
    private readonly Timer _reportTimer;
    
```

> Cross-ref: See `sdk-diagnostics` for capturing diagnostics.

### 8.4 Track RU Consumption

**Impact: MEDIUM** (enables cost optimization)

## Track RU Consumption

Monitor Request Unit (RU) consumption to identify inefficient operations. Every response exposes `RequestCharge` — capture it.

**Incorrect (ignoring RU — no cost visibility):**

```csharp
// ❌ No visibility into whether this costs 1 RU or 100 RU
var result = await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
return result.Resource;
```

**Correct (tracking RU per operation):**


```csharp
var response = await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
_logger.LogDebug("ReadItem {Id}: {RU} RU", orderId, response.RequestCharge);

// For queries — sum across pages, alert on expensive ones
double totalRU = 0;
while (iterator.HasMoreResults)
```

```typescript
// Node.js — requestCharge on every response
const response = await container.item(id, userId).read();
logger.debug({ op: 'ReadItem', ru: response.requestCharge });

// Query — sum across pages
let totalRU = 0;
```

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
```

```csharp
// Azure Monitor alert rule for throttling
// Create alert in Azure Portal or via ARM:
{
    "type": "Microsoft.Insights/metricAlerts",
    "properties": {
        "criteria": {
            "odata.type": "Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria",
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
> Cross-ref: See `sdk-diagnostics` for capturing diagnostics.
> Cross-ref: See `sdk-429-retry` for retry/throttle handling.

---

## 9. Design Patterns

**Impact: HIGH**

### 9.1 Use Point Reads for AI-Grounding and RAG Retrieval When ID Is Known

**Impact: HIGH** (1 RU point read vs ~2.5+ RU query per grounding fetch; reduces tool-call latency in LLM loops)

## Use Point Reads for AI-Grounding and RAG Retrieval When ID Is Known

In AI-grounded workloads an LLM tool-use loop typically resolves a concrete entity id (e.g., `orderId`, `sessionId`, `documentId`) from the user turn or tool-call arguments, then fetches the full document from Cosmos DB to build the grounding context for the model. Because the id and partition key are both known at call time, a point read should always be used instead of a query.

**Incorrect (query when id and partition key are both available from the tool call):**

```typescript
// ❌ Generic query — id is already known from the user turn / tool call
export async function groundOrderContext(orderId: string, userId: string) {
  const { resources: orders } = await ordersContainer.items
    .query<Order>({
      query: "SELECT * FROM c WHERE c.orderId = @o",
      parameters: [{ name: "@o", value: orderId }],
    })
```

**Correct (point read for the primary document, partition-scoped projection for related items):**


```typescript
// ✅ Point read for the order (id + partition key both known from tool call)
export async function groundOrderContext(orderId: string, userId: string) {
  const orderResp = await ordersContainer.item(orderId, userId).read<Order>();
  const order = orderResp.resource;
  if (!order) return null;

  // ✅ Partition-key-scoped projection for related event list
```

```python
# ✅ Point read — 1 RU, no query engine overhead
def ground_order_context(order_id: str, user_id: str):
    order = orders_container.read_item(item=order_id, partition_key=user_id)
    return build_grounding_context(order)
```

### 9.2 Use Background Tasks for Non-Blocking Chat History Storage

**Impact: MEDIUM** (reduces API response latency by 50-200ms per request)

## Use Background Tasks for Non-Blocking Chat History Storage

**Impact: MEDIUM (reduces API response latency by 50-200ms per request)**

After a LangGraph agent produces a response, storing chat history and debug logs in Cosmos DB is important for the UI but not for the immediate API response. Use FastAPI's `BackgroundTasks` to defer these writes, returning the agent response to the user immediately.

**Incorrect (blocking writes before returning response):**

```python
from fastapi import FastAPI

@app.post("/chat/{session_id}")
async def chat(session_id: str, user_message: str):
    response = await graph.ainvoke(state, config, stream_mode="updates")
    messages = extract_response(response)
```

**Correct (defer writes with BackgroundTasks):**


```python
from fastapi import FastAPI, BackgroundTasks

def process_post_response(messages, session_id, tenant_id, user_id, active_agent):
    """Runs after the response is sent to the client."""
    for msg in messages:
        store_chat_history(msg)
```

### 9.3 Use Change Feed for cross-partition query optimization with materialized views

**Impact: HIGH** (eliminates cross-partition query overhead for admin/analytics scenarios)

## Use Change Feed for cross-partition query optimization with materialized views

When frequent cross-partition queries are needed (admin dashboards, lookups by non-PK attributes), use Change Feed to maintain a separate container optimized for those patterns, or use Global Secondary Index (GSI).

**Incorrect (expensive cross-partition fan-out):**

```csharp
// Fans out to ALL partitions — expensive at scale
var query = container.GetItemQueryIterator<Order>(
    "SELECT * FROM c WHERE c.status = 'Pending' ORDER BY c.createdAt DESC");
```

**Correct (materialized view via Change Feed):**


```csharp
// Source: "orders" partitioned by /customerId
// Target: "orders-by-status" partitioned by /status — single-partition queries
ChangeFeedProcessor processor = ordersContainer
    .GetChangeFeedProcessorBuilder<Order>("statusViewProcessor", async (changes, ct) =>
    {
        foreach (Order order in changes)
```

```csharp
// ❌ counter += 1 will double-count on replay
profile.TotalGamesPlayed += 1;
profile.TotalScore += score.Score;
```

### 9.4 Use count-based or cached rank approaches instead of full partition scans for ranking

**Impact: HIGH** (reduces rank lookups from O(N) partition scans to O(1) or O(log N) operations)

## Use count-based or cached rank approaches instead of full partition scans for ranking

## Efficient Ranking in Cosmos DB

When implementing leaderboards or rankings, avoid scanning an entire partition to determine a single player's rank. Full partition scans for rank lookups are an anti-pattern that becomes unsustainable at scale.

**Incorrect:**

```csharp
// Anti-pattern: Reads ALL entries in a partition to find one player's rank
// At 500K players, this consumes thousands of RU and takes seconds
public async Task<int> GetPlayerRankAsync(string leaderboardKey, string playerId)
{
    var query = new QueryDefinition(
        "SELECT c.playerId, c.bestScore FROM c WHERE c.type = @type ORDER BY c.bestScore DESC"
    ).WithParameter("@type", "leaderboardEntry");
```

**Correct:**


```csharp
// Count players with higher scores to determine rank
// Single query, ~3-5 RU regardless of partition size
public async Task<int> GetPlayerRankAsync(string leaderboardKey, string playerId, int playerScore)
{
    var countQuery = new QueryDefinition(
        "SELECT VALUE COUNT(1) FROM c WHERE c.type = @type AND c.bestScore > @score"
    )
    .WithParameter("@type", "leaderboardEntry")
```

```csharp
// Maintain a rank cache that is periodically updated
// Leaderboard entry includes pre-computed rank
public class RankedLeaderboardEntry
{
    [JsonPropertyName("id")]
    public string Id { get; set; }  // playerId

    [JsonPropertyName("leaderboardKey")]
```

### 9.5 Tag AI Messages with Agent Name for API Response Attribution

**Impact: MEDIUM** (enables API layer to report which agent generated a response for UI display and logging)

## Tag AI Messages with Agent Name for API Response Attribution

**Impact: MEDIUM (enables API layer to report which agent generated a response for UI display and logging)**

`create_react_agent` does not set the `name` field on AI messages it produces. If the API layer needs to report which agent generated a response (e.g., for UI display or logging), it has no way to determine this from the message itself.

**Incorrect (no attribution — API cannot determine which agent responded):**

```python
async def call_product_search(state, config):
    response = await product_search_agent.ainvoke(state)
    # BAD: No way to tell which agent produced this response at the API layer
    return Command(update=response, goto=END)
```

**Correct (tag last AI message with agent name):**


```python
def _tag_last_ai_message(response: dict, agent_name: str) -> dict:
    """Set `name` on the last AI message for API-layer attribution."""
    msgs = response.get("messages", [])
    for msg in reversed(msgs):
        if hasattr(msg, "type") and msg.type == "ai" and msg.content:
            msg.name = agent_name
```

### 9.6 Persist Active Agent in Cosmos DB for Deterministic Routing

**Impact: HIGH** (eliminates LLM re-classification overhead and prevents routing drift)

## Persist Active Agent in Cosmos DB for Deterministic Routing

**Impact: HIGH (eliminates LLM re-classification overhead and prevents routing drift)**

In multi-agent systems, once a user has been routed to a specialist agent, persist the active agent name in Cosmos DB alongside the conversation session. On subsequent messages, perform a point read to retrieve the active agent instead of re-invoking the coordinator LLM to classify intent.

**Incorrect (re-classify every message through the coordinator):**

```python
async def route_message(state, config):
    # BAD: Every user message goes through the coordinator LLM for classification
    # Adds latency and may incorrectly re-route mid-conversation
    response = await coordinator_agent.ainvoke(state)
    return determine_agent_from_response(response)
```

**Correct (async point read for active agent, coordinator only for new conversations):**


```python
import asyncio
from azure.cosmos import CosmosClient

def _read_active_agent_from_db(tenant_id: str, user_id: str, thread_id: str) -> str:
    """Synchronous helper — runs in a thread pool."""
    try:
        item = container.read_item(
```

```python
from azure.cosmos import PartitionKey

def patch_active_agent(tenant_id, user_id, thread_id, new_agent):
    """Partial update — only modifies the activeAgent field (minimal RU cost)."""
    container.patch_item(
        item=thread_id,
        partition_key=[tenant_id, user_id, thread_id],
```

### 9.7 Wrap Cosmos DB Sync Calls in asyncio.to_thread for LangGraph Routing Functions

**Impact: CRITICAL** (prevents event loop blocking that causes all concurrent requests to hang)

## Wrap Cosmos DB Sync Calls in asyncio.to_thread for LangGraph Routing Functions

**Impact: CRITICAL (prevents event loop blocking that causes all concurrent requests to hang)**

LangGraph's `add_conditional_edges` routing function runs inside the async event loop. If the routing function calls `DefaultAzureCredential` or `container.read_item()` synchronously, it blocks the entire event loop — causing all concurrent requests to hang and potentially triggering timeouts.

**Incorrect (synchronous Cosmos DB call blocks the event loop):**

```python
from azure.cosmos import CosmosClient

def get_active_agent(state, config) -> str:
    thread_id = config["configurable"]["thread_id"]
    # BAD: Blocks the event loop when called from LangGraph's async runtime
    item = container.read_item(item=thread_id, partition_key=thread_id)
```

**Correct (async wrapper with timeout and fallback):**


```python
import asyncio
from azure.cosmos import CosmosClient

def _read_active_agent_from_db(thread_id: str) -> str:
    """Synchronous helper — runs in a thread pool."""
    container = get_sync_container("ChatSessions")
```

### 9.8 Use asyncio.to_thread for Active Agent Writes in LangGraph Node Functions

**Impact: HIGH** (prevents event loop blocking during Cosmos DB upserts in async node functions)

## Use asyncio.to_thread for Active Agent Writes in LangGraph Node Functions

**Impact: HIGH (prevents event loop blocking during Cosmos DB upserts in async node functions)**

When saving the active agent after a transfer (inside a LangGraph node function), using the sync Cosmos DB SDK also blocks the event loop. Node functions in LangGraph run as coroutines.

**Incorrect (synchronous upsert blocks the event loop inside an async node):**

```python
async def call_agent(state, config):
    response = await agent.ainvoke(state)
    # BAD: Blocks the event loop during upsert
    container.upsert_item({
        "id": thread_id,
        "sessionId": thread_id,
```

**Correct (non-blocking write with asyncio.to_thread):**


```python
import asyncio
import logging

logger = logging.getLogger(__name__)

async def save_active_agent_to_db_async(
```

### 9.9 Store Chat History Separately from LangGraph Checkpoints

**Impact: MEDIUM** (enables efficient message retrieval and agent attribution)

## Store Chat History Separately from LangGraph Checkpoints

**Impact: MEDIUM (enables efficient message retrieval and agent attribution)**

LangGraph's checkpointer (CosmosDBSaver) stores full graph state for resumption, but it is not optimized for retrieving displayable chat history. Checkpoint data contains internal graph metadata, tool messages, system messages, and duplicate entries from each node execution.

**Incorrect (reading chat history from the checkpointer store):**

```python
@app.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str):
    config = {"configurable": {"thread_id": session_id, "checkpoint_ns": ""}}
    # BAD: Checkpointer stores ALL graph state — tool messages, system messages,
    # intermediate states, duplicates from each node. Expensive to scan and filter.
    checkpoints = [cp async for cp in checkpointer.alist(config)]
```

**Correct (store displayable history in a dedicated container):**


```python
from azure.cosmos import CosmosClient

# Dedicated container with partition key /sessionId for efficient retrieval
history_container = database.get_container_client("ChatHistory")

def store_chat_message(session_id: str, tenant_id: str, user_id: str, 
```

### 9.10 Initialize LangGraph Agents in FastAPI Startup with Retry

**Impact: HIGH** (prevents request failures when dependent services are not yet ready)

## Initialize LangGraph Agents in FastAPI Startup with Retry

**Impact: HIGH (prevents request failures when dependent services are not yet ready)**

LangGraph agents that depend on external services (MCP servers, Cosmos DB, Azure OpenAI) must be initialized asynchronously during application startup, not at module import time or on first request. Use FastAPI's startup event (or lifespan) with retry logic to handle cases where dependent services take time to become available (e.g., in container orchestration environments where services start in parallel).

**Incorrect (initialize at module level — blocks import, no retry):**

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

# BAD: Runs at import time, fails if MCP server isn't ready yet
client = MultiServerMCPClient({"server": {"transport": "streamable_http", "url": mcp_url}})
tools = asyncio.run(load_tools(client))  # Blocks and may fail
```

**Correct (startup event with retry and fallback):**


```python
import asyncio
from fastapi import FastAPI, HTTPException

app = FastAPI()
_agents_ready = False

```

### 9.11 Use LangGraph Interrupt for Human-in-the-Loop Confirmation

**Impact: HIGH** (enables safe confirmation flows for sensitive operations)

## Use LangGraph Interrupt for Human-in-the-Loop Confirmation

**Impact: HIGH (enables safe confirmation flows for sensitive operations)**

When agents perform sensitive operations (e.g., money transfers, account creation, data deletion), use LangGraph's `interrupt()` mechanism to pause execution and wait for user confirmation. The graph state is persisted to Cosmos DB via the checkpointer, and execution resumes from the same point when the user responds.

**Incorrect (no confirmation — agent executes sensitive action immediately):**

```python
from langgraph.graph import StateGraph, MessagesState

async def call_transactions_agent(state: MessagesState, config):
    # BAD: Agent may call bank_transfer without user confirmation
    response = await transactions_agent.ainvoke(state)
    return {"messages": response["messages"]}
```

**Correct (interrupt pauses graph, state saved to Cosmos DB):**


```python
from langgraph.types import Command, interrupt
from langgraph.graph import StateGraph, MessagesState
from langchain_azure_cosmosdb import CosmosDBSaver

def human_node(state: MessagesState, config) -> None:
    """Pauses the graph and waits for the next user message."""
```

### 9.12 Use StateGraph with Conditional Edges for Multi-Agent Routing

**Impact: HIGH** (enables deterministic agent hand-off in multi-agent LangGraph applications)

## Use StateGraph with Conditional Edges for Multi-Agent Routing

**Impact: HIGH (enables deterministic agent hand-off in multi-agent LangGraph applications)**

When building multi-agent systems with LangGraph backed by Cosmos DB checkpointing, use `StateGraph` with `add_conditional_edges` to route between agents based on tool call results or persisted state. Each agent node should return a `Command` that updates state and directs the graph to the next node (e.g., a human-input node).

**Incorrect (linear chain — no dynamic routing between agents):**

```python
from langgraph.graph import StateGraph, START, MessagesState

builder = StateGraph(MessagesState)
builder.add_node("agent_a", call_agent_a)
builder.add_node("agent_b", call_agent_b)

# BAD: Fixed linear flow — cannot route dynamically
```

**Correct (conditional edges with dynamic routing):**


```python
from typing import Literal
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.types import Command
from langchain_azure_cosmosdb import CosmosDBSaver

async def call_agent_a(state: MessagesState, config) -> Command[Literal["agent_a", "human"]]:
    response = await agent_a.ainvoke(state)
```

```python
async def call_agent_a(state: MessagesState, config) -> Command[Literal["agent_a", "agent_b", "human"]]:
    response = await agent_a.ainvoke(state)

    # CRITICAL: Only check NEW messages added by this invocation
    existing_count = len(state.get("messages", []))
    new_messages = response.get("messages", [])[existing_count:]

```

### 9.13 Resume LangGraph from Checkpoint After Interrupt

**Impact: HIGH** (enables multi-turn conversations with persistent state)

## Resume LangGraph from Checkpoint After Interrupt

**Impact: HIGH (enables multi-turn conversations with persistent state)**

When a LangGraph graph pauses at an `interrupt()` node, the next user message must resume from the last checkpoint rather than starting fresh. Retrieve the last checkpoint, append the new user message, inject `langgraph_triggers` to signal which node to resume, and call `ainvoke` with `stream_mode="updates"`.

**Incorrect (always starts a fresh graph invocation):**

```python
@app.post("/chat/{session_id}")
async def chat(session_id: str, user_message: str):
    config = {"configurable": {"thread_id": session_id}}
    # BAD: Always starts from scratch — ignores prior conversation state
    state = {"messages": [{"role": "user", "content": user_message}]}
    response = await graph.ainvoke(state, config, stream_mode="updates")
```

**Correct (resume from last checkpoint when one exists):**


```python
@app.post("/chat/{session_id}")
async def chat(session_id: str, user_message: str):
    config = {"configurable": {"thread_id": session_id, "checkpoint_ns": ""}}

    # Check for existing checkpoint (prior conversation state)
    checkpoints = [cp async for cp in checkpointer.alist(config)]
```

### 9.14 Use a service layer to hydrate document references before rendering

**Impact: HIGH** (bridges document storage with frameworks expecting object graphs, prevents empty/null relationship data)

## Use a service layer to hydrate document references before rendering

When using ID-based references between Cosmos DB documents (see `model-relationship-references`), create a service layer that populates transient relationship properties before returning entities to controllers, templates, or API responses. Never return repository results directly to the presentation layer without hydrating relationships.

**Incorrect (controller accesses repository directly — empty relationships):**

```java
@Controller
public class VetController {

    @Autowired
    private VetRepository vetRepository;

    @GetMapping("/vets")
```

**Correct (service layer hydrates relationships):**


```java
@Service
public class VetService {

    private final VetRepository vetRepository;
    private final SpecialtyRepository specialtyRepository;

    public VetService(VetRepository vetRepository,
```

```java
@Controller
public class VetController {

    @Autowired
    private VetService vetService;  // ✅ Service, not repository

    @GetMapping("/vets")
```

---

## 10. Developer Tooling

**Impact: MEDIUM**

### 10.1 Use Azure Cosmos DB Emulator for local development and testing

**Impact: MEDIUM** (prevents accidental cloud usage and speeds up local iteration)

## Use Azure Cosmos DB Emulator for Local Development and Testing

Prefer the Azure Cosmos DB Emulator for local development, exploratory testing, and repeatable developer workflows. It avoids cloud cost during local work, keeps feedback loops fast, and reduces the risk of accidentally using shared or production resources while iterating.

**Incorrect (local development against cloud resources by default):**

```yaml
# Local development profile
azure:
  cosmos:
    endpoint: https://my-prod-account.documents.azure.com:443/
    key: ${COSMOS_KEY}
```

**Correct (default local development to the emulator):**

```yaml
# Local development profile
azure:
  cosmos:
    endpoint: https://localhost:8081/
    key: C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
```

Run the emulator locally or in Docker, and keep production endpoints in environment-specific profiles or deployment configuration. For SDK-specific SSL and gateway-mode details, also apply the linked emulator configuration rules.

Related rules:
- `sdk-emulator-ssl`
- `sdk-local-dev-config`

Reference: [Use the Azure Cosmos DB Emulator for local development](https://learn.microsoft.com/azure/cosmos-db/emulator)

### 10.2 Use Azure Cosmos DB VS Code extension for routine inspection and management

**Impact: MEDIUM** (speeds up data inspection and reduces one-off scripts for routine tasks)

## Use Azure Cosmos DB VS Code Extension for Routine Inspection and Management

For day-to-day inspection tasks, prefer the Azure Cosmos DB VS Code extension over ad hoc scripts or direct SDK calls. The extension is faster for browsing accounts, querying containers, inspecting items, and validating local-versus-cloud data without introducing disposable code into the repository.

**Incorrect (writing one-off code for routine inspection):**

```bash
# Need to inspect a few items or verify a container layout
# Result: write a throwaway script just to browse data
node inspect-cosmos.js
python list_items.py
```

**Correct (use the extension for routine inspection first):**

```text
1. Install the Azure Cosmos DB VS Code extension:
   ms-azuretools.vscode-cosmosdb
2. Use the extension to connect to the target account or emulator.
3. Browse databases, containers, and items directly in VS Code.
4. Run exploratory queries there before deciding whether permanent code is needed.
```

Use code only when the task is repeatable, automated, or belongs in the product. For one-off inspection, prefer the tool built for inspection.

Reference: [Azure Cosmos DB extension for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-cosmosdb)

---

## 11. Vector Search

**Impact: HIGH**

### 11.1 Use VectorDistance for Similarity Search

**Impact: HIGH** (Enables semantic search and RAG patterns)

## Use VectorDistance for Similarity Search

**Impact: HIGH (Enables semantic search and RAG patterns)**

Use the VectorDistance() system function to perform vector similarity searches. This function computes the distance between a query vector and stored vectors using the distance function specified in the vector embedding policy.

**Incorrect (missing ORDER BY or parameterization):**

```csharp
// .NET - Not parameterized, no ORDER BY
var query = "SELECT c.title FROM c WHERE VectorDistance(c.embedding, [0.1, 0.2, ...]) < 0.5";
// Issues: 
// 1. Hard-coded embedding array (query plan cache misses)
// 2. No ORDER BY (doesn't return most similar first)
// 3. Using WHERE instead of ORDER BY (less efficient)
```

**Correct (parameterized with ORDER BY):**


```csharp
// .NET - SDK 3.45.0+
float[] queryEmbedding = await GetEmbeddingAsync("search query");

var queryDef = new QueryDefinition(
    query: "SELECT TOP 10 c.title, VectorDistance(c.embedding, @embedding) AS SimilarityScore " +
           "FROM c ORDER BY VectorDistance(c.embedding, @embedding)"
).WithParameter("@embedding", queryEmbedding);
```

```python
# Python
query_embedding = get_embedding("search query")  # Returns list of floats

for item in container.query_items( 
    query='SELECT TOP 10 c.title, VectorDistance(c.embedding, @embedding) AS SimilarityScore ' +
          'FROM c ORDER BY VectorDistance(c.embedding, @embedding)', 
    parameters=[
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
> Cross-ref: See `query-parameterize` for parameterized queries.

### 11.2 Define Vector Embedding Policy

**Impact: CRITICAL** (Required for vector search functionality)

## Define Vector Embedding Policy

**Impact: CRITICAL (Required for vector search functionality)**

The vector embedding policy provides essential information to the Azure Cosmos DB query engine about how to handle vector properties in the VectorDistance system functions. This policy is required and cannot be modified after container creation.

**Incorrect (no vector embedding policy):**

```csharp
// .NET - Missing vector embedding policy
var containerProperties = new ContainerProperties("mycontainer", "/partitionKey");
await database.CreateContainerAsync(containerProperties);
```

**Correct (with vector embedding policy):**


```csharp
// .NET - SDK 3.45.0+
List<Embedding> embeddings = new List<Embedding>()
{
    new Embedding()
    {
        Path = "/embedding",
```

```python
# Python
vector_embedding_policy = { 
    "vectorEmbeddings": [ 
        { 
            "path": "/embedding", 
            "dataType": "float32", 
```

### 11.3 Enable Vector Search Feature on Account

**Impact: CRITICAL** (Required before using vector search)

## Enable Vector Search Feature on Account

**Impact: CRITICAL (Required before using vector search)**

Vector search must be explicitly enabled on the Azure Cosmos DB account before creating containers with vector policies. The feature can be enabled via Azure Portal or Azure CLI.

**Incorrect (attempting to use vectors without enabling feature):**

```csharp
// .NET - This will FAIL if feature not enabled
var embeddings = new List<Embedding>() { /* ... */ };
var properties = new ContainerProperties("docs", "/id")
{
    VectorEmbeddingPolicy = new(new Collection<Embedding>(embeddings))
};
```

**Correct (enable feature first, wait, then create):**


```bash
# Step 1: Enable feature
az cosmosdb update \
    --resource-group myResourceGroup \
    --name myCosmosAccount \
    --capabilities EnableNoSQLVectorSearch

```

### 11.4 Configure Vector Indexes in Indexing Policy

**Impact: CRITICAL** (Required for vector search performance)

## Configure Vector Indexes in Indexing Policy

**Impact: CRITICAL (Required for vector search performance)**

Vector indexes must be added to the indexing policy to enable efficient vector similarity search. Choose between QuantizedFlat (faster builds, good for smaller datasets) or DiskANN (better for larger datasets, requires more memory).

**Incorrect (no vector indexes or missing excludedPaths):**

```csharp
// .NET - Missing vector indexes
var properties = new ContainerProperties("documents", "/category")
{
    VectorEmbeddingPolicy = new(embeddings)
};
// No VectorIndexes configured!
```

**Correct (with vector indexes and excluded paths):**


```csharp
// .NET - SDK 3.45.0+
ContainerProperties properties = new ContainerProperties(
    id: "documents", 
    partitionKeyPath: "/category")
{   
    VectorEmbeddingPolicy = new(collection),
    IndexingPolicy = new IndexingPolicy()
```

```python
# Python
indexing_policy = { 
    "includedPaths": [{"path": "/*"}], 
    "excludedPaths": [
        {"path": "/\"_etag\"/?"},
        {"path": "/embedding/*"}  # CRITICAL: Exclude vector path
    ], 
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.

### 11.5 Normalize Embeddings for Cosine Similarity

**Impact: MEDIUM** (Ensures accurate similarity scores and consistent test results)

## Normalize Embeddings for Cosine Similarity

When using cosine distance, normalize embeddings to unit length (L2 norm = 1). Cosine similarity measures angle, not magnitude — unnormalized vectors produce inconsistent scores.

**Incorrect (unnormalized mock embeddings):**

```python
import random
def generate_mock_embedding(dimensions=1536):
    return [random.uniform(-1, 1) for _ in range(dimensions)]
    # Magnitude varies — cosine scores inconsistent
```

**Correct (normalized to unit length):**


```python
import numpy as np

def generate_mock_embedding(text: str, dimensions: int = 1536) -> list:
    """Normalized mock embedding. Uses text hash as seed for reproducibility."""
    seed = hash(text) % (2**32)
    np.random.seed(seed)
```

```csharp
public static float[] GenerateMockEmbedding(string text, int dimensions = 1536)
{
    var random = new Random(Math.Abs(text.GetHashCode()));
    var vector = new float[dimensions];
    for (int i = 0; i < dimensions; i++)
    {
```

### 11.6 Implement Repository Pattern for Vector Search

**Impact: HIGH** (Provides clean abstraction for vector operations and data access)

## Implement Repository Pattern for Vector Search

Encapsulate Cosmos DB vector operations in a repository to separate data access from business logic. Key methods: `upsert_document`, `vector_search`, `get_document`, `delete_document`.

**Incorrect (direct container access scattered throughout app):**

```python
# BAD: Vector search logic mixed with API logic, no abstraction
@app.post("/api/search")
async def search(request: SearchRequest):
    query = f"""SELECT TOP {request.limit} c.title,
        VectorDistance(c.embedding, @embedding) AS score FROM c
        ORDER BY VectorDistance(c.embedding, @embedding)"""
```

**Correct (repository pattern):**


```python
class DocumentRepository:
    def __init__(self, container: ContainerProxy):
        self.container = container

    async def vector_search(self, query_embedding: List[float], limit: int = 5,
                            similarity_threshold: float = 0.0,
```

```csharp
// .NET repository
public class DocumentRepository
{
    private readonly Container _container;
    public DocumentRepository(Container container) => _container = container;

```

> Cross-ref: See `query-parameterize` for parameterized queries.

---

## 12. Full-Text Search

**Impact: HIGH**

### 12.1 Add Full-Text Index in the Indexing Policy

**Impact: HIGH** (without the index, FTS functions fall back to a full scan)

## Add Full-Text Index in the Indexing Policy

**Impact: HIGH (without the index, FTS functions fall back to a full scan)**

The `fullTextIndexes` array in the `indexingPolicy` tells Cosmos DB to build an inverted index for the corresponding path. This is separate from the range index — a field can have both. Fields covered by a full-text index should **not** also appear in `excludedPaths`.

**Incorrect (field excluded from range index but no FTS index — slow scan):**

```bicep
excludedPaths: [
  { path: '/description/?' }   // excluded from range index...
]                               // ...but no fullTextIndexes entry → full scan
```

**Correct (Bicep):**

```bicep
indexingPolicy: {
  indexingMode: 'consistent'
  includedPaths: [
    { path: '/name/?' }
    { path: '/userid/?' }
  ]
  excludedPaths: [
    { path: '/*' }             // root wildcard
    // description NOT listed here — managed by FTS index below
  ]
  #disable-next-line BCP037
  fullTextIndexes: [
    { path: '/description' }   // inverted index — case-insensitive, tokenized
  ]
}
```

> A field under `fullTextIndexes` incurs **extra write RU** for index maintenance. Only index fields that are actually queried with `FullTextContains` or `FullTextScore`.

Reference: [Indexing policy for full-text search](https://learn.microsoft.com/azure/cosmos-db/gen-ai/full-text-search)

### 12.2 Define Full-Text Policy on the Container

**Impact: HIGH** (required for tokenizer and stop-word configuration)

## Define Full-Text Policy on the Container

**Impact: HIGH (required for tokenizer and stop-word configuration)**

The `fullTextPolicy` declares which paths are full-text searchable and their language. Supported languages: `en-US`, `de-DE` (preview), `fr-FR` (preview), `it-IT` (preview), `pt-BR` (preview), `pt-PT` (preview), `es-ES` (preview). Language codes are **case-sensitive** — use the exact casing shown (e.g., `en-US` not `en-us`).

**Incorrect (wrong language casing causes ARM BadRequest):**

```bicep
fullTextPolicy: {
  defaultLanguage: 'en-us'       // ❌ lowercase — rejected by ARM
  fullTextPaths: [
    { path: '/description', language: 'en-us' }  // ❌
  ]
}
```

**Correct (Bicep):**

```bicep
#disable-next-line BCP037
fullTextPolicy: {
  defaultLanguage: 'en-US'       // ✅ exact casing required
  fullTextPaths: [
    {
      path: '/description'
      language: 'en-US'          // ✅
    }
  ]
}
```

**Correct — Java SDK (container creation):**

```java
FullTextPolicy ftsPolicy = new FullTextPolicy()
    .setDefaultLanguage("en-US")
    .setFullTextPaths(List.of(
        new FullTextPath().setPath("/description").setLanguage("en-US")
    ));

CosmosContainerProperties props = new CosmosContainerProperties("videos", "/videoid");
props.setFullTextPolicy(ftsPolicy);
database.createContainerIfNotExists(props).block();
```

Reference: [Configure full-text policy](https://learn.microsoft.com/azure/cosmos-db/gen-ai/full-text-search)

### 12.3 Enable Full-Text Search Capability on Account

**Impact: HIGH** (prerequisite — FTS SQL functions fail without it)

## Enable Full-Text Search Capability on Account

**Impact: HIGH (prerequisite — FTS SQL functions fail without it)**

Full-text search is an opt-in account-level capability. The SQL functions `FullTextContains`, `FullTextContainsAll`, `FullTextContainsAny`, and `FullTextScore` all return an error if this capability is not enabled.

**Incorrect (capability absent — FTS queries fail at runtime):**

```sql
-- This query fails with "Function 'FullTextContains' is not supported"
-- when EnableNoSQLFullTextSearch capability is missing on the account
SELECT * FROM c WHERE FullTextContains(c.description, 'cosmos')
```

**Correct — enable via Azure CLI:**

```bash
az cosmosdb update \
  --resource-group <rg> \
  --name <account-name> \
  --capabilities EnableNoSQLFullTextSearch
```

**Correct — enable via Bicep (account resource):**

```bicep
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosAccountName
  properties: {
    // ... other properties ...
    capabilities: [
      { name: 'EnableNoSQLFullTextSearch' }
    ]
  }
}
```

> **Note:** As of Bicep type library v0.41, `fullTextIndexes` and `fullTextPolicy` may emit `BCP037` warnings. Suppress with `#disable-next-line BCP037` — the properties are valid at the ARM REST API level.

Reference: [Full-text search in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/gen-ai/full-text-search)

### 12.4 Combine FTS predicates with range or equality filters for hybrid queries

**Impact: MEDIUM** (avoids full-container scans when combined with equality/range filters)

## Combine FTS predicates with range or equality filters for hybrid queries

**Impact: MEDIUM (avoids full-container scans when combined with equality/range filters)**

FTS predicates can be combined with standard SQL predicates. Cosmos DB uses the most selective predicate first.

**Incorrect (FTS-only query — no range filters, scans all partitions):**

```sql
-- ❌ No equality filter — Cosmos DB must scan every partition before ranking
SELECT * FROM c
WHERE FullTextContains(c.description, @q)
ORDER BY RANK FullTextScore(c.description, @q)
```

**Correct — filter by partition + FTS:**


```sql
SELECT * FROM c
WHERE c.type = 'video'
  AND c.userid = @userid
  AND FullTextContains(c.description, @q)
ORDER BY RANK FullTextScore(c.description, @q)
```

```java
// Hybrid: exact field filters narrow partition, FTS ranks within results
String sql = "SELECT * FROM c " +
    "WHERE c.type = 'video' " +
    "AND FullTextContains(c.description, @q) " +
    "ORDER BY RANK FullTextScore(c.description, @q)";

```

### 12.5 Use FullTextContains for keyword matching on indexed text fields

**Impact: HIGH** (replaces expensive CONTAINS(LOWER(...)) string scans with O(log n) inverted index lookup)

## Use FullTextContains for keyword matching on indexed text fields

**Impact: HIGH (replaces expensive CONTAINS(LOWER(...)) string scans with O(log n) inverted index lookup)**

`FullTextContains(path, term)` performs a single-keyword lookup against the inverted index and is case-insensitive by design. It is dramatically faster than `CONTAINS(LOWER(c.field), @q)` on large containers because it does an `O(log n)` index lookup instead of a full document scan.

**Incorrect (scan-based — avoid for long text fields with FTS index):**

```sql
-- Full document scan, case folding at query time
SELECT * FROM c
WHERE CONTAINS(LOWER(c.description), @q)
```

**Correct:**


```sql
-- Inverted index lookup — no LOWER() needed, FTS tokenizer handles casing
SELECT * FROM c
WHERE FullTextContains(c.description, @q)
```

```java
// Java SDK — parameterized query with FullTextContains
String sql = "SELECT * FROM c WHERE c.type = 'video' " +
    "AND (CONTAINS(LOWER(c.name), @q) " +          // short field — range index OK
    "OR FullTextContains(c.description, @q) " +    // long text — FTS index
    "OR EXISTS(SELECT VALUE t FROM t IN c.tags WHERE CONTAINS(LOWER(t), @q)))";

```

> Cross-ref: See `query-parameterize` for parameterized queries.

### 12.6 Use FullTextScore with ORDER BY RANK for BM25 relevance ranking

**Impact: MEDIUM-HIGH** (enables BM25-based ranked results instead of arbitrary order)

## Use FullTextScore for Relevance Ranking

**Impact: MEDIUM-HIGH (enables BM25-based ranked results instead of arbitrary order)**

`FullTextScore(path, term)` returns a BM25 relevance score. Use it in `ORDER BY` to surface the most relevant documents first. It **requires** `FullTextContains` in the WHERE clause on the same path.

**Incorrect (FullTextScore without FullTextContains — parse error):**

```sql
SELECT * FROM c
ORDER BY FullTextScore(c.description, 'cosmos')  -- ❌ missing WHERE FullTextContains
```

**Correct:**

```sql
SELECT c.name, c.description, c.addedDate
FROM c
WHERE FullTextContains(c.description, @q)
ORDER BY RANK FullTextScore(c.description, @q)
```

```java
String sql = "SELECT c.name, c.description, c.addedDate FROM c " +
    "WHERE FullTextContains(c.description, @q) " +
    "ORDER BY RANK FullTextScore(c.description, @q)";

SqlQuerySpec querySpec = new SqlQuerySpec(sql, new SqlParameter("@q", searchTerm));
```

> `RANK FullTextScore(...)` is cross-partition — Cosmos DB merges and re-ranks results from all partitions before returning the page.

Reference: [FullTextScore function](https://learn.microsoft.com/azure/cosmos-db/nosql/query/fulltextscore)

---

## 13. Security

**Impact: HIGH**

### 13.1 Enable Continuous Backup for Point-in-Time Restore

**Impact: MEDIUM** (enables recovery from accidental data loss)

## Enable Continuous Backup for Point-in-Time Restore

**Impact: MEDIUM (enables recovery from accidental data loss)**

Data loss is more often caused by mistakes than by attackers. Enable continuous backup (7 or 30 days) to allow point-in-time restore.

**Incorrect (relying on default periodic backup):**

```bash
# Default periodic backup:
# - 4 hour intervals between backups

az cosmosdb create \
  --name myaccount \
  --resource-group myrg
```

**Correct (continuous backup enabled):**


```bash
# Enable at account creation (preferred)
az cosmosdb create \
  --name myaccount \
  --resource-group myrg \
  --backup-policy-type Continuous \
  --continuous-tier Continuous7Days
```

```bash
# Restore to a specific point in time (self-service, no support ticket)
az cosmosdb restore \
  --account-name myaccount \
  --resource-group myrg \
  --target-database-account-name myaccount-restored \
  --restore-timestamp "2026-05-29T10:00:00Z" \
```

### 13.2 Disable Local Authentication (Keys)

**Impact: CRITICAL** (eliminates credential leakage risk)

## Disable Local Authentication (Keys)

**Impact: CRITICAL (eliminates credential leakage risk)**

Disable local authentication (shared keys and connection strings) on your Cosmos DB account. Keys are bearer tokens — anyone who has one can read, modify, or delete all data.

**Incorrect (using connection string with keys):**

```csharp
// WRONG: Connection string contains a master key
// If this leaks via source control, logs, or config, all data is exposed
var connectionString = "AccountEndpoint=https://myaccount.documents.azure.com:443/;AccountKey=abc123...==;";
var client = new CosmosClient(connectionString);

// Risks:
```

**Correct (disable keys, use Entra ID exclusively):**


```bash
# Disable local authentication on the account
az cosmosdb update \
  --name <your-account> \
  --resource-group <your-rg> \
  --disable-local-auth true
```

```csharp
// Connect using Entra ID — no keys or connection strings needed
using Azure.Identity;
using Microsoft.Azure.Cosmos;

var client = new CosmosClient(
    accountEndpoint: "https://myaccount.documents.azure.com:443/",
```

### 13.3 Use Managed Identity with DefaultAzureCredential

**Impact: CRITICAL** (zero-secret authentication for all environments)

## Use Managed Identity with DefaultAzureCredential

**Impact: CRITICAL (zero-secret authentication for all environments)**

Authenticate to Cosmos DB using managed identity and `DefaultAzureCredential`. This provides a single code path that works in local development (via `az login`), Azure compute (via system-assigned managed identity), and CI/CD (via service principal or federated identity) — with no secrets in code or configuration.

**Incorrect (hard-coded keys or environment-specific auth):**

```csharp
// WRONG: Key stored in configuration
var client = new CosmosClient(
    "https://myaccount.documents.azure.com:443/",
    "abc123masterkey=="
);

```

**Correct (DefaultAzureCredential everywhere):**


```csharp
using Azure.Identity;
using Microsoft.Azure.Cosmos;

// Same code works in all environments:
// - Local dev: uses az login / Visual Studio / VS Code credentials
var client = new CosmosClient(
```

```python
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient

credential = DefaultAzureCredential()
client = CosmosClient("https://myaccount.documents.azure.com:443/", credential)
```

### 13.4 Restrict Network Access

**Impact: HIGH** (reduces attack surface from public internet)

## Restrict Network Access

**Impact: HIGH (reduces attack surface from public internet)**

By default, a Cosmos DB endpoint is publicly reachable from anywhere on the internet. If a credential leaks, nothing stands between an attacker and your data.

**Incorrect (unrestricted public access):**

```bash
# WRONG: Default configuration — account is accessible from any IP address worldwide
# No --ip-range-filter means open to the internet

az cosmosdb create \
  --name myaccount \
  --resource-group myrg
```

**Correct (restrict to known IPs as baseline):**


```bash
# Restrict access to known IP addresses (office, CI/CD egress, developer IPs)
az cosmosdb update \
  --name myaccount \
  --resource-group myrg \
  --ip-range-filter "203.0.113.10,198.51.100.0/24"

```

### 13.5 Assign Minimum RBAC Roles with Narrow Scope

**Impact: HIGH** (limits blast radius of compromised identities)

## Assign Minimum RBAC Roles with Narrow Scope

**Impact: HIGH (limits blast radius of compromised identities)**

Grant each identity only the Cosmos DB data plane role it needs, scoped to the narrowest resource level possible. Avoid account-wide contributor access when an app only reads from a single container.

**Incorrect (over-privileged access):**

```bash
# WRONG: Granting full Contributor at account scope to an app that only reads data
az cosmosdb sql role assignment create \
  --account-name myaccount \
  --resource-group myrg \
  --role-definition-id "00000000-0000-0000-0000-000000000002" \
  --principal-id <app-principal-id> \
```

**Correct (least privilege, narrowly scoped):**


```bash
# Built-in data plane roles:
# Cosmos DB Built-in Data Reader:      00000000-0000-0000-0000-000000000001

# Read-only app: grant Reader scoped to specific container
az cosmosdb sql role assignment create \
  --account-name myaccount \
```

---

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
