---
title: Respect Partition Key Value Length Limits
impact: HIGH
impactDescription: prevents write failures from oversized keys
tags: partition, limits, key-length, design
---

## Respect Partition Key Value Length Limits

Azure Cosmos DB enforces a maximum partition key value length of **2,048 bytes** (or **101 bytes** if large partition keys are not enabled). Exceeding this limit causes write failures at runtime.

**Incorrect (risk of exceeding partition key length):**

```csharp
// Anti-pattern: concatenating many fields into a partition key
public class Document
{
    public string Id { get; set; }
    
    // Partition key built from long descriptions - DANGER!
```

**Correct (bounded partition key values):**


```csharp
// Use short, bounded identifiers for partition keys
public class Document
{
    public string Id { get; set; }
    
    // Short, deterministic IDs - always well under 2,048 bytes
```

```csharp
// If you must derive a key from long values, hash or truncate them
public class Document
{
    public string Id { get; set; }
    public string LongCategoryPath { get; set; }  // e.g., deep taxonomy
    
```
