---
name: cosmosdb-throughput
description: |
  Azure Cosmos DB throughput and scaling best practices: autoscale for variable
  workloads, right-sizing provisioned throughput, serverless for dev/test,
  burst capacity, and container vs database throughput allocation.
  USE FOR: Cosmos DB autoscale, provisioned throughput, serverless, burst capacity,
  RU/s sizing, container throughput, database throughput, cost optimization,
  over-provisioning, under-provisioning, throttling prevention.
  DO NOT USE FOR: RU consumption monitoring (use cosmosdb-monitoring),
  partition key design (use cosmosdb-partition-key).

license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.0.0"
---

# Azure Cosmos DB Throughput & Scaling

Best practices for provisioning and managing throughput in Azure Cosmos DB.

## When to Apply

Reference these guidelines when:
- Choosing between autoscale and provisioned throughput
- Right-sizing RU/s for workloads
- Evaluating serverless vs provisioned
- Setting up container vs database level throughput

## Rules

- [throughput-autoscale](rules/throughput-autoscale.md) - Use autoscale for variable workloads
- [throughput-right-size](rules/throughput-right-size.md) - Right-size provisioned throughput
- [throughput-serverless](rules/throughput-serverless.md) - Consider serverless for dev/test
- [throughput-burst](rules/throughput-burst.md) - Understand burst capacity
- [throughput-container-vs-database](rules/throughput-container-vs-database.md) - Choose allocation level wisely

## Full Compiled Document

For all rules expanded: [AGENTS.md](AGENTS.md)
