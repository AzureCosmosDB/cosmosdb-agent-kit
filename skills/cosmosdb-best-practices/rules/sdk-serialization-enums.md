---
title: Use consistent enum serialization between Cosmos SDK and application layer
impact: CRITICAL
impactDescription: mismatched enum storage causes queries to silently return empty results
tags: sdk, serialization, enums, bug-prevention
---

## Use Consistent Enum Serialization

Cosmos DB SDK default stores enums as integers, but many frameworks (ASP.NET Core, Spring Boot) serialize as strings. This mismatch causes queries to silently return empty results.

**Incorrect (default integer storage — queries fail silently):**

```csharp
// Stored as {"status": 1} but queried with "Active" → no results
public enum OrderStatus { Pending, Active, Completed }
public class Order { public OrderStatus Status { get; set; } }
// SELECT * FROM c WHERE c.status = "Active" → 0 results (stored as 1)
```

**Correct (explicit string serialization):**

```csharp
// .NET — System.Text.Json
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum OrderStatus { Pending, Active, Completed }

// Or configure globally on CosmosClient
var options = new CosmosClientOptions {
    SerializerOptions = new CosmosSerializationOptions {
        PropertyNamingPolicy = CosmosPropertyNamingPolicy.CamelCase
    }
};
// Use [JsonConverter(typeof(JsonStringEnumConverter))] on each enum
```

```java
// Java — Jackson annotation
@JsonFormat(shape = JsonFormat.Shape.STRING)
public enum OrderStatus { PENDING, ACTIVE, COMPLETED }
```

**Key rule:** Pick one (string or integer) and use it everywhere — SDK, queries, and API layer. String is safer for readability and cross-system compatibility.

Reference: See `query-parameterize` for parameterized queries.
