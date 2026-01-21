---
title: Rule Title Here
impact: MEDIUM
impactDescription: Optional description of impact (e.g., "10-50x improvement")
tags: tag1, tag2
---

## Rule Title Here

**Impact: MEDIUM (optional impact description)**

Brief explanation of the rule and why it matters. This should be clear and concise, explaining the performance implications for Azure Cosmos DB.

**Incorrect (description of what's wrong):**

```csharp
// Bad code example here
var container = cosmosClient.GetContainer("db", "container");
// Example of anti-pattern
```

**Correct (description of what's right):**

```csharp
// Good code example here
var container = cosmosClient.GetContainer("db", "container");
// Example of best practice
```

Reference: [Link to documentation or resource](https://learn.microsoft.com/azure/cosmos-db/)
