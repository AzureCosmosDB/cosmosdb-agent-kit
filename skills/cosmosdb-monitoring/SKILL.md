---
name: cosmosdb-monitoring
description: |
  Azure Cosmos DB monitoring and diagnostics best practices: RU consumption
  tracking, P99 latency monitoring, throttling alerts, Azure Monitor integration,
  and diagnostic logging.
  USE FOR: Cosmos DB monitoring, RU consumption, request units tracking,
  P99 latency, throttling alerts, 429 monitoring, Azure Monitor, diagnostic logs,
  metrics, alerts, performance monitoring, troubleshooting, observability.
  DO NOT USE FOR: SDK diagnostics logging (use cosmosdb-sdk),
  throughput right-sizing (use cosmosdb-throughput).

license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.0.0"
---

# Azure Cosmos DB Monitoring & Diagnostics

Best practices for monitoring Azure Cosmos DB performance and diagnosing issues.

## When to Apply

Reference these guidelines when:
- Setting up monitoring for Cosmos DB accounts
- Tracking RU consumption and latency
- Configuring alerts for throttling
- Enabling diagnostic logging
- Integrating with Azure Monitor

## Rules

- [monitoring-ru-consumption](rules/monitoring-ru-consumption.md) - Track RU consumption
- [monitoring-latency](rules/monitoring-latency.md) - Monitor P99 latency
- [monitoring-throttling](rules/monitoring-throttling.md) - Alert on throttling
- [monitoring-azure-monitor](rules/monitoring-azure-monitor.md) - Integrate Azure Monitor
- [monitoring-diagnostic-logs](rules/monitoring-diagnostic-logs.md) - Enable diagnostic logging

## Full Compiled Document

For all rules expanded: [AGENTS.md](AGENTS.md)
