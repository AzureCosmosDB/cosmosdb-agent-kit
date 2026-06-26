---
title: Enable Diagnostic Logging
impact: LOW-MEDIUM
impactDescription: enables troubleshooting
tags: monitoring, diagnostics, logging, troubleshooting
---

## Enable Diagnostic Logging

Enable diagnostic logging to capture detailed operation data for troubleshooting. Essential for root cause analysis of production issues.

**Incorrect (no diagnostic logging):**

```csharp
// When issues occur, you have no data to investigate
// "Why is this query slow?"
// "Why did we get throttled yesterday at 3am?"
// "Which operations are using the most RU?"
// No answers without logging!
```

**Correct (comprehensive diagnostic logging):**


```csharp
// Azure diagnostic settings for detailed logs
// Enable via Azure Portal > Cosmos DB > Diagnostic settings

// Categories to enable:
// 1. DataPlaneRequests - All CRUD operations

// ARM template for diagnostic settings
```

```csharp
// Application-level diagnostic logging
public class DiagnosticLoggingRepository
{
    private readonly Container _container;
    private readonly ILogger _logger;
    
    public async Task<T> ExecuteWithDiagnostics<T>(
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
> Cross-ref: See `sdk-diagnostics` for capturing diagnostics.
