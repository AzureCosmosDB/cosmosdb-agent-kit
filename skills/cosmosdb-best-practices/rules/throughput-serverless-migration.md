---
title: Choose the Correct Serverless and Provisioned Migration Path
impact: MEDIUM
impactDescription: align capacity mode, cost, and scale with the workload
tags: throughput, serverless, provisioned, migration, cost, irreversible
---

## Choose the Correct Serverless and Provisioned Migration Path

Choose migration direction from measured RU usage, required features, and cost.

- **Provisioned → serverless:** use this for intermittent traffic, long idle periods, or low average-to-peak utilization (for example, under 10%), if single-region is acceptable and shared database throughput is not required. This is **not** in-place: create a new serverless account and migrate data.
- **Serverless → provisioned:** use this when traffic becomes sustained or predictable, provisioned pricing is better, a physical partition needs more than 5,000 RU/s, or you need provisioned-only features (for example, multiple regions or shared database throughput). For Azure Cosmos DB for NoSQL, this direction is **in-place**.

Do not decide from a single spike. Review representative Azure Monitor **Request Units consumed** data, partition-level distribution, required regions, and monthly cost.

**Incorrect (leaving a low-traffic workload on always-on provisioned throughput):**

```csharp
// Provisioned account pays the 400 RU/s floor continuously even though the workload
// is idle most of the day and never approaches that throughput.
await database.CreateContainerIfNotExistsAsync(
    new ContainerProperties("events", "/tenantId"),
    throughput: 400);
```

**Correct (create a new serverless account, then migrate data into it):**

```json
// Serverless is an account-level capability set at creation (single region).
{
  "type": "Microsoft.DocumentDB/databaseAccounts",
  "apiVersion": "2021-10-15",
  "name": "events-serverless",
  "properties": {
    "databaseAccountOfferType": "Standard",
    "capabilities": [ { "name": "EnableServerless" } ],
    "locations": [ { "locationName": "West US 2", "failoverPriority": 0 } ]
  }
}
```

```csharp
// Then copy data into the new account (change feed or bulk), cut over reads/writes,
// and retire the old account. Container creation in serverless takes no throughput:
await database.CreateContainerIfNotExistsAsync(
    new ContainerProperties("events", "/tenantId"));
```

Verify these feasibility gates BEFORE migrating:
- Single region only (serverless does not support multi-region distribution).
- No database-level (shared) throughput — serverless is per-container consumption.
- Demand on each physical partition does not exceed 5,000 RU/s.
- A supported API and account configuration.

**Incorrect (trying to migrate a serverless account by assigning throughput to a container):**

```csharp
// Adding throughput does not convert a serverless container or account.
// A throughput value on container creation in a serverless account is rejected.
await database.CreateContainerAsync(
    new ContainerProperties("orders", "/customerId"),
    throughput: 10000);
```

**Correct (change the existing NoSQL account's capacity mode):**

```text
Azure portal > Azure Cosmos DB for NoSQL account > Overview
  > Change capacity mode to provisioned throughput
  > Review changes and initial throughput > Confirm
  > Wait until the account state is no longer Updating
  > Optionally change each container from manual throughput to autoscale
```

Before confirming a serverless → provisioned migration:

- Estimate initial cost for **every** container. Migration converts each container to manual throughput using `RU/s = number of physical partitions × 5,000`.
- Plan a temporary management freeze. Account management operations are blocked during migration, and there is no migration-duration SLA.
- Treat this as irreversible in-place. You cannot switch that account back to serverless in-place; returning to serverless requires a new account plus data migration.
- After migration, right-size manual throughput or move containers to autoscale. Add provisioned-only settings (for example, extra regions) after the migration completes.

For choosing serverless on a new (greenfield) project, see `throughput-serverless`.

References:
- [Serverless in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/serverless)
- [Change from serverless to provisioned throughput](https://learn.microsoft.com/azure/cosmos-db/how-to-change-capacity-mode)
