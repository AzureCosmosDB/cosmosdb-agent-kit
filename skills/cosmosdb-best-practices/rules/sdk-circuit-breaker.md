---
title: Configure Partition-Level Circuit Breaker
impact: HIGH
impactDescription: prevents cascading failures, improves write availability
tags: sdk, circuit-breaker, high-availability, resilience, partition, failover
---

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
