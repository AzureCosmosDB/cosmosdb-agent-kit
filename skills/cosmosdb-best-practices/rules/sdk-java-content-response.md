---
title: Enable content response on write operations in Java SDK
impact: MEDIUM
impactDescription: ensures created/updated documents are returned from write operations
tags: sdk, java, content-response, create, upsert
---

## Enable Content Response on Write Operations (Java)

By default, the Java Cosmos DB SDK does **not** return the document content after create/upsert operations. The response contains only metadata (headers, diagnostics) but the `getItem()` method returns null. You must explicitly enable content response if you need the created document.

**Problem - createItem returns null:**

```java
// Default behavior - item is null!
CosmosItemResponse<Order> response = container.createItem(order);
Order createdOrder = response.getItem();  // ❌ Returns null!

// This also affects upsertItem
CosmosItemResponse<Order> response = container.upsertItem(order);
Order upsertedOrder = response.getItem();  // ❌ Returns null!
```

**Solution - Enable contentResponseOnWriteEnabled:**

```java
// Option 1: Set at client level (applies to all operations)
CosmosClient client = new CosmosClientBuilder()
    .endpoint(endpoint)
    .key(key)
    .contentResponseOnWriteEnabled(true)  // Enable for all writes
    .buildClient();

// Now createItem returns the document
CosmosItemResponse<Order> response = container.createItem(order);
Order createdOrder = response.getItem();  // ✅ Returns the created document
```

```java
// Option 2: Set per-request (more granular control)
CosmosItemRequestOptions options = new CosmosItemRequestOptions();
options.setContentResponseOnWriteEnabled(true);

CosmosItemResponse<Order> response = container.createItem(
    order, 
    new PartitionKey(order.getCustomerId()),
    options
);
Order createdOrder = response.getItem();  // ✅ Returns the created document
```

**Async client:**

```java
// With CosmosAsyncClient
CosmosAsyncClient asyncClient = new CosmosClientBuilder()
    .endpoint(endpoint)
    .key(key)
    .contentResponseOnWriteEnabled(true)
    .buildAsyncClient();

// Or per-request
CosmosItemRequestOptions options = new CosmosItemRequestOptions();
options.setContentResponseOnWriteEnabled(true);

container.createItem(order, new PartitionKey(customerId), options)
    .map(response -> response.getItem())  // ✅ Now has the document
    .subscribe(createdOrder -> {
        System.out.println("Created: " + createdOrder.getId());
    });
```

**Spring Data Cosmos:**

```java
// Spring Data Cosmos handles this automatically
// The repository methods return the saved entity

@Repository
public interface OrderRepository extends CosmosRepository<Order, String> {
    // save() returns the saved entity automatically
}

// Usage
Order savedOrder = orderRepository.save(newOrder);  // ✅ Returns saved document
```

**When NOT to enable content response:**

If you don't need the created document (fire-and-forget writes), leave it disabled to save bandwidth:

```java
// High-throughput ingestion - don't need response content
CosmosItemRequestOptions options = new CosmosItemRequestOptions();
options.setContentResponseOnWriteEnabled(false);  // Default, saves bandwidth

for (Order order : ordersToInsert) {
    container.createItem(order, new PartitionKey(order.getCustomerId()), options);
    // Just need to know it succeeded, don't need the document back
}
```

**RU cost consideration:**

Enabling content response does NOT increase RU cost - the document is already fetched server-side for the write operation. It only affects the response payload size over the network.

**Key Points:**
- Java SDK returns null by default for created/upserted items
- Enable `contentResponseOnWriteEnabled(true)` to get documents back
- Can be set at client level (all operations) or per-request
- Spring Data Cosmos handles this automatically
- Disable for high-throughput scenarios where response content is not needed

Reference: [Azure Cosmos DB Java SDK best practices](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-java)
