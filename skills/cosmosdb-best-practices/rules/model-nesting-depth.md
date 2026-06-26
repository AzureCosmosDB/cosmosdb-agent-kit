---
title: Stay Within 128-Level Nesting Depth Limit
impact: MEDIUM
impactDescription: prevents document rejection on deeply nested structures
tags: model, nesting, limits, design, json
---

## Stay Within 128-Level Nesting Depth Limit

Azure Cosmos DB allows a maximum of **128 levels** of nesting for embedded objects and arrays. While 128 is generous, recursive or auto-generated structures can exceed this limit unexpectedly.

**Incorrect (risk of exceeding nesting limit):**

```csharp
// Anti-pattern 1: Recursive tree stored as deeply nested JSON
public class TreeNode
{
    public string Id { get; set; }
    public string Name { get; set; }
    
```

**Correct (bounded nesting depth):**


```csharp
// Solution 1: Flatten deep hierarchies using path-based approach
public class CategoryNode
{
    public string Id { get; set; }
    public string Name { get; set; }
    public string ParentId { get; set; }
```

```csharp
// Solution 2: Cap nesting depth when building recursive structures
public class TreeNode
{
    public string Id { get; set; }
    public string Name { get; set; }
    public List<TreeNode> Children { get; set; }
```
