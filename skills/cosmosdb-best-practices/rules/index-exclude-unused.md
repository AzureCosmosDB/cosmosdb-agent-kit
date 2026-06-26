---
title: Exclude Unused Index Paths
impact: HIGH
impactDescription: reduces write RU by 20-80%
tags: index, exclusion, write-performance, optimization
---

## Exclude Unused Index Paths

Exclude paths from indexing that you never query. Every indexed path adds write cost with no read benefit.

**Incorrect (indexing everything):**

```csharp
// Default indexing policy indexes ALL paths
// Great for flexibility, expensive for writes
{
    "indexingMode": "consistent",
    "automatic": true,
    "includedPaths": [
        {
```

**Correct (exclude-all-first, then include back):**


```csharp
// Exclude everything, then include only what you query
var indexingPolicy = new IndexingPolicy
{
    IndexingMode = IndexingMode.Consistent,
    Automatic = true,
    
    // Start with exclude all — no field is indexed by default
```

```json
// JSON equivalent indexing policy
{
    "indexingMode": "consistent",
    "automatic": true,
    "excludedPaths": [
        { "path": "/*" }
    ],
```
