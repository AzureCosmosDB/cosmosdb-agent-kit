# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Developer tooling guidance for Azure Cosmos DB: VS Code extension for inspection and management, and emulator setup for local development and testing.

---

## Table of Contents

1. [Developer Tooling](#1-developer-tooling) — **MEDIUM**
   - 1.1 [Use Azure Cosmos DB Emulator for local development and testing](#11-use-azure-cosmos-db-emulator-for-local-development-and-testing)
   - 1.2 [Use Azure Cosmos DB VS Code extension for routine inspection and management](#12-use-azure-cosmos-db-vs-code-extension-for-routine-inspection-and-management)

---

## 1. Developer Tooling

**Impact: MEDIUM**

### 1.1 Use Azure Cosmos DB Emulator for local development and testing

**Impact: MEDIUM** (prevents accidental cloud usage and speeds up local iteration)

## Use Azure Cosmos DB Emulator for Local Development and Testing

Prefer the Azure Cosmos DB Emulator for local development, exploratory testing, and repeatable developer workflows. It avoids cloud cost during local work, keeps feedback loops fast, and reduces the risk of accidentally using shared or production resources while iterating.

**Incorrect (local development against cloud resources by default):**

```yaml
# Local development profile
azure:
  cosmos:
    endpoint: https://my-prod-account.documents.azure.com:443/
    key: ${COSMOS_KEY}
```

**Correct (default local development to the emulator):**

```yaml
# Local development profile
azure:
  cosmos:
    endpoint: https://localhost:8081/
    key: C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
```

Run the emulator locally or in Docker, and keep production endpoints in environment-specific profiles or deployment configuration. For SDK-specific SSL and gateway-mode details, also apply the linked emulator configuration rules.

Related rules:
- `sdk-emulator-ssl`
- `sdk-local-dev-config`

Reference: [Use the Azure Cosmos DB Emulator for local development](https://learn.microsoft.com/azure/cosmos-db/emulator)

### 1.2 Use Azure Cosmos DB VS Code extension for routine inspection and management

**Impact: MEDIUM** (speeds up data inspection and reduces one-off scripts for routine tasks)

## Use Azure Cosmos DB VS Code Extension for Routine Inspection and Management

For day-to-day inspection tasks, prefer the Azure Cosmos DB VS Code extension over ad hoc scripts or direct SDK calls. The extension is faster for browsing accounts, querying containers, inspecting items, and validating local-versus-cloud data without introducing disposable code into the repository.

**Incorrect (writing one-off code for routine inspection):**

```bash
# Need to inspect a few items or verify a container layout
# Result: write a throwaway script just to browse data
node inspect-cosmos.js
python list_items.py
```

**Correct (use the extension for routine inspection first):**

```text
1. Install the Azure Cosmos DB VS Code extension:
   ms-azuretools.vscode-cosmosdb
2. Use the extension to connect to the target account or emulator.
3. Browse databases, containers, and items directly in VS Code.
4. Run exploratory queries there before deciding whether permanent code is needed.
```

Use code only when the task is repeatable, automated, or belongs in the product. For one-off inspection, prefer the tool built for inspection.

Reference: [Azure Cosmos DB extension for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-cosmosdb)

---

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
