---
title: Review Idle Containers for Lifecycle Action
impact: MEDIUM
impactDescription: recovers provisioned or autoscale-floor capacity
tags: throughput, lifecycle, idle, ttl, decommission, cost
---

## Review Idle Containers for Lifecycle Action

A container with near-zero traffic still carries its provisioned throughput, or an autoscale floor (10% of the configured max) that is billed even while idle. Abandoned import staging, deprecated features, and one-off migrations commonly leave such containers behind. Before deleting anything, confirm retention, compliance, and recovery requirements; then decommission, archive, or apply TTL so unused data and capacity do not persist and bill indefinitely.

**Incorrect (leaving an abandoned container provisioned):**

```csharp
// Legacy import container kept after a migration; no application reads or writes it,
// yet it bills the 400 RU/s floor continuously.
await database.CreateContainerIfNotExistsAsync(
    new ContainerProperties("legacy-imports", "/tenantId"),
    throughput: 400);
```

**Correct (apply TTL and decommission after validation):**

```csharp
// Expire remaining data on a retention window instead of holding it forever.
var properties = await container.ReadContainerAsync();
properties.Resource.DefaultTimeToLive = 60 * 60 * 24 * 30; // retain 30 days
await container.ReplaceContainerAsync(properties.Resource);

// After owner approval and a validated backup/export:
// await container.DeleteContainerAsync();
```

Safety gates before removing an idle container:
1. Confirm the container is genuinely idle (no reads or writes over a representative window, not just low RU).
2. Get owner approval and check retention/compliance requirements.
3. Take and validate a backup or export.
4. Prefer TTL or archival first; delete only after monitoring confirms nothing depends on it.

This differs from `throughput-right-size`, which tunes an *active but oversized* container; here the container is effectively unused and the question is whether it should exist at all.

Reference: [Time to Live (TTL) in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/time-to-live)
