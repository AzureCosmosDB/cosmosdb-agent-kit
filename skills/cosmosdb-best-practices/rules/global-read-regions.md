---
title: Add Read Regions Near Users
impact: MEDIUM
impactDescription: reduces read latency globally
tags: global, regions, read-latency, distribution
---

## Add Read Regions Near Users

Add read regions in geographic locations close to your users. Reads can be served from any region, reducing latency for global users.

**Incorrect (single region for global users):**

```csharp
// Only one region configured
// Users from all locations read from single region

{
    "properties": {
        "locations": [
```

**Correct (read regions near user populations):**


```csharp
// Add read replicas near major user bases
{
    "type": "Microsoft.DocumentDB/databaseAccounts",
    "properties": {
        "locations": [
            // Primary write region
```

```csharp
// Configure SDK for region-local reads
// Deployed in Europe - prioritize European region
var europeClient = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationPreferredRegions = new List<string>
    {
```

> Cross-ref: See `sdk-diagnostics` for capturing diagnostics.
