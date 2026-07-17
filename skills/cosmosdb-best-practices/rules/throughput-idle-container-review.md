---
title: Review Idle Containers for Lifecycle Action
impact: MEDIUM
impactDescription: recovers provisioned or autoscale-floor capacity
tags: throughput, lifecycle, idle, ttl, decommission, cost
---

## Review Idle Containers for Lifecycle Action

A container with near-zero traffic still bills for throughput: **manual** provisioning bills its full RU/s 24/7, and **autoscale** bills each hour for the highest RU/s it scaled to that hour (between 10% and 100% of the configured max) — so an idle autoscale container still bills the 10% minimum. Abandoned import staging, deprecated features, and one-off migrations commonly leave such containers behind. The lever that recovers that cost is **decommissioning the container** (or dropping it to the minimum RU/s if it must stay) — note that **TTL and archival reduce stored *data*, not the provisioned RU/s bill**. Before removing anything, confirm retention, compliance, and recovery requirements.

**Incorrect (leaving an abandoned container provisioned):**

```csharp
// Legacy import container kept after a migration; no application reads or writes it,
// yet it bills the 400 RU/s floor continuously.
await database.CreateContainerIfNotExistsAsync(
    new ContainerProperties("legacy-imports", "/tenantId"),
    throughput: 400);
```

**Correct (decommission to recover cost; TTL only handles data retention):**

```csharp
// NOTE: TTL only expires data — it does NOT reduce the provisioned/autoscale RU bill.
// Recovering the throughput cost requires decommissioning the container (or, if it must
// stay, dropping it to the minimum RU/s).

// 1. Optional retention: expire remaining data instead of holding it forever.
var properties = await container.ReadContainerAsync();
properties.Resource.DefaultTimeToLive = 60 * 60 * 24 * 30; // retain 30 days
await container.ReplaceContainerAsync(properties.Resource);

// 2. After owner approval and a validated backup/export, delete it to stop paying:
// await container.DeleteContainerAsync();
```

Safety gates before removing an idle container:
1. Confirm the container is genuinely idle (no reads or writes over a representative window, not just low RU).
2. Get owner approval and check retention/compliance requirements.
3. Take and validate a backup or export.
4. TTL/archival control *data retention*, not throughput cost — to stop paying, delete the container (or lower its RU/s). Delete only after monitoring confirms nothing depends on it.

This differs from `throughput-right-size`, which tunes an *active but oversized* container; here the container is effectively unused and the question is whether it should exist at all.

References:
- [Time to Live (TTL) in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/time-to-live)
- [Provisioned throughput with autoscale (billing model)](https://learn.microsoft.com/azure/cosmos-db/provision-throughput-autoscale)
