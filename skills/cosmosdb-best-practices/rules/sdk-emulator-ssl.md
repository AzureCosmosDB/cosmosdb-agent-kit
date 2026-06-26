---
title: Configure SSL and connection mode for Cosmos DB Emulator
impact: MEDIUM
impactDescription: enables local development with all SDKs
tags: sdk, emulator, ssl, local-development, certificate, gateway-mode, java, netty, truststore
---

## Configure SSL and connection mode for Cosmos DB Emulator

The emulator uses a self-signed certificate requiring special handling. **All SDKs must use Gateway mode** — Direct mode has known SSL issues with the emulator.

**Incorrect (Direct mode with emulator):**

```java
// Direct mode fails with SSL errors even after cert import
CosmosClientBuilder builder = new CosmosClientBuilder()
    .endpoint("https://localhost:8081")
    .key("...")
    .directMode();  // WRONG: SSL handshake will fail
```

**Correct (Gateway mode, per-SDK SSL handling):**


```csharp
// .NET — Gateway + accept self-signed cert
var client = new CosmosClient("https://localhost:8081", emulatorKey, new CosmosClientOptions
{
    ConnectionMode = ConnectionMode.Gateway,
    HttpClientFactory = () => new HttpClient(new HttpClientHandler
    {
```

```python
# Python — Gateway by default, disable SSL verification
client = CosmosClient(
    url="https://localhost:8081", credential=emulator_key,
    connection_verify=False  # Disable SSL for emulator only
)
```
