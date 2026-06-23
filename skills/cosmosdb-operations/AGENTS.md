# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Best practices for operating Azure Cosmos DB: throughput and scaling, global distribution and consistency, monitoring and diagnostics, and security hardening.

---

## Table of Contents

1. [Throughput & Scaling](#1-throughput-scaling) — **MEDIUM**
   - 1.1 [Use Autoscale for Variable Workloads](#11-use-autoscale-for-variable-workloads)
   - 1.2 [Understand Burst Capacity](#12-understand-burst-capacity)
   - 1.3 [Choose Container vs Database Throughput](#13-choose-container-vs-database-throughput)
   - 1.4 [Right-Size Provisioned Throughput](#14-right-size-provisioned-throughput)
   - 1.5 [Consider Serverless for Dev/Test](#15-consider-serverless-for-dev-test)
2. [Global Distribution](#2-global-distribution) — **MEDIUM**
   - 2.1 [Implement Conflict Resolution](#21-implement-conflict-resolution)
   - 2.2 [Choose Appropriate Consistency Level](#22-choose-appropriate-consistency-level)
   - 2.3 [Configure Automatic Failover](#23-configure-automatic-failover)
   - 2.4 [Configure Multi-Region Writes](#24-configure-multi-region-writes)
   - 2.5 [Add Read Regions Near Users](#25-add-read-regions-near-users)
   - 2.6 [Configure Zone Redundancy for High Availability](#26-configure-zone-redundancy-for-high-availability)
3. [Monitoring & Diagnostics](#3-monitoring-diagnostics) — **LOW-MEDIUM**
   - 3.1 [Integrate Azure Monitor](#31-integrate-azure-monitor)
   - 3.2 [Enable Diagnostic Logging](#32-enable-diagnostic-logging)
   - 3.3 [Monitor P99 Latency](#33-monitor-p99-latency)
   - 3.4 [Track RU Consumption](#34-track-ru-consumption)
   - 3.5 [Alert on Throttling (429s)](#35-alert-on-throttling-429s-)
4. [Security](#4-security) — **HIGH**
   - 4.1 [Enable Continuous Backup for Point-in-Time Restore](#41-enable-continuous-backup-for-point-in-time-restore)
   - 4.2 [Disable Local Authentication (Keys)](#42-disable-local-authentication-keys-)
   - 4.3 [Use Managed Identity with DefaultAzureCredential](#43-use-managed-identity-with-defaultazurecredential)
   - 4.4 [Restrict Network Access](#44-restrict-network-access)
   - 4.5 [Assign Minimum RBAC Roles with Narrow Scope](#45-assign-minimum-rbac-roles-with-narrow-scope)

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

### 1.4 Right-Size Provisioned Throughput

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

### 1.5 Consider Serverless for Dev/Test

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

## 2. Global Distribution

**Impact: MEDIUM**

### 2.1 Implement Conflict Resolution

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

### 2.2 Choose Appropriate Consistency Level

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

### 2.3 Configure Automatic Failover

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

### 2.4 Configure Multi-Region Writes

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

### 2.5 Add Read Regions Near Users

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

### 2.6 Configure Zone Redundancy for High Availability

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

## 3. Monitoring & Diagnostics

**Impact: LOW-MEDIUM**

### 3.1 Integrate Azure Monitor

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

### 3.2 Enable Diagnostic Logging

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

### 3.3 Monitor P99 Latency

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

### 3.4 Track RU Consumption

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

### Node.js / TypeScript (@azure/cosmos v4)

Every `@azure/cosmos` operation exposes `requestCharge` as a top-level numeric property on the response. Capture it on every call — point reads, queries, writes, and bulk operations.

**Incorrect (discarding requestCharge — no visibility into cost):**

```typescript
// ❌ requestCharge available but never captured
const { resource } = await container.item(orderId, userId).read();
return resource;
// Is this costing 1 RU or 100 RU? Unknown!
```

**Correct (capturing requestCharge on reads and writes):**

```typescript
import { Container, FeedResponse } from '@azure/cosmos';

// ✅ Point read — capture requestCharge
export async function getOrder(container: Container, id: string, userId: string) {
  const response = await container.item(id, userId).read();
  logger.debug({
    op: 'ReadItem',
    container: container.id,
    ru: response.requestCharge,
    statusCode: response.statusCode,
    activityId: response.activityId,
  }, 'cosmos.readItem');
  return response.resource;
}

// ✅ Write — create/upsert/replace/patch/delete all expose requestCharge
export async function createOrder(container: Container, order: Order) {
  const response = await container.items.create(order);
  logger.debug({ op: 'CreateItem', ru: response.requestCharge }, 'cosmos.createItem');
  return response.resource;
}
```

**Correct (accumulating RU across query pages — single-page tracking undercounts paged results):**

```typescript
// ✅ Query — sum requestCharge across all pages
export async function getCustomerOrders(container: Container, userId: string) {
  const iterator = container.items.query<OrderSummary>({
    query: 'SELECT c.id, c.userId, c.status, c.total, c.createdAt FROM c WHERE c.userId = @u ORDER BY c.createdAt DESC',
    parameters: [{ name: '@u', value: userId }],
  }, { partitionKey: userId });

  const results: OrderSummary[] = [];
  let totalRU = 0;

  while (iterator.hasMoreResults()) {
    const page: FeedResponse<OrderSummary> = await iterator.fetchNext();
    results.push(...page.resources);
    totalRU += page.requestCharge;
  }

  logger.info({ op: 'Query', container: container.id, count: results.length, totalRU }, 'cosmos.query.total');
  if (totalRU > 100) {
    logger.warn({ totalRU, count: results.length }, 'cosmos.query.expensive');
  }
  return results;
}
```

**`requestCharge` API surface in `@azure/cosmos` v4:**

| Operation | Response type | RU property |
|-----------|---------------|-------------|
| `container.item(id, pk).read()` | `ItemResponse<T>` | `response.requestCharge` |
| `container.items.create(doc)` | `ItemResponse<T>` | `response.requestCharge` |
| `container.items.upsert(doc)` | `ItemResponse<T>` | `response.requestCharge` |
| `container.item(id, pk).replace(doc)` | `ItemResponse<T>` | `response.requestCharge` |
| `container.item(id, pk).patch(ops)` | `ItemResponse<T>` | `response.requestCharge` |
| `container.item(id, pk).delete()` | `ItemResponse<T>` | `response.requestCharge` |
| `container.items.query(...).fetchAll()` | `FeedResponse<T>` | `response.requestCharge` |
| `container.items.query(...).fetchNext()` | `FeedResponse<T>` per page | sum across pages |
| `container.items.bulk(ops)` | `OperationResponse[]` | `op.requestCharge` per operation |

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

### 3.5 Alert on Throttling (429s)

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

## 4. Security

**Impact: HIGH**

### 4.1 Enable Continuous Backup for Point-in-Time Restore

**Impact: MEDIUM** (enables recovery from accidental data loss)

## Enable Continuous Backup for Point-in-Time Restore

**Impact: MEDIUM (enables recovery from accidental data loss)**

Data loss is more often caused by mistakes than by attackers. Enable continuous backup (7 or 30 days) to allow point-in-time restore. Enable it at account creation if possible — switching from periodic to continuous is supported but is a one-way change.

**Incorrect (relying on default periodic backup):**

```bash
# Default periodic backup:
# - 4 hour intervals between backups
# - Only 2 copies retained
# - Recovery requires a support ticket
# - Cannot restore to a specific point in time
# - Data written between backups can be lost permanently

az cosmosdb create \
  --name myaccount \
  --resource-group myrg
  # Default periodic backup — limited recovery options
```

**Correct (continuous backup enabled):**

```bash
# Enable at account creation (preferred)
az cosmosdb create \
  --name myaccount \
  --resource-group myrg \
  --backup-policy-type Continuous \
  --continuous-tier Continuous7Days

# Or upgrade an existing account (one-way change)
az cosmosdb update \
  --name myaccount \
  --resource-group myrg \
  --backup-policy-type Continuous \
  --continuous-tier Continuous7Days

# Tiers available:
# Continuous7Days  — 7-day retention, lower cost
# Continuous30Days — 30-day retention, for compliance-sensitive workloads
```

```bash
# Restore to a specific point in time (self-service, no support ticket)
az cosmosdb restore \
  --account-name myaccount \
  --resource-group myrg \
  --target-database-account-name myaccount-restored \
  --restore-timestamp "2026-05-29T10:00:00Z" \
  --location "East US"
```

Continuous backup protects against:
- Accidental deletion of containers or databases
- Buggy deployments that corrupt data
- Unintended bulk updates or deletes
- Ransomware or malicious data modification (when combined with audit logs to identify the point of compromise)

Reference: [Continuous backup with point-in-time restore in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/continuous-backup-restore-introduction)

### 4.2 Disable Local Authentication (Keys)

**Impact: CRITICAL** (eliminates credential leakage risk)

## Disable Local Authentication (Keys)

**Impact: CRITICAL (eliminates credential leakage risk)**

Disable local authentication (shared keys and connection strings) on your Cosmos DB account. Keys are bearer tokens — anyone who has one can read, modify, or delete all data. If a key leaks, the only option is to regenerate it and update every dependent system. Disabling keys forces all access through Entra ID, eliminating this entire class of risk.

**Incorrect (using connection string with keys):**

```csharp
// WRONG: Connection string contains a master key
// If this leaks via source control, logs, or config, all data is exposed
var connectionString = "AccountEndpoint=https://myaccount.documents.azure.com:443/;AccountKey=abc123...==;";
var client = new CosmosClient(connectionString);

// Risks:
// - Key in source control (even in .env files that get committed)
// - Key in CI/CD logs or screenshots
// - Key shared across teams with no audit trail
// - No way to attribute access to a specific identity
// - Rotation requires updating every system simultaneously
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
    tokenCredential: new DefaultAzureCredential()
);

// Benefits:
// - No secrets to leak
// - Access is auditable per identity
// - Revocation is instant and targeted
// - Works in dev (az login), Azure (managed identity), and CI/CD (service principal)
```

If you cannot disable keys immediately, at minimum: never store connection strings in source control, use Azure Key Vault for secret storage, and enable secret scanning in your repository.

Reference: [Disable local authentication in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/how-to-setup-rbac#disable-local-auth)

### 4.3 Use Managed Identity with DefaultAzureCredential

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

// WRONG: Connection string in environment variable still contains a secret
var connectionString = Environment.GetEnvironmentVariable("COSMOS_CONNECTION_STRING");
var client = new CosmosClient(connectionString);

// WRONG: Different auth code per environment
if (isDevelopment)
    client = new CosmosClient(connectionString);  // key-based
else
    client = new CosmosClient(endpoint, new ManagedIdentityCredential());  // identity
```

**Correct (DefaultAzureCredential everywhere):**

```csharp
using Azure.Identity;
using Microsoft.Azure.Cosmos;

// Same code works in all environments:
// - Local dev: uses az login / Visual Studio / VS Code credentials
// - Azure (App Service, Functions, Container Apps, AKS): uses managed identity
// - CI/CD: uses service principal or workload identity federation
var client = new CosmosClient(
    accountEndpoint: "https://myaccount.documents.azure.com:443/",
    tokenCredential: new DefaultAzureCredential()
);
```

```python
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient

credential = DefaultAzureCredential()
client = CosmosClient("https://myaccount.documents.azure.com:443/", credential)
```

```javascript
const { DefaultAzureCredential } = require("@azure/identity");
const { CosmosClient } = require("@azure/cosmos");

const credential = new DefaultAzureCredential();
const client = new CosmosClient({
    endpoint: "https://myaccount.documents.azure.com:443/",
    aadCredentials: credential
});
```

```java
import com.azure.identity.DefaultAzureCredentialBuilder;
import com.azure.cosmos.CosmosClientBuilder;

CosmosClient client = new CosmosClientBuilder()
    .endpoint("https://myaccount.documents.azure.com:443/")
    .credential(new DefaultAzureCredentialBuilder().build())
    .buildClient();
```

For Azure compute, assign a system-assigned managed identity:

```bash
# App Service
az webapp identity assign --name <your-app> --resource-group <your-rg>

# Azure Functions
az functionapp identity assign --name <your-app> --resource-group <your-rg>

# Container Apps
az containerapp identity assign --name <your-app> --resource-group <your-rg> --system-assigned
```

Starting with `DefaultAzureCredential` from day one avoids a painful migration later — moving from keys to managed identity means touching every deployment, every environment, and potentially every SDK call.

Reference: [DefaultAzureCredential Class](https://learn.microsoft.com/dotnet/api/azure.identity.defaultazurecredential)

### 4.4 Restrict Network Access

**Impact: HIGH** (reduces attack surface from public internet)

## Restrict Network Access

**Impact: HIGH (reduces attack surface from public internet)**

By default, a Cosmos DB endpoint is publicly reachable from anywhere on the internet. If a credential leaks, nothing stands between an attacker and your data. Restrict access to known IP ranges as a baseline, and plan to move to private endpoints for production workloads.

**Incorrect (unrestricted public access):**

```bash
# WRONG: Default configuration — account is accessible from any IP address worldwide
# No --ip-range-filter means open to the internet

az cosmosdb create \
  --name myaccount \
  --resource-group myrg
  # No network restrictions = reachable from anywhere
```

**Correct (restrict to known IPs as baseline):**

```bash
# Restrict access to known IP addresses (office, CI/CD egress, developer IPs)
az cosmosdb update \
  --name myaccount \
  --resource-group myrg \
  --ip-range-filter "203.0.113.10,198.51.100.0/24"

# For production: use private endpoints (no public internet exposure)
az cosmosdb update \
  --name myaccount \
  --resource-group myrg \
  --public-network-access DISABLED

# Create a private endpoint in your VNet
az network private-endpoint create \
  --name myaccount-pe \
  --resource-group myrg \
  --vnet-name myvnet \
  --subnet default \
  --private-connection-resource-id <cosmos-account-resource-id> \
  --group-id Sql \
  --connection-name myaccount-connection
```

Network restriction tiers (from minimum to most secure):
1. **IP allowlisting** (day one minimum): restrict to office, CI/CD, and developer IPs
2. **Service endpoints**: allow access from specific Azure VNet subnets
3. **Private endpoints** (production goal): no public exposure, traffic stays on Microsoft backbone

Even with Entra ID authentication, network restrictions add defense-in-depth — a compromised token is useless if the attacker cannot reach the endpoint.

Reference: [Configure IP firewall in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/how-to-configure-firewall)

### 4.5 Assign Minimum RBAC Roles with Narrow Scope

**Impact: HIGH** (limits blast radius of compromised identities)

## Assign Minimum RBAC Roles with Narrow Scope

**Impact: HIGH (limits blast radius of compromised identities)**

Grant each identity only the Cosmos DB data plane role it needs, scoped to the narrowest resource level possible. Avoid account-wide contributor access when an app only reads from a single container. Separate data plane access (read/write data) from control plane access (manage account settings).

**Incorrect (over-privileged access):**

```bash
# WRONG: Granting full Contributor at account scope to an app that only reads data
az cosmosdb sql role assignment create \
  --account-name myaccount \
  --resource-group myrg \
  --role-definition-id "00000000-0000-0000-0000-000000000002" \
  --principal-id <app-principal-id> \
  --scope "/"

# WRONG: Giving the app control plane access (can delete containers, change settings)
az role assignment create \
  --role "Contributor" \
  --assignee <app-principal-id> \
  --scope "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.DocumentDB/databaseAccounts/myaccount"

# WRONG: Sharing one identity across multiple services
# If one service is compromised, attacker gets access to everything
```

**Correct (least privilege, narrowly scoped):**

```bash
# Built-in data plane roles:
# Cosmos DB Built-in Data Reader:      00000000-0000-0000-0000-000000000001
# Cosmos DB Built-in Data Contributor: 00000000-0000-0000-0000-000000000002

# Read-only app: grant Reader scoped to specific container
az cosmosdb sql role assignment create \
  --account-name myaccount \
  --resource-group myrg \
  --role-definition-id "00000000-0000-0000-0000-000000000001" \
  --principal-id <reader-app-principal-id> \
  --scope "/dbs/mydb/colls/products"

# Read-write app: grant Contributor scoped to specific database
az cosmosdb sql role assignment create \
  --account-name myaccount \
  --resource-group myrg \
  --role-definition-id "00000000-0000-0000-0000-000000000002" \
  --principal-id <writer-app-principal-id> \
  --scope "/dbs/mydb"

# CI/CD pipeline: only data plane write for schema migrations
az cosmosdb sql role assignment create \
  --account-name myaccount \
  --resource-group myrg \
  --role-definition-id "00000000-0000-0000-0000-000000000002" \
  --principal-id <cicd-principal-id> \
  --scope "/dbs/mydb"
```

Guidelines for role assignment:
- **Application**: Data plane only, minimum role (Reader vs Contributor), scoped to its database or container
- **Developers**: Data plane access on dev accounts, scoped narrowly, using their own Entra ID identity
- **CI/CD pipeline**: Only permissions required to deploy — often just data plane write, sometimes control plane for container management
- **Each identity gets its own access** — never share a single credential across users, environments, or systems

Reference: [Use data plane role-based access control with Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/security/how-to-grant-data-plane-role-based-access)

---

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
