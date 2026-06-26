---
title: Handle JSON serialization correctly for Cosmos DB documents
impact: HIGH
impactDescription: prevents data loss, null constructor errors, and serialization failures
tags: model, serialization, json, jackson, jsonignore, jsonproperty, bigdecimal, jsonignoreproperties, system-metadata
---

## Handle JSON serialization correctly for Cosmos DB documents

Cosmos DB stores documents as JSON. Every field on an entity that must be persisted needs to be serializable.

**Incorrect (common serialization mistakes):**

```java
@Container(containerName = "users")
public class User {

    @Id
    private String id;

    @PartitionKey
```

**Correct (proper serialization for Cosmos DB):**


```java
@JsonIgnoreProperties(ignoreUnknown = true)  // ✅ Ignore Cosmos DB system metadata (_rid, _self, _etag, _ts, _lsn)
@Container(containerName = "users")
public class User {

    @Id
    private String id;

```

```java
// ❌ Data loss: field is not stored in Cosmos
@JsonIgnore
private String password;

// ✅ Field is stored in Cosmos
private String password;

```

> Cross-ref: See `query-parameterize` for parameterized queries.
