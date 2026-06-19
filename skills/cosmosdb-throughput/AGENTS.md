# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Best practices for Azure Cosmos DB throughput management: autoscale, right-sizing, serverless, burst capacity, and container vs database throughput allocation.

---

## Table of Contents

1. [Throughput & Scaling](#1-throughput-scaling) — **MEDIUM**
   - 1.1 [Use Autoscale for Variable Workloads](#11-use-autoscale-for-variable-workloads)
   - 1.2 [Understand Burst Capacity](#12-understand-burst-capacity)
   - 1.3 [Choose Container vs Database Throughput](#13-choose-container-vs-database-throughput)
   - 1.4 [Use Integrated Cache for Read-Heavy Workloads with Dedicated Gateway](#14-use-integrated-cache-for-read-heavy-workloads-with-dedicated-gateway)
   - 1.5 [Right-Size Provisioned Throughput](#15-right-size-provisioned-throughput)
   - 1.6 [Consider Serverless for Dev/Test](#16-consider-serverless-for-dev-test)

---

## 1. Throughput & Scaling

**Impact: MEDIUM**

### 1.1 Use Autoscale for Variable Workloads

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

```python
from azure.cosmos import PartitionKey, ThroughputProperties

# Incorrect: fixed throughput for variable workload
container = await database.create_container_if_not_exists(
    id="orders",
    partition_key=PartitionKey(path="/customerId"),
    offer_throughput=10000,  # Fixed 10,000 RU/s, not autoscale
)

# Correct: autoscale throughput for variable workload
container = await database.create_container_if_not_exists(
    id="orders-autoscale",
    partition_key=PartitionKey(path="/customerId"),
    offer_throughput=ThroughputProperties(
        auto_scale_max_throughput=10000,
    ),
)
# Scales automatically between 1,000-10,000 RU/s
```

```python
from azure.cosmos import ThroughputProperties

# Read current throughput settings
throughput = await container.get_throughput()
print(f"Manual throughput: {throughput.offer_throughput}")
print(f"Autoscale max: {throughput.auto_scale_max_throughput}")

# Update autoscale max throughput
await container.replace_throughput(
    ThroughputProperties(auto_scale_max_throughput=20000)
)
# Now scales between 2,000-20,000 RU/s
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

Reference: [Autoscale throughput](https://learn.microsoft.com/en-us/azure/cosmos-db/provision-throughput-autoscale)

### 1.2 Understand Burst Capacity

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

### 1.3 Choose Container vs Database Throughput

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

### 1.4 Use Integrated Cache for Read-Heavy Workloads with Dedicated Gateway

**Impact: MEDIUM** (Significant RU reduction for repeated point reads and queries — cache hits cost 0 RUs)

## Use Integrated Cache for Read-Heavy Workloads with Dedicated Gateway

**Impact: MEDIUM (significant RU reduction for repeated reads — cache hits cost 0 RUs)**

The Cosmos DB integrated cache (available via the dedicated gateway) caches point reads and query results in-memory at the gateway tier. For read-heavy workloads with repeated access to the same data, this can eliminate RU charges entirely for cache hits. Developers often connect through the public endpoint by default and miss out on this optimization entirely.

Use the integrated cache when:
- Your workload is read-heavy with high repetition (e.g., product catalogs, reference data, user profiles)
- You can tolerate slight staleness (eventual or session consistency)
- You want to reduce RU consumption without scaling up provisioned throughput

**Do not use the integrated cache when:**
- Your workload is write-heavy or reads are rarely repeated — cache hit rate will be too low to justify the cost
- You use Change Feed — it bypasses the cache entirely
- You require strong, bounded staleness, or consistent prefix consistency — these bypass the cache
- Note: The dedicated gateway is **separately billed** (hourly, per node) — factor this into your cost analysis before provisioning

**Limitations:**
- Only works with **session** or **eventual** consistency reads — consistent prefix, bounded staleness, and strong consistency bypass the cache entirely
- Requires a **dedicated gateway** to be provisioned and requests to be routed through the **dedicated gateway endpoint** using **Gateway connection mode** (not Direct mode)
- Each gateway node has an **independent cache** — sticky sessions are not guaranteed across nodes
- Cache staleness is controlled via `MaxIntegratedCacheStaleness` — tune this to your freshness requirements

---

**Incorrect (connecting via public endpoint — integrated cache bypassed):**

```csharp
// Using the standard public endpoint — integrated cache is NOT used
CosmosClient client = new CosmosClientBuilder("AccountEndpoint=https://<account>.documents.azure.com:443/;AccountKey=<key>;")
    .WithConsistencyLevel(ConsistencyLevel.Session)
    .Build();

Container container = client.GetContainer("mydb", "mycontainer");

// This point read hits the backend every time — full RU cost on each call
ItemResponse<Product> response = await container.ReadItemAsync<Product>(
    id: "product-123",
    partitionKey: new PartitionKey("electronics")
);
```

**Correct (connecting via dedicated gateway endpoint — integrated cache enabled):**

```csharp
// Use the dedicated gateway endpoint to enable the integrated cache
// Dedicated gateway endpoint format: https://<account>.sqlx.cosmos.azure.com:443/
CosmosClient client = new CosmosClientBuilder(
        "AccountEndpoint=https://<account>.sqlx.cosmos.azure.com:443/;AccountKey=<key>;")
    .WithConnectionModeGateway()   // Required: Direct mode bypasses the dedicated gateway and cache
    .WithConsistencyLevel(ConsistencyLevel.Session)
    .Build();

Container container = client.GetContainer("mydb", "mycontainer");

// Configure staleness tolerance — cache hits within this window cost 0 RUs
ItemRequestOptions options = new ItemRequestOptions
{
    DedicatedGatewayRequestOptions = new DedicatedGatewayRequestOptions
    {
        MaxIntegratedCacheStaleness = TimeSpan.FromMinutes(5)
    }
};

// First call: cache miss — fetches from backend (normal RU cost)
// Subsequent calls within staleness window: cache hit — 0 RUs charged
ItemResponse<Product> response = await container.ReadItemAsync<Product>(
    id: "product-123",
    partitionKey: new PartitionKey("electronics"),
    requestOptions: options
);
```

**Query caching example:**

```csharp
QueryRequestOptions queryOptions = new QueryRequestOptions
{
    DedicatedGatewayRequestOptions = new DedicatedGatewayRequestOptions
    {
        MaxIntegratedCacheStaleness = TimeSpan.FromMinutes(5)
    }
};

var query = new QueryDefinition("SELECT * FROM c WHERE c.category = @category")
    .WithParameter("@category", "electronics");

// Repeated queries with the same text and parameters benefit from cache hits
FeedIterator<Product> iterator = container.GetItemQueryIterator<Product>(
    query,
    requestOptions: queryOptions
);
```

Reference: [Azure Cosmos DB integrated cache](https://learn.microsoft.com/azure/cosmos-db/integrated-cache)

### 1.5 Right-Size Provisioned Throughput

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

### 1.6 Consider Serverless for Dev/Test

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

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
