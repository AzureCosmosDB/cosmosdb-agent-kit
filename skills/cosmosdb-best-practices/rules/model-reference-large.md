---
title: Reference Data When Items Grow Large
impact: CRITICAL
impactDescription: prevents hitting 2MB limit
tags: model, referencing, normalization, large-documents
---

## Reference Data When Items Grow Large

Use document references instead of embedding when embedded data would make items too large, or when embedded data changes independently.

**Incorrect (embedded array grows unbounded):**

```csharp
// Anti-pattern: blog post with all comments embedded
public class BlogPost
{
    public string Id { get; set; }
    public string Title { get; set; }
    public string Content { get; set; }
```

**Correct (reference pattern for unbounded relationships):**


```csharp
// Blog post document (bounded size)
public class BlogPost
{
    public string Id { get; set; }
    public string PostId { get; set; }  // Partition key
    public string Type { get; set; } = "post";
```

> Cross-ref: See `query-parameterize` for parameterized queries.
