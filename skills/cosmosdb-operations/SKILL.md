---
name: cosmosdb-operations
description: |
  Azure Cosmos DB operations, scaling, and security: throughput provisioning (autoscale vs manual, serverless for dev, RU estimation, bursts), global distribution (multi-region writes, read regions, failover, consistency levels, conflict resolution, zone redundancy), monitoring and diagnostics (RU consumption, throttling/429 alerts, P99 latency, Azure Monitor, diagnostic logs), and security (managed identity, disable key auth, RBAC least privilege, network restriction, continuous backup / point-in-time restore).
  USE FOR: provision RU/s, autoscale, serverless, multi-region writes, region failover, choose consistency level, alert on throttling, track P99 latency, push metrics to Azure Monitor, authenticate with managed identity, lock down to a VNet, RBAC, restore.
  DO NOT USE FOR: modeling, partition keys, indexing, queries (use cosmosdb-data-and-queries); SDK client code (use cosmosdb-sdk); vector/full-text search and AI agents (use cosmosdb-ai-and-search).
license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.0.0"
---

# Azure Cosmos DB Operations, Scaling & Security

Best practices for operating Azure Cosmos DB: throughput and scaling, global distribution and consistency, monitoring and diagnostics, and security hardening.

## When to Apply

Reference these guidelines when provisioning throughput, configuring global distribution, setting up monitoring, or hardening security for Azure Cosmos DB.

## Rules

### Throughput & Scaling

- [throughput-autoscale](rules/throughput-autoscale.md) - Use Autoscale for Variable Workloads
- [throughput-burst](rules/throughput-burst.md) - Understand Burst Capacity
- [throughput-container-vs-database](rules/throughput-container-vs-database.md) - Choose Container vs Database Throughput
- [throughput-right-size](rules/throughput-right-size.md) - Right-Size Provisioned Throughput
- [throughput-serverless](rules/throughput-serverless.md) - Consider Serverless for Dev/Test

### Global Distribution

- [global-conflict-resolution](rules/global-conflict-resolution.md) - Implement Conflict Resolution
- [global-consistency](rules/global-consistency.md) - Choose Appropriate Consistency Level
- [global-failover](rules/global-failover.md) - Configure Automatic Failover
- [global-multi-region](rules/global-multi-region.md) - Configure Multi-Region Writes
- [global-read-regions](rules/global-read-regions.md) - Add Read Regions Near Users
- [global-zone-redundancy](rules/global-zone-redundancy.md) - Configure Zone Redundancy for High Availability

### Monitoring & Diagnostics

- [monitoring-azure-monitor](rules/monitoring-azure-monitor.md) - Integrate Azure Monitor
- [monitoring-diagnostic-logs](rules/monitoring-diagnostic-logs.md) - Enable Diagnostic Logging
- [monitoring-latency](rules/monitoring-latency.md) - Monitor P99 Latency
- [monitoring-ru-consumption](rules/monitoring-ru-consumption.md) - Track RU Consumption
- [monitoring-throttling](rules/monitoring-throttling.md) - Alert on Throttling (429s)

### Security

- [security-continuous-backup](rules/security-continuous-backup.md) - Enable Continuous Backup for Point-in-Time Restore
- [security-disable-local-auth](rules/security-disable-local-auth.md) - Disable Local Authentication (Keys)
- [security-managed-identity](rules/security-managed-identity.md) - Use Managed Identity with DefaultAzureCredential
- [security-network-restrict](rules/security-network-restrict.md) - Restrict Network Access
- [security-rbac-least-privilege](rules/security-rbac-least-privilege.md) - Assign Minimum RBAC Roles with Narrow Scope
