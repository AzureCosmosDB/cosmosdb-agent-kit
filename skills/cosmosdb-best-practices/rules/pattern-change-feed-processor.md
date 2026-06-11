---
title: Use Change Feed Processor for Event-Driven Workflows
impact: HIGH
impactDescription: enables scalable event processing with leases and checkpointing
tags: pattern, change-feed, processor, event-driven
---

## Use Change Feed Processor for Event-Driven Workflows

Use the change feed processor when an application must react to item changes at scale. The processor manages polling, leases, checkpointing, and partition distribution across worker instances so each change can be processed reliably.

**Incorrect (custom polling without leases or checkpoints):**

```csharp
while (true)
{
    FeedIterator<Order> iterator = container.GetItemQueryIterator<Order>(
        "SELECT * FROM c WHERE c.status = 'ReadyForProcessing'");

    while (iterator.HasMoreResults)
    {
        foreach (Order order in await iterator.ReadNextAsync())
        {
            await ProcessOrderAsync(order);
        }
    }
}
```

Custom polling can miss ordering guarantees, duplicate work across instances, waste request units, and make restart recovery difficult.

**Correct (use a change feed processor with a lease container):**

```csharp
Container monitoredContainer = client.GetContainer("sales", "orders");
Container leaseContainer = client.GetContainer("sales", "orderLeases");

ChangeFeedProcessor processor = monitoredContainer
    .GetChangeFeedProcessorBuilder<Order>(
        processorName: "order-events",
        onChangesDelegate: async (changes, cancellationToken) =>
        {
            foreach (Order order in changes)
            {
                await ProcessOrderAsync(order);
            }
        })
    .WithInstanceName(Environment.MachineName)
    .WithLeaseContainer(leaseContainer)
    .Build();

await processor.StartAsync();
```

Choose a start position deliberately: start from now for new event pipelines, or from the beginning when backfilling. Plan error handling for poison messages so a single failing item does not block the processor forever. Run multiple processor instances when throughput increases; leases let Azure Cosmos DB balance partition work across them.

Reference: [Change feed processor in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/change-feed-processor)

Reference: [Change feed design patterns in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/change-feed-design-patterns)
