---
title: Unwrap CosmosItemResponse and enable content response in Java SDK
impact: MEDIUM
impactDescription: prevents type errors from missing getItem() on reads and null content on writes
tags: sdk, java, content-response, readItem, create, upsert, getItem
---

## Unwrap CosmosItemResponse and enable content response in Java SDK

All Java SDK operations (`readItem`, `createItem`, `upsertItem`, `replaceItem`) return `CosmosItemResponse<T>`, not `T` directly. Call `.getItem()` to extract the entity.

**Incorrect (treating response as entity):**

```java
// ❌ Compilation error — readItem returns CosmosItemResponse<Player>, not Player
Player player = container.readItem(playerId, new PartitionKey(playerId), Player.class);
```

**Correct (unwrap with getItem):**


```java
// ✅ Unwrap the response
CosmosItemResponse<Player> response = container.readItem(
    playerId, new PartitionKey(playerId), Player.class);
Player player = response.getItem();

// ✅ Async — map to extract entity
```

```java
// ❌ getItem() returns null without contentResponseOnWriteEnabled
CosmosItemResponse<Order> response = container.createItem(order);
response.getItem();  // null!

// ✅ Enable at client level
CosmosClient client = new CosmosClientBuilder()
```
