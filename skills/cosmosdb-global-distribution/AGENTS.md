# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Best practices for Azure Cosmos DB global distribution: multi-region writes, consistency levels, conflict resolution, automatic failover, read regions, and zone redundancy.

---

## Table of Contents

1. [Global Distribution](#1-global-distribution) — **MEDIUM**
   - 1.1 [Implement Conflict Resolution](#11-implement-conflict-resolution)
   - 1.2 [Choose Appropriate Consistency Level](#12-choose-appropriate-consistency-level)
   - 1.3 [Configure Automatic Failover](#13-configure-automatic-failover)
   - 1.4 [Configure Multi-Region Writes](#14-configure-multi-region-writes)
   - 1.5 [Add Read Regions Near Users](#15-add-read-regions-near-users)
   - 1.6 [Configure Zone Redundancy for High Availability](#16-configure-zone-redundancy-for-high-availability)

---

## 1. Global Distribution

**Impact: MEDIUM**

### 1.1 Implement Conflict Resolution

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

### 1.2 Choose Appropriate Consistency Level

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

### 1.3 Configure Automatic Failover

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

### 1.4 Configure Multi-Region Writes

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

### 1.5 Add Read Regions Near Users

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

### 1.6 Configure Zone Redundancy for High Availability

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

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
