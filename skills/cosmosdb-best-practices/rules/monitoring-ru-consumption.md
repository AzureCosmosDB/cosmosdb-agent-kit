---
title: Track RU Consumption
impact: MEDIUM
impactDescription: enables cost optimization
tags: monitoring, ru, metrics, cost
---

## Track RU Consumption

Monitor Request Unit (RU) consumption to identify inefficient operations. Every response exposes `RequestCharge` — capture it.

**Incorrect (ignoring RU — no cost visibility):**

```csharp
// ❌ No visibility into whether this costs 1 RU or 100 RU
var result = await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
return result.Resource;
```

**Correct (tracking RU per operation):**


```csharp
var response = await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
_logger.LogDebug("ReadItem {Id}: {RU} RU", orderId, response.RequestCharge);

// For queries — sum across pages, alert on expensive ones
double totalRU = 0;
while (iterator.HasMoreResults)
```

```typescript
// Node.js — requestCharge on every response
const response = await container.item(id, userId).read();
logger.debug({ op: 'ReadItem', ru: response.requestCharge });

// Query — sum across pages
let totalRU = 0;
```
