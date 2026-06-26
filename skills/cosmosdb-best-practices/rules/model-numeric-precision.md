---
title: Understand IEEE 754 Numeric Precision Limits
impact: MEDIUM
impactDescription: prevents silent data loss on large or precise numbers
tags: model, numeric, precision, limits, json, design
---

## Understand IEEE 754 Numeric Precision Limits

Azure Cosmos DB stores numbers using **IEEE 754 double-precision 64-bit** format. This means integers larger than 2^53 and decimals requiring more than ~15-17 significant digits will lose precision silently.

**Incorrect (precision loss with large numbers):**

```csharp
// Anti-pattern 1: Storing large integers that exceed safe range
public class Transaction
{
    public string Id { get; set; }
    
    // 64-bit integer IDs from external systems - DANGER!
```

**Correct (preserving precision):**


```csharp
// Solution 1: Store large integers and precise decimals as strings
public class Transaction
{
    public string Id { get; set; }
    
    // Store large IDs as strings to preserve all digits
```

```csharp
// Solution 3: Store amounts as integer minor units (cents, paise, etc.)
public class Payment
{
    public string Id { get; set; }
    
    // Store $199.99 as 19999 cents - always safe as integer within 2^53
```
