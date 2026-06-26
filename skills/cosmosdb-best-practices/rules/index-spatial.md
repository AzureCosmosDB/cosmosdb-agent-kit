---
title: Add Spatial Indexes for Geo Queries
impact: MEDIUM-HIGH
impactDescription: enables efficient location queries
tags: index, spatial, geospatial, location
---

## Add Spatial Indexes for Geo Queries

Create spatial indexes for properties that store geographic data when you need to perform proximity or geometry queries.

**Incorrect (geo queries without spatial index):**

```csharp
// Document with location
{
    "id": "store-1",
    "name": "Downtown Store",
    "location": {
        "type": "Point",
```

**Correct (spatial index for location queries):**


```csharp
// Create indexing policy with spatial index
var indexingPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,
    
    // Include path with spatial index
```

```json
// JSON indexing policy with spatial index
{
    "indexingMode": "consistent",
    "spatialIndexes": [
        {
            "path": "/location/?",
```

> Cross-ref: See `query-parameterize` for parameterized queries.
