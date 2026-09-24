---
title: Use the correct parameter names for ThroughputProperties factory methods (.NET)
impact: HIGH
impactDescription: prevents CS1739 build-breaking named-argument errors
tags: sdk, dotnet, throughput, api-surface, build-error, CS1739
---

## Use the Correct Parameter Names for ThroughputProperties Factory Methods (.NET)

**Impact: HIGH (build-breaking)**

The .NET SDK's `ThroughputProperties.CreateAutoscaleThroughput` takes a single `int` parameter named **`autoscaleMaxThroughput`**, not `maxThroughput`. `ThroughputProperties.CreateManualThroughput` takes a single `int` parameter named `throughput`. Passing either factory method a named argument with the wrong name fails to compile with **CS1739** ("the best overload does not have a parameter named ...").

**Incorrect (CS1739 — no parameter named `maxThroughput`):**

```csharp
var databaseResponse = await client.CreateDatabaseIfNotExistsAsync(
    databaseName,
    throughputProperties: ThroughputProperties.CreateAutoscaleThroughput(
        maxThroughput: 10000
    ));
```

**Correct (named argument):**

```csharp
var databaseResponse = await client.CreateDatabaseIfNotExistsAsync(
    databaseName,
    throughputProperties: ThroughputProperties.CreateAutoscaleThroughput(
        autoscaleMaxThroughput: 10000
    ));

// Manual throughput
var manualThroughputProperties = ThroughputProperties.CreateManualThroughput(
    throughput: 400
);
```

**Also correct (positional argument avoids the naming pitfall entirely):**

```csharp
ThroughputProperties.CreateAutoscaleThroughput(10000);
ThroughputProperties.CreateManualThroughput(400);
```

Reference: [ThroughputProperties.CreateAutoscaleThroughput — .NET API](https://learn.microsoft.com/en-us/dotnet/api/microsoft.azure.cosmos.throughputproperties.createautoscalethroughput)
