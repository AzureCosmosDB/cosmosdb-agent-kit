---
title: Avoid Multi-Region Writes Without an Active-Active Need
impact: MEDIUM
impactDescription: removes conflict-resolution complexity and replicated write cost
tags: global, multi-region, write, antipattern, conflict, cost
---

## Avoid Multi-Region Writes Without an Active-Active Need

Multi-region writes (multi-master) are valuable for true active-active write availability and RTO≈0, but they add conflict-resolution complexity and can increase replicated write cost. Enabling them where they provide no benefit is an antipattern: non-production accounts that copy a production template, accounts where the workload only ever writes to one region, or a single-region account with the flag enabled as a latent tripwire. In these cases, disabling multi-region writes removes complexity and surprise cost with no loss of capability.

**Incorrect (cloning production multi-write config into a dev account that writes to one region):**

```json
{
  "type": "Microsoft.DocumentDB/databaseAccounts",
  "name": "orders-dev",
  "properties": {
    "enableMultipleWriteLocations": true,
    "locations": [
      { "locationName": "West US 2", "failoverPriority": 0 },
      { "locationName": "East US", "failoverPriority": 1 }
    ]
  }
}
```

**Correct (single write region unless the workload truly needs active-active writes):**

```json
{
  "type": "Microsoft.DocumentDB/databaseAccounts",
  "name": "orders-dev",
  "properties": {
    "enableMultipleWriteLocations": false,
    "locations": [
      { "locationName": "West US 2", "failoverPriority": 0 }
    ]
  }
}
```

When multi-region writes ARE justified (keep them enabled):
- The application genuinely writes from multiple regions concurrently and needs local write latency.
- You require write availability during a regional outage (RTO≈0) and have a conflict-resolution policy.

If you enable multi-region writes for those reasons, pair them with a deliberate conflict-resolution strategy (see `global-conflict-resolution`). For the legitimate active-active pattern, see `global-multi-region`.

Reference: [Configure multi-region writes](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-multi-master)
