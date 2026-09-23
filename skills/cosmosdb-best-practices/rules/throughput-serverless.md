---
title: Use Serverless for New, Bursty, and Dev/Test Workloads
impact: MEDIUM
impactDescription: pay-per-request pricing
tags: throughput, serverless, development, bursty, cost
---

## Use Serverless for New, Bursty, and Dev/Test Workloads

Use serverless for new workloads with unknown demand and for bursty or low-baseline traffic. Serverless bills per RU consumed, with no always-on throughput floor.

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

**Correct (serverless for new, bursty, and low-baseline traffic):**

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
- New application development and testing
- Unknown or hard-to-forecast traffic patterns
- Proofs of concept and prototypes
- Low sustained demand (below 5,000 RU/s per physical partition)
- Sporadic workloads with long idle periods
- Variable traffic with a low baseline

When NOT to use serverless:
- Sustained high-throughput production workloads
- Workloads that need more than 5,000 RU/s per physical partition
- Multi-region deployments (serverless is single-region)
- Workloads that require guaranteed pre-provisioned throughput

```csharp
// Serverless limitations to be aware of
// - Maximum 5,000 RU/s per partition; container throughput grows with storage
// - Single region only
// - No dedicated gateway
// - No analytical store (Synapse Link)

// Cost comparison:
// - Use current Azure pricing tools for your region and currency
// - Compare against your actual RU telemetry, not peak RU/s alone
// - Re-check around ~90M RU/month for the 400 RU/s provisioned baseline
```

Reference: [Serverless in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/serverless)
