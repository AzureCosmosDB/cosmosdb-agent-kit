---
title: Use Point Reads for AI-Grounding and RAG Retrieval When ID Is Known
impact: HIGH
impactDescription: 1 RU point read vs ~2.5+ RU query per grounding fetch; reduces tool-call latency in LLM loops
tags: pattern, ai, grounding, rag, point-read, tool-call, llm, retrieval
---

## Use Point Reads for AI-Grounding and RAG Retrieval When ID Is Known

In AI-grounded workloads an LLM tool-use loop typically resolves a concrete entity id (e.g., `orderId`, `sessionId`, `documentId`) from the user turn or tool-call arguments, then fetches the full document from Cosmos DB to build the grounding context for the model. Because the id and partition key are both known at call time, a point read should always be used instead of a query.

**Incorrect (query when id and partition key are both available from the tool call):**

```typescript
// ❌ Generic query — id is already known from the user turn / tool call
export async function groundOrderContext(orderId: string, userId: string) {
  const { resources: orders } = await ordersContainer.items
    .query<Order>({
      query: "SELECT * FROM c WHERE c.orderId = @o",
      parameters: [{ name: "@o", value: orderId }],
    })
```

**Correct (point read for the primary document, partition-scoped projection for related items):**


```typescript
// ✅ Point read for the order (id + partition key both known from tool call)
export async function groundOrderContext(orderId: string, userId: string) {
  const orderResp = await ordersContainer.item(orderId, userId).read<Order>();
  const order = orderResp.resource;
  if (!order) return null;

  // ✅ Partition-key-scoped projection for related event list
```

```python
# ✅ Point read — 1 RU, no query engine overhead
def ground_order_context(order_id: str, user_id: str):
    order = orders_container.read_item(item=order_id, partition_key=user_id)
    return build_grounding_context(order)
```
