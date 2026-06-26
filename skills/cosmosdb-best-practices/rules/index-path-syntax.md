---
title: Use Correct Indexing Path Syntax
impact: HIGH
impactDescription: prevents container creation failures from invalid paths
tags: index, path, syntax, array, wildcard
---

## Use Correct Indexing Path Syntax

Cosmos DB indexing paths use specific notation for scalars, arrays, and wildcards. Using the wrong notation causes container creation to fail with a BadRequest error.

**Incorrect (using `*` for array traversal):**

```json
// ❌ WRONG — * cannot be used mid-path for array traversal
// This causes: "The indexing path could not be accepted, failed near position ..."
{
    "excludedPaths": [
        { "path": "/lineItems/*/productSnapshot/?" },
        { "path": "/orders/*/items/?" }
```

**Correct (using `[]` for array traversal):**


```json
// ✅ CORRECT — use [] to traverse array elements
{
    "excludedPaths": [
        { "path": "/lineItems/[]/productSnapshot/?" },
        { "path": "/orders/[]/items/?" }
    ]
```

```json
// ✅ CORRECT — * at the END of a path matches everything below
{
    "includedPaths": [
        { "path": "/*" }
    ],
    "excludedPaths": [
```
