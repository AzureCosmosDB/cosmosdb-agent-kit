---
name: cosmosdb-global-distribution
description: |
  Azure Cosmos DB global distribution best practices: multi-region writes,
  consistency levels, conflict resolution, automatic failover, read regions,
  and zone redundancy for high availability.
  USE FOR: Cosmos DB multi-region, consistency levels, strong consistency,
  bounded staleness, session consistency, eventual consistency, conflict resolution,
  automatic failover, read regions, zone redundancy, global replication,
  disaster recovery, geo-redundancy, multi-master.
  DO NOT USE FOR: SDK preferred regions (use cosmosdb-sdk),
  monitoring (use cosmosdb-monitoring).

license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.0.0"
---

# Azure Cosmos DB Global Distribution

Best practices for configuring multi-region distribution and consistency in Azure Cosmos DB.

## When to Apply

Reference these guidelines when:
- Configuring multi-region writes
- Choosing a consistency level
- Setting up conflict resolution policies
- Planning for disaster recovery and failover
- Adding read regions for global low-latency access

## Rules

- [global-multi-region](rules/global-multi-region.md) - Configure multi-region writes
- [global-consistency](rules/global-consistency.md) - Choose appropriate consistency level
- [global-conflict-resolution](rules/global-conflict-resolution.md) - Implement conflict resolution
- [global-failover](rules/global-failover.md) - Configure automatic failover
- [global-read-regions](rules/global-read-regions.md) - Add read regions near users
- [global-zone-redundancy](rules/global-zone-redundancy.md) - Enable zone redundancy for HA

## Full Compiled Document

For all rules expanded: [AGENTS.md](AGENTS.md)
