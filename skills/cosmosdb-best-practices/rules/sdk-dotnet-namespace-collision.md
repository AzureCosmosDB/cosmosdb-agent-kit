---
title: Avoid Microsoft.Azure.Cosmos namespace collisions with domain models
impact: HIGH
impactDescription: prevents CS0104 build-breaking ambiguous reference errors
tags: sdk, dotnet, namespace, collision, using, CS0104
---

## Avoid Microsoft.Azure.Cosmos namespace collisions with domain models

The `Microsoft.Azure.Cosmos` namespace exports top-level types including `User`, `Database`, `Container`, `Conflict`, `Trigger`, and `Permission`. When an application defines a domain entity by the same name and both namespaces are imported with unqualified `using` directives in the same file, every reference to the shared name becomes ambiguous and the build fails with **CS0104**.

**Incorrect (ambiguous reference — CS0104):**

```csharp
using ECommerce.Core.Models;      // defines User
using Microsoft.Azure.Cosmos;     // also defines User

public class UserRepository
{
    private readonly Container _container;
```

**Correct (alias the SDK import):**


```csharp
using Cosmos = Microsoft.Azure.Cosmos;
using ECommerce.Core.Models;      // defines User — no collision

public class UserRepository
{
    private readonly Cosmos.Container _container;
```

```csharp
using ECommerce.Core.Models;

public class UserRepository
{
    private readonly Microsoft.Azure.Cosmos.Container _container;

```
