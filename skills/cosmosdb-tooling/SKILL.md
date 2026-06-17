---
name: cosmosdb-tooling
description: |
  Azure Cosmos DB developer tooling guidance: VS Code extension for data inspection
  and management, and Cosmos DB Emulator setup for local development and testing.
  USE FOR: Cosmos DB VS Code extension, Cosmos DB Emulator, local development,
  data inspection, container management, emulator setup, dev/test environment.
  DO NOT USE FOR: SDK emulator SSL configuration (use cosmosdb-sdk),
  production deployment, CI/CD pipelines.

license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.0.0"
---

# Azure Cosmos DB Developer Tooling

Guidance for developer tools that improve local development and data inspection workflows.

## When to Apply

Reference these guidelines when:
- Setting up local development with the Cosmos DB Emulator
- Using the VS Code extension for data inspection
- Configuring developer tooling for Cosmos DB

## Rules

- [tooling-vscode-extension](rules/tooling-vscode-extension.md) - Use the VS Code extension for inspection and management
- [tooling-emulator-setup](rules/tooling-emulator-setup.md) - Use the Emulator for local development and testing

## Full Compiled Document

For all rules expanded: [AGENTS.md](AGENTS.md)
