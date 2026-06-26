---
title: Use current Go Cosmos DB SDK versions and explicit partition-key metadata
impact: HIGH
impactDescription: prevents cross-SDK partition-key metadata incompatibilities
tags: sdk, go, azcosmos, partition-key, interoperability, versioning
---

## Use current Go Cosmos DB SDK versions and explicit partition-key metadata

When creating Azure Cosmos DB containers from Go with `github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos`, avoid stale SDK pins such as `v1.0.0`. The primary fix is **upgrading the SDK**: `azcosmos v1.0.0` serializes a `Paths`-only `PartitionKeyDefinition` as `{"paths":["/h3Cell"]}` — omitting `kind` entirely — whereas `v1.3.0` serializes `{"kind":"Hash","paths":["/h3Cell"]}`.

**Incorrect (stale SDK pin — serializes without `kind`):**

```

```

**Correct (current SDK — serializes `kind:"Hash"`; explicit `Kind` is defensive best practice):**


```

```
