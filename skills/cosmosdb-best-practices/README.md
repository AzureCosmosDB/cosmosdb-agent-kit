# cosmosdb-best-practices

Azure Cosmos DB best practices for AI coding agents, following the [Agent Skills](https://agentskills.io) specification.

## Overview

This skill currently contains 127 rules across 13 categories and serves as the broad, catch-all Cosmos DB skill.

This monolith skill remains available for broad prompts while focused skills (for example SDK, query, indexing, and security) are also shipped for narrower prompts.

| Category | Impact | Description |
|----------|--------|-------------|
| Data Modeling | CRITICAL | Document structure and embedding vs referencing patterns |
| Partition Key Design | CRITICAL | Key selection for scalability and query efficiency |
| Query Optimization | HIGH | Minimize RU consumption and latency |
| SDK Best Practices | HIGH | Connection management and error handling |
| Indexing Strategies | MEDIUM-HIGH | Index configuration for cost/performance balance |
| Throughput & Scaling | MEDIUM | RU provisioning and scaling strategies |
| Global Distribution | MEDIUM | Multi-region configuration |
| Monitoring & Diagnostics | LOW-MEDIUM | Observability and troubleshooting |
| Design Patterns | HIGH | Reusable Cosmos DB architecture patterns |
| Developer Tooling | MEDIUM | Emulator and extension guidance for day-to-day work |
| Vector Search | HIGH | Semantic search and RAG-related configuration |
| Full-Text Search | HIGH | Keyword matching, BM25 ranking, and hybrid search configuration |
| Security | HIGH | Authentication, RBAC, network isolation, and backup configuration |

## Installation

### Using add-skill (recommended)

```bash
npx skills add AzureCosmosDB/cosmosdb-agent-kit
```

### Manual Installation

```bash
git clone https://github.com/AzureCosmosDB/cosmosdb-agent-kit.git
cp -r cosmosdb-agent-kit/skills/cosmosdb-best-practices ~/.copilot/skills/
```

### Claude Code

```bash
cp -r skills/cosmosdb-best-practices ~/.claude/skills/
```

## File Structure

```text
skills/cosmosdb-best-practices/
|- SKILL.md
|- AGENTS.md
|- metadata.json
|- README.md
`- rules/
   |- _sections.md
   |- _template.md
   |- model-*.md
   |- partition-*.md
   |- query-*.md
   |- sdk-*.md
   |- index-*.md
   |- throughput-*.md
   |- global-*.md
   |- monitoring-*.md
   |- pattern-*.md
   |- tooling-*.md
   |- vector-*.md
   |- fts-*.md
   `- security-*.md
```

## How It Works

Agents typically use SKILL.md for routing and AGENTS.md for compiled guidance.

- SKILL.md: routing cues and high-level intent matching
- rules/: source-of-truth rule authoring files
- AGENTS.md: generated, consolidated runtime-friendly document

## Build and Validate

Compile this skill:

```bash
npm run build:skill -- cosmosdb-best-practices
```

Validate this skill:

```bash
npm run validate:skill -- cosmosdb-best-practices
```

Compile all skills:

```bash
npm run build
```

Validate all skills:

```bash
npm run validate
```

## Contributing Notes

When adding or editing rules in this skill:

1. Start from rules/_template.md.
2. Keep required frontmatter fields: title, impact, impactDescription, tags.
3. Include both Incorrect and Correct sections with code blocks.
4. Rebuild AGENTS.md after rule changes.
5. Run validation before opening a PR.

For broader repository contribution rules, see [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Compatibility

This skill follows the [Agent Skills](https://agentskills.io) standard and is compatible with major hosts, including GitHub Copilot, Claude Code, Gemini CLI, and Codex-compatible workflows.

## License

MIT
