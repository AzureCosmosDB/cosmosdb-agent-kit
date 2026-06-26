---
title: Never share a single CosmosItemRequestOptions instance across multiple createItem calls
impact: HIGH
impactDescription: causes wrong partition key to be sent, producing silent data corruption or 400/404 errors
tags:
  - sdk
  - java
  - request-options
  - concurrency
  - correctness
---

## Never share a single CosmosItemRequestOptions instance across multiple createItem calls

**Impact: HIGH (causes wrong partition key to be sent, producing silent data corruption or 400/404 errors)**

`CosmosItemRequestOptions` is a mutable object. The SDK may mutate the options object internally during request preparation (e.g., stamping the resolved partition key).

**Incorrect (shared mutable options — second call sends wrong partition key):**

```java
// ❌ Anti-pattern: one options instance reused for two different createItem calls
CosmosItemRequestOptions options = new CosmosItemRequestOptions()
    .setIfNoneMatchETag("*");

// First call: writes UserCredentials with PK = email
credentialsContainer.createItem(credentials, new PartitionKey(email), options).block();
```

**Correct (separate instance per call):**


```java
// ✅ Each createItem gets its own fresh options instance
CosmosItemRequestOptions credsOptions = new CosmosItemRequestOptions()
    .setIfNoneMatchETag("*");
CosmosItemRequestOptions userOptions = new CosmosItemRequestOptions()
    .setIfNoneMatchETag("*");

```

```java
// ✅ Or construct inline to make sharing structurally impossible
credentialsContainer.createItem(
    credentials, new PartitionKey(email),
    new CosmosItemRequestOptions().setIfNoneMatchETag("*")).block();

usersContainer.createItem(
```
