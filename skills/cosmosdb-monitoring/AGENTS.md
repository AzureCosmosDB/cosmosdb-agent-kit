# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Best practices for Azure Cosmos DB monitoring: RU consumption tracking, P99 latency monitoring, throttling alerts, Azure Monitor integration, and diagnostic logging.

---

## Table of Contents

1. [Monitoring & Diagnostics](#1-monitoring-diagnostics) — **LOW-MEDIUM**
   - 1.1 [Integrate Azure Monitor](#11-integrate-azure-monitor)
   - 1.2 [Enable Diagnostic Logging](#12-enable-diagnostic-logging)
   - 1.3 [Monitor P99 Latency](#13-monitor-p99-latency)
   - 1.4 [Track RU Consumption](#14-track-ru-consumption)
   - 1.5 [Alert on Throttling (429s)](#15-alert-on-throttling-429s-)

---

## 1. Monitoring & Diagnostics

**Impact: LOW-MEDIUM**

### 1.1 Integrate Azure Monitor

**Impact: MEDIUM** (enables comprehensive observability)

## Integrate Azure Monitor

Enable Azure Monitor integration for comprehensive visibility into Cosmos DB performance, availability, and cost metrics.

**Incorrect (no monitoring integration):**

```csharp
// Flying blind - no visibility into:
// - RU consumption trends
// - Latency patterns
// - Throttling events
// - Availability issues
// - Cost attribution

// Application runs but you only know about problems from user complaints
```

**Correct (Azure Monitor integration):**

```csharp
// Step 1: Enable diagnostic settings (Azure Portal, CLI, or ARM)
{
    "type": "Microsoft.DocumentDB/databaseAccounts/providers/diagnosticSettings",
    "properties": {
        "logs": [
            {
                "category": "DataPlaneRequests",
                "enabled": true,
                "retentionPolicy": { "enabled": true, "days": 30 }
            },
            {
                "category": "QueryRuntimeStatistics",
                "enabled": true
            },
            {
                "category": "PartitionKeyStatistics",
                "enabled": true
            },
            {
                "category": "PartitionKeyRUConsumption",
                "enabled": true
            }
        ],
        "metrics": [
            {
                "category": "Requests",
                "enabled": true
            }
        ],
        "workspaceId": "/subscriptions/.../workspaces/my-workspace"
    }
}
```

```csharp
// Step 2: Key metrics to monitor in Azure Monitor

// a) Normalized RU Consumption (% of provisioned used)
// Alert if > 90% sustained - indicates need to scale

// b) Total Requests by Status Code
// Alert on 429s (throttling) and 5xx (errors)

// c) Server Side Latency
// Track P50, P99 for performance baselines

// d) Data Usage
// Monitor storage growth

// e) Availability
// Alert on availability drops below 99.99%
```

```csharp
// Step 3: Application Insights integration
public static class CosmosDbTelemetry
{
    public static void ConfigureWithAppInsights(
        CosmosClientOptions options, 
        TelemetryClient telemetry)
    {
        // Track all operations as dependencies
        options.CosmosClientTelemetryOptions = new CosmosClientTelemetryOptions
        {
            DisableDistributedTracing = false  // Enable distributed tracing
        };
        
        // Custom handler for detailed telemetry
        options.CustomHandlers.Add(new AppInsightsHandler(telemetry));
    }
}

public class AppInsightsHandler : RequestHandler
{
    private readonly TelemetryClient _telemetry;
    
    public override async Task<ResponseMessage> SendAsync(
        RequestMessage request, 
        CancellationToken cancellationToken)
    {
        using var operation = _telemetry.StartOperation<DependencyTelemetry>(
            "CosmosDB", 
            request.RequestUri.ToString());
        
        operation.Telemetry.Type = "Azure DocumentDB";
        operation.Telemetry.Target = request.RequestUri.Host;
        
        var response = await base.SendAsync(request, cancellationToken);
        
        operation.Telemetry.Success = response.IsSuccessStatusCode;
        operation.Telemetry.ResultCode = ((int)response.StatusCode).ToString();
        operation.Telemetry.Properties["RU"] = response.Headers.RequestCharge.ToString();
        
        return response;
    }
}
```

```kusto
// Useful Log Analytics queries

// RU consumption by operation
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| summarize TotalRU = sum(requestCharge_s), 
            AvgRU = avg(requestCharge_s),
            Count = count()
    by OperationName
| order by TotalRU desc

// Slow queries
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| where duration_s > 100  // > 100ms
| project TimeGenerated, OperationName, duration_s, 
          requestCharge_s, partitionKey_s, querytext_s

// Storage growth trend
AzureMetrics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| where MetricName == "DataUsage"
| summarize StorageGB = max(Total) / 1073741824 by bin(TimeGenerated, 1d)
| order by TimeGenerated
```

Essential alerts to configure:
1. Throttling (429s) > 0
2. Normalized RU > 90% for 5 min
3. Availability < 99.99%
4. P99 latency > threshold
5. Storage approaching limits

Reference: [Monitor Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/monitor)

### 1.2 Enable Diagnostic Logging

**Impact: LOW-MEDIUM** (enables troubleshooting)

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
// 2. QueryRuntimeStatistics - Query execution details
// 3. PartitionKeyStatistics - Partition key distribution
// 4. PartitionKeyRUConsumption - RU by partition
// 5. ControlPlaneRequests - Management operations

// ARM template for diagnostic settings
{
    "type": "Microsoft.Insights/diagnosticSettings",
    "name": "cosmos-diagnostics",
    "properties": {
        "logs": [
            { "category": "DataPlaneRequests", "enabled": true },
            { "category": "QueryRuntimeStatistics", "enabled": true },
            { "category": "PartitionKeyStatistics", "enabled": true },
            { "category": "PartitionKeyRUConsumption", "enabled": true },
            { "category": "ControlPlaneRequests", "enabled": true }
        ],
        "logAnalyticsDestinationType": "Dedicated",
        "workspaceId": "[resourceId('Microsoft.OperationalInsights/workspaces', 'my-workspace')]"
    }
}
```

```csharp
// Application-level diagnostic logging
public class DiagnosticLoggingRepository
{
    private readonly Container _container;
    private readonly ILogger _logger;
    
    public async Task<T> ExecuteWithDiagnostics<T>(
        string operationName,
        Func<Task<Response<T>>> operation)
    {
        var correlationId = Activity.Current?.Id ?? Guid.NewGuid().ToString();
        
        try
        {
            var response = await operation();
            
            // Always log basic info
            _logger.LogDebug(
                "[{CorrelationId}] {Operation}: {RU} RU, {LatencyMs}ms, Status: {Status}",
                correlationId,
                operationName,
                response.RequestCharge,
                response.Diagnostics.GetClientElapsedTime().TotalMilliseconds,
                "Success");
            
            // Log full diagnostics for slow operations
            if (response.Diagnostics.GetClientElapsedTime() > TimeSpan.FromMilliseconds(100))
            {
                _logger.LogWarning(
                    "[{CorrelationId}] Slow {Operation}: {Diagnostics}",
                    correlationId,
                    operationName,
                    response.Diagnostics.ToString());
            }
            
            return response.Resource;
        }
        catch (CosmosException ex)
        {
            _logger.LogError(ex,
                "[{CorrelationId}] {Operation} failed: Status={Status}, SubStatus={SubStatus}, " +
                "RU={RU}, RetryAfter={RetryAfter}, ActivityId={ActivityId}, Diagnostics={Diagnostics}",
                correlationId,
                operationName,
                ex.StatusCode,
                ex.SubStatusCode,
                ex.RequestCharge,
                ex.RetryAfter,
                ex.ActivityId,
                ex.Diagnostics?.ToString());
            
            throw;
        }
    }
}
```

```csharp
// Query-specific diagnostics
public async Task<List<T>> ExecuteQueryWithDiagnostics<T>(
    string queryName,
    QueryDefinition query,
    QueryRequestOptions options = null)
{
    options ??= new QueryRequestOptions();
    options.PopulateIndexMetrics = true;  // Get index usage info
    
    var results = new List<T>();
    var totalRU = 0.0;
    var pageCount = 0;
    
    var iterator = _container.GetItemQueryIterator<T>(query, requestOptions: options);
    
    while (iterator.HasMoreResults)
    {
        var response = await iterator.ReadNextAsync();
        results.AddRange(response);
        totalRU += response.RequestCharge;
        pageCount++;
        
        // Log index metrics (helps identify missing indexes)
        if (!string.IsNullOrEmpty(response.IndexMetrics))
        {
            _logger.LogDebug(
                "Query '{QueryName}' page {Page} index metrics: {IndexMetrics}",
                queryName, pageCount, response.IndexMetrics);
        }
    }
    
    _logger.LogInformation(
        "Query '{QueryName}': {Count} results, {TotalRU} RU, {Pages} pages",
        queryName, results.Count, totalRU, pageCount);
    
    return results;
}
```

Key diagnostic data to capture:
- Operation name and duration
- RU consumption
- Partition key (for hot partition analysis)
- Full diagnostics for errors/slow operations
- Index metrics for queries
- ActivityId (for Azure support)

Reference: [Diagnostic logging](https://learn.microsoft.com/azure/cosmos-db/monitor-resource-logs)

### 1.3 Monitor P99 Latency

**Impact: MEDIUM** (identifies performance issues)

## Monitor P99 Latency

Track P99 (99th percentile) latency to identify performance outliers. Average latency hides tail latency issues that affect user experience.

**Incorrect (only tracking average latency):**

```csharp
// Average latency looks good: 5ms
// But P99 could be 500ms - 1% of users have terrible experience!

public async Task<Order> GetOrder(string orderId, string customerId)
{
    var sw = Stopwatch.StartNew();
    var result = await _container.ReadItemAsync<Order>(orderId, pk);
    sw.Stop();
    
    // Only tracking average is misleading
    _metrics.TrackAverage("CosmosDB.Latency", sw.ElapsedMilliseconds);
    // Average: 5ms (hides that some requests take 500ms)
    
    return result.Resource;
}
```

**Correct (tracking latency distribution):**

```csharp
public async Task<Order> GetOrder(string orderId, string customerId)
{
    var sw = Stopwatch.StartNew();
    var response = await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
    sw.Stop();
    
    var clientLatency = sw.ElapsedMilliseconds;
    var serverLatency = response.Diagnostics.GetClientElapsedTime().TotalMilliseconds;
    
    // Track as histogram (enables percentile calculations)
    _metrics.TrackHistogram("CosmosDB.Latency.Client", clientLatency);
    _metrics.TrackHistogram("CosmosDB.Latency.Server", serverLatency);
    
    // Alert on slow requests
    if (clientLatency > 100)  // 100ms threshold
    {
        _logger.LogWarning(
            "Slow Cosmos DB read: {LatencyMs}ms, Diagnostics: {Diagnostics}",
            clientLatency,
            response.Diagnostics.ToString());
    }
    
    return response.Resource;
}
```

```csharp
// Track percentiles with Application Insights
public class LatencyTracker
{
    private readonly TelemetryClient _telemetry;
    private readonly ConcurrentBag<double> _recentLatencies = new();
    private readonly Timer _reportTimer;
    
    public LatencyTracker(TelemetryClient telemetry)
    {
        _telemetry = telemetry;
        _reportTimer = new Timer(ReportPercentiles, null, 
            TimeSpan.FromMinutes(1), TimeSpan.FromMinutes(1));
    }
    
    public void RecordLatency(double latencyMs)
    {
        _recentLatencies.Add(latencyMs);
    }
    
    private void ReportPercentiles(object state)
    {
        var latencies = _recentLatencies.ToArray();
        _recentLatencies.Clear();
        
        if (latencies.Length == 0) return;
        
        Array.Sort(latencies);
        
        var p50 = GetPercentile(latencies, 50);
        var p90 = GetPercentile(latencies, 90);
        var p99 = GetPercentile(latencies, 99);
        
        _telemetry.TrackMetric("CosmosDB.Latency.P50", p50);
        _telemetry.TrackMetric("CosmosDB.Latency.P90", p90);
        _telemetry.TrackMetric("CosmosDB.Latency.P99", p99);
        
        // Alert if P99 exceeds threshold
        if (p99 > 100)
        {
            _telemetry.TrackEvent("HighP99Latency", 
                new Dictionary<string, string> { { "P99", p99.ToString() } });
        }
    }
    
    private static double GetPercentile(double[] sorted, int percentile)
    {
        var index = (int)Math.Ceiling(percentile / 100.0 * sorted.Length) - 1;
        return sorted[Math.Max(0, index)];
    }
}
```

```csharp
// Azure Monitor / Log Analytics query for P99
// Query to get latency percentiles
/*
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| where TimeGenerated > ago(1h)
| summarize 
    P50 = percentile(duration_s, 50),
    P90 = percentile(duration_s, 90),
    P99 = percentile(duration_s, 99),
    Max = max(duration_s)
    by bin(TimeGenerated, 5m), OperationName
| order by TimeGenerated desc
*/
```

What P99 latency reveals:
- Network issues (high client vs server latency gap)
- Hot partitions (certain keys slow)
- Query efficiency problems
- Cross-partition query overhead
- Regional routing issues

Target latencies:
- Point reads: P99 < 10ms (same region)
- Queries: P99 < 50ms (depends on complexity)
- Cross-region: Add ~RTT to target

Reference: [Monitor latency](https://learn.microsoft.com/azure/cosmos-db/monitor-server-side-latency)

### 1.4 Track RU Consumption

**Impact: MEDIUM** (enables cost optimization)

## Track RU Consumption

Monitor Request Unit (RU) consumption to optimize costs and identify inefficient operations. Every operation has an RU cost.

**Incorrect (ignoring RU consumption):**

```csharp
// Operations without tracking cost
public async Task<Order> GetOrder(string orderId, string customerId)
{
    // No visibility into cost
    return await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
    // Is this costing 1 RU or 100 RU? Unknown!
}
```

**Correct (tracking RU at operation level):**

```csharp
public async Task<Order> GetOrder(string orderId, string customerId)
{
    var response = await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
    
    // Log RU consumption
    _logger.LogDebug(
        "Read order {OrderId}: {RU} RU, {Latency}ms",
        orderId,
        response.RequestCharge,
        response.Diagnostics.GetClientElapsedTime().TotalMilliseconds);
    
    // Track in metrics/telemetry
    _telemetry.TrackMetric("CosmosDB.ReadItem.RU", response.RequestCharge, 
        new Dictionary<string, string> 
        { 
            { "Operation", "ReadItem" },
            { "Container", "orders" }
        });
    
    return response.Resource;
}
```

```csharp
// Track RU for queries (can be high!)
public async Task<List<Order>> GetCustomerOrders(string customerId)
{
    var query = new QueryDefinition("SELECT * FROM c WHERE c.status = @status")
        .WithParameter("@status", "active");
    
    var totalRU = 0.0;
    var results = new List<Order>();
    
    var iterator = _container.GetItemQueryIterator<Order>(
        query,
        requestOptions: new QueryRequestOptions 
        { 
            PartitionKey = new PartitionKey(customerId),
            PopulateIndexMetrics = true  // Also get index metrics
        });
    
    while (iterator.HasMoreResults)
    {
        var response = await iterator.ReadNextAsync();
        results.AddRange(response);
        totalRU += response.RequestCharge;
        
        // Log per-page RU
        _logger.LogDebug(
            "Query page: {Count} items, {RU} RU, Index: {IndexMetrics}",
            response.Count,
            response.RequestCharge,
            response.IndexMetrics);
    }
    
    // Log total query cost
    _logger.LogInformation(
        "GetCustomerOrders: {Total} items, {TotalRU} total RU",
        results.Count,
        totalRU);
    
    // Alert on expensive queries
    if (totalRU > 100)
    {
        _logger.LogWarning(
            "Expensive query detected: {TotalRU} RU for {Count} items",
            totalRU, results.Count);
    }
    
    return results;
}
```

```csharp
// Middleware to track all operations
public class CosmosDbMetricsHandler : RequestHandler
{
    private readonly IMetricTracker _metrics;
    
    public override async Task<ResponseMessage> SendAsync(
        RequestMessage request, 
        CancellationToken cancellationToken)
    {
        var sw = Stopwatch.StartNew();
        var response = await base.SendAsync(request, cancellationToken);
        sw.Stop();
        
        _metrics.TrackDependency(
            "CosmosDB",
            request.RequestUri.ToString(),
            sw.Elapsed,
            response.IsSuccessStatusCode,
            new Dictionary<string, string>
            {
                { "RU", response.Headers.RequestCharge.ToString() },
                { "StatusCode", response.StatusCode.ToString() }
            });
        
        return response;
    }
}

// Register handler
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    CustomHandlers = { new CosmosDbMetricsHandler(_metrics) }
});
```

### Node.js / TypeScript (@azure/cosmos v4)

Every `@azure/cosmos` operation exposes `requestCharge` as a top-level numeric property on the response. Capture it on every call — point reads, queries, writes, and bulk operations.

**Incorrect (discarding requestCharge — no visibility into cost):**

```typescript
// ❌ requestCharge available but never captured
const { resource } = await container.item(orderId, userId).read();
return resource;
// Is this costing 1 RU or 100 RU? Unknown!
```

**Correct (capturing requestCharge on reads and writes):**

```typescript
import { Container, FeedResponse } from '@azure/cosmos';

// ✅ Point read — capture requestCharge
export async function getOrder(container: Container, id: string, userId: string) {
  const response = await container.item(id, userId).read();
  logger.debug({
    op: 'ReadItem',
    container: container.id,
    ru: response.requestCharge,
    statusCode: response.statusCode,
    activityId: response.activityId,
  }, 'cosmos.readItem');
  return response.resource;
}

// ✅ Write — create/upsert/replace/patch/delete all expose requestCharge
export async function createOrder(container: Container, order: Order) {
  const response = await container.items.create(order);
  logger.debug({ op: 'CreateItem', ru: response.requestCharge }, 'cosmos.createItem');
  return response.resource;
}
```

**Correct (accumulating RU across query pages — single-page tracking undercounts paged results):**

```typescript
// ✅ Query — sum requestCharge across all pages
export async function getCustomerOrders(container: Container, userId: string) {
  const iterator = container.items.query<OrderSummary>({
    query: 'SELECT c.id, c.userId, c.status, c.total, c.createdAt FROM c WHERE c.userId = @u ORDER BY c.createdAt DESC',
    parameters: [{ name: '@u', value: userId }],
  }, { partitionKey: userId });

  const results: OrderSummary[] = [];
  let totalRU = 0;

  while (iterator.hasMoreResults()) {
    const page: FeedResponse<OrderSummary> = await iterator.fetchNext();
    results.push(...page.resources);
    totalRU += page.requestCharge;
  }

  logger.info({ op: 'Query', container: container.id, count: results.length, totalRU }, 'cosmos.query.total');
  if (totalRU > 100) {
    logger.warn({ totalRU, count: results.length }, 'cosmos.query.expensive');
  }
  return results;
}
```

**`requestCharge` API surface in `@azure/cosmos` v4:**

| Operation | Response type | RU property |
|-----------|---------------|-------------|
| `container.item(id, pk).read()` | `ItemResponse<T>` | `response.requestCharge` |
| `container.items.create(doc)` | `ItemResponse<T>` | `response.requestCharge` |
| `container.items.upsert(doc)` | `ItemResponse<T>` | `response.requestCharge` |
| `container.item(id, pk).replace(doc)` | `ItemResponse<T>` | `response.requestCharge` |
| `container.item(id, pk).patch(ops)` | `ItemResponse<T>` | `response.requestCharge` |
| `container.item(id, pk).delete()` | `ItemResponse<T>` | `response.requestCharge` |
| `container.items.query(...).fetchAll()` | `FeedResponse<T>` | `response.requestCharge` |
| `container.items.query(...).fetchNext()` | `FeedResponse<T>` per page | sum across pages |
| `container.items.bulk(ops)` | `OperationResponse[]` | `op.requestCharge` per operation |

Azure Monitor queries for RU analysis:
```kusto
// Top expensive operations
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| summarize TotalRU = sum(requestCharge_s) by OperationName
| order by TotalRU desc

// RU per partition key (detect hot partitions)
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| summarize TotalRU = sum(requestCharge_s) by partitionKey_s
| order by TotalRU desc
```

Reference: [Monitor RU/s](https://learn.microsoft.com/azure/cosmos-db/monitor-request-unit-usage)

### 1.5 Alert on Throttling (429s)

**Impact: HIGH** (prevents silent failures)

## Alert on Throttling (429s)

Set up alerts for HTTP 429 (Request Rate Too Large) errors. Throttling indicates your application is exceeding provisioned throughput.

**Incorrect (ignoring throttling):**

```csharp
// SDK retries silently, application seems "slow" but no alerts
public async Task<Order> GetOrder(string orderId, string customerId)
{
    // SDK retries 429s automatically (up to 9 times by default)
    // But you have no visibility into this happening!
    return await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
    // Users experience slow responses, you see nothing in logs
}
```

**Correct (tracking and alerting on throttling):**

```csharp
// Option 1: Track via exception handling
public async Task<Order> GetOrder(string orderId, string customerId)
{
    try
    {
        var response = await _container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
        return response.Resource;
    }
    catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.TooManyRequests)
    {
        // This fires only after ALL retries exhausted
        _logger.LogError(
            "Throttled after max retries! RetryAfter: {RetryAfter}s, Diagnostics: {Diagnostics}",
            ex.RetryAfter?.TotalSeconds,
            ex.Diagnostics?.ToString());
        
        _metrics.IncrementCounter("CosmosDB.ThrottledRequests");
        throw;
    }
}

// Option 2: Custom handler to track all 429s (even those retried)
public class ThrottlingTracker : RequestHandler
{
    private readonly ILogger _logger;
    private readonly IMetricTracker _metrics;
    
    public override async Task<ResponseMessage> SendAsync(
        RequestMessage request, 
        CancellationToken cancellationToken)
    {
        var response = await base.SendAsync(request, cancellationToken);
        
        if (response.StatusCode == HttpStatusCode.TooManyRequests)
        {
            _logger.LogWarning(
                "429 Throttled: {Uri}, RetryAfter: {RetryAfter}",
                request.RequestUri,
                response.Headers.RetryAfter);
            
            _metrics.IncrementCounter("CosmosDB.429.Total");
        }
        
        return response;
    }
}

// Register handler
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    CustomHandlers = { new ThrottlingTracker(_logger, _metrics) }
});
```

```csharp
// Azure Monitor alert rule for throttling
// Create alert in Azure Portal or via ARM:
{
    "type": "Microsoft.Insights/metricAlerts",
    "properties": {
        "criteria": {
            "odata.type": "Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria",
            "allOf": [
                {
                    "name": "TotalRequests429",
                    "metricName": "TotalRequests",
                    "dimensions": [
                        {
                            "name": "StatusCode",
                            "operator": "Include",
                            "values": ["429"]
                        }
                    ],
                    "operator": "GreaterThan",
                    "threshold": 0,
                    "timeAggregation": "Total"
                }
            ]
        },
        "actions": [
            {
                "actionGroupId": "/subscriptions/.../actionGroups/ops-team"
            }
        ],
        "severity": 2,
        "windowSize": "PT5M",
        "evaluationFrequency": "PT1M"
    }
}
```

```kusto
// Log Analytics query for throttling analysis
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.DOCUMENTDB"
| where statusCode_s == "429"
| summarize ThrottledCount = count() by 
    bin(TimeGenerated, 5m),
    partitionKeyRangeId_s,
    OperationName
| order by TimeGenerated desc

// Identify which partition keys are throttling
AzureDiagnostics
| where statusCode_s == "429"
| summarize Count = count() by partitionKey_s
| order by Count desc
| take 10
```

Response to throttling:
1. **Immediate**: SDK retries automatically
2. **Short-term**: Scale up throughput (manual or autoscale)
3. **Long-term**: 
   - Optimize queries to use less RU
   - Review partition key for hot partitions
   - Consider autoscale for variable workloads

Reference: [Monitor throttling](https://learn.microsoft.com/azure/cosmos-db/monitor-normalized-request-units)

---

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
