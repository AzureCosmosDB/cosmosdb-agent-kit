---
title: Use createItem for atomic create-only writes
impact: HIGH
impactDescription: prevents duplicate documents on concurrent or retried creates without a prior read
tags:
  - sdk
  - create
  - concurrency
  - java
  - upsert
  - uniqueness
---

## Use createItem for Atomic Create-Only Writes

**Impact: HIGH (prevents duplicate documents on concurrent or retried creates without a prior read)**

When creating a document that must not overwrite an existing item, use `createItem`, not `upsertItem`. A normal create atomically fails with HTTP 409 Conflict if the same `id` already exists in the same logical partition; no prior read or ETag option is needed. Concurrent or retried requests must use the same deterministic `id` and partition key for the same logical item.

**Incorrect (upsert silently overwrites existing records):**

```java
// ❌ upsertItem overwrites an existing user-credentials document silently
// A duplicate email gets no error — the old credentials are lost
container.upsertItem(credentialsDto, new PartitionKey(email), null).block();
```

**Correct (create-only write — 409 on duplicate):**

```java
CosmosItemRequestOptions options = new CosmosItemRequestOptions();

try {
    credentialsContainer
        .createItem(credentialsDto, new PartitionKey(email), options)
        .block();
} catch (CosmosException ex) {
    if (ex.getStatusCode() == 409) {
        // Email already registered — surface as domain error
        throw new AlreadyExistsException("Email already in use: " + email);
    }
    throw ex;
}
```

```java
// ✅ Reactive chain
credentialsContainer
    .createItem(credentialsDto, new PartitionKey(email),
        new CosmosItemRequestOptions())
    .onErrorMap(CosmosException.class, ex ->
        ex.getStatusCode() == 409
            ? new AlreadyExistsException("Email already in use")
            : ex);
```

**No `If-None-Match` needed:** The Java SDK documents `setIfNoneMatchETag` for conditional reads and ignores it for write requests, including creates. It does not add create-only protection; that protection comes from `createItem` itself. For read-modify-write concurrency on existing items, use `If-Match` as described in [sdk-etag-concurrency](sdk-etag-concurrency.md).

**Key Points:**
- Use `createItem`, not `upsertItem`, when an existing item must not be overwritten
- The 409 check is done atomically server-side — no extra read RU consumed
- Uniqueness is scoped to the document's `id` + partition key, not arbitrary field values; a new random `id` on every retry defeats this protection
- Handle 409 as an existing item and propagate other failures; fresh request options keep deferred or concurrent calls independent

References: [Create a Document (409 Conflict)](https://learn.microsoft.com/rest/api/cosmos-db/create-a-document#status-codes), [CosmosItemRequestOptions.setIfNoneMatchETag](https://learn.microsoft.com/java/api/com.azure.cosmos.models.cosmositemrequestoptions?view=azure-java-stable#com-azure-cosmos-models-cosmositemrequestoptions-setifnonematchetag(java-lang-string))
