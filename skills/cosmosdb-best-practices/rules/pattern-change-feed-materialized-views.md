---
title: Use Change Feed for cross-partition query optimization with materialized views
impact: HIGH
impactDescription: eliminates cross-partition query overhead for admin/analytics scenarios
tags: pattern, change-feed, materialized-views, cross-partition, query-optimization
---

## Use Change Feed for Materialized Views

When your application requires frequent cross-partition queries (e.g., admin dashboards, analytics), consider using Change Feed to maintain materialized views in a separate container optimized for those query patterns.

**Problem: Cross-partition queries are expensive**

```csharp
// This query fans out to ALL partitions - expensive at scale!
// Container partitioned by /customerId
var query = container.GetItemQueryIterator<Order>(
    "SELECT * FROM c WHERE c.status = 'Pending' ORDER BY c.createdAt DESC"
);
// With 100,000 customers = 100,000+ physical partitions queried
```

Cross-partition queries:
- Consume RUs from every partition (high cost)
- Have higher latency (parallel fan-out)
- Don't scale well as data grows

**Solution: Materialized view with Change Feed**

Create a second container optimized for your admin queries:

```
Container 1: "orders" (partitioned by /customerId)
├── Efficient for: customer order history, point reads
└── Pattern: Single-partition queries

Container 2: "orders-by-status" (partitioned by /status)  
├── Efficient for: admin status queries
├── Pattern: Single-partition queries within status
└── Populated by: Change Feed processor
```

**Implementation - .NET:**

```csharp
// Change Feed processor to sync materialized view
Container leaseContainer = database.GetContainer("leases");
Container ordersContainer = database.GetContainer("orders");
Container ordersByStatusContainer = database.GetContainer("orders-by-status");

ChangeFeedProcessor processor = ordersContainer
    .GetChangeFeedProcessorBuilder<Order>("statusViewProcessor", HandleChangesAsync)
    .WithInstanceName("instance-1")
    .WithLeaseContainer(leaseContainer)
    .WithStartFromBeginning()
    .Build();

async Task HandleChangesAsync(
    IReadOnlyCollection<Order> changes, 
    CancellationToken cancellationToken)
{
    foreach (Order order in changes)
    {
        // Create/update the materialized view document
        var statusView = new OrderStatusView
        {
            Id = order.Id,
            CustomerId = order.CustomerId,
            Status = order.Status,  // This becomes the partition key
            CreatedAt = order.CreatedAt,
            Total = order.Total
        };
        
        await ordersByStatusContainer.UpsertItemAsync(
            statusView,
            new PartitionKey(order.Status.ToString()),
            cancellationToken: cancellationToken
        );
    }
}

await processor.StartAsync();
```

**Implementation - Java:**

```java
// Change Feed processor with Spring Boot
@Component
public class OrderStatusViewProcessor {
    
    @Autowired
    private CosmosAsyncContainer ordersByStatusContainer;
    
    public void startProcessor(CosmosAsyncContainer ordersContainer, 
                               CosmosAsyncContainer leaseContainer) {
        
        ChangeFeedProcessor processor = new ChangeFeedProcessorBuilder<Order>()
            .hostName("processor-1")
            .feedContainer(ordersContainer)
            .leaseContainer(leaseContainer)
            .handleChanges(this::handleChanges)
            .buildChangeFeedProcessor();
            
        processor.start().block();
    }
    
    private void handleChanges(List<Order> changes, ChangeFeedProcessorContext context) {
        for (Order order : changes) {
            OrderStatusView view = new OrderStatusView(
                order.getId(),
                order.getCustomerId(), 
                order.getStatus(),
                order.getCreatedAt(),
                order.getTotal()
            );
            
            ordersByStatusContainer.upsertItem(
                view,
                new PartitionKey(order.getStatus().getValue()),
                new CosmosItemRequestOptions()
            ).block();
        }
    }
}
```

**Implementation - Python:**

```python
from azure.cosmos import CosmosClient
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
import asyncio

async def process_change_feed():
    """Process changes and update materialized view"""
    
    async with AsyncCosmosClient(endpoint, credential=key) as client:
        orders_container = client.get_database_client(db).get_container_client("orders")
        status_container = client.get_database_client(db).get_container_client("orders-by-status")
        
        # Read change feed
        async for changes in orders_container.query_items_change_feed():
            for order in changes:
                # Upsert to materialized view
                status_view = {
                    "id": order["id"],
                    "customerId": order["customerId"],
                    "status": order["status"],  # Partition key in target container
                    "createdAt": order["createdAt"],
                    "total": order["total"]
                }
                
                await status_container.upsert_item(
                    body=status_view,
                    partition_key=order["status"]
                )
```

**Query the materialized view (single-partition!):**

```csharp
// Now this is a single-partition query - fast and cheap!
var query = ordersByStatusContainer.GetItemQueryIterator<OrderStatusView>(
    new QueryDefinition("SELECT * FROM c WHERE c.status = @status ORDER BY c.createdAt DESC")
        .WithParameter("@status", "Pending"),
    requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey("Pending") }
);
```

**When to use this pattern:**

| Use Materialized Views When | Stick with Cross-Partition When |
|-----------------------------|---------------------------------|
| High-frequency admin queries | Rare/occasional admin queries |
| Large dataset (100K+ docs) | Small dataset (<10K docs) |
| Query latency is critical | Latency is acceptable |
| Consistent query patterns | Ad-hoc query patterns |

**Trade-offs:**

| Benefit | Cost |
|---------|------|
| Fast single-partition queries | Additional storage (duplicated data) |
| Predictable latency | Change Feed processor complexity |
| Better scalability | Eventual consistency (slight delay) |
| Lower RU cost per query | RU cost for writes to both containers |

**Key Points:**
- Change Feed provides reliable, ordered event stream of all document changes
- Materialized views trade storage cost for query efficiency
- Updates are eventually consistent (typically <1 second delay)
- Use lease container to track processor progress (enables resume after failures)
- Consider Azure Functions with Cosmos DB trigger for serverless implementation

Reference: [Change feed in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/change-feed)
