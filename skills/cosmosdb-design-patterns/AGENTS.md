# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Design patterns for Azure Cosmos DB applications: change feed materialized views, efficient ranking, service layer relationships, LangGraph multi-agent orchestration, and human-in-the-loop flows.

---

## Table of Contents

1. [Design Patterns](#1-design-patterns) — **HIGH**
   - 1.1 [Use Point Reads for AI-Grounding and RAG Retrieval When ID Is Known](#11-use-point-reads-for-ai-grounding-and-rag-retrieval-when-id-is-known)
   - 1.2 [Use Background Tasks for Non-Blocking Chat History Storage](#12-use-background-tasks-for-non-blocking-chat-history-storage)
   - 1.3 [Use Change Feed for cross-partition query optimization with materialized views](#13-use-change-feed-for-cross-partition-query-optimization-with-materialized-views)
   - 1.4 [Use count-based or cached rank approaches instead of full partition scans for ranking](#14-use-count-based-or-cached-rank-approaches-instead-of-full-partition-scans-for-ranking)
   - 1.5 [Map Cosmos DB documents to FastAPI response DTOs](#15-map-cosmos-db-documents-to-fastapi-response-dtos)
   - 1.6 [Tag AI Messages with Agent Name for API Response Attribution](#16-tag-ai-messages-with-agent-name-for-api-response-attribution)
   - 1.7 [Persist Active Agent in Cosmos DB for Deterministic Routing](#17-persist-active-agent-in-cosmos-db-for-deterministic-routing)
   - 1.8 [Wrap Cosmos DB Sync Calls in asyncio.to_thread for LangGraph Routing Functions](#18-wrap-cosmos-db-sync-calls-in-asyncio-to-thread-for-langgraph-routing-functions)
   - 1.9 [Use asyncio.to_thread for Active Agent Writes in LangGraph Node Functions](#19-use-asyncio-to-thread-for-active-agent-writes-in-langgraph-node-functions)
   - 1.10 [Store Chat History Separately from LangGraph Checkpoints](#110-store-chat-history-separately-from-langgraph-checkpoints)
   - 1.11 [Initialize LangGraph Agents in FastAPI Startup with Retry](#111-initialize-langgraph-agents-in-fastapi-startup-with-retry)
   - 1.12 [Use LangGraph Interrupt for Human-in-the-Loop Confirmation](#112-use-langgraph-interrupt-for-human-in-the-loop-confirmation)
   - 1.13 [Use StateGraph with Conditional Edges for Multi-Agent Routing](#113-use-stategraph-with-conditional-edges-for-multi-agent-routing)
   - 1.14 [Resume LangGraph from Checkpoint After Interrupt](#114-resume-langgraph-from-checkpoint-after-interrupt)
   - 1.15 [Use a service layer to hydrate document references before rendering](#115-use-a-service-layer-to-hydrate-document-references-before-rendering)

---

## 1. Design Patterns

**Impact: HIGH**

### 1.1 Use Point Reads for AI-Grounding and RAG Retrieval When ID Is Known

**Impact: HIGH** (1 RU point read vs ~2.5+ RU query per grounding fetch; reduces tool-call latency in LLM loops)

## Use Point Reads for AI-Grounding and RAG Retrieval When ID Is Known

In AI-grounded workloads an LLM tool-use loop typically resolves a concrete entity id (e.g., `orderId`, `sessionId`, `documentId`) from the user turn or tool-call arguments, then fetches the full document from Cosmos DB to build the grounding context for the model. Because the id and partition key are both known at call time, a point read should always be used instead of a query. This applies to any retrieval step that feeds data into an LLM context window — RAG retrieval, tool-call handlers, grounding functions, or agent data-fetching steps.

**How to recognize this pattern — static tell-tales:**

- An LLM / AI client import in the same module (e.g., `OpenAI`, `AzureOpenAI`, `ChatCompletionClient`, Semantic Kernel, LangChain)
- A function that parses tool-call arguments or assembles a `messages` array
- A Cosmos DB call using a single-id equality filter where the id was extracted from user input or a tool-call response

**Incorrect (query when id and partition key are both available from the tool call):**

```typescript
// ❌ Generic query — id is already known from the user turn / tool call
export async function groundOrderContext(orderId: string, userId: string) {
  const { resources: orders } = await ordersContainer.items
    .query<Order>({
      query: "SELECT * FROM c WHERE c.orderId = @o",
      parameters: [{ name: "@o", value: orderId }],
    })
    .fetchAll();

  const { resources: events } = await eventsContainer.items
    .query<DeliveryEvent>({
      query: "SELECT * FROM c WHERE c.orderId = @o ORDER BY c.timestamp DESC",
      parameters: [{ name: "@o", value: orderId }],
    })
    .fetchAll();

  return buildGroundingContext(orders[0], events);
}
```

```python
# ❌ Query instead of point read — id and partition key both known
def ground_order_context(order_id: str, user_id: str):
    orders = list(orders_container.query_items(
        query="SELECT * FROM c WHERE c.id = @id",
        parameters=[{"name": "@id", "value": order_id}],
        partition_key=user_id,
    ))
    return build_grounding_context(orders[0]) if orders else None
```

**Correct (point read for the primary document, partition-scoped projection for related items):**

```typescript
// ✅ Point read for the order (id + partition key both known from tool call)
export async function groundOrderContext(orderId: string, userId: string) {
  const orderResp = await ordersContainer.item(orderId, userId).read<Order>();
  const order = orderResp.resource;
  if (!order) return null;

  // ✅ Partition-key-scoped projection for related event list
  const { resources: events } = await eventsContainer.items
    .query<DeliveryEvent>(
      {
        query:
          "SELECT c.id, c.orderId, c.timestamp, c.status, c.note FROM c WHERE c.orderId = @o ORDER BY c.timestamp DESC",
        parameters: [{ name: "@o", value: orderId }],
      },
      { partitionKey: orderId }
    )
    .fetchAll();

  return buildGroundingContext(order, events);
}
```

```python
# ✅ Point read — 1 RU, no query engine overhead
def ground_order_context(order_id: str, user_id: str):
    order = orders_container.read_item(item=order_id, partition_key=user_id)
    return build_grounding_context(order)
```

**Why this matters for AI workloads:**

1. **Latency-sensitive** — each tool call adds to perceived LLM response time; a point read (1 RU, single backend hop) is the fastest possible retrieval
2. **Throughput-sensitive** — hot conversations drive the same partition key repeatedly; cross-partition fan-out under load hot-spots a single logical partition fastest
3. **ID is known by construction** — the LLM tool-use loop hands the agent an id parsed from the user turn or a prior tool result; agents should recognise this signal and reach for the point read

See also: `query-point-reads` (general point-read guidance), `query-use-projections` (select only needed fields), `query-avoid-cross-partition` (avoid cross-partition fan-out).

Reference: [Request Units — point reads cost fewer RUs than queries](https://learn.microsoft.com/azure/cosmos-db/request-units#request-unit-considerations)

### 1.2 Use Background Tasks for Non-Blocking Chat History Storage

**Impact: MEDIUM** (reduces API response latency by 50-200ms per request)

## Use Background Tasks for Non-Blocking Chat History Storage

**Impact: MEDIUM (reduces API response latency by 50-200ms per request)**

After a LangGraph agent produces a response, storing chat history and debug logs in Cosmos DB is important for the UI but not for the immediate API response. Use FastAPI's `BackgroundTasks` to defer these writes, returning the agent response to the user immediately. This avoids adding Cosmos DB write latency (typically 5-20ms per write, more with multiple writes) to the user-facing response time.

**Incorrect (blocking writes before returning response):**

```python
from fastapi import FastAPI

@app.post("/chat/{session_id}")
async def chat(session_id: str, user_message: str):
    response = await graph.ainvoke(state, config, stream_mode="updates")
    messages = extract_response(response)

    # BAD: User waits for all these DB writes to complete before seeing the response
    for msg in messages:
        store_chat_history(msg)  # 5-20ms each
    store_debug_log(session_id, response)  # Another 10-20ms
    update_active_agent(session_id, last_agent)  # Another 5-10ms

    return messages  # User waited an extra 50-200ms unnecessarily
```

**Correct (defer writes with BackgroundTasks):**

```python
from fastapi import FastAPI, BackgroundTasks

def process_post_response(messages, session_id, tenant_id, user_id, active_agent):
    """Runs after the response is sent to the client."""
    for msg in messages:
        store_chat_history(msg)
    update_active_agent_in_latest_message(session_id, active_agent)

@app.post("/chat/{session_id}")
async def chat(
    session_id: str,
    user_message: str,
    background_tasks: BackgroundTasks
):
    response = await graph.ainvoke(state, config, stream_mode="updates")
    messages = extract_response(response)

    # Schedule writes to run after the response is sent
    background_tasks.add_task(
        process_post_response, messages, session_id, tenant_id, user_id, active_agent
    )

    # Response returned immediately — user sees it while writes happen in background
    return messages
```

**When to use background tasks vs. blocking:**
- **Background:** Chat history storage, debug log writes, session name updates, analytics
- **Blocking:** Active agent patch (if needed for the *current* response routing), session creation, critical state that the next request depends on

**Note:** Background tasks in FastAPI run in the same process after the response. For truly fire-and-forget workloads at scale, consider Azure Cosmos DB change feed triggers or message queues.

Reference: [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

### 1.3 Use Change Feed for cross-partition query optimization with materialized views

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
                
                # Python writes derive the partition key from status_view["status"].
                await status_container.upsert_item(body=status_view)
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

### 1.4 Use count-based or cached rank approaches instead of full partition scans for ranking

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

### 1.5 Map Cosmos DB documents to FastAPI response DTOs

**Impact: HIGH** (prevents strict response_model failures and avoids leaking system fields, storage-only fields, or raw embeddings)

## Map Cosmos DB Documents to FastAPI Response DTOs

**Impact: HIGH (prevents API 500s and keeps storage internals out of public responses)**

Cosmos DB documents are persistence records, not public API response contracts. FastAPI `response_model` validation checks the returned value against the declared response shape. If the returned value is invalid, FastAPI treats that as an application bug and returns a server error.

Do not return raw Cosmos DB SDK documents from endpoints with a strict `response_model` or an exact API contract. Cosmos items include system fields like `_rid`, `_self`, `_etag`, `_attachments`, and `_ts`, and application storage documents often include internal fields like `type`, `schemaVersion`, synthetic ids, denormalized helper fields, or raw `embedding` vectors. Map the storage document to an explicit DTO/dict before returning it.

**Incorrect (raw Cosmos document returned through response_model):**

```python
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

app = FastAPI()

class SessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sessionId: str
    userId: str
    title: str
    createdAt: str

@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, user_id: str):
    doc = sessions_container.read_item(item=session_id, partition_key=user_id)
    return doc  # BAD: may include id, type, _etag, _rid, _ts, etc.
```

**Correct (map to the API contract):**

```python
def to_session_response(doc: dict) -> dict:
    return {
        "sessionId": doc["sessionId"],
        "userId": doc["userId"],
        "title": doc.get("title", ""),
        "createdAt": doc["createdAt"],
    }

@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, user_id: str):
    doc = sessions_container.read_item(item=session_id, partition_key=user_id)
    return to_session_response(doc)
```

**Correct (project and map vector-search results):**

```python
def to_search_result(item: dict) -> dict:
    return {
        "documentId": item.get("documentId", item["id"]),
        "content": item["content"],
        "category": item["category"],
        "metadata": item.get("metadata", {}),
        "score": item["score"],
    }

safe_limit = max(1, min(int(limit), 50))
query = f"""
SELECT TOP {safe_limit}
    c.documentId,
    c.content,
    c.category,
    c.metadata,
    VectorDistance(c.embedding, @embedding) AS score
FROM c
WHERE c.category = @category
ORDER BY VectorDistance(c.embedding, @embedding)
"""

# category is the partition key, so scope the read to one logical
# partition instead of fanning out with enable_cross_partition_query.
items = documents_container.query_items(
    query=query,
    parameters=[
        {"name": "@embedding", "value": embedding},
        {"name": "@category", "value": category},
    ],
    partition_key=category,
)
return {"results": [to_search_result(item) for item in items]}
```

**Key points:**

- Keep Cosmos system fields internal unless the API contract explicitly asks for them.
- Keep raw embeddings internal unless building an embedding export endpoint.
- Prefer SQL projections for query endpoints so extra fields do not leave the data layer.
- Do not fix contract drift by changing Pydantic models to `extra="allow"`; map the storage document to the public contract instead.

References: [FastAPI response model](https://fastapi.tiangolo.com/tutorial/response-model/) | [Azure Cosmos DB Python ContainerProxy API](https://learn.microsoft.com/python/api/azure-cosmos/azure.cosmos.containerproxy)

### 1.6 Tag AI Messages with Agent Name for API Response Attribution

**Impact: MEDIUM** (enables API layer to report which agent generated a response for UI display and logging)

## Tag AI Messages with Agent Name for API Response Attribution

**Impact: MEDIUM (enables API layer to report which agent generated a response for UI display and logging)**

`create_react_agent` does not set the `name` field on AI messages it produces. If the API layer needs to report which agent generated a response (e.g., for UI display or logging), it has no way to determine this from the message itself. Tag the last AI message with the agent name before returning from each node function.

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
            break
    return response

async def call_product_search(state, config):
    response = await product_search_agent.ainvoke(state)
    # Tag the response so the API layer knows which agent answered
    _tag_last_ai_message(response, "product_search_agent")
    return Command(update=response, goto=END)
```

**Key points:**
1. Iterate in reverse to find the last AI message with content (skip empty tool-call messages)
2. Set `msg.name = agent_name` — LangGraph preserves this field through state updates
3. Apply tagging in every node function before returning the `Command`
4. The API layer can then read `message.name` to display agent attribution in the UI

Reference: [LangGraph multi-agent patterns](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)

### 1.7 Persist Active Agent in Cosmos DB for Deterministic Routing

**Impact: HIGH** (eliminates LLM re-classification overhead and prevents routing drift)

## Persist Active Agent in Cosmos DB for Deterministic Routing

**Impact: HIGH (eliminates LLM re-classification overhead and prevents routing drift)**

In multi-agent systems, once a user has been routed to a specialist agent, persist the active agent name in Cosmos DB alongside the conversation session. On subsequent messages, perform a point read to retrieve the active agent instead of re-invoking the coordinator LLM to classify intent. This is faster (single-digit millisecond point read vs. hundreds of milliseconds for LLM inference), deterministic, and avoids mid-conversation routing flip-flops.

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
            item=thread_id,
            partition_key=[tenant_id, user_id, thread_id]
        )
        return item.get("activeAgent", "unknown")
    except Exception:
        return "unknown"

async def get_active_agent(state, config) -> str:
    """Routing function — must be async and must NEVER raise."""
    thread_id = config.get("configurable", {}).get("thread_id", "")
    user_id = config.get("configurable", {}).get("userId", "")
    tenant_id = config.get("configurable", {}).get("tenantId", "")

    # O(1) point read — single-digit ms latency, 1 RU cost
    # Wrapped in asyncio.to_thread to avoid blocking the event loop
    try:
        active_agent = await asyncio.wait_for(
            asyncio.to_thread(_read_active_agent_from_db, tenant_id, user_id, thread_id),
            timeout=5.0,
        )
    except Exception:
        # Covers: CosmosResourceNotFoundError (new session),
        # asyncio.TimeoutError (cold start / slow DB),
        # CredentialUnavailableError (auth not ready)
        return "coordinator"

    # If an agent is already assigned, route directly — skip coordinator
    if active_agent not in [None, "unknown", "coordinator"]:
        return active_agent

    # Only invoke coordinator for new/unrouted conversations
    return "coordinator"
```

**Updating the active agent:** When a transfer tool is called (e.g., `transfer_to_sales_agent`), patch the Cosmos DB document with the new active agent name:

```python
from azure.cosmos import PartitionKey

def patch_active_agent(tenant_id, user_id, thread_id, new_agent):
    """Partial update — only modifies the activeAgent field (minimal RU cost)."""
    container.patch_item(
        item=thread_id,
        partition_key=[tenant_id, user_id, thread_id],
        patch_operations=[
            {"op": "set", "path": "/activeAgent", "value": new_agent}
        ]
    )
```

**Key design points:**
1. Use hierarchical partition key (`/tenantId`, `/userId`, `/sessionId`) for efficient multi-tenant lookups
2. The point read costs 1 RU regardless of document size
3. Use patch operations (not full replace) to update the active agent — costs fewer RUs
4. Fall back to the coordinator only when `activeAgent` is `null` or `"unknown"`
5. The routing function must NEVER raise — any exception (404, timeout, credential error) should fall through to the coordinator
6. Always use `asyncio.to_thread()` for sync Cosmos DB calls in routing functions to avoid blocking the event loop

Reference: [Azure Cosmos DB point reads](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-read-item)

### 1.8 Wrap Cosmos DB Sync Calls in asyncio.to_thread for LangGraph Routing Functions

**Impact: CRITICAL** (prevents event loop blocking that causes all concurrent requests to hang)

## Wrap Cosmos DB Sync Calls in asyncio.to_thread for LangGraph Routing Functions

**Impact: CRITICAL (prevents event loop blocking that causes all concurrent requests to hang)**

LangGraph's `add_conditional_edges` routing function runs inside the async event loop. If the routing function calls `DefaultAzureCredential` or `container.read_item()` synchronously, it blocks the entire event loop — causing all concurrent requests to hang and potentially triggering timeouts. Always wrap synchronous Cosmos DB SDK calls in `asyncio.to_thread()` and add a timeout to prevent hung routing if Cosmos DB is slow or unreachable.

**Incorrect (synchronous Cosmos DB call blocks the event loop):**

```python
from azure.cosmos import CosmosClient

def get_active_agent(state, config) -> str:
    thread_id = config["configurable"]["thread_id"]
    # BAD: Blocks the event loop when called from LangGraph's async runtime
    item = container.read_item(item=thread_id, partition_key=thread_id)
    active_agent = item.get("activeAgent", "unknown")
    if active_agent not in [None, "unknown", "coordinator"]:
        return active_agent
    return "coordinator"
```

**Correct (async wrapper with timeout and fallback):**

```python
import asyncio
from azure.cosmos import CosmosClient

def _read_active_agent_from_db(thread_id: str) -> str:
    """Synchronous helper — runs in a thread pool."""
    container = get_sync_container("ChatSessions")
    item = container.read_item(item=thread_id, partition_key=thread_id)
    return item.get("activeAgent", "unknown")

async def get_active_agent_from_db(thread_id: str) -> str:
    """Non-blocking wrapper with timeout for reading active agent from Cosmos DB."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_read_active_agent_from_db, thread_id),
            timeout=5.0,
        )
    except Exception:
        # Covers: CosmosResourceNotFoundError (new session),
        # asyncio.TimeoutError (cold start / slow DB),
        # CredentialUnavailableError (auth not ready)
        return "unknown"

async def get_active_agent(state, config) -> str:
    """Routing function for add_conditional_edges — must be async def."""
    thread_id = config.get("configurable", {}).get("thread_id", "")
    active_agent = await get_active_agent_from_db(thread_id)
    if active_agent not in [None, "unknown", "coordinator"]:
        return active_agent
    return "coordinator"
```

**Key points:**
1. The routing function MUST be `async def` when using Cosmos DB lookups
2. Always wrap `DefaultAzureCredential` and `read_item()` in `asyncio.to_thread()`
3. Add a timeout (5s) to prevent hung routing if Cosmos DB is slow or unreachable
4. Fall back to "coordinator" on any exception — never let a DB failure crash the graph
5. The routing function must NEVER raise — it runs on every single message as a graph entry point

Reference: [Python asyncio.to_thread documentation](https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread)

### 1.9 Use asyncio.to_thread for Active Agent Writes in LangGraph Node Functions

**Impact: HIGH** (prevents event loop blocking during Cosmos DB upserts in async node functions)

## Use asyncio.to_thread for Active Agent Writes in LangGraph Node Functions

**Impact: HIGH (prevents event loop blocking during Cosmos DB upserts in async node functions)**

When saving the active agent after a transfer (inside a LangGraph node function), using the sync Cosmos DB SDK also blocks the event loop. Node functions in LangGraph run as coroutines. Wrap synchronous write operations in `asyncio.to_thread()` to keep the event loop responsive.

**Incorrect (synchronous upsert blocks the event loop inside an async node):**

```python
async def call_agent(state, config):
    response = await agent.ainvoke(state)
    # BAD: Blocks the event loop during upsert
    container.upsert_item({
        "id": thread_id,
        "sessionId": thread_id,
        "activeAgent": "target_agent",
    })
    return Command(update=response, goto="target_agent")
```

**Correct (non-blocking write with asyncio.to_thread):**

```python
import asyncio
import logging

logger = logging.getLogger(__name__)

async def save_active_agent_to_db_async(
    thread_id: str, agent_name: str, tenant_id: str, user_id: str
):
    """Non-blocking upsert of active agent to Cosmos DB."""
    def _save():
        try:
            container = get_sync_container("ChatSessions")
            container.upsert_item({
                "id": thread_id,
                "sessionId": thread_id,
                "tenantId": tenant_id,
                "userId": user_id,
                "activeAgent": agent_name,
            })
        except Exception as e:
            logger.error(f"Failed to save active agent: {e}")
    await asyncio.to_thread(_save)

async def call_agent(state, config):
    response = await agent.ainvoke(state)
    thread_id = config.get("configurable", {}).get("thread_id", "")
    tenant_id = config.get("configurable", {}).get("tenantId", "")
    user_id = config.get("configurable", {}).get("userId", "")
    # Non-blocking write — errors logged but not propagated
    await save_active_agent_to_db_async(thread_id, "target_agent", tenant_id, user_id)
    return Command(update=response, goto="target_agent")
```

**Key points:**
1. Wrap all synchronous Cosmos DB write operations in `asyncio.to_thread()` inside async node functions
2. Writes can be fire-and-forget — errors are logged but not propagated, since failing to persist the active agent is not fatal to the current request
3. Keep the synchronous logic in a nested helper function for clarity and thread-safety
4. Use `upsert_item` (not `create_item`) to handle both new and existing sessions

Reference: [Python asyncio.to_thread documentation](https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread)

### 1.10 Store Chat History Separately from LangGraph Checkpoints

**Impact: MEDIUM** (enables efficient message retrieval and agent attribution)

## Store Chat History Separately from LangGraph Checkpoints

**Impact: MEDIUM (enables efficient message retrieval and agent attribution)**

LangGraph's checkpointer (CosmosDBSaver) stores full graph state for resumption, but it is not optimized for retrieving displayable chat history. Checkpoint data contains internal graph metadata, tool messages, system messages, and duplicate entries from each node execution. Instead, maintain a separate Cosmos DB container for chat history with only the fields your UI needs (sender, text, timestamp, which agent responded). This enables efficient queries, proper agent attribution, and avoids scanning checkpoint blobs.

**Incorrect (reading chat history from the checkpointer store):**

```python
@app.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str):
    config = {"configurable": {"thread_id": session_id, "checkpoint_ns": ""}}
    # BAD: Checkpointer stores ALL graph state — tool messages, system messages,
    # intermediate states, duplicates from each node. Expensive to scan and filter.
    checkpoints = [cp async for cp in checkpointer.alist(config)]
    if not checkpoints:
        return []
    
    # Must dig into checkpoint internals to extract displayable messages
    messages = checkpoints[-1].checkpoint["channel_values"]["messages"]
    # No record of which agent responded — lost in checkpoint format
    return filter_displayable(messages)
```

**Correct (store displayable history in a dedicated container):**

```python
from azure.cosmos import CosmosClient

# Dedicated container with partition key /sessionId for efficient retrieval
history_container = database.get_container_client("ChatHistory")

def store_chat_message(session_id: str, tenant_id: str, user_id: str, 
                       sender: str, text: str, agent_name: str):
    """Store a single displayable message after graph execution completes."""
    history_container.create_item({
        "id": str(uuid.uuid4()),
        "sessionId": session_id,
        "tenantId": tenant_id,
        "userId": user_id,
        "sender": sender,
        "agentName": agent_name,  # Which agent responded — not available in checkpoints
        "text": text,
        "timestamp": datetime.utcnow().isoformat(),
    })

@app.get("/sessions/{session_id}/messages")
def get_messages(session_id: str):
    # Single-partition query — fast and cheap (few RUs)
    return list(history_container.query_items(
        query="SELECT * FROM c WHERE c.sessionId = @sid ORDER BY c.timestamp",
        parameters=[{"name": "@sid", "value": session_id}],
        partition_key=session_id
    ))
```

**Why separate storage:**
1. **Agent attribution** — checkpoints don't track which agent produced each response
2. **Query efficiency** — dedicated container with `/sessionId` partition key enables single-partition queries
3. **Cleaner data** — no tool messages, system messages, or graph internal state
4. **Independent scaling** — chat history access patterns differ from checkpointing (read-heavy vs. write-heavy)

Reference: [Azure Cosmos DB container design](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-model-partition-example)

### 1.11 Initialize LangGraph Agents in FastAPI Startup with Retry

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

**Incorrect (initialize on first request — slow first response, no retry):**

```python
@app.post("/chat")
async def chat(message: str):
    global _initialized
    if not _initialized:
        # BAD: First user pays full initialization cost (seconds)
        # No retry if MCP server is temporarily unavailable
        await setup_agents()
        _initialized = True
    # ...
```

**Correct (startup event with retry and fallback):**

```python
import asyncio
from fastapi import FastAPI, HTTPException

app = FastAPI()
_agents_ready = False

@app.on_event("startup")
async def initialize_agents():
    global _agents_ready
    max_retries = 5
    retry_delay = 10  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            await setup_agents()  # Connects to MCP, loads tools, creates agents, inits checkpointer
            _agents_ready = True
            return
        except Exception as e:
            if attempt < max_retries:
                await asyncio.sleep(retry_delay)
            else:
                # Start anyway — will initialize on demand
                _agents_ready = False

async def ensure_ready():
    """Dependency that ensures agents are initialized before handling requests."""
    if not _agents_ready:
        try:
            await setup_agents()
        except Exception:
            raise HTTPException(status_code=503, detail="Service unavailable — agents not initialized")

@app.post("/chat")
async def chat(message: str):
    await ensure_ready()
    # ... handle request ...
```

**Production tips:**
- Set retry delay via environment variable (e.g., `STARTUP_DELAY_SECONDS`) for container orchestration tuning
- Add a `/health/ready` endpoint that returns 503 until `_agents_ready` is `True` — used by load balancers and container health probes
- For FastAPI >= 0.93, prefer `lifespan` context manager over deprecated `on_event`

Reference: [FastAPI lifespan events](https://fastapi.tiangolo.com/advanced/events/)

### 1.12 Use LangGraph Interrupt for Human-in-the-Loop Confirmation

**Impact: HIGH** (enables safe confirmation flows for sensitive operations)

## Use LangGraph Interrupt for Human-in-the-Loop Confirmation

**Impact: HIGH (enables safe confirmation flows for sensitive operations)**

When agents perform sensitive operations (e.g., money transfers, account creation, data deletion), use LangGraph's `interrupt()` mechanism to pause execution and wait for user confirmation. The graph state is persisted to Cosmos DB via the checkpointer, and execution resumes from the same point when the user responds. This avoids custom polling loops or separate confirmation APIs.

**Incorrect (no confirmation — agent executes sensitive action immediately):**

```python
from langgraph.graph import StateGraph, MessagesState

async def call_transactions_agent(state: MessagesState, config):
    # BAD: Agent may call bank_transfer without user confirmation
    response = await transactions_agent.ainvoke(state)
    return {"messages": response["messages"]}
```

**Incorrect (manual polling loop instead of interrupt):**

```python
async def call_transactions_agent(state: MessagesState, config):
    response = await transactions_agent.ainvoke(state)
    # BAD: Custom polling — reinvents what LangGraph interrupt provides
    while not await check_user_confirmed(config):
        await asyncio.sleep(1)
    return {"messages": response["messages"]}
```

**Correct (interrupt pauses graph, state saved to Cosmos DB):**

```python
from langgraph.types import Command, interrupt
from langgraph.graph import StateGraph, MessagesState
from langchain_azure_cosmosdb import CosmosDBSaver

def human_node(state: MessagesState, config) -> None:
    """Pauses the graph and waits for the next user message."""
    interrupt(value="Ready for user input.")
    return None

async def call_transactions_agent(state: MessagesState, config) -> Command:
    response = await transactions_agent.ainvoke(state)
    # Route to human node — graph pauses, state persisted to Cosmos DB
    return Command(update=response, goto="human")

builder = StateGraph(MessagesState)
builder.add_node("transactions_agent", call_transactions_agent)
builder.add_node("human", human_node)
# ... add edges ...

graph = builder.compile(checkpointer=CosmosDBSaver(async_container))
```

**How it works:**
1. Agent node returns `Command(goto="human")` after processing
2. The `human_node` calls `interrupt()`, which persists state and pauses
3. The caller receives a response indicating the graph is waiting
4. When the user sends a new message, the caller resumes the graph with `graph.stream(new_input, config)`
5. The checkpointer restores state from Cosmos DB and continues from where it paused

Reference: [LangGraph human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)

### 1.13 Use StateGraph with Conditional Edges for Multi-Agent Routing

**Impact: HIGH** (enables deterministic agent hand-off in multi-agent LangGraph applications)

## Use StateGraph with Conditional Edges for Multi-Agent Routing

**Impact: HIGH (enables deterministic agent hand-off in multi-agent LangGraph applications)**

When building multi-agent systems with LangGraph backed by Cosmos DB checkpointing, use `StateGraph` with `add_conditional_edges` to route between agents based on tool call results or persisted state. Each agent node should return a `Command` that updates state and directs the graph to the next node (e.g., a human-input node). A conditional edge function inspects the state (or Cosmos DB) to determine which agent handles the next turn.

**Incorrect (linear chain — no dynamic routing between agents):**

```python
from langgraph.graph import StateGraph, START, MessagesState

builder = StateGraph(MessagesState)
builder.add_node("agent_a", call_agent_a)
builder.add_node("agent_b", call_agent_b)

# BAD: Fixed linear flow — cannot route dynamically
builder.add_edge(START, "agent_a")
builder.add_edge("agent_a", "agent_b")
builder.add_edge("agent_b", END)
```

**Correct (conditional edges with dynamic routing):**

```python
from typing import Literal
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.types import Command
from langchain_azure_cosmosdb import CosmosDBSaver

async def call_agent_a(state: MessagesState, config) -> Command[Literal["agent_a", "human"]]:
    response = await agent_a.ainvoke(state)
    return Command(update=response, goto="human")

async def call_agent_b(state: MessagesState, config) -> Command[Literal["agent_b", "human"]]:
    response = await agent_b.ainvoke(state)
    return Command(update=response, goto="human")

def route_to_agent(state: MessagesState, config) -> str:
    """Determine which agent handles the next message based on state or DB lookup."""
    # Inspect tool messages for routing hints, or query Cosmos DB for active agent
    # Return the node name to route to
    return "agent_a"  # or "agent_b" based on logic

builder = StateGraph(MessagesState)
builder.add_node("coordinator", call_coordinator)
builder.add_node("agent_a", call_agent_a)
builder.add_node("agent_b", call_agent_b)
builder.add_node("human", human_node)

builder.add_edge(START, "coordinator")
builder.add_conditional_edges(
    "coordinator",
    route_to_agent,
    {"agent_a": "agent_a", "agent_b": "agent_b", "coordinator": "coordinator"}
)

graph = builder.compile(checkpointer=CosmosDBSaver(async_container))
```

**Critical: Only check NEW messages for routing decisions.** When a sub-agent is invoked with `await agent.ainvoke(state)`, the response contains ALL messages — both the existing conversation history AND new messages. If node functions iterate all messages to find routing ToolMessages, they will find old routing messages from previous turns and re-route infinitely, causing a `GraphRecursionError`.

```python
async def call_agent_a(state: MessagesState, config) -> Command[Literal["agent_a", "agent_b", "human"]]:
    response = await agent_a.ainvoke(state)

    # CRITICAL: Only check NEW messages added by this invocation
    existing_count = len(state.get("messages", []))
    new_messages = response.get("messages", [])[existing_count:]

    for msg in reversed(new_messages):
        if isinstance(msg, ToolMessage):
            goto = extract_routing_info(msg)
            if goto:
                return Command(update=response, goto=goto)

    return Command(update=response, goto="human")
```

**Key principles:**
1. Each agent node returns `Command(update=response, goto="human")` to yield control back for user input
2. After user input, the coordinator's conditional edge function decides which agent continues
3. Use Cosmos DB point reads in the routing function for O(1) active-agent lookups
4. Include a fallback route to the coordinator when the active agent is unknown
5. Always slice `response["messages"]` by `len(state["messages"])` to get only new messages — never iterate the full history for routing decisions

Reference: [LangGraph multi-agent patterns](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)

### 1.14 Resume LangGraph from Checkpoint After Interrupt

**Impact: HIGH** (enables multi-turn conversations with persistent state)

## Resume LangGraph from Checkpoint After Interrupt

**Impact: HIGH (enables multi-turn conversations with persistent state)**

When a LangGraph graph pauses at an `interrupt()` node, the next user message must resume from the last checkpoint rather than starting fresh. Retrieve the last checkpoint, append the new user message, inject `langgraph_triggers` to signal which node to resume, and call `ainvoke` with `stream_mode="updates"`. Without proper resume logic, each message starts a new conversation with no memory of prior turns.

**Incorrect (always starts a fresh graph invocation):**

```python
@app.post("/chat/{session_id}")
async def chat(session_id: str, user_message: str):
    config = {"configurable": {"thread_id": session_id}}
    # BAD: Always starts from scratch — ignores prior conversation state
    state = {"messages": [{"role": "user", "content": user_message}]}
    response = await graph.ainvoke(state, config, stream_mode="updates")
    return extract_response(response)
```

**Correct (resume from last checkpoint when one exists):**

```python
@app.post("/chat/{session_id}")
async def chat(session_id: str, user_message: str):
    config = {"configurable": {"thread_id": session_id, "checkpoint_ns": ""}}

    # Check for existing checkpoint (prior conversation state)
    checkpoints = [cp async for cp in checkpointer.alist(config)]

    if not checkpoints:
        # First message — start fresh
        state = {"messages": [{"role": "user", "content": user_message}]}
    else:
        # Resume from last checkpoint
        last_checkpoint = checkpoints[-1]
        state = last_checkpoint.checkpoint

        if "messages" not in state:
            state["messages"] = []
        state["messages"].append({"role": "user", "content": user_message})

        # Signal which node to resume from (required after interrupt)
        # Determine the last active agent from channel_versions or external state
        resume_node = determine_resume_node(state)
        state["langgraph_triggers"] = [f"resume:{resume_node}"]

    response = await graph.ainvoke(state, config, stream_mode="updates")
    return extract_response(response)
```

**Key details:**
1. `stream_mode="updates"` returns per-node state diffs, making it easy to extract only the final agent response
2. `langgraph_triggers` tells the graph which paused node to resume — without it, the graph may restart from START
3. The `checkpoint_ns` must match what was used when the checkpoint was written (typically `""`)
4. Use `checkpointer.alist(config)` to list checkpoints — this is an async generator

Reference: [LangGraph persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)

### 1.15 Use a service layer to hydrate document references before rendering

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
