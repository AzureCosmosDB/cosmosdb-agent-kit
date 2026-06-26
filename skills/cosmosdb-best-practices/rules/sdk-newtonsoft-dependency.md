---
title: Explicitly reference Newtonsoft.Json package
impact: HIGH
impactDescription: Prevents build failures and security vulnerabilities from missing or outdated Newtonsoft.Json dependency
tags: sdk, dotnet, dependencies, security, build-error, csproj, project-setup, new-project
---

## Explicitly reference Newtonsoft.Json package

## Explicitly reference Newtonsoft.Json package

When creating any .NET project that references `Microsoft.Azure.Cosmos` (version 3.43.0 or later), your `.csproj` **MUST** include an explicit `PackageReference` for `Newtonsoft.Json` (version 13.0.3 or higher). Without this reference the project will not build.

**Incorrect:**

```csharp
// Your .csproj only references Cosmos DB SDK
<ItemGroup>
  <PackageReference Include="Microsoft.Azure.Cosmos" Version="3.47.0" />
  <!-- Missing Newtonsoft.Json reference! -->
</ItemGroup>

// Build error:
```

**Correct:**


```xml
<!-- Standard .csproj projects -->
<ItemGroup>
  <PackageReference Include="Microsoft.Azure.Cosmos" Version="3.47.0" />
  <PackageReference Include="Newtonsoft.Json" Version="13.0.4" />
</ItemGroup>
```

```xml
<!-- Directory.Packages.props -->
<Project>
  <ItemGroup>
    <PackageVersion Include="Microsoft.Azure.Cosmos" Version="3.47.0" />
    <PackageVersion Include="Newtonsoft.Json" Version="13.0.4" />
  </ItemGroup>
</Project>
```
