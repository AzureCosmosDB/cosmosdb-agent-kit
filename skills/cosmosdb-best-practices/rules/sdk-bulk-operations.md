---
title: Use Bulk Operations for High-Volume Ingestion
impact: HIGH
impactDescription: improves throughput for large write workloads
tags: sdk, bulk, ingestion, throughput
---

## Use Bulk Operations for High-Volume Ingestion

Use SDK bulk support when inserting, updating, or deleting hundreds or thousands of items. Bulk execution lets the SDK group work, manage parallelism, and use provisioned throughput more efficiently than a long series of independent point writes.

**Incorrect (serial writes for a large import):**

```csharp
foreach (Product item in productsToImport)
{
    await container.CreateItemAsync(item, new PartitionKey(item.CategoryId));
}
```

Serial writes underuse available throughput and add round-trip latency to every item. They also make retry handling harder when a large import hits throttling.

**Correct (enable SDK bulk support for large writes):**

```csharp
var client = new CosmosClient(
    connectionString,
    new CosmosClientOptions
    {
        AllowBulkExecution = true
    });

var container = client.GetContainer("catalog", "products");

IEnumerable<Task> tasks = productsToImport.Select(item =>
    container.CreateItemAsync(item, new PartitionKey(item.CategoryId)));

await Task.WhenAll(tasks);
```

Use bulk support for backfills, migrations, high-volume ingestion, and batch updates where throughput matters more than the latency of a single item. Avoid bulk execution for small batches, latency-sensitive reads, or request paths where each item must return independently to a user action.

Reference: [Bulk import data to Azure Cosmos DB for NoSQL](https://learn.microsoft.com/azure/cosmos-db/nosql/tutorial-dotnet-bulk-import)

Reference: [Use bulk support in the Azure Cosmos DB .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet#use-bulk-support)
