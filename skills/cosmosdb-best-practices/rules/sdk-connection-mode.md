---
title: Use Direct Connection Mode for Production
impact: HIGH
impactDescription: reduces latency by 30-50%
tags: sdk, connection-mode, direct, performance
---

## Use Direct Connection Mode for Production

Use Direct connection mode for production workloads. Gateway mode adds an extra network hop and is only needed for firewall-restricted environments.

**Incorrect (defaulting to Gateway mode):**

```csharp
// Gateway mode adds extra hop through Azure gateway
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ConnectionMode = ConnectionMode.Gateway  // Extra network hop!
});

```

**Correct (Direct mode for production):**


```csharp
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    // Direct mode connects straight to backend partitions
    ConnectionMode = ConnectionMode.Direct,
    
    // Protocol.Tcp for best performance (default in Direct mode)
```

```csharp
// When to use Gateway mode (exceptions):
var gatewayClient = new CosmosClient(connectionString, new CosmosClientOptions
{
    // Use Gateway when:
    // 1. Corporate firewall blocks TCP port range 10000-20000
    ConnectionMode = ConnectionMode.Gateway
```
