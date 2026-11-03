# Azure Cosmos DB Fault Testing

An interactive skill for scoped Cosmos DB fault-testing and recovery exercises.
Ask your agent: **"Use cosmosdb-fault-testing to plan a PPAF drill."** The agent
collects missing inputs, explains cost and disruption risks, requests approval,
and guides execution and verified cleanup. Reading this overview is not required
to use the skill.

## Supported scenarios

| Scenario | Scope |
|----------|-------|
| PPAF | Service-side per-partition automatic failover on an existing eligible account, with an approved workload in a supported SDK |

PPAF is the first scenario. Account-wide failover, resource provisioning, and
SDK-local fault injection are not currently supported.

## Install

```bash
npx skills add AzureCosmosDB/cosmosdb-agent-kit
```

Alternatively, copy this directory into `~/.copilot/skills/` or
`~/.claude/skills/`.

## Package

- [SKILL.md](SKILL.md): entry point and interactive workflow.
- [references/ppaf.md](references/ppaf.md): PPAF-specific commands and safeguards.
- [scripts/EnableDisableChaosFault.ps1](scripts/EnableDisableChaosFault.ps1):
  bundled upstream snapshot; no download is required for the default path.
- [Script provenance](references/script-provenance.md): source revision,
  SHA-256, license, limitations, and optional update procedure.

Workload traffic consumes RUs and may affect availability and charges. The
agent requires explicit scope, budget, recovery, and production-impact approval;
installing or invoking the skill is not permission to inject faults.

This procedural skill has no generated `AGENTS.md`. Explanation-only scenarios
and offline bundle tests live in `evals/cosmosdb-fault-testing/`. They do not
authorize live Azure execution.
