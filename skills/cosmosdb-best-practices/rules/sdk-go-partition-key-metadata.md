---
title: Use current Go Cosmos DB SDK versions and explicit partition-key metadata
impact: HIGH
impactDescription: prevents cross-SDK partition-key metadata incompatibilities
tags: sdk, go, azcosmos, partition-key, interoperability, versioning
---

## Use current Go Cosmos DB SDK versions and explicit partition-key metadata

When creating Azure Cosmos DB containers from Go with `github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos`, avoid stale SDK pins such as `v1.0.0`. The primary fix is **upgrading the SDK**: `azcosmos v1.0.0` serializes a `Paths`-only `PartitionKeyDefinition` as `{"paths":["/h3Cell"]}` — omitting `kind` entirely — whereas `v1.3.0` serializes `{"kind":"Hash","paths":["/h3Cell"]}`. A container created without `kind` will cause a `KeyError: 'kind'` when another SDK (e.g. Python `azure-cosmos`) later reads its partition-key metadata.

The tagged [v1.2.0 implementation](https://github.com/Azure/azure-sdk-for-go/blob/sdk/data/azcosmos/v1.2.0/sdk/data/azcosmos/partition_key_definition.go) already includes `Kind` and a `MarshalJSON` implementation that infers `Hash` for a single path. Version 1.3.0 below is a working example, not the minimum version that fixes this metadata issue. Prefer a current stable release; v1.2.0 is also a valid fix for the missing `kind` serialization.

Setting `Kind` explicitly in the struct is good defensive practice; the SDK upgrade alone fixes serialization for new container definitions. It does not rewrite metadata on an existing malformed container; verify the stored definition and recreate/migrate the container if needed. Note: `Version: 2` enables large partition keys (up to 2 KB) and is unrelated to this cross-SDK `kind` incompatibility — omit it unless your application specifically needs large keys.

**Note:** This failure reproduces reliably on the Cosmos DB vNext emulator. Real Azure Cosmos DB may inject a default `kind` server-side; however, writing complete partition-key metadata is correct regardless and avoids relying on server-side normalization.

**Incorrect (stale SDK pin — serializes without `kind`):**

```go.mod
require (
    github.com/Azure/azure-sdk-for-go/sdk/azcore v1.10.0
    github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos v1.0.0
)
```

```go
props := azcosmos.ContainerProperties{
    ID: "driver_state",
    PartitionKeyDefinition: azcosmos.PartitionKeyDefinition{
        Paths: []string{"/h3Cell"},
    },
}

_, err := db.CreateContainer(ctx, props, nil)
if err != nil {
    return err
}
```

**Correct (current SDK — serializes `kind:"Hash"`; explicit `Kind` is defensive best practice):**

```go.mod
require (
    github.com/Azure/azure-sdk-for-go/sdk/azcore v1.16.0
    github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos v1.3.0
)
```

```go
props := azcosmos.ContainerProperties{
    ID: "driver_state",
    PartitionKeyDefinition: azcosmos.PartitionKeyDefinition{
        Paths: []string{"/h3Cell"},
        Kind:  azcosmos.PartitionKeyKindHash,
    },
}

_, err := db.CreateContainer(ctx, props, nil)
if err != nil {
    return fmt.Errorf("create container: %w", err)
}

pk := azcosmos.NewPartitionKeyString(doc.H3Cell)
_, err = container.UpsertItem(ctx, pk, body, nil)
if err != nil {
    return fmt.Errorf("upsert %s: %w", doc.ID, err)
}
```

Use the same explicit partition key value for writes and partition-scoped queries. Only use `MultiHash` for true hierarchical partition keys.

References:
- [Azure Cosmos DB for NoSQL partitioning overview](https://learn.microsoft.com/azure/cosmos-db/partitioning-overview)
- [Azure Cosmos DB Go SDK (`azcosmos`) package docs](https://pkg.go.dev/github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos)
