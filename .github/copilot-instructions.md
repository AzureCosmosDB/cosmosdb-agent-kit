# Copilot Coding Agent Instructions

This file tells Copilot how to work with the cosmosdb-agent-kit repository.

## Repository Purpose

This repository contains AI coding agent skills (best practice rules) for Azure Cosmos DB,
plus a testing framework that measures how well agents apply those skills when building apps.

## Key Directories

- `skills/cosmosdb-best-practices/` — The Cosmos DB best practices skill (rules + compiled AGENTS.md)
- `testing-v2/` — The testing framework (scenarios, contracts, tests, harness)
- `scripts/` — Build scripts (compile.js compiles rules into AGENTS.md)

## When Assigned to an Issue

### "Run Test Iteration" issues

Follow the **Agent Instructions** section in the issue body exactly. The key steps are:
1. Read `skills/cosmosdb-best-practices/AGENTS.md` (the full rules — apply them all)
2. Read the scenario's `SCENARIO.md` and `api-contract.yaml`
3. Generate code that implements the contract exactly
4. Create `iteration-config.yaml` in the iteration folder
5. Open a PR

### "Create New Scenario" issues

Follow the recipe in `testing-v2/CREATE-SCENARIO.md` exactly. Use
`testing-v2/scenarios/gaming-leaderboard/` as the format reference for all files.

## When Asked to Evaluate Test Results (PR comment)

Follow the recipe in `testing-v2/EVALUATE.md` exactly. The key steps are:
1. Read the test results from the PR comment above
2. Read the scenario's `api-contract.yaml` and the generated code
3. Classify each failure (contract violation, missing rule, unclear rule, SDK quirk)
4. Create or update rules in `skills/cosmosdb-best-practices/rules/`
5. Run `npm run build` to regenerate AGENTS.md
6. Update `testing-v2/IMPROVEMENTS-LOG.md`
7. Commit everything to the PR branch

## Build Commands

```bash
# Compile rules into AGENTS.md (run after adding/changing rules)
npm run build

# Validate rule files
npm run validate
```

## Conventions

- Rule files: `skills/cosmosdb-best-practices/rules/<prefix>-<description>.md`
- Rule prefixes: model-, partition-, query-, sdk-, index-, throughput-, global-, monitoring-, pattern-
- All API field names: camelCase
- Test data: hardcoded/deterministic, never random
- Iteration folders: `testing-v2/scenarios/<scenario>/iterations/iteration-<NNN>-<language>/`
