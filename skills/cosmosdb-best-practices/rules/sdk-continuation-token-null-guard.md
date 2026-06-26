---
title: Guard against empty continuation tokens before calling byPage
impact: HIGH
impactDescription: empty string token causes runtime "INVALID JSON in continuation token" error; null is the correct sentinel for first-page requests
tags:
  - sdk
  - java
  - pagination
  - continuation-token
  - grpc
  - correctness
---

## Guard against empty continuation tokens before calling byPage

**Impact: HIGH (empty string token causes runtime `INVALID JSON in continuation token` error; `null` is the correct sentinel for first-page requests)**

When integrating Cosmos DB pagination with frameworks that use empty strings as default values for "no token" (e.g., gRPC/proto3, where string fields default to `""`), passing `""` to `byPage(continuationToken, pageSize)` triggers a server-side parse error. The correct sentinel for "no paging state" is `null`.

**Incorrect (empty string passed as continuation token):**

```java
// ❌ gRPC/proto3: string fields default to "" — NOT null
String pagingState = request.getPagingState();  // returns "" on first call

// Passing "" to byPage causes:
// CosmosException: INVALID JSON in continuation token
return container.queryItems(querySpec, opts, Video.class)
```

**Correct (null-guard before passing to byPage):**


```java
// ✅ Convert empty string to null before passing as continuation token
String raw = request.getPagingState();     // "" on first call, token on subsequent calls
String continuationToken = (raw == null || raw.isEmpty()) ? null : raw;

return container.queryItems(querySpec, opts, Video.class)
    .byPage(continuationToken, pageSize)   // ✅ null = first page, token = continuation
```

```java
// ✅ Or with Optional pattern
Optional<String> pageState = Optional.ofNullable(
    raw == null || raw.isEmpty() ? null : raw);

return container.queryItems(querySpec, opts, Video.class)
    .byPage(pageState.orElse(null), pageSize)
```
