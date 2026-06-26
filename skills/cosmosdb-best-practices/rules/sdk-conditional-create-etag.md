---
title: Use IfNoneMatchETag("*") for conditional creates to prevent duplicates
impact: HIGH
impactDescription: prevents duplicate documents on concurrent or retried creates without a prior read
tags:
  - sdk
  - etag
  - concurrency
  - java
  - upsert
  - uniqueness
---

## Use IfNoneMatchETag("*") for conditional creates to prevent duplicates

**Impact: HIGH (prevents duplicate documents on concurrent or retried creates without a prior read)**

When creating a document that must be unique (e.g., user credentials keyed by email), pass `IfNoneMatchETag("*")` on the `createItem` options. Cosmos DB rejects the write with HTTP 409 Conflict if a document with the same `id` in the same partition already exists, making duplicate detection atomic and free of an extra read.

**Incorrect (upsert silently overwrites existing records):**

```java
// ❌ upsertItem overwrites an existing user-credentials document silently
// A duplicate email gets no error — the old credentials are lost
container.upsertItem(credentialsDto, new PartitionKey(email), null).block();
```

**Correct (conditional create — 409 on duplicate):**


```java
// ✅ createItem with IfNoneMatchETag("*") rejects if the document already exists
CosmosItemRequestOptions options = new CosmosItemRequestOptions()
    .setIfNoneMatchETag("*");  // Reject if any document exists with this id+PK

try {
    credentialsContainer
```

```java
// ✅ Reactive chain
credentialsContainer
    .createItem(credentialsDto, new PartitionKey(email),
        new CosmosItemRequestOptions().setIfNoneMatchETag("*"))
    .onErrorMap(CosmosException.class, ex ->
        ex.getStatusCode() == 409
```
