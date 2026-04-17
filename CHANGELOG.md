# Changelog

Improvements to the `cosmosdb-best-practices` skill (rules and compiled `AGENTS.md`). Harness, docs site, and CI-only changes are intentionally omitted.

## 2026-04-07 — Rule clarifications ([#108](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/108))

Expanded and clarified five existing rules so agents apply them correctly:

- `partition-hierarchical` — clearer guidance on when to use hierarchical partition keys.
- `query-pagination` — expanded pagination patterns and anti-patterns.
- `query-top-literal` — reworked `TOP` vs parameterized-limit guidance.
- `sdk-java-cosmos-config` — added missing config knobs.
- `sdk-spring-data-annotations` — minor correctness fix.
- Also tightened `scripts/validate.js` to catch malformed frontmatter.

## 2026-04-03 — +10 rules, new Full-Text Search category ([#95](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/95))

- Added 4 new SDK rules (4.21–4.24).
- Added a brand-new **Full-Text Search** category with 6 rules (12.1–12.6) covering the capability flag, `fullTextPolicy`, `fullTextIndexes`, BM25 ranking, keyword matching, and hybrid queries.
- Skill now totals 89 rules across 12 categories.

## 2026-04-02 — Cascade delete/update guidance ([#208](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/208))

- Extended `model-denormalize-reads` with explicit cascade semantics:
  - Deleting a source document must also delete all derived/embedded copies in other containers.
  - Updating a field used as a partition key in derived containers requires delete-and-recreate in the new partition.
- Added Python and C# examples for both patterns.
- Gap was surfaced by the batch-191 gaming-leaderboard evaluation.

---

## How to update

When a PR changes anything under `skills/cosmosdb-best-practices/` (rules or compiled `AGENTS.md`), add an entry at the top:

```
## YYYY-MM-DD — short summary ([#NNN](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/pull/NNN))

- What changed / why it matters.
```
