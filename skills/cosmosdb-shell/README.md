# Cosmos DB Shell Skill

Workflow guidance for agents using Cosmos DB Shell and its MCP tools to explore
data and carry out user-requested operations. Adapted from the Shell skill in the
[Azure Cosmos DB VS Code extension](https://github.com/microsoft/vscode-cosmosdb/tree/dev/mkrueger/cosmosdb-shell-skill/skills/cosmosdb-shell).

## Installation

Use the kit's skill installer and select `cosmosdb-shell`:

```bash
npx skills add AzureCosmosDB/cosmosdb-agent-kit
```

Alternatively, copy this directory to your agent's skill location:

**Claude Code:**

```bash
cp -r skills/cosmosdb-shell ~/.claude/skills/
```

**GitHub Copilot / VS Code:**

```bash
cp -r skills/cosmosdb-shell ~/.copilot/skills/
```

## Prerequisites

Install [Cosmos DB Shell](https://learn.microsoft.com/azure/cosmos-db/shell/overview)
and configure its MCP server in your agent client to execute operations. Installing
this skill does not install the shell, configure MCP, or grant database access.
Without MCP, the agent can explain commands and provide manual instructions.

VS Code users with the Azure Cosmos DB extension can use its Shell integration and
enable `cosmosDB.shell.MCP.enabled`. Other clients configure the Shell MCP server
using their own integration mechanism.

## Example Requests

- "Use Cosmos DB Shell to list the databases on my current connection."
- "Use Cosmos DB Shell to show five item IDs from database demo, container orders."
- "Explain how to inspect this container's TTL with Cosmos DB Shell, without changing it."
- "Why are the Cosmos DB Shell MCP tools unavailable in VS Code?"

## Scope

The skill covers connection and target verification, bounded reads, write safety,
confirmation handling, and credentials. The Shell server must enforce authorization
and required confirmations; skill instructions are not a security boundary.

For query and data-model design, use the kit's `cosmosdb-best-practices` skill.
VS Code query-editor skills are optional integrations, not dependencies of this skill.

This is a workflow skill, not a rule collection. Its instructions live directly in
`SKILL.md`; there is no `rules/` directory or generated `AGENTS.md`. The kit's rule
validator and compiler skip workflow-only skills.
