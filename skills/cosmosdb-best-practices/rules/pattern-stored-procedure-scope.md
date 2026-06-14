---
title: Use stored procedures only for multi-document atomic operations within a single partition
impact: MEDIUM
impactDescription: avoids server-side JavaScript that is slow to execute, hard to debug, and capped at 5 seconds
tags: pattern, stored-procedures, transactional-batch, atomicity, single-partition
---

## Use Stored Procedures Only for Multi-Document Atomic Operations Within a Single Partition

Stored procedures run JavaScript inside the database engine and are scoped to a single logical partition. Their one real strength is transactional execution: all operations in a stored procedure either commit together or roll back together. They are not a general server-side compute layer, and using them that way produces logic that is hard to test, hard to debug, and subject to strict execution limits.

Reach for a stored procedure only when you need ACID guarantees across multiple items in the same partition and transactional batch cannot express the operation, for example when a write depends on data read inside the transaction, or when you exceed the batch limits of 100 operations or 2 MB per request.

**Limitations to be aware of:**

- Bounded execution of roughly 5 seconds; long-running scripts must implement continuation logic or they are rolled back
- Scoped to one logical partition; a stored procedure can never read or write items across partitions
- JavaScript only, with no breakpoints, no SDK-level diagnostics, and weak logging, so failures are hard to investigate
- Script source lives in the database rather than your codebase, which complicates versioning, code review, and deployment

**Incorrect (stored procedure for single-item CRUD):**

```csharp
// A script invocation, serialization, and JS execution just to create one document
var scripts = container.Scripts;
await scripts.ExecuteStoredProcedureAsync<Order>(
    "createOrder",
    new PartitionKey(order.CustomerId),
    new dynamic[] { order });
```

**Correct (plain SDK call):**

```csharp
// One point write, fully typed, retriable, and easy to debug
await container.CreateItemAsync(order, new PartitionKey(order.CustomerId));
```

**Incorrect (heavy computation or cross-partition logic in a script):**

```javascript
// Aggregating "all" orders server-side: only sees one partition,
// and hits the bounded execution limit as data grows
function monthlyRevenue() {
    var collection = getContext().getCollection();
    collection.queryDocuments(collection.getSelfLink(),
        "SELECT * FROM c WHERE c.type = 'order'",
        function (err, docs) {
            var total = 0;
            for (var i = 0; i < docs.length; i++) {
                total += docs[i].amount; // unbounded loop inside the engine
            }
            getContext().getResponse().setBody(total);
        });
}
```

**Correct (transactional batch for multi-item atomicity in one partition):**

```csharp
// Atomic create + update + audit entry, same partition key, no server-side code
var batch = container.CreateTransactionalBatch(new PartitionKey(order.CustomerId))
    .CreateItem(order)
    .ReplaceItem(customer.Id, customer)
    .CreateItem(auditEntry);

var response = await batch.ExecuteAsync();
if (!response.IsSuccessStatusCode)
{
    // The whole batch rolled back; inspect per-operation status codes
}
```

Aggregations and other computation belong in your application code, in queries using `SUM`/`COUNT`/`GROUP BY`, or in materialized views maintained through the change feed.

**When a stored procedure is still the right tool:**

```javascript
// Conditional read-modify-write across two items that must commit atomically:
// debit one account item and credit another, but only if the balance allows it.
// Transactional batch cannot make a write depend on a read inside the transaction.
function transfer(fromId, toId, amount) {
    var collection = getContext().getCollection();
    collection.readDocument(documentLink(fromId), function (err, from) {
        if (err) throw err;
        if (from.balance < amount) throw new Error("Insufficient funds");
        from.balance -= amount;
        collection.replaceDocument(from._self, from, function (err) {
            if (err) throw err; // any failure rolls back the whole transfer
            // ...read and credit the destination account next
        });
    });
}
```

Both account items must share the same partition key for this to work.

**Key points:**

- Default to SDK-side logic; use transactional batch for multi-item atomic writes within a partition
- Use a stored procedure only when the transaction needs server-side reads to decide its writes, or exceeds batch limits
- Never use stored procedures for single-item CRUD, cross-partition operations, or general computation
- Keep scripts small and idempotent so they finish well within the bounded execution window

Reference(s):
[Stored procedures, triggers, and UDFs in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/stored-procedures-triggers-udfs)
[Transactional batch operations in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/transactional-batch)
