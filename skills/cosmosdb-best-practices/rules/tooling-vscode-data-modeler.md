---
title: Consider VS Code Data Modeler for guided NoSQL partition key exploration
impact: MEDIUM
impactDescription: makes partition key trade-offs and workload assumptions visible before resource creation
tags: tooling, vscode-extension, data-modeling, partition-key, preview
---

## Consider VS Code Data Modeler for Guided NoSQL Partition Key Exploration

When designing an Azure Cosmos DB for NoSQL application in VS Code, consider
the Azure Cosmos DB extension's **Data Modeler (Preview)** for guided partition
key exploration with GitHub Copilot. Use it to compare options, not as proof
that a design is optimal or validated. Routine browsing and inspection belong
to the [existing VS Code extension workflow](tooling-vscode-extension.md).

**Incorrect (treating a recommendation as a deployment decision):**

```text
The first suggested partition key is guaranteed optimal and will save RUs.
Deploy it now without reviewing the workload assumptions or asking permission.
```

**Correct (offer a conditional workflow with a separate deployment choice):**

```text
For this NoSQL design in VS Code, Data Modeler (Preview) could help compare
partition key options if available GitHub Copilot models and AI features are
enabled. I will not install anything or enable settings without your agreement.

1. Open Try Data Modeler from Account Overview or an account in Explorer,
   or use Data Modeling Wizard in the Command Palette.
2. Start from a workload template or supply your own schemas, common queries,
   and scale estimates.
3. Compare the single-path partition-key recommendations, query routing,
   and warnings. Review the workload assumptions before creating resources.
4. Choose separately whether to export editable Bicep, Terraform, or C# SDK
   code for review, or to deploy selected databases and containers later.
   Deployment needs resource-creation permissions, may incur Azure charges,
   and does not upload documents. I will not deploy without explicit agreement.

For an explanation-only request, stop at the proposed workflow. If the modeler
is unavailable, continue with existing data modeling and partition key guidance.
```

Do not promise automatic optimality, model validation, RU savings, or
hierarchical partition-key recommendations from this workflow. Continue to
apply [partition key query-pattern guidance](partition-query-patterns.md)
when reviewing the assumptions; the tool does not replace modeling judgment.

Reference: [Azure Cosmos DB VS Code extension - Data Modeler](https://github.com/microsoft/vscode-cosmosdb/blob/d2bbc7212813147eeabbe0de3270546ebe383d44/README.md#data-modeler)
