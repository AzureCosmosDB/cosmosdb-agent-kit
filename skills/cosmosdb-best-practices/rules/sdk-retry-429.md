---
title: Handle 429 Errors with Retry-After
impact: HIGH
impactDescription: prevents cascading failures
tags: sdk, retry, throttling, resilience
---

## Handle 429 Errors with Retry-After

Properly handle rate limiting (HTTP 429) responses by respecting the Retry-After header. The SDK handles this automatically, but configuration and logging are important.

**Incorrect (ignoring or mishandling throttling):**

```csharp
// Anti-pattern: Retrying immediately without backoff
public async Task<Order> GetOrderWithBadRetry(string orderId, string customerId)
{
    while (true)
    {
        try
```

**Correct (leverage SDK's built-in retry):**


```csharp
// Configure client with appropriate retry settings
var cosmosClient = new CosmosClient(connectionString, new CosmosClientOptions
{
    // SDK automatically retries 429s up to this many times
    MaxRetryAttemptsOnRateLimitedRequests = 9,
    
```

```csharp
// Log throttling for monitoring and capacity planning
public async Task<Order> GetOrderWithDiagnostics(string orderId, string customerId)
{
    try
    {
        var response = await _container.ReadItemAsync<Order>(
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
> Cross-ref: See `sdk-diagnostics` for capturing diagnostics.
> Cross-ref: See `sdk-429-retry` for retry/throttle handling.
