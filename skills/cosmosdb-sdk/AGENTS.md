# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Best practices for Azure Cosmos DB SDK usage: singleton client, async APIs, connection modes, retry handling, diagnostics, serialization, emulator configuration, and framework-specific patterns for .NET, Java, Python, Spring Boot, and LangChain.

---

## Table of Contents

1. [SDK Best Practices](#1-sdk-best-practices) — **HIGH**
   - 1.1 [Use Async APIs for Better Throughput](#11-use-async-apis-for-better-throughput)
   - 1.2 [Configure Threshold-Based Availability Strategy (Hedging)](#12-configure-threshold-based-availability-strategy-hedging-)
   - 1.3 [Configure Partition-Level Circuit Breaker](#13-configure-partition-level-circuit-breaker)
   - 1.4 [Use IfNoneMatchETag("*") for conditional creates to prevent duplicates](#14-use-ifnonematchetag-for-conditional-creates-to-prevent-duplicates)
   - 1.5 [Use Direct Connection Mode for Production](#15-use-direct-connection-mode-for-production)
   - 1.6 [Guard against empty continuation tokens before calling byPage](#16-guard-against-empty-continuation-tokens-before-calling-bypage)
   - 1.7 [Log Diagnostics for Troubleshooting](#17-log-diagnostics-for-troubleshooting)
   - 1.8 [Use Microsoft.Azure.Cosmos package, not abandoned Azure.Cosmos](#18-use-microsoft-azure-cosmos-package-not-abandoned-azure-cosmos)
   - 1.9 [Avoid Microsoft.Azure.Cosmos namespace collisions with domain models](#19-avoid-microsoft-azure-cosmos-namespace-collisions-with-domain-models)
   - 1.10 [Configure SSL and connection mode for Cosmos DB Emulator](#110-configure-ssl-and-connection-mode-for-cosmos-db-emulator)
   - 1.11 [Use ETags for optimistic concurrency on read-modify-write operations](#111-use-etags-for-optimistic-concurrency-on-read-modify-write-operations)
   - 1.12 [Configure Excluded Regions for Dynamic Failover](#112-configure-excluded-regions-for-dynamic-failover)
   - 1.13 [Use current Go Cosmos DB SDK versions and explicit partition-key metadata](#113-use-current-go-cosmos-db-sdk-versions-and-explicit-partition-key-metadata)
   - 1.14 [Unwrap CosmosItemResponse and enable content response in Java SDK](#114-unwrap-cosmositemresponse-and-enable-content-response-in-java-sdk)
   - 1.15 [Use dependent @Bean methods for Cosmos DB initialization in Spring Boot](#115-use-dependent-bean-methods-for-cosmos-db-initialization-in-spring-boot)
   - 1.16 [Spring Boot and Java version compatibility for Cosmos DB SDK](#116-spring-boot-and-java-version-compatibility-for-cosmos-db-sdk)
   - 1.17 [Initialize Async Cosmos DB Container Before CosmosDBSaver](#117-initialize-async-cosmos-db-container-before-cosmosdbsaver)
   - 1.18 [Use CosmosDBSaver for LangGraph Checkpointing](#118-use-cosmosdbsaver-for-langgraph-checkpointing)
   - 1.19 [Use AzureCosmosDBNoSQLChatMessageHistory for Persistent Conversations in JS/TS](#119-use-azurecosmosdbnosqlchatmessagehistory-for-persistent-conversations-in-js-ts)
   - 1.20 [Configure Azure OpenAI Embedding Deployment Name for JS/TS LangChain](#120-configure-azure-openai-embedding-deployment-name-for-js-ts-langchain)
   - 1.21 [Prevent Filter Injection in JS/TS LangChain Vector Store Queries](#121-prevent-filter-injection-in-js-ts-langchain-vector-store-queries)
   - 1.22 [Configure Full-Text Prerequisites Before JS/TS LangChain Hybrid Search](#122-configure-full-text-prerequisites-before-js-ts-langchain-hybrid-search)
   - 1.23 [Use Managed Identity for JS/TS LangChain Cosmos DB Integration](#123-use-managed-identity-for-js-ts-langchain-cosmos-db-integration)
   - 1.24 [Choose the Correct Search Type for JS/TS LangChain Vector Store](#124-choose-the-correct-search-type-for-js-ts-langchain-vector-store)
   - 1.25 [Use AzureCosmosDBNoSQLSemanticCache for LLM Cost Reduction in JS/TS](#125-use-azurecosmosdbnosqlsemanticcache-for-llm-cost-reduction-in-js-ts)
   - 1.26 [Correctly Initialize AzureCosmosDBNoSQLVectorStore in JavaScript/TypeScript](#126-correctly-initialize-azurecosmosdbnosqlvectorstore-in-javascript-typescript)
   - 1.27 [Use Persistent MCP Client Sessions for Multi-Agent Applications](#127-use-persistent-mcp-client-sessions-for-multi-agent-applications)
   - 1.28 [Handle MCP ToolMessage Content Format Variations](#128-handle-mcp-toolmessage-content-format-variations)
   - 1.29 [Filter MCP Tools by Name Prefix for Agent Assignment](#129-filter-mcp-tools-by-name-prefix-for-agent-assignment)
   - 1.30 [Configure local development environment to avoid cloud connection conflicts](#130-configure-local-development-environment-to-avoid-cloud-connection-conflicts)
   - 1.31 [Explicitly reference Newtonsoft.Json package](#131-explicitly-reference-newtonsoft-json-package)
   - 1.32 [Use the Patch API for atomic counter increments](#132-use-the-patch-api-for-atomic-counter-increments)
   - 1.33 [Configure Preferred Regions for Availability](#133-configure-preferred-regions-for-availability)
   - 1.34 [Include aiohttp When Using Python Async SDK](#134-include-aiohttp-when-using-python-async-sdk)
   - 1.35 [Never share a single CosmosItemRequestOptions instance across multiple createItem calls](#135-never-share-a-single-cosmositemrequestoptions-instance-across-multiple-createitem-calls)
   - 1.36 [Handle 429 Errors with Retry-After](#136-handle-429-errors-with-retry-after)
   - 1.37 [Use consistent enum serialization between Cosmos SDK and application layer](#137-use-consistent-enum-serialization-between-cosmos-sdk-and-application-layer)
   - 1.38 [Reuse CosmosClient as Singleton](#138-reuse-cosmosclient-as-singleton)
   - 1.39 [Annotate entities for Spring Data Cosmos with @Container, @PartitionKey, and String IDs](#139-annotate-entities-for-spring-data-cosmos-with-container-partitionkey-and-string-ids)
   - 1.40 [Use CosmosRepository correctly and handle Iterable return types](#140-use-cosmosrepository-correctly-and-handle-iterable-return-types)

---

## 1. SDK Best Practices

**Impact: HIGH**

### 1.1 Use Async APIs for Better Throughput

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

### 1.2 Configure Threshold-Based Availability Strategy (Hedging)

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

### 1.3 Configure Partition-Level Circuit Breaker

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

### 1.4 Use IfNoneMatchETag("*") for conditional creates to prevent duplicates

**Impact: HIGH** (prevents duplicate documents on concurrent or retried creates without a prior read)

## Use IfNoneMatchETag("*") for Conditional Creates to Prevent Duplicates

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
        .createItem(credentialsDto, new PartitionKey(email), options)
        .block();
} catch (CosmosException ex) {
    if (ex.getStatusCode() == 409) {
        // Email already registered — surface as domain error
        throw new AlreadyExistsException("Email already in use: " + email);
    }
    throw ex;
}
```

```java
// ✅ Reactive chain
credentialsContainer
    .createItem(credentialsDto, new PartitionKey(email),
        new CosmosItemRequestOptions().setIfNoneMatchETag("*"))
    .onErrorMap(CosmosException.class, ex ->
        ex.getStatusCode() == 409
            ? new AlreadyExistsException("Email already in use")
            : ex);
```

**Why `"*"` (wildcard):** In HTTP `If-None-Match: *` semantics, `"*"` means "match any existing document". Combined with `createItem` (not `upsertItem`), the server rejects the write if _any_ document with the same `id` and partition key already exists — regardless of its ETag value.

**Key Points:**
- Use `createItem` + `setIfNoneMatchETag("*")`, never `upsertItem`, when uniqueness is a domain invariant
- The 409 check is done atomically server-side — no extra read RU consumed
- Gated on the document's `id` field + partition key (not arbitrary field values)
- Particularly critical for email-keyed credential stores and idempotent API endpoints

Reference: [Optimistic concurrency in Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/database-transactions-optimistic-concurrency)

### 1.5 Use Direct Connection Mode for Production

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

### 1.6 Guard against empty continuation tokens before calling byPage

**Impact: HIGH** (empty string token causes runtime "INVALID JSON in continuation token" error; null is the correct sentinel for first-page requests)

## Guard Against Empty Continuation Tokens Before Calling byPage

**Impact: HIGH (empty string token causes runtime `INVALID JSON in continuation token` error; `null` is the correct sentinel for first-page requests)**

When integrating Cosmos DB pagination with frameworks that use empty strings as default values for "no token" (e.g., gRPC/proto3, where string fields default to `""`), passing `""` to `byPage(continuationToken, pageSize)` triggers a server-side parse error. The correct sentinel for "no paging state" is `null`.

**Incorrect (empty string passed as continuation token):**

```java
// ❌ gRPC/proto3: string fields default to "" — NOT null
String pagingState = request.getPagingState();  // returns "" on first call

// Passing "" to byPage causes:
// CosmosException: INVALID JSON in continuation token
return container.queryItems(querySpec, opts, Video.class)
    .byPage(pagingState, pageSize)          // ❌ "" is not a valid token
    .next()
    .toFuture();
```

**Correct (null-guard before passing to byPage):**

```java
// ✅ Convert empty string to null before passing as continuation token
String raw = request.getPagingState();     // "" on first call, token on subsequent calls
String continuationToken = (raw == null || raw.isEmpty()) ? null : raw;

return container.queryItems(querySpec, opts, Video.class)
    .byPage(continuationToken, pageSize)   // ✅ null = first page, token = continuation
    .next()
    .map(page -> new ResultListPage<>(page.getResults(), page.getContinuationToken()))
    .switchIfEmpty(Mono.just(new ResultListPage<>()))
    .toFuture();
```

```java
// ✅ Or with Optional pattern
Optional<String> pageState = Optional.ofNullable(
    raw == null || raw.isEmpty() ? null : raw);

return container.queryItems(querySpec, opts, Video.class)
    .byPage(pageState.orElse(null), pageSize)
    .next()
    .toFuture();
```

**General pattern for any pagination layer:**

| Input value | Meaning | Pass to byPage as |
|-------------|---------|------------------|
| `null` | First page | `null` |
| `""` (empty string) | First page (proto3/gRPC default) | `null` |
| `"eyJ..."` (token) | Continuation | Pass as-is |

**Key Points:**
- `byPage(String continuationToken, int pageSize)` — `continuationToken` must be `null` for the first page request, never `""`
- This issue appears in any integration where the paging state field has a non-null empty default: gRPC/proto3 strings, Jackson deserialization of missing JSON fields, HTTP query parameters
- `page.getContinuationToken()` returns `null` when there are no more pages — map `null` back to `""` when sending to clients that expect non-null strings (e.g., proto3 response fields)
- `switchIfEmpty(Mono.just(new ResultListPage<>()))` handles the case where the query matches zero documents and `byPage(...).next()` emits nothing

Reference: [Query with continuation tokens (Java SDK)](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-java-get-started)

### 1.7 Log Diagnostics for Troubleshooting

**Impact: MEDIUM** (enables root cause analysis)

## Log Diagnostics for Troubleshooting

Capture and log diagnostics from Cosmos DB responses, especially for slow or failed operations. Diagnostics contain crucial information for troubleshooting.

`CosmosException.Diagnostics` (type `CosmosDiagnostics`) is a first-class structured signal the SDK provides for debugging failures (RU spend, latency tails, 429s, region selection, and channel reuse). Demonstrating the pattern is not enough — it must be applied at the point of failure.

**Required (strict syntactic minimum):** Every `catch` block whose declared exception type is `Microsoft.Azure.Cosmos.CosmosException` (or a subclass) **must reference `.Diagnostics` on the caught exception variable somewhere inside the catch-block body** — either by logging it as a structured field, or by attaching it to a re-thrown exception's message/data. A bare swallow (`catch (CosmosException) { }`, `catch (CosmosException) { return null; }`, `return default;`, `return new T();`, etc., without first surfacing `.Diagnostics`) is a violation unless the block first surfaces `.Diagnostics` (for example, by logging it before returning).

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

```csharp
// Pattern A — log message text only, drop Diagnostics (VIOLATION)
catch (CosmosException ex)
{
    _logger.LogError(ex, "Cosmos call failed: {Message}", ex.Message);
    throw;
}

// Pattern B — re-wrap without surfacing Diagnostics (VIOLATION)
catch (CosmosException ex)
{
    throw new InvalidOperationException($"Cosmos error: {ex.StatusCode}", ex);
}

// Pattern C — bare swallow (VIOLATION)
catch (CosmosException)
{
    return null;
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

Minimal acceptable catch block — `ex.Diagnostics` is the non-negotiable part. `StatusCode`, `ActivityId`, and `RequestCharge` are strongly recommended (`CosmosDiagnostics.ToString()` includes the latter two, but having them as structured fields makes log search trivial):

```csharp
catch (CosmosException ex)
{
    _logger.LogError(ex,
        "Cosmos call failed. StatusCode={Status} ActivityId={ActivityId} " +
        "RequestCharge={RU} Diagnostics={Diagnostics}",
        ex.StatusCode, ex.ActivityId, ex.RequestCharge, ex.Diagnostics);
    throw;
}
```

If you must re-wrap, carry the diagnostics forward so they are not lost:

```csharp
catch (CosmosException ex)
{
    throw new InvalidOperationException(
        $"Cosmos error: {ex.StatusCode}. Diagnostics={ex.Diagnostics}", ex);
}
```

Key diagnostic fields:
- `GetClientElapsedTime()`: Total client-side time
- `RequestCharge`: RU consumed
- Server response time, regions contacted
- Retry information
- Connection information

**Detector (mechanical check):** For each `catch` clause whose declared type binds to `Microsoft.Azure.Cosmos.CosmosException` (or a subclass), verify the block body contains a member access ending in `.Diagnostics` on the caught variable. If absent, flag the catch-block source range. This is expressible as a Roslyn analyzer or a regex over `.cs` files (excluding `bin/`, `obj/`, and test directories).

**Why it matters:** `Diagnostics` carries the RU charge, activity ID, the region the call hit, and the per-channel timing breakdown. On a 429 it also contains the back-end retry hints. Without it, the operator loses exactly the information needed to debug the failure. See the throughput / RU rules for why `RequestCharge` matters at observability time, and the retry / 429 handling guidance for why 429 catch blocks must capture diagnostics.

Reference: [Capture diagnostics — Troubleshoot .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/troubleshoot-dotnet-sdk#capture-diagnostics)

### 1.8 Use Microsoft.Azure.Cosmos package, not abandoned Azure.Cosmos

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

### 1.9 Avoid Microsoft.Azure.Cosmos namespace collisions with domain models

**Impact: HIGH** (prevents CS0104 build-breaking ambiguous reference errors)

## Avoid Microsoft.Azure.Cosmos Namespace Collisions with Domain Models

The `Microsoft.Azure.Cosmos` namespace exports top-level types including `User`, `Database`, `Container`, `Conflict`, `Trigger`, and `Permission`. When an application defines a domain entity by the same name and both namespaces are imported with unqualified `using` directives in the same file, every reference to the shared name becomes ambiguous and the build fails with **CS0104**.

**Incorrect (ambiguous reference — CS0104):**

```csharp
using ECommerce.Core.Models;      // defines User
using Microsoft.Azure.Cosmos;     // also defines User

public class UserRepository
{
    private readonly Container _container;

    public UserRepository(CosmosClient client)
        => _container = client.GetContainer("db", "users");

    // CS0104: 'User' is an ambiguous reference between
    // 'ECommerce.Core.Models.User' and 'Microsoft.Azure.Cosmos.User'
    public async Task<User> GetUserAsync(string id, string partitionKey)
        => await _container.ReadItemAsync<User>(id, new PartitionKey(partitionKey));
}
```

**Correct (alias the SDK import):**

```csharp
using Cosmos = Microsoft.Azure.Cosmos;
using ECommerce.Core.Models;      // defines User — no collision

public class UserRepository
{
    private readonly Cosmos.Container _container;

    public UserRepository(Cosmos.CosmosClient client)
        => _container = client.GetContainer("db", "users");

    public async Task<User> GetUserAsync(string id, string partitionKey)
        => await _container.ReadItemAsync<User>(id, new Cosmos.PartitionKey(partitionKey));
}
```

**Also correct (fully qualify SDK types):**

```csharp
using ECommerce.Core.Models;

public class UserRepository
{
    private readonly Microsoft.Azure.Cosmos.Container _container;

    public UserRepository(Microsoft.Azure.Cosmos.CosmosClient client)
        => _container = client.GetContainer("db", "users");

    public async Task<User> GetUserAsync(string id, string partitionKey)
        => await _container.ReadItemAsync<User>(
            id, new Microsoft.Azure.Cosmos.PartitionKey(partitionKey));
}
```

**Key points:**
- Do not place both `using Microsoft.Azure.Cosmos;` and a domain `using` that exposes a colliding name (`User`, `Database`, `Container`, etc.) in the same file.
- Prefer the alias approach (`using Cosmos = Microsoft.Azure.Cosmos;`) — it keeps code concise while eliminating ambiguity.
- Common colliding names: `User`, `Database`, `Container`, `Conflict`, `Trigger`, `Permission`.

Reference: [C# CS0104 — ambiguous reference](https://learn.microsoft.com/dotnet/csharp/misc/cs0104)

### 1.10 Configure SSL and connection mode for Cosmos DB Emulator

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

> **Which emulator are you on?**
> - **Windows desktop emulator** → follow this section.
> - **Linux (vNext) emulator** (`...azure-cosmos-emulator:vnext-latest`, `--protocol https`) → see
>   [Java SDK + Linux (vNext) Emulator over HTTPS](#java-sdk--linux-vnext-emulator-over-https) below.
>   In addition to trusting the cert, the Linux emulator requires connecting via a **SAN-matching
>   host** (`localhost`/`127.0.0.1`) and setting **`endpointDiscoveryEnabled(false)`** — details there.

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

---

### Java SDK + Linux (vNext) Emulator over HTTPS

The steps above target the **Windows desktop emulator**. The **Linux (vNext) emulator**
(`mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-latest`) run with
`--protocol https` needs two things for the Java SDK that are easy to miss: the emulator's
certificate must be **trusted** (a trust-all `SSLContext` in code is ignored), and you must
connect via a host in the certificate **SAN** (`localhost`/`127.0.0.1`).

**Symptoms (three distinct failures):**

```text
# (a) Cert not trusted, surfaced through Netty's native OpenSSL provider
#     (netty-tcnative). This is the same trust failure as (b), just wrapped
#     by the OpenSSL engine rather than the JDK SSL engine:
com.azure.cosmos.CosmosException: ... General OpenSslEngine problem

# (b) Cert not trusted, surfaced through the JDK SSL provider:
javax.net.ssl.SSLHandshakeException: PKIX path building failed:
  sun.security.provider.certpath.SunCertPathBuilderException:
  unable to find valid certification path to requested target

# (c) Cert trusted, but connecting via a host outside the cert SAN —
#     the Java SDK enforces strict TLS hostname verification:
javax.net.ssl.SSLPeerUnverifiedException:
  No subject alternative DNS name matching <host> found. SANs in the cert: localhost, 127.0.0.1
```

> Note: `(a)` and `(b)` are the **same** underlying trust failure reported by whichever SSL
> provider is active (`netty-tcnative` OpenSSL vs. the JDK). Importing the emulator certificate
> resolves both; the provider does not change the fix.

**⚠️ A programmatic trust-all `SSLContext` does NOT work** — the Java SDK builds its own
Netty `SslContext` from the configured truststore and does **not** honor the JVM-default
`SSLContext`, so an all-trusting `TrustManager` installed via `SSLContext.setDefault(...)` is
silently ignored and the handshake still fails (`PKIX path building failed`). Unlike the
Go/Node/.NET/Python SDKs, the Java SDK has no direct "disable certificate validation" switch —
trust the emulator certificate explicitly via the truststore instead.

**Recommended pattern:**

**Step 1 (primary fix) — Export and import the emulator certificate into the JDK truststore:**
This is sufficient on its own with current SDK builds (verified with `azure-cosmos` 4.65.0 on
Windows and Linux): the native OpenSSL provider (`netty-tcnative`) honors the certificates in
the configured truststore.

```bash
# Export the cert presented by the Linux emulator:
openssl s_client -connect localhost:8081 -servername localhost </dev/null 2>/dev/null \
  | openssl x509 -outform PEM > emulator.crt

# Import it into the JDK truststore (cacerts):
keytool -importcert -trustcacerts -alias cosmos-emulator \
  -file emulator.crt -keystore "$JAVA_HOME/lib/security/cacerts" \
  -storepass changeit -noprompt
```

**Step 2 — Connect via a host that is in the certificate SAN** (`localhost` or `127.0.0.1`).
Any other host name (a container/service alias, for example) fails strict SAN verification
with `No subject alternative DNS name matching <host> found`:

```bash
COSMOS_ENDPOINT=https://localhost:8081
```

**Step 3 — Use Gateway mode, pin the endpoint, and disable endpoint discovery.**
`endpointDiscoveryEnabled(false)` stops the SDK from following the advertised `127.0.0.1`
loopback; do **not** rely on a trust-all `SSLContext`:

```java
CosmosClient client = new CosmosClientBuilder()
    .endpoint(System.getenv("COSMOS_ENDPOINT"))   // https://localhost:8081 (SAN-matching host)
    .key(System.getenv("COSMOS_KEY"))             // well-known emulator key
    .gatewayMode()                                 // required for the emulator
    .endpointDiscoveryEnabled(false)               // don't follow the advertised 127.0.0.1 loopback
    .buildClient();
```

**Step 4 (fallback) — If the imported cert is not honored on your Netty/tcnative build,**
force the JDK SSL provider so the JDK truststore (`cacerts`) is consulted directly. Some
older `netty-tcnative` builds keep separate trust material; this switch sidesteps that:

```bash
# As a JVM system property:
-Dio.netty.handler.ssl.noOpenSsl=true

# Equivalently, exclude netty-tcnative-boringssl-static from the dependency tree.
```

**Verify:**

```bash
# With the emulator cert imported into the truststore -> connects over HTTPS:
mvn -q compile exec:java -Dexec.mainClass=com.example.Main

# If your build still fails with "General OpenSslEngine problem", add the JDK-SSL-provider switch:
MAVEN_OPTS="-Dio.netty.handler.ssl.noOpenSsl=true" \
  mvn -q compile exec:java -Dexec.mainClass=com.example.Main
```

**Key Points (Linux vNext + Java):**
- Importing the emulator certificate into the truststore (`cacerts` or a custom truststore via `-Djavax.net.ssl.trustStore`) is the primary fix — with current builds the `netty-tcnative` OpenSSL provider honors it (verified with `azure-cosmos` 4.65.0).
- A programmatic trust-all `SSLContext` is ignored — the SDK builds its own `SslContext` from the configured truststore, not the JVM-default `SSLContext`. Trust the cert explicitly instead.
- The emulator's self-signed cert has SAN = `localhost, 127.0.0.1` only — connect via one of those hosts or strict TLS hostname verification fails.
- Use `gatewayMode()` and `endpointDiscoveryEnabled(false)`; pin the endpoint to the SAN-matching host.
- Fallback: if a particular `netty-tcnative` build does not honor the imported cert, set `-Dio.netty.handler.ssl.noOpenSsl=true` (or exclude `netty-tcnative-boringssl-static`) to force the JDK SSL provider.

Reference: [Azure Cosmos DB Java SDK v4](https://learn.microsoft.com/azure/cosmos-db/sdk-java-v4)

---

### Rust SDK (`azure_data_cosmos`)

The Rust SDK provides a built-in method to accept the emulator's self-signed certificate:

```rust
use azure_data_cosmos::{
    CosmosAccountEndpoint, CosmosAccountReference, CosmosClient, CosmosClientBuilder,
};
use azure_core::credentials::Secret;

// ✅ Emulator configuration — accepts invalid certificates
let endpoint: CosmosAccountEndpoint = "https://localhost:8081"
    .parse()
    .expect("valid endpoint");

let account = CosmosAccountReference::with_master_key(
    endpoint,
    Secret::from("C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==".to_string()),
);

let client = CosmosClientBuilder::new()
    .with_allow_emulator_invalid_certificates(true)  // Accept self-signed cert
    .build(account)
    .await
    .expect("build client");

// For production, omit with_allow_emulator_invalid_certificates:
// CosmosClientBuilder::new().build(account).await
```

**Required Cargo.toml features:**
```toml
[dependencies]
azure_data_cosmos = { version = "0.31", features = ["key_auth", "hmac_rust", "allow_invalid_certificates"] }
azure_core = "0.32"
```

> **Note:** The `allow_invalid_certificates` feature must be enabled in Cargo.toml for
> `with_allow_emulator_invalid_certificates(true)` to compile.

---

Reference: [Use the Azure Cosmos DB Emulator for local development](https://learn.microsoft.com/azure/cosmos-db/emulator)

### 1.11 Use ETags for optimistic concurrency on read-modify-write operations

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
# Python SDK: Use ETag with MatchConditions from azure.core
from azure.core import MatchConditions
from azure.cosmos.exceptions import CosmosHttpResponseError

response = container.read_item(item=player_id, partition_key=player_id)
etag = response.get('_etag')

# Modify response dict...

try:
    container.upsert_item(
        body=response,
        etag=etag,
        match_condition=MatchConditions.IfNotModified  # NOT a string, must be enum
    )
except CosmosHttpResponseError as e:
    if e.status_code == 412:
        # Retry: document was modified concurrently
        pass
```

> **⚠️ Python SDK Pitfall**: `match_condition` must be `MatchConditions.IfNotModified`
> from `azure.core`, not a string like `"IfMatch"`. Passing a string raises
> `TypeError: Invalid match condition`. The `MatchConditions` enum values are:
> `IfNotModified`, `IfModified`, `IfPresent`, `IfMissing`.

**When to use ETags:**
- **Always use** for read-modify-write patterns (counters, aggregates, status updates)
- **Always use** when multiple users/services can modify the same document
- **Always use** when updating denormalized data (see below)
- **Skip** for append-only operations (new document creation with unique IDs)
- **Skip** for idempotent overwrites where last-writer-wins is acceptable

**Rust (`azure_data_cosmos`) equivalent:**

```rust
use azure_data_cosmos::{ItemOptions, PartitionKey};
use azure_core::http::StatusCode;

// Read document and capture ETag from response headers
let container = cosmos.database_client("db").container_client("orders").await;
let pk = PartitionKey::from(customer_id.to_string());

// Read the current document
let response = container.read_item::<serde_json::Value>(pk.clone(), &order_id, None)
    .await
    .map_err(|e| format!("read failed: {}", e))?;

let etag = response.etag().map(|e| e.to_string());
let mut order: Order = serde_json::from_value(response.into_body())?;

// Modify the document
order.status = "shipped".to_string();

// Write with ETag condition — fails if document changed since read
// Note: Pass the ETag as an If-Match header for conditional writes.
// The azure_data_cosmos SDK (v0.31+) supports this via ItemOptions;
// check your SDK version for the exact method name.
let options = ItemOptions::default();
// options = options.with_if_match_etag(etag.unwrap());

let item = serde_json::to_value(&order)?;
match container.replace_item(pk, &order.id, item, Some(options)).await {
    Ok(_) => { /* Success */ }
    Err(e) if e.http_status() == Some(StatusCode::PreconditionFailed) => {
        // HTTP 412: Document was modified — retry from read
    }
    Err(e) => return Err(e.into()),
}
```

### ⚠️ Critical: ETags for Denormalized Data Updates

Denormalized fields (e.g., task counts on a project, user names on related documents) are especially vulnerable to lost updates. When multiple operations update the same parent document's counters concurrently, **ETag checks are mandatory**:

```java
// ❌ Anti-pattern: Updating denormalized counts without ETag
public void updateProjectTaskCounts(String tenantId, String projectId) {
    // Two tasks created simultaneously — both read count=5
    CosmosItemResponse<Project> response = container.readItem(
        projectId, partitionKey, Project.class);
    Project project = response.getItem();
    
    project.setTaskCountTotal(countTasksInProject(tenantId, projectId)); // = 7
    container.upsertItem(project, partitionKey, null);
    // Second concurrent call also sets count to 7, missing the other's task!
}

// ✅ Correct: ETag-protected denormalized count update with retry
public void updateProjectTaskCounts(String tenantId, String projectId) {
    for (int attempt = 0; attempt < 3; attempt++) {
        try {
            CosmosItemResponse<Project> response = container.readItem(
                projectId, partitionKey, Project.class);
            Project project = response.getItem();
            String etag = response.getETag();

            // Re-count from source of truth
            project.setTaskCountTotal(countTasksInProject(tenantId, projectId));
            project.setTaskCountOpen(countTasksByStatus(tenantId, projectId, "open"));

            CosmosItemRequestOptions options = new CosmosItemRequestOptions();
            options.setIfMatchETag(etag);  // Fail if another update landed
            container.upsertItem(project, partitionKey, options);
            return;
        } catch (CosmosException ex) {
            if (ex.getStatusCode() == 412 && attempt < 2) continue; // Retry
            throw ex;
        }
    }
}
```

**Why denormalized data is high-risk:**
- Multiple child operations (create task, delete task, update status) all touch the same parent
- Without ETag checks, concurrent operations silently overwrite each other's count updates
- The resulting counts become permanently incorrect until manually recalculated
- This is the most common source of data inconsistency in Cosmos DB applications

**Key Points:**
- Every Cosmos DB document has a system-managed `_etag` property that changes on every write
- Pass `IfMatchEtag` (or `setIfMatchETag` in Java) to get HTTP 412 on conflicts
- Always implement retry logic (typically 3 attempts) for ETag conflicts
- ETag checks add no extra RU cost — it's a header comparison, not an additional read
- For high-contention scenarios (thousands of concurrent updates to same document), consider a different data model (e.g., append scores as separate documents, aggregate periodically)

Reference: [Optimistic concurrency control in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/database-transactions-optimistic-concurrency#optimistic-concurrency-control)

### 1.12 Configure Excluded Regions for Dynamic Failover

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

### 1.13 Use current Go Cosmos DB SDK versions and explicit partition-key metadata

**Impact: HIGH** (prevents cross-SDK partition-key metadata incompatibilities)

## Use current Go Cosmos DB SDK versions and explicit partition-key metadata

When creating Azure Cosmos DB containers from Go with `github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos`, avoid stale SDK pins such as `v1.0.0`. The primary fix is **upgrading the SDK**: `azcosmos v1.0.0` serializes a `Paths`-only `PartitionKeyDefinition` as `{"paths":["/h3Cell"]}` — omitting `kind` entirely — whereas `v1.3.0` serializes `{"kind":"Hash","paths":["/h3Cell"]}`. A container created without `kind` will cause a `KeyError: 'kind'` when another SDK (e.g. Python `azure-cosmos`) later reads its partition-key metadata.

Setting `Kind` explicitly in the struct is good defensive practice; the SDK upgrade alone is the load-bearing change. Note: `Version: 2` enables large partition keys (up to 2 KB) and is unrelated to this cross-SDK `kind` incompatibility — omit it unless your application specifically needs large keys.

**Note:** This failure reproduces reliably on the Cosmos DB vNext emulator. Real Azure Cosmos DB may inject a default `kind` server-side; however, writing complete partition-key metadata is correct regardless and avoids relying on server-side normalization.

**Incorrect (stale SDK pin — serializes without `kind`):**

```go.mod
require (
    github.com/Azure/azure-sdk-for-go/sdk/azcore v1.10.0
    github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos v1.0.0
)
```

```go
props := azcosmos.ContainerProperties{
    ID: "driver_state",
    PartitionKeyDefinition: azcosmos.PartitionKeyDefinition{
        Paths: []string{"/h3Cell"},
    },
}

_, err := db.CreateContainer(ctx, props, nil)
if err != nil {
    return err
}
```

**Correct (current SDK — serializes `kind:"Hash"`; explicit `Kind` is defensive best practice):**

```go.mod
require (
    github.com/Azure/azure-sdk-for-go/sdk/azcore v1.16.0
    github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos v1.3.0
)
```

```go
props := azcosmos.ContainerProperties{
    ID: "driver_state",
    PartitionKeyDefinition: azcosmos.PartitionKeyDefinition{
        Paths: []string{"/h3Cell"},
        Kind:  azcosmos.PartitionKeyKindHash,
    },
}

_, err := db.CreateContainer(ctx, props, nil)
if err != nil {
    return fmt.Errorf("create container: %w", err)
}

pk := azcosmos.NewPartitionKeyString(doc.H3Cell)
_, err = container.UpsertItem(ctx, pk, body, nil)
if err != nil {
    return fmt.Errorf("upsert %s: %w", doc.ID, err)
}
```

Use the same explicit partition key value for writes and partition-scoped queries. Only use `MultiHash` for true hierarchical partition keys.

References:
- [Azure Cosmos DB for NoSQL partitioning overview](https://learn.microsoft.com/azure/cosmos-db/partitioning-overview)
- [Azure Cosmos DB Go SDK (`azcosmos`) package docs](https://pkg.go.dev/github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos)

### 1.14 Unwrap CosmosItemResponse and enable content response in Java SDK

**Impact: MEDIUM** (prevents type errors from missing getItem() on reads and null content on writes)

## Unwrap CosmosItemResponse with getItem() (Java)

All Cosmos DB Java SDK point-read and write operations (`readItem`, `createItem`, `upsertItem`, `replaceItem`) return `CosmosItemResponse<T>`, **not** `T` directly. You must call `.getItem()` to extract the entity. Treating the response wrapper as the entity causes compilation errors or incorrect behavior.

### Always unwrap readItem() with getItem()

`readItem()` always returns `CosmosItemResponse<T>`. You must call `.getItem()` to get the actual document.

**Incorrect — treating CosmosItemResponse as the entity:**

```java
// ❌ WRONG: readItem returns CosmosItemResponse<Player>, NOT Player
public Player getPlayer(String playerId) {
    Player player = container.readItem(
        playerId, new PartitionKey(playerId), Player.class);  // ❌ Compilation error!
    return player;
}
```

```java
// ❌ WRONG (async): Mono<CosmosItemResponse<Player>> is not Mono<Player>
public Mono<Player> getPlayer(String playerId) {
    return container.readItem(
        playerId, new PartitionKey(playerId), Player.class);  // ❌ Type mismatch!
}
```

**Correct — unwrap with getItem():**

```java
// ✅ CORRECT: Call getItem() to extract the entity from the response
public Player getPlayer(String playerId) {
    CosmosItemResponse<Player> response = container.readItem(
        playerId, new PartitionKey(playerId), Player.class);
    return response.getItem();  // ✅ Returns the Player entity
}
```

```java
// ✅ CORRECT (async): Map the response to extract the entity
public Mono<Player> getPlayer(String playerId) {
    return container.readItem(
            playerId, new PartitionKey(playerId), Player.class)
        .map(response -> response.getItem());  // ✅ Unwrap to Player
}
```

> **Why this matters:** `CosmosItemResponse<T>` is a wrapper that holds the entity (`getItem()`),
> request charge (`getRequestCharge()`), ETag (`getETag()`), headers, and diagnostics.
> Assigning the response directly to a variable of type `T` is a compile-time error in
> synchronous code and a type-mismatch error in reactive chains. This affects `readItem`,
> `createItem`, `upsertItem`, and `replaceItem` — all return `CosmosItemResponse<T>`.

### Enable Content Response on Write Operations

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

**⚠️ Reactor / reactive streams — never set `contentResponseOnWriteEnabled(false)` on `CosmosAsyncClient`:**

When using `CosmosAsyncClient` with Project Reactor, setting `contentResponseOnWriteEnabled(false)` causes `CosmosItemResponse.getItem()` to return `null`. Reactor does not allow `null` signals in its pipeline (Reactive Streams Specification, Rule 2.13), so any downstream `.map(CosmosItemResponse::getItem)` or similar operator throws a `NullPointerException` from inside Reactor internals — not from your code — making the root cause very hard to diagnose.

```java
// ❌ Causes NPE in reactive stream — never do this with CosmosAsyncClient
CosmosAsyncClient asyncClient = new CosmosClientBuilder()
    .endpoint(endpoint)
    .key(key)
    .contentResponseOnWriteEnabled(false)
    .buildAsyncClient();

container.upsertItem(item)
    .map(CosmosItemResponse::getItem)  // ❌ getItem() returns null → NPE
    .block();
```

```java
// ✅ Option 1 (recommended): Keep content response enabled for async clients
CosmosAsyncClient asyncClient = new CosmosClientBuilder()
    .endpoint(endpoint)
    .key(key)
    .contentResponseOnWriteEnabled(true)
    .buildAsyncClient();

container.upsertItem(item)
    .map(CosmosItemResponse::getItem)  // ✅ Non-null, safe in Reactor
    .block();
```

```java
// ✅ Option 2: If you must suppress content, guard against null before mapping
container.upsertItem(item)
    .flatMap(response -> {
        MyItem result = response.getItem();
        return result != null ? Mono.just(result) : Mono.empty();
    });
```

**When NOT to enable content response:**

If you don't need the created document (fire-and-forget writes) **and you are using the synchronous `CosmosClient`**, leave it disabled to save bandwidth:

```java
// High-throughput ingestion with synchronous client - don't need response content
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
- `readItem()`, `createItem()`, `upsertItem()`, and `replaceItem()` all return `CosmosItemResponse<T>` — always call `.getItem()` to get `T`
- In reactive/async code, use `.map(response -> response.getItem())` to unwrap the entity from the `Mono`
- Java SDK returns null from `getItem()` by default for created/upserted items — enable `contentResponseOnWriteEnabled(true)` to get documents back after writes
- Can be set at client level (all operations) or per-request
- Spring Data Cosmos handles both unwrapping and content response automatically
- **Never set `contentResponseOnWriteEnabled(false)` with `CosmosAsyncClient` / reactive streams** — it causes `NullPointerException` in the Reactor pipeline
- Only disable content response for high-throughput fire-and-forget writes with the synchronous `CosmosClient`

Reference: [Azure Cosmos DB Java SDK best practices](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-java)

### 1.15 Use dependent @Bean methods for Cosmos DB initialization in Spring Boot

**Impact: HIGH** (prevents circular dependency, startup failures, class name collisions, and compile errors)

## Use Dependent @Bean Methods for Cosmos DB Initialization in Spring Boot

When configuring `CosmosClient`, `CosmosDatabase`, and `CosmosContainer` beans in a Spring Boot `@Configuration` class, use dependent `@Bean` methods with parameter injection instead of `@PostConstruct`. Calling a `@Bean` method from `@PostConstruct` in the same class creates a circular dependency that crashes the application on startup.

Follow these additional rules to avoid common startup failures:

1. **Do not name your configuration class `CosmosConfig`.** This collides with `com.azure.spring.data.cosmos.config.CosmosConfig` in the Spring Data Cosmos SDK, causing cascading compile errors. Use `CosmosDbConfig`, `CosmosConfiguration`, or `AppCosmosConfig` instead.

2. **Always call `createDatabaseIfNotExists()` before `createContainerIfNotExists()`.** On a fresh Cosmos DB instance (including the emulator), the database does not exist. Calling `createContainerIfNotExists()` without first ensuring the database exists throws `CosmosException: NotFound`.

3. **When extending `AbstractCosmosConfiguration`, do not annotate `cosmosClientBuilder()` with `@Override`.** It is not declared as overridable in `AbstractCosmosConfiguration`. Provide it as a `@Bean` method instead. The only method you should override is `getDatabaseName()`.

**Incorrect (@PostConstruct calling @Bean — circular dependency):**

```java
// ❌ Anti-pattern: @PostConstruct + @Bean in same class causes circular dependency
@Configuration
public class CosmosDbConfig {

    @Value("${azure.cosmos.endpoint}")
    private String endpoint;

    @Value("${azure.cosmos.key}")
    private String key;

    @Bean
    public CosmosClient cosmosClient() {
        return new CosmosClientBuilder()
            .endpoint(endpoint)
            .key(key)
            .consistencyLevel(ConsistencyLevel.SESSION)
            .buildClient();
    }

    @PostConstruct  // ❌ This calls cosmosClient() which is a @Bean — circular!
    public void initializeDatabase() {
        CosmosClient client = cosmosClient(); // Triggers proxy interception loop
        client.createDatabaseIfNotExists("mydb");
        CosmosDatabase db = client.getDatabase("mydb");
        db.createContainerIfNotExists(
            new CosmosContainerProperties("items", "/partitionKey"),
            ThroughputProperties.createAutoscaledThroughput(4000));
    }

    @Bean
    public CosmosDatabase cosmosDatabase() {
        return cosmosClient().getDatabase("mydb");
    }

    @Bean
    public CosmosContainer cosmosContainer() {
        return cosmosDatabase().getContainer("items");
    }
}
// Runtime error: BeanCurrentlyInCreationException — circular dependency detected
```

**Correct (dependent @Bean chain with parameter injection):**

```java
// ✅ Correct: Use @Bean dependency injection chain — initialization in bean methods
@Configuration
public class CosmosDbConfig {

    @Value("${azure.cosmos.endpoint}")
    private String endpoint;

    @Value("${azure.cosmos.key}")
    private String key;

    @Value("${azure.cosmos.database}")
    private String databaseName;

    @Value("${azure.cosmos.container}")
    private String containerName;

    @Bean(destroyMethod = "close")
    public CosmosClient cosmosClient() {
        DirectConnectionConfig directConfig = DirectConnectionConfig.getDefaultConfig();
        GatewayConnectionConfig gatewayConfig = GatewayConnectionConfig.getDefaultConfig();

        // Use Gateway for emulator, Direct for production
        CosmosClientBuilder builder = new CosmosClientBuilder()
            .endpoint(endpoint)
            .key(key)
            .consistencyLevel(ConsistencyLevel.SESSION)
            .contentResponseOnWriteEnabled(true);

        if (endpoint.contains("localhost") || endpoint.contains("127.0.0.1")) {
            builder.gatewayMode(gatewayConfig);
        } else {
            builder.directMode(directConfig);
        }

        return builder.buildClient();
    }

    @Bean  // ✅ Spring injects cosmosClient from the bean above
    public CosmosDatabase cosmosDatabase(CosmosClient cosmosClient) {
        // Database initialization happens here — no @PostConstruct needed
        cosmosClient.createDatabaseIfNotExists(databaseName);
        return cosmosClient.getDatabase(databaseName);
    }

    @Bean  // ✅ Spring injects cosmosDatabase from the bean above
    public CosmosContainer cosmosContainer(CosmosDatabase cosmosDatabase) {
        CosmosContainerProperties props = new CosmosContainerProperties(
            containerName, "/partitionKey");

        cosmosDatabase.createContainerIfNotExists(
            props,
            ThroughputProperties.createAutoscaledThroughput(4000));

        return cosmosDatabase.getContainer(containerName);
    }
}
```

**Why this works:**
- Spring resolves the dependency graph: `cosmosClient()` → `cosmosDatabase(CosmosClient)` → `cosmosContainer(CosmosDatabase)`
- Database and container creation happens naturally during bean initialization
- No circular reference because each method receives its dependency as a parameter
- `destroyMethod = "close"` ensures `CosmosClient` is properly shut down

**With Hierarchical Partition Keys:**

```java
@Bean
public CosmosContainer cosmosContainer(CosmosDatabase cosmosDatabase) {
    // Hierarchical partition key definition
    List<String> partitionKeyPaths = Arrays.asList(
        "/tenantId", "/type", "/projectId");

    CosmosContainerProperties props = new CosmosContainerProperties(
        containerName,
        partitionKeyPaths,
        PartitionKeyDefinitionVersion.V2,
        PartitionKind.MULTI_HASH);

    cosmosDatabase.createContainerIfNotExists(
        props,
        ThroughputProperties.createAutoscaledThroughput(4000));

    return cosmosDatabase.getContainer(containerName);
}
```

**Alternative: `SmartInitializingSingleton` for post-init logic:**

```java
// If you need to run logic AFTER all beans are created
@Bean
public SmartInitializingSingleton cosmosInitializer(CosmosContainer container) {
    return () -> {
        // Seed data, verify connectivity, warm up, etc.
        logger.info("Cosmos container ready: {}", container.getId());
    };
}
```

**Common mistake: Missing `createDatabaseIfNotExists()` before container creation:**

```java
// ❌ Crashes on a fresh Cosmos DB instance — database doesn't exist yet
@EventListener(ApplicationReadyEvent.class)
public void initializeCosmosDb() {
    CosmosAsyncClient client = cosmosAsyncClient();
    CosmosAsyncDatabase db = client.getDatabase(databaseName);
    db.createContainerIfNotExists(containerName,
        "/partitionKey").block();  // CosmosException: Database not found
}
```

```java
// ✅ Always create the database first
@EventListener(ApplicationReadyEvent.class)
public void initializeCosmosDb() {
    CosmosAsyncClient client = cosmosAsyncClient();
    client.createDatabaseIfNotExists(databaseName).block();  // ← required
    CosmosAsyncDatabase db = client.getDatabase(databaseName);
    db.createContainerIfNotExists(containerName,
        "/partitionKey").block();
}
```

**When extending `AbstractCosmosConfiguration`:**

```java
// ❌ cosmosClientBuilder() is not overridable — compile error
@Configuration
@EnableCosmosRepositories
public class CosmosDbConfig extends AbstractCosmosConfiguration {

    @Override  // ❌ "method does not override or implement a method from a supertype"
    public CosmosClientBuilder cosmosClientBuilder() {
        return new CosmosClientBuilder()
            .endpoint(endpoint)
            .key(key);
    }

    @Override
    protected String getDatabaseName() {
        return databaseName;
    }
}
```

```java
// ✅ Provide cosmosClientBuilder() as a @Bean, only override getDatabaseName()
@Configuration
@EnableCosmosRepositories
public class CosmosDbConfig extends AbstractCosmosConfiguration {

    @Bean  // ✅ Not an override — declare as a bean
    public CosmosClientBuilder cosmosClientBuilder() {
        return new CosmosClientBuilder()
            .endpoint(endpoint)
            .key(key)
            .consistencyLevel(ConsistencyLevel.SESSION)
            .contentResponseOnWriteEnabled(true);
    }

    @Override  // ✅ getDatabaseName() is the only overridable method
    protected String getDatabaseName() {
        return databaseName;
    }
}
```

**Key Points:**
- Never call `@Bean` methods from `@PostConstruct` in the same `@Configuration` class
- Use parameter injection in `@Bean` methods to express initialization order
- Always set `destroyMethod = "close"` on `CosmosClient` bean
- Keep `CosmosClient` as a singleton `@Bean` (Rule 4.16)
- Set `contentResponseOnWriteEnabled(true)` in the builder (Rule 4.9)
- Do not name your configuration class `CosmosConfig` — it collides with `com.azure.spring.data.cosmos.config.CosmosConfig`
- Always call `createDatabaseIfNotExists()` before `createContainerIfNotExists()`
- When extending `AbstractCosmosConfiguration`, use `@Bean` (not `@Override`) on `cosmosClientBuilder()`

**Global Jackson fallback for Cosmos system metadata:**

When entity classes miss `@JsonIgnoreProperties(ignoreUnknown = true)`, reads can fail with `UnrecognizedPropertyException` on Cosmos system fields (for example `_rid`, `_self`, `_etag`, `_ts`). Add a global fallback in Spring Boot:

```yaml
spring:
    jackson:
        deserialization:
            fail-on-unknown-properties: false
```

This is a defense-in-depth safety net and does not replace correct entity annotations.

References:
- [Spring Framework @Bean documentation](https://docs.spring.io/spring-framework/reference/core/beans/java/bean-annotation.html)
- [`CosmosAsyncClient.createDatabaseIfNotExists()` Javadoc](https://learn.microsoft.com/java/api/com.azure.cosmos.cosmosasyncclient?view=azure-java-stable)
- [`AbstractCosmosConfiguration` Javadoc](https://learn.microsoft.com/java/api/com.azure.spring.data.cosmos.config.abstractcosmosconfiguration?view=azure-java-stable)

### 1.16 Spring Boot and Java version compatibility for Cosmos DB SDK

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

### 1.17 Initialize Async Cosmos DB Container Before CosmosDBSaver

**Impact: HIGH** (prevents credential and event-loop errors in async applications)

## Initialize Async Cosmos DB Container Before CosmosDBSaver

**Impact: HIGH (prevents credential and event-loop errors in async applications)**

When using `CosmosDBSaver` with the async Cosmos DB SDK, the container client must be created within an active async context (e.g., inside an `async def` function). Creating it at module level causes event-loop errors because the async credential and client require a running loop. Always initialize the async client inside your application's startup routine and recompile the LangGraph graph afterward.

**Incorrect (module-level initialization — event loop not running):**

```python
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from langchain_azure_cosmosdb import CosmosDBSaver

# BAD: No event loop running at module import time
credential = AsyncDefaultAzureCredential()
client = AsyncCosmosClient(url, credential=credential)
container = client.get_database_client("db").get_container_client("Checkpoints")
checkpointer = CosmosDBSaver(container)  # May raise RuntimeError
```

**Incorrect (mixing sync credential with async client):**

```python
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.identity import DefaultAzureCredential  # sync credential

# BAD: Sync credential cannot be used with async CosmosClient
credential = DefaultAzureCredential()
client = AsyncCosmosClient(url, credential=credential)
```

**Correct (initialize in async startup function):**

```python
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from langchain_azure_cosmosdb import CosmosDBSaver
from langgraph.graph import StateGraph, MessagesState

builder = StateGraph(MessagesState)
# ... add nodes and edges ...
graph = builder.compile(checkpointer=None)  # initial compile without persistence

async def setup():
    """Call during application startup (e.g., FastAPI lifespan)."""
    global graph
    credential = AsyncDefaultAzureCredential()
    client = AsyncCosmosClient(cosmos_url, credential=credential)
    database = client.get_database_client("MyDatabase")
    container = database.get_container_client("Checkpoints")
    checkpointer = CosmosDBSaver(container)
    graph = builder.compile(checkpointer=checkpointer)
```

**Tip:** Keep a reference to the `AsyncCosmosClient` so you can close it gracefully on shutdown with `await client.close()`.

Reference: [Azure Cosmos DB async Python SDK](https://learn.microsoft.com/python/api/azure-cosmos/azure.cosmos.aio?view=azure-python)

### 1.18 Use CosmosDBSaver for LangGraph Checkpointing

**Impact: HIGH** (enables persistent multi-turn conversation state across restarts)

## Use CosmosDBSaver for LangGraph Checkpointing

**Impact: HIGH (enables persistent multi-turn conversation state across restarts)**

When building LangGraph agents that require multi-turn conversation persistence, use `CosmosDBSaver` from `langchain-azure-cosmosdb` as the checkpointer. This stores graph state in Cosmos DB, enabling conversations to survive process restarts and scale across multiple instances. The checkpointer requires an **async** container client — using a sync client will raise runtime errors.

**Incorrect (using in-memory checkpointer — state lost on restart):**

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState

builder = StateGraph(MessagesState)
# ... add nodes and edges ...

# BAD: State is lost when the process restarts
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

**Incorrect (passing a sync container client — will fail at runtime):**

```python
from azure.cosmos import CosmosClient
from langchain_azure_cosmosdb import CosmosDBSaver

# BAD: CosmosDBSaver requires an async container client
sync_client = CosmosClient(url, credential=credential)
sync_container = sync_client.get_database_client("db").get_container_client("Checkpoints")
checkpointer = CosmosDBSaver(sync_container)  # RuntimeError
```

**Correct (async container client with CosmosDBSaver):**

```python
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from langchain_azure_cosmosdb import CosmosDBSaver
from langgraph.graph import StateGraph, MessagesState

builder = StateGraph(MessagesState)
# ... add nodes and edges ...

# Compile initially without checkpointer (setup may be async)
graph = builder.compile(checkpointer=None)

async def initialize_checkpointer():
    credential = AsyncDefaultAzureCredential()
    client = AsyncCosmosClient(cosmos_url, credential=credential)
    database = client.get_database_client("MyDatabase")
    container = database.get_container_client("Checkpoints")
    checkpointer = CosmosDBSaver(container)
    # Recompile graph with persistent checkpointer
    return builder.compile(checkpointer=checkpointer)
```

Reference: [langchain-azure-cosmosdb documentation](https://python.langchain.com/docs/integrations/providers/azure_cosmos_db/)

### 1.19 Use AzureCosmosDBNoSQLChatMessageHistory for Persistent Conversations in JS/TS

**Impact: HIGH** (enables persistent multi-turn conversations that survive restarts and scale horizontally)

## Use AzureCosmosDBNoSQLChatMessageHistory for Persistent Conversations in JS/TS

**Impact: HIGH (enables persistent multi-turn conversations that survive restarts and scale horizontally)**

When building conversational AI applications with LangChain.js, use `AzureCosmosDBNoSQLChatMessageHistory` to persist chat messages in Cosmos DB. This ensures conversations survive process restarts, enables horizontal scaling across multiple instances, and provides a queryable audit trail. Each conversation session is stored as a document identified by a `sessionId`, with the partition key enabling efficient retrieval.

**Incorrect (in-memory history — lost on restart, no horizontal scaling):**

```typescript
import { ChatMessageHistory } from "langchain/memory";

// BAD: Messages lost when process restarts or user hits different instance
const history = new ChatMessageHistory();
await history.addUserMessage("Hello");
await history.addAIMessage("Hi there!");
// Process restarts... conversation is gone
```

**Incorrect (wrong partition key — cross-partition queries for session lookup):**

```typescript
import { AzureCosmosDBNoSQLChatMessageHistory } from "@langchain/azure-cosmosdb";

// BAD: If container partition key is /userId but you query by sessionId,
// lookups become cross-partition scans
const history = new AzureCosmosDBNoSQLChatMessageHistory({
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
  databaseName: "mydb",
  containerName: "chat-history", // partitioned by /userId
  sessionId: "session-123",     // queries will fan out across partitions
});
```

**Correct (persistent chat history with proper session isolation):**

```typescript
import { AzureCosmosDBNoSQLChatMessageHistory } from "@langchain/azure-cosmosdb";
import { DefaultAzureCredential } from "@azure/identity";
import { RunnableWithMessageHistory } from "@langchain/core/runnables";
import { ChatOpenAI } from "@langchain/openai";

const credential = new DefaultAzureCredential();

const model = new ChatOpenAI({
  azureOpenAIApiDeploymentName: "gpt-4o",
});

// Factory function creates history per session
function getMessageHistory(sessionId: string) {
  return new AzureCosmosDBNoSQLChatMessageHistory({
    endpoint: process.env.COSMOS_ENDPOINT,
    credential,
    databaseName: "mydb",
    containerName: "chat-history", // partition key should be /sessionId
    sessionId,
  });
}

// Wrap model with persistent history
const withHistory = new RunnableWithMessageHistory({
  runnable: model,
  getMessageHistory,
  inputMessagesKey: "input",
  historyMessagesKey: "history",
});

// Invoke with session tracking — messages persist across restarts
const response = await withHistory.invoke(
  { input: "What did we discuss earlier?" },
  { configurable: { sessionId: "user-123-session-456" } }
);
```

**Container design tips:**
- Use `/sessionId` as partition key for efficient single-session retrieval
- Enable TTL to auto-expire old conversations (e.g., 30 days)
- Use a composite index on `sessionId` + `_ts` if you query history by time range

Reference: [LangChain.js Azure Cosmos DB Chat History](https://js.langchain.com/docs/integrations/chat_memory/azure_cosmosdb_nosql/)

### 1.20 Configure Azure OpenAI Embedding Deployment Name for JS/TS LangChain

**Impact: MEDIUM** (incorrect deployment name causes 404 errors or uses wrong model)

## Configure Azure OpenAI Embedding Deployment Name for JS/TS LangChain

**Impact: MEDIUM (incorrect deployment name causes 404 errors or uses wrong model)**

When using `AzureOpenAIEmbeddings` with `@langchain/openai` in JavaScript/TypeScript, you must specify the Azure OpenAI **deployment name** (the name you chose when deploying the model in Azure AI Studio or via CLI) — not the bare model name. Azure OpenAI uses deployment names to route requests, and these can differ from the underlying model name. Passing a bare model name like `"text-embedding-3-small"` only works if your deployment happens to use that exact name.

**Incorrect (using bare model name or wrong property):**

```typescript
import { AzureOpenAIEmbeddings } from "@langchain/openai";

// BAD: "model" property is for OpenAI API, not Azure OpenAI
const embeddings = new AzureOpenAIEmbeddings({
  model: "text-embedding-3-small",  // Wrong property for Azure
});

// BAD: Using model name instead of deployment name
const embeddings2 = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small", // Only works if deployment has this exact name
  azureOpenAIApiVersion: "2024-06-01",
});

// BAD: Missing API version — will use an outdated default
const embeddings3 = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "my-embeddings",
});
```

**Correct (explicit deployment name and API version):**

```typescript
import { AzureOpenAIEmbeddings } from "@langchain/openai";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "my-embedding-deployment", // Your actual deployment name
  azureOpenAIApiVersion: "2024-06-01",
  // Endpoint and key from environment variables:
  // AZURE_OPENAI_API_INSTANCE_NAME or azureOpenAIApiInstanceName
  // AZURE_OPENAI_API_KEY or azureOpenAIApiKey (if not using managed identity)
});
```

**Correct (with managed identity — no API key needed):**

```typescript
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const credential = new DefaultAzureCredential();

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "my-embedding-deployment",
  azureOpenAIApiVersion: "2024-06-01",
  azureOpenAIApiInstanceName: "my-openai-resource", // just the resource name, not full URL
  credentials: credential,
});
```

**Tip:** Verify your deployment name with `az cognitiveservices account deployment list --name <resource> --resource-group <rg> --query "[].name"`.

Reference: [LangChain.js Azure OpenAI Embeddings](https://js.langchain.com/docs/integrations/text_embedding/azure_openai/)

### 1.21 Prevent Filter Injection in JS/TS LangChain Vector Store Queries

**Impact: CRITICAL** (prevents NoSQL injection attacks that can exfiltrate or corrupt data)

## Prevent Filter Injection in JS/TS LangChain Vector Store Queries

**Impact: CRITICAL (prevents NoSQL injection attacks that can exfiltrate or corrupt data)**

When passing filter clauses to `AzureCosmosDBNoSQLVectorStore` similarity searches, **never** concatenate user input directly into the filter string. Cosmos DB NoSQL queries support parameterized queries with `@param` placeholders — always use these to safely inject user-provided values. Concatenated filters allow attackers to manipulate query logic, bypass tenant isolation, or extract unauthorized data.

**Incorrect (string concatenation — SQL injection vulnerability):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

async function searchByCategory(store: AzureCosmosDBNoSQLVectorStore, userInput: string) {
  // CRITICAL VULNERABILITY: User can inject arbitrary SQL predicates
  // e.g., userInput = "electronics' OR c.secret != '"
  const results = await store.similaritySearch("find products", 10, {
    filter: `c.category = '${userInput}'`,
  });
  return results;
}

// Also BAD: Template literals are just string concatenation
async function searchByTenant(store: AzureCosmosDBNoSQLVectorStore, tenantId: string) {
  const results = await store.similaritySearch("query", 10, {
    filter: `c.tenantId = "${tenantId}"`,  // STILL INJECTABLE
  });
  return results;
}
```

**Correct (parameterized queries with @param placeholders):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

async function searchByCategory(store: AzureCosmosDBNoSQLVectorStore, userInput: string) {
  // SAFE: Parameters are escaped by the SDK — no injection possible
  const results = await store.similaritySearch("find products", 10, {
    filter: "c.category = @category",
    filterParams: [{ name: "@category", value: userInput }],
  });
  return results;
}

async function searchByTenant(store: AzureCosmosDBNoSQLVectorStore, tenantId: string) {
  // SAFE: Multi-tenant isolation with parameterized filter
  const results = await store.similaritySearch("query", 10, {
    filter: "c.tenantId = @tenantId AND c.isActive = true",
    filterParams: [{ name: "@tenantId", value: tenantId }],
  });
  return results;
}

// Multiple parameters
async function searchFiltered(
  store: AzureCosmosDBNoSQLVectorStore,
  category: string,
  minPrice: number
) {
  const results = await store.similaritySearch("query", 10, {
    filter: "c.category = @category AND c.price >= @minPrice",
    filterParams: [
      { name: "@category", value: category },
      { name: "@minPrice", value: minPrice },
    ],
  });
  return results;
}
```

**Why this matters:** In multi-tenant RAG applications, filter injection can bypass tenant isolation. An attacker providing `tenantA' OR '1'='1` as a tenant ID would access all tenants' data if the filter is concatenated.

Reference: [Azure Cosmos DB Parameterized Queries](https://learn.microsoft.com/azure/cosmos-db/nosql/query/parameterized-queries)

### 1.22 Configure Full-Text Prerequisites Before JS/TS LangChain Hybrid Search

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
  databaseName: "mydb",
  containerName: "docs",
});

// FAILS: "Full-text search is not enabled" or similar runtime error
const results = await store.similaritySearch("query", 10, {
  searchType: "Hybrid",
});
```

**Correct (container configured with full-text policy and indexes):**

First, configure the container (via ARM/Bicep/Terraform or CLI):

```json
{
  "containerProperties": {
    "id": "docs",
    "partitionKey": { "paths": ["/tenantId"], "kind": "Hash" },
    "fullTextPolicy": {
      "defaultLanguage": "en-US",
      "fullTextPaths": [
        { "path": "/content", "language": "en-US" },
        { "path": "/title", "language": "en-US" }
      ]
    },
    "indexingPolicy": {
      "includedPaths": [{ "path": "/*" }],
      "excludedPaths": [{ "path": "/embedding/*" }],
      "fullTextIndexes": [
        { "path": "/content" },
        { "path": "/title" }
      ],
      "vectorIndexes": [
        { "path": "/embedding", "type": "diskANN" }
      ]
    },
    "vectorEmbeddingPolicy": {
      "vectorEmbeddings": [
        {
          "path": "/embedding",
          "dataType": "float32",
          "distanceFunction": "cosine",
          "dimensions": 1536
        }
      ]
    }
  }
}
```

Then use hybrid search in your application:

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
});

const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential: new DefaultAzureCredential(),
  databaseName: "mydb",
  containerName: "docs",  // container has fullTextPolicy + fullTextIndexes
});

// Now hybrid search works — combines vector similarity with BM25 keyword matching
const results = await store.similaritySearch("specific keyword plus semantic meaning", 10, {
  searchType: "Hybrid",
});
```

**Checklist before enabling full-text/hybrid search:**
1. Account has full-text search capability enabled (`az cosmosdb update --capabilities EnableNoSQLFullTextSearch`)
2. Container has `fullTextPolicy` with paths and languages defined
3. Container indexing policy has `fullTextIndexes` for the same paths
4. Container has `vectorEmbeddingPolicy` and `vectorIndexes` (for hybrid)

Reference: [Azure Cosmos DB Full-Text Search](https://learn.microsoft.com/azure/cosmos-db/nosql/query/full-text-search)

### 1.23 Use Managed Identity for JS/TS LangChain Cosmos DB Integration

**Impact: CRITICAL** (zero-secret authentication eliminates credential leakage risk)

## Use Managed Identity for JS/TS LangChain Cosmos DB Integration

**Impact: CRITICAL (zero-secret authentication eliminates credential leakage risk)**

In production JavaScript/TypeScript applications using `@langchain/azure-cosmosdb`, always authenticate with `DefaultAzureCredential` from `@azure/identity` instead of connection strings. Connection strings contain master keys that grant full access — if leaked, they compromise the entire account. Managed identity provides automatic credential rotation and least-privilege access via RBAC roles.

**Incorrect (connection string in production):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
});

// BAD: Connection string contains master key — full account access if leaked
const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  connectionString: process.env.COSMOS_CONNECTION_STRING,
  databaseName: "mydb",
  containerName: "vectors",
});
```

**Correct (endpoint + DefaultAzureCredential):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
});

// GOOD: No secrets in code or config; works with system/user-assigned managed identity
const credential = new DefaultAzureCredential();
const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT, // e.g., "https://myaccount.documents.azure.com:443/"
  credential,
  databaseName: "mydb",
  containerName: "vectors",
});
```

**Required RBAC setup:** Assign the `Cosmos DB Built-in Data Contributor` role to your app's managed identity:

```bash
az cosmosdb sql role assignment create \
  --account-name myaccount \
  --resource-group myrg \
  --role-definition-id 00000000-0000-0000-0000-000000000002 \
  --principal-id <managed-identity-object-id> \
  --scope "/"
```

**Note:** When using RBAC, the database and container must be pre-created (via Bicep, Terraform, or CLI) — the SDK cannot create resources with data-plane-only permissions.

Reference: [Azure Cosmos DB RBAC with Azure Identity](https://learn.microsoft.com/azure/cosmos-db/nosql/security/how-to-grant-data-plane-role-based-access)

### 1.24 Choose the Correct Search Type for JS/TS LangChain Vector Store

**Impact: HIGH** (selecting wrong search type returns irrelevant results or causes errors)

## Choose the Correct Search Type for JS/TS LangChain Vector Store

**Impact: HIGH (selecting wrong search type returns irrelevant results or causes errors)**

The `@langchain/azure-cosmosdb` package supports multiple search types via `AzureCosmosDBNoSQLVectorStore`. Choose the appropriate type based on your retrieval needs. Using full-text or hybrid search requires pre-configured `fullTextPolicy` and `fullTextIndexes` on the container — otherwise queries will fail at runtime.

| Search Type | Use Case | Requires Full-Text Config |
|---|---|---|
| `Vector` | Pure semantic similarity (default) | No |
| `VectorScoreThreshold` | Semantic with minimum relevance cutoff | No |
| `FullTextSearch` | Keyword/BM25 matching only | Yes |
| `Hybrid` | Vector + full-text combined (RRF fusion) | Yes |
| `HybridScoreThreshold` | Hybrid with minimum score cutoff | Yes |

**Incorrect (using hybrid search without full-text configuration):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
  databaseName: "mydb",
  containerName: "vectors", // container has NO fullTextPolicy configured
});

// BAD: Will fail — container doesn't have full-text indexes
const results = await store.similaritySearch("query", 10, {
  searchType: "Hybrid",
});
```

**Correct (vector search — no special container config needed):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
  databaseName: "mydb",
  containerName: "vectors",
});

// Pure vector similarity search
const results = await store.similaritySearch("semantic query", 5);

// With score threshold — only return results above 0.7 similarity
const filtered = await store.similaritySearchWithScore("semantic query", 10, {
  searchType: "VectorScoreThreshold",
  scoreThreshold: 0.7,
});
```

**Correct (hybrid search — container has fullTextPolicy and fullTextIndexes):**

```typescript
// Container must have fullTextPolicy and fullTextIndexes configured FIRST
const results = await store.similaritySearch("keyword and semantic query", 10, {
  searchType: "Hybrid",
});
```

Reference: [LangChain.js Azure Cosmos DB NoSQL Vector Store](https://js.langchain.com/docs/integrations/vectorstores/azure_cosmosdb_nosql/)

### 1.25 Use AzureCosmosDBNoSQLSemanticCache for LLM Cost Reduction in JS/TS

**Impact: MEDIUM** (reduces LLM API costs and latency by caching semantically similar queries)

## Use AzureCosmosDBNoSQLSemanticCache for LLM Cost Reduction in JS/TS

**Impact: MEDIUM (reduces LLM API costs and latency by caching semantically similar queries)**

When building LLM-powered applications with LangChain.js, use `AzureCosmosDBNoSQLSemanticCache` to cache LLM responses in Cosmos DB. Unlike exact-match caches, semantic cache uses vector similarity to return cached responses for queries that are semantically similar (not just identical). This reduces LLM API costs for repeated or paraphrased queries and cuts response latency from seconds to milliseconds.

**Incorrect (no caching — every request hits the LLM):**

```typescript
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  azureOpenAIApiDeploymentName: "gpt-4o",
});

// BAD: Every call pays full LLM cost, even for repeated/similar questions
const response1 = await model.invoke("What is Azure Cosmos DB?");
const response2 = await model.invoke("Tell me about Azure Cosmos DB"); // Pays again
```

**Incorrect (exact-match cache misses paraphrased queries):**

```typescript
import { InMemoryCache } from "langchain/cache";

const model = new ChatOpenAI({
  azureOpenAIApiDeploymentName: "gpt-4o",
  cache: new InMemoryCache(), // Only matches exact string — misses paraphrases
});
```

**Correct (semantic cache with Cosmos DB):**

```typescript
import { AzureCosmosDBNoSQLSemanticCache } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings, ChatOpenAI } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const credential = new DefaultAzureCredential();

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
  azureOpenAIApiVersion: "2024-06-01",
});

const cache = new AzureCosmosDBNoSQLSemanticCache(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
  databaseName: "mydb",
  containerName: "semantic-cache",
  similarityScoreThreshold: 0.8, // Only return cache hits above 80% similarity
});

const model = new ChatOpenAI({
  azureOpenAIApiDeploymentName: "gpt-4o",
  cache, // Semantically similar queries return cached responses
});

// Second call with paraphrased question hits cache — no LLM API call
const response1 = await model.invoke("What is Azure Cosmos DB?");
const response2 = await model.invoke("Tell me about Azure Cosmos DB"); // Cache hit!
```

**Container requirements:** The cache container needs a vector embedding policy configured for the embedding dimension (e.g., 1536 for text-embedding-3-small). Use TTL on the container to auto-expire stale cache entries.

Reference: [LangChain.js Azure Cosmos DB Semantic Cache](https://js.langchain.com/docs/integrations/llm_caching/azure_cosmosdb_nosql/)

### 1.26 Correctly Initialize AzureCosmosDBNoSQLVectorStore in JavaScript/TypeScript

**Impact: HIGH** (prevents runtime connection failures and misconfigured vector stores)

## Correctly Initialize AzureCosmosDBNoSQLVectorStore in JavaScript/TypeScript

**Impact: HIGH (prevents runtime connection failures and misconfigured vector stores)**

When using `@langchain/azure-cosmosdb` in JavaScript/TypeScript, initialize `AzureCosmosDBNoSQLVectorStore` with either a connection string (development) or endpoint + `DefaultAzureCredential` (production). The target database and container must already exist when using RBAC/managed identity — the SDK will not auto-create them. Always pass the embedding model instance at construction time.

**Incorrect (missing embedding model, relying on auto-create with RBAC):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

// BAD: No embedding model provided — store cannot generate vectors
const store = new AzureCosmosDBNoSQLVectorStore({
  connectionString: process.env.COSMOS_CONNECTION_STRING,
  databaseName: "mydb",
  containerName: "vectors",
});

// BAD: With RBAC, database/container must pre-exist — SDK cannot create them
const store2 = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  databaseName: "nonexistent-db",
  containerName: "nonexistent-container",
});
```

**Correct (connection string for development):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
});

const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  connectionString: process.env.COSMOS_CONNECTION_STRING,
  databaseName: "mydb",
  containerName: "vectors",
});
```

**Correct (managed identity for production — database/container pre-created):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
});

const credential = new DefaultAzureCredential();
const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
  databaseName: "mydb",       // must already exist
  containerName: "vectors",   // must already exist with vector policy
});
```

Reference: [LangChain.js Azure Cosmos DB Integration](https://js.langchain.com/docs/integrations/vectorstores/azure_cosmosdb_nosql/)

### 1.27 Use Persistent MCP Client Sessions for Multi-Agent Applications

**Impact: HIGH** (prevents session initialization overhead and connection churn)

## Use Persistent MCP Client Sessions for Multi-Agent Applications

**Impact: HIGH (prevents session initialization overhead and connection churn)**

When using `MultiServerMCPClient` with LangGraph agents, avoid creating a new client instance per request. MCP sessions involve transport negotiation, tool discovery, and server handshakes. Creating a client per request adds latency and may exhaust server connection limits.

**Note:** The API changed significantly in `langchain-mcp-adapters >= 0.2.0`. The persistent session pattern (manual `__aenter__`/`__aexit__`) only applies to versions `< 0.2.0`. In `>= 0.2.0`, sessions are managed internally per call via `get_tools()`.

**Incorrect (new client per request — high overhead, applies to all versions):**

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

async def handle_request(user_input):
    # BAD: Creates a new client (and underlying sessions) for every single request
    client = MultiServerMCPClient({
        "my_server": {"transport": "streamable_http", "url": "http://localhost:8080/mcp"}
    })
    tools = await client.get_tools()
    # ... invoke agent ...
    # Client discarded, next request pays setup cost again
```

**Correct (>= 0.2.0 — single client instance, get_tools() manages sessions internally):**

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

_mcp_client: MultiServerMCPClient | None = None

async def setup_mcp():
    """Call once during application startup."""
    global _mcp_client
    _mcp_client = MultiServerMCPClient({
        "my_server": {
            "transport": "streamable_http",
            "url": f"{MCP_SERVER_BASE_URL}/mcp",
        }
    })
    # get_tools() creates a per-call session under the hood
    tools = await _mcp_client.get_tools()
    return tools

# No explicit cleanup needed — sessions are per-call in >= 0.2.0
```

**Correct (< 0.2.0 only — persistent session initialized once at startup):**

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

_mcp_client = None
_session_context = None
_persistent_session = None

async def setup_mcp():
    """Call once during application startup (< 0.2.0 API only)."""
    global _mcp_client, _session_context, _persistent_session

    _mcp_client = MultiServerMCPClient({
        "my_server": {"transport": "streamable_http", "url": mcp_server_url}
    })
    _session_context = _mcp_client.session("my_server")
    _persistent_session = await _session_context.__aenter__()

    # Load tools once — they remain valid for the session lifetime
    tools = await load_mcp_tools(_persistent_session)
    return tools

async def cleanup_mcp():
    """Call during application shutdown (< 0.2.0 API only)."""
    global _session_context, _persistent_session
    if _session_context and _persistent_session:
        await _session_context.__aexit__(None, None, None)
        _session_context = None
        _persistent_session = None
```

**Tip:** Wrap the session setup in retry logic with exponential backoff for production deployments where the MCP server may take time to become ready.

Reference: [langchain-mcp-adapters documentation](https://github.com/langchain-ai/langchain-mcp-adapters)

### 1.28 Handle MCP ToolMessage Content Format Variations

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

### 1.29 Filter MCP Tools by Name Prefix for Agent Assignment

**Impact: MEDIUM** (reduces agent confusion and improves routing accuracy)

## Filter MCP Tools by Name Prefix for Agent Assignment

**Impact: MEDIUM (reduces agent confusion and improves routing accuracy)**

When a single MCP server exposes tools for multiple domains, assign each LangGraph agent only the subset of tools it needs. Use a name-prefix convention on the server side (e.g., `get_transaction_history`, `get_offer_information`, `transfer_to_sales_agent`) and filter client-side by prefix. This prevents agents from calling tools outside their domain and reduces prompt confusion from irrelevant tool descriptions.

**Incorrect (all agents receive all tools):**

```python
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

all_tools = await load_mcp_tools(session)

# BAD: Every agent sees every tool — leads to wrong tool calls
support_agent = create_react_agent(model, all_tools, prompt=support_prompt)
sales_agent = create_react_agent(model, all_tools, prompt=sales_prompt)
transactions_agent = create_react_agent(model, all_tools, prompt=transactions_prompt)
```

**Correct (filter tools by prefix per agent):**

```python
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

all_tools = await load_mcp_tools(session)

def filter_tools_by_prefix(tools, prefixes):
    """Return only tools whose name starts with one of the given prefixes."""
    return [t for t in tools if any(t.name.startswith(p) for p in prefixes)]

# Each agent gets only the tools relevant to its domain
support_tools = filter_tools_by_prefix(all_tools, [
    "service_request", "get_branch_location", "transfer_to_"
])
sales_tools = filter_tools_by_prefix(all_tools, [
    "get_offer_information", "create_account", "calculate_monthly_payment", "transfer_to_"
])
transactions_tools = filter_tools_by_prefix(all_tools, [
    "bank_transfer", "get_transaction_history", "bank_balance", "transfer_to_"
])

support_agent = create_react_agent(model, support_tools, prompt=support_prompt)
sales_agent = create_react_agent(model, sales_tools, prompt=sales_prompt)
transactions_agent = create_react_agent(model, transactions_tools, prompt=transactions_prompt)
```

**Naming convention tip:** Include `transfer_to_` prefixed tools in each agent's set so agents can hand off conversations to other agents via the routing mechanism.

Reference: [LangGraph prebuilt agents](https://langchain-ai.github.io/langgraph/reference/prebuilt/)

### 1.30 Configure local development environment to avoid cloud connection conflicts

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

### 1.31 Explicitly reference Newtonsoft.Json package

**Impact: HIGH** (Prevents build failures and security vulnerabilities from missing or outdated Newtonsoft.Json dependency)

## Explicitly reference Newtonsoft.Json package

When creating any .NET project that references `Microsoft.Azure.Cosmos` (version 3.43.0 or later), your `.csproj` **MUST** include an explicit `PackageReference` for `Newtonsoft.Json` (version 13.0.3 or higher). Without this reference the project will not build. Add the reference at project-creation time — do not wait for a build error.

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

### 1.32 Use the Patch API for atomic counter increments

**Impact: HIGH** (eliminates read-modify-write for counters; reduces RU cost and eliminates concurrency conflicts)

## Use the Patch API for Atomic Counter Increments

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
    new PartitionKey(videoId),
    ops,
    Video.class
).block();
```

```java
// ✅ Patch multiple counters in one round-trip (e.g., rate-video: two fields)
CosmosPatchOperations ratingOps = CosmosPatchOperations.create()
    .increment("/ratingsCount", 1)
    .increment("/ratingsTotal", ratingValue);

videosContainer.patchItem(
    videoId, new PartitionKey(videoId), ratingOps, Video.class).block();
```

```java
// ✅ Async / reactive
CosmosPatchOperations ops = CosmosPatchOperations.create().increment("/views", 1);

return container.patchItem(videoId, new PartitionKey(videoId), ops, Video.class)
    .then();  // Mono<Void> — caller doesn't need the updated document
```

**Patch operations supported:**
- `incr(path, value)` — numeric increment (positive or negative)
- `set(path, value)` — set a field to a new value
- `add(path, value)` — add to an array or set a field
- `remove(path)` — remove a field
- `replace(path, value)` — replace an existing field (fails if absent)
- `move(from, to)` — rename a field

**Key Points:**
- `incr()` requires the field to already exist as a numeric type in the document; initialize it to `0` on document creation
- At most 10 patch operations per `patchItem` call
- Patch is idempotent for `set`/`replace` but **not** for `incr` — a retried increment will double-count. Use conditional patch (`setFilterPredicate`) or accept the retry risk for high-volume counters
- RU cost: ~1 write RU (same as a regular write), no read RU
- Prefer Patch over Stored Procedures for simple counter increments — Patch is natively supported without custom server-side code

Reference: [Partial document update (Patch API)](https://learn.microsoft.com/azure/cosmos-db/partial-document-update)

### 1.33 Configure Preferred Regions for Availability

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

### 1.34 Include aiohttp When Using Python Async SDK

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

### 1.35 Never share a single CosmosItemRequestOptions instance across multiple createItem calls

**Impact: HIGH** (causes wrong partition key to be sent, producing silent data corruption or 400/404 errors)

## Never Share a Single CosmosItemRequestOptions Instance Across Multiple createItem Calls

**Impact: HIGH (causes wrong partition key to be sent, producing silent data corruption or 400/404 errors)**

`CosmosItemRequestOptions` is a mutable object. The SDK may mutate the options object internally during request preparation (e.g., stamping the resolved partition key). Reusing the same instance across two `createItem` calls causes the second call to inherit state from the first, resulting in an incorrect partition key being sent to the service.

**Incorrect (shared mutable options — second call sends wrong partition key):**

```java
// ❌ Anti-pattern: one options instance reused for two different createItem calls
CosmosItemRequestOptions options = new CosmosItemRequestOptions()
    .setIfNoneMatchETag("*");

// First call: writes UserCredentials with PK = email
credentialsContainer.createItem(credentials, new PartitionKey(email), options).block();

// Second call: SDK re-uses the mutated options — may send PK = email (WRONG)
// instead of PK = userId, causing misrouted write or silent corruption
usersContainer.createItem(userProfile, new PartitionKey(userId), options).block();
```

**Correct (separate instance per call):**

```java
// ✅ Each createItem gets its own fresh options instance
CosmosItemRequestOptions credsOptions = new CosmosItemRequestOptions()
    .setIfNoneMatchETag("*");
CosmosItemRequestOptions userOptions = new CosmosItemRequestOptions()
    .setIfNoneMatchETag("*");

credentialsContainer
    .createItem(credentials, new PartitionKey(email), credsOptions).block();
usersContainer
    .createItem(userProfile, new PartitionKey(userId), userOptions).block();
```

```java
// ✅ Or construct inline to make sharing structurally impossible
credentialsContainer.createItem(
    credentials, new PartitionKey(email),
    new CosmosItemRequestOptions().setIfNoneMatchETag("*")).block();

usersContainer.createItem(
    userProfile, new PartitionKey(userId),
    new CosmosItemRequestOptions().setIfNoneMatchETag("*")).block();
```

**Key Points:**
- `CosmosItemRequestOptions` is **not thread-safe and not reuse-safe** across different requests
- The bug is especially insidious because: (a) the first call succeeds, (b) the second call may also succeed but route to the wrong partition, (c) the document appears at the wrong partition key value, breaking point reads
- The same rule applies to `CosmosQueryRequestOptions` and `CosmosPatchItemRequestOptions`
- Prefer inline construction (`new CosmosItemRequestOptions()...`) to make accidental sharing impossible by inspection

Reference: [Java SDK createItem](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-java-get-started)

### 1.36 Handle 429 Errors with Retry-After

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

### 1.37 Use consistent enum serialization between Cosmos SDK and application layer

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

## Python: Pydantic `mode="json"` for Cosmos DB Writes

The Python `azure-cosmos` SDK serializes request bodies with `json.dumps(data)` and **no custom encoder**. Pydantic v2's default `model_dump()` returns native Python objects (`datetime`, `UUID`, `Decimal`, etc.) that raise `TypeError: Object of type X is not JSON serializable` when passed to `create_item`, `upsert_item`, or `replace_item`.

Always pass `mode="json"` so Pydantic converts these to JSON-safe primitives first.

### Incorrect

```python
class ScoreDoc(BaseModel):
    id: str
    submitted_at: datetime = Field(alias="submittedAt")

# ❌ raises TypeError: Object of type datetime is not JSON serializable
await container.create_item(body=doc.model_dump(by_alias=True))
```

### Correct

```python
# ✅ datetime → ISO-8601 string, UUID → hex string, Decimal → string
await container.create_item(body=doc.model_dump(by_alias=True, mode="json"))
```

## Warning Signs

- Queries return empty results but you know matching documents exist
- Point reads work but filtered queries don't
- API returns different enum format than stored in Cosmos DB

### 1.38 Reuse CosmosClient as Singleton

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

**`CosmosClient` is synchronously disposable only (.NET).** `CosmosClient` implements `IDisposable`, **not** `IAsyncDisposable`. There is no `DisposeAsync()` method. Any wrapper or context type that holds a `CosmosClient` must implement `IDisposable` and call `Dispose()` — never `IAsyncDisposable` / `DisposeAsync()`.

**Incorrect (IAsyncDisposable — causes CS1061):**

```csharp
// WRONG: CosmosClient does not implement IAsyncDisposable
public sealed class CosmosDbContext : IAsyncDisposable
{
    private readonly CosmosClient _client;
    public CosmosDbContext(string connectionString)
        => _client = new CosmosClient(connectionString);
    // CS1061: 'CosmosClient' does not contain a definition for 'DisposeAsync'
    public ValueTask DisposeAsync() => _client.DisposeAsync();
}
```

**Correct (IDisposable):**

```csharp
// RIGHT: Use IDisposable — CosmosClient.Dispose() exists
public sealed class CosmosDbContext : IDisposable
{
    private readonly CosmosClient _client;
    public CosmosDbContext(string connectionString)
        => _client = new CosmosClient(connectionString);
    public void Dispose() => _client.Dispose();
}
```

```rust
// Rust (azure_data_cosmos): Singleton via Arc shared across async handlers
use azure_data_cosmos::{
    CosmosAccountEndpoint, CosmosAccountReference, CosmosClient, CosmosClientBuilder,
};
use azure_core::credentials::Secret;
use std::sync::Arc;

pub type SharedCosmos = Arc<CosmosClient>;

async fn create_singleton_client(endpoint: &str, key: &str) -> SharedCosmos {
    let endpoint: CosmosAccountEndpoint = endpoint.parse().expect("valid endpoint");
    let account = CosmosAccountReference::with_master_key(
        endpoint,
        Secret::from(key.to_string()),
    );
    let client = CosmosClientBuilder::new()
        .build(account)
        .await
        .expect("build client");
    Arc::new(client)
}

// Share the Arc<CosmosClient> via Axum state
#[tokio::main]
async fn main() {
    let cosmos = create_singleton_client("https://...", "key...").await;
    let app = axum::Router::new()
        .route("/orders", axum::routing::get(list_orders))
        .with_state(cosmos); // Single client reused by all handlers
    // ...
}

async fn list_orders(
    axum::extract::State(cosmos): axum::extract::State<SharedCosmos>,
) -> impl axum::response::IntoResponse {
    let container = cosmos.database_client("db").container_client("orders").await;
    // Use container...
    axum::http::StatusCode::OK
}
```

Reference: [CosmosClient best practices](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)

### 1.39 Annotate entities for Spring Data Cosmos with @Container, @PartitionKey, and String IDs

**Impact: CRITICAL** (prevents startup failures and data access errors in Spring Data Cosmos applications)

## Annotate Entities for Spring Data Cosmos

Spring Data Cosmos requires specific annotations on entity classes. JPA annotations (`@Entity`, `@Table`, `@Column`, `@JoinColumn`) are not recognized. Every entity must have `@Container`, a `String` ID with `@Id` and `@GeneratedValue`, and a `@PartitionKey` field.

**Incorrect (JPA annotations — not recognized by Cosmos):**

```java
import jakarta.persistence.*;

@Entity
@Table(name = "owners")
public class Owner {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "first_name")
    private String firstName;

    @OneToMany(cascade = CascadeType.ALL, mappedBy = "owner")
    private List<Pet> pets;
}
```

**Correct (Spring Data Cosmos annotations):**

```java
import com.azure.spring.data.cosmos.core.mapping.Container;
import com.azure.spring.data.cosmos.core.mapping.PartitionKey;
import com.azure.spring.data.cosmos.core.mapping.GeneratedValue;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import org.springframework.data.annotation.Id;

@JsonIgnoreProperties(ignoreUnknown = true)
@Container(containerName = "owners")
public class Owner {

    @Id
    @GeneratedValue
    private String id;

    @PartitionKey
    private String partitionKey;

    private String firstName;
    private List<String> petIds = new ArrayList<>(); // Store IDs, not entity references

    public Owner() {
        this.partitionKey = "owner"; // Set partition key in constructor
    }
}
```

Add `@JsonIgnoreProperties(ignoreUnknown = true)` to every Cosmos entity class so deserialization ignores Cosmos DB system metadata (`_rid`, `_self`, `_etag`, `_ts`, `_lsn`). This reinforces the serialization safety guidance from `model-json-serialization` at the point where entities are usually generated.

**Key annotation mappings:**

| JPA Annotation | Spring Data Cosmos Equivalent | Notes |
|----------------|-------------------------------|-------|
| `@Entity` | `@Container(containerName = "...")` | Container name should be plural |
| `@Table(name = "...")` | `@Container(containerName = "...")` | Same annotation handles both |
| `@Id` + `@GeneratedValue(strategy = ...)` | `@Id` + `@GeneratedValue` | Must use `org.springframework.data.annotation.Id` |
| `@Column` | *(remove)* | All fields are stored automatically |
| `@JoinColumn` | *(remove)* | No joins in document databases |
| `@OneToMany`, `@ManyToOne`, `@ManyToMany` | *(remove)* | Use embedded data or ID references |
| *(none)* | `@PartitionKey` | **Required** — must be added |

**Critical requirements:**

1. **IDs must be `String` type** — Cosmos DB uses string IDs natively. `Integer`/`Long` IDs cause type conversion failures:
   ```java
   // Wrong: Integer IDs don't work with CosmosRepository<Entity, String>
   private Integer id;

   // Correct: Always use String IDs
   @Id
   @GeneratedValue
   private String id;
   ```

2. **Every entity needs a `@PartitionKey`** — without it, queries cannot be routed efficiently:
   ```java
   @PartitionKey
   private String partitionKey;
   ```

3. **The container's partition key path must match the `@PartitionKey` field name** — when creating a container programmatically, the partition key path must be `/<fieldName>` where `fieldName` is the Java field annotated with `@PartitionKey`. A mismatch causes `IllegalArgumentException: partitionKey must not be null` or silent data routing errors at runtime:
   ```java
   // ❌ Wrong: container path "/id" doesn't match @PartitionKey field "playerId"
   @Container(containerName = "players")
   public class Player {
       @Id
       @GeneratedValue
       private String id;

       @PartitionKey
       private String playerId;
   }
   // Container created with: new CosmosContainerProperties("players", "/id")
   // Runtime error: IllegalArgumentException: partitionKey must not be null

   // ✅ Correct: container path matches @PartitionKey field name
   // Container created with: new CosmosContainerProperties("players", "/playerId")
   ```

4. **Remove ALL `jakarta.persistence.*` imports** — they cause compilation errors after removing JPA dependencies

5. **Remove relationship annotations** — `@OneToMany`, `@ManyToOne`, `@ManyToMany`, `@JoinColumn` have no Cosmos equivalent. Use ID references or embedded data instead (see `model-embed-related` and `model-relationship-references` rules).

Reference: [Spring Data Azure Cosmos DB annotations](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-java-spring-data)

### 1.40 Use CosmosRepository correctly and handle Iterable return types

**Impact: HIGH** (prevents ClassCastException and query failures in Spring Data Cosmos repositories)

## Use CosmosRepository Correctly

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
    List<PetType> findAllByOrderByName(); // Renamed, no pagination
}
```

**Critical: Iterable-to-List conversion**

Cosmos repositories return `Iterable`, not `List`. Direct casting causes `ClassCastException`:

```java
// WRONG — ClassCastException: BlockingIterable cannot be cast to java.util.List
default List<Entity> findAllSorted() {
    return (List<Entity>) this.findAll();
}

// CORRECT — Use StreamSupport to convert
import java.util.stream.StreamSupport;
import java.util.stream.Collectors;

default List<Entity> findAllSorted() {
    return StreamSupport.stream(this.findAll().spliterator(), false)
            .collect(Collectors.toList());
}
```

**Query method conversion patterns:**

| JPA Pattern | CosmosRepository Pattern | Notes |
|-------------|-------------------------|-------|
| `Page<E> findByX(String x, Pageable p)` | `List<E> findByX(String x)` | Remove pagination parameter |
| `findPetTypes()` | `findAllByOrderByName()` | Use Spring Data naming conventions |
| `@Query("SELECT p FROM Pet p WHERE ...")` | `@Query("SELECT * FROM c WHERE ...")` | Use Cosmos SQL syntax |
| `findById(Integer id)` | `findById(String id)` | IDs are always `String` |
| `extends JpaRepository<E, Integer>` | `extends CosmosRepository<E, String>` | Entity type + String ID |

**Custom query annotations:**

```java
// JPA JPQL — does not work with Cosmos
@Query("SELECT p FROM Pet p WHERE p.owner.id = :ownerId")
List<Pet> findByOwnerId(@Param("ownerId") Integer ownerId);

// Cosmos SQL — correct syntax
@Query("SELECT * FROM c WHERE c.ownerId = @ownerId")
List<Pet> findByOwnerId(@Param("ownerId") String ownerId);
```

**Method signature conflicts after ID type changes:**

When converting IDs from `Integer` to `String`, methods that previously had different signatures may conflict:

```java
// CONFLICT: Both methods now have same signature (String parameter)
Pet getPet(String name);    // by name
Pet getPet(String id);      // by ID — same signature!

// SOLUTION: Rename to be explicit
Pet getPetByName(String name);
Pet getPetById(String id);
```

**Update all callers** — controllers, tests, formatters, and other services must reference the renamed methods.

Reference: [Spring Data Azure Cosmos DB repository](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-java-spring-data#define-a-repository)

---

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
