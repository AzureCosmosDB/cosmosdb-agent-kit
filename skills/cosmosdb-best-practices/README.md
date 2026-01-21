# cosmosdb-best-practices

Azure Cosmos DB best practices for AI coding agents, following the [Agent Skills](https://agentskills.io) specification.

## Overview

This skill contains 45+ rules across 8 categories, ordered by impact:

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

## Installation

### Using add-skill (Recommended)

```bash
npx add-skill AzureCosmosDB/cosmosdb-agent-kit
```

This installs the skill into your `.copilot/skills/` directory.

### Manual Installation

Clone this repository and copy the skill:

```bash
git clone https://github.com/AzureCosmosDB/cosmosdb-agent-kit.git
cp -r cosmosdb-agent-kit/skills/cosmosdb-best-practices ~/.copilot/skills/
```

### Claude Code

```bash
cp -r skills/cosmosdb-best-practices ~/.claude/skills/
```

## File Structure

```
skills/cosmosdb-best-practices/
├── SKILL.md              # Skill definition (triggers agent activation)
├── AGENTS.md             # Compiled rules (what agents read)
├── metadata.json         # Version and metadata
├── README.md             # This file
└── rules/
    ├── _sections.md      # Section definitions
    ├── _template.md      # Template for new rules
    ├── model-*.md        # Data modeling rules (6)
    ├── partition-*.md    # Partition key rules (6)
    ├── query-*.md        # Query optimization rules (6)
    ├── sdk-*.md          # SDK best practices rules (6)
    ├── index-*.md        # Indexing rules (5)
    ├── throughput-*.md   # Throughput rules (5)
    ├── global-*.md       # Global distribution rules (5)
    └── monitoring-*.md   # Monitoring rules (5)
```

## How It Works

When you're working on Cosmos DB code, AI coding agents (Claude Code, GitHub Copilot, Gemini CLI, etc.) that support Agent Skills will automatically:

1. Detect the skill based on `SKILL.md` triggers
2. Load `AGENTS.md` rules into context
3. Apply best practices while generating or reviewing code

## Compiling Rules

To rebuild `AGENTS.md` from individual rules:

```bash
npm run build
# or
node scripts/compile.js
```

## Contributing

### Adding a New Rule

1. Copy `rules/_template.md` to a new file in the appropriate category
2. Fill in the frontmatter (title, impact, impactDescription, tags)
3. Add Incorrect and Correct code examples
4. Run `npm run build` to recompile AGENTS.md
5. Submit a pull request

### Rule Format

```markdown
---
title: Rule Title
impact: HIGH
impactDescription: Brief explanation of why this matters
tags: [relevant, tags, here]
---

**Incorrect (brief reason):**

```csharp
// Anti-pattern code
```

**Correct (brief reason):**

```csharp
// Best practice code
```
```

### Impact Levels

- **CRITICAL**: Prevents data loss, outages, or unrecoverable issues
- **HIGH**: Significant performance or cost impact
- **MEDIUM-HIGH**: Notable optimization opportunity
- **MEDIUM**: Recommended best practice
- **LOW-MEDIUM**: Nice to have
- **LOW**: Minor optimization

## Compatibility

This skill follows the [Agent Skills](https://agentskills.io) open standard and is compatible with:

- Claude Code
- VS Code (GitHub Copilot)
- GitHub.com
- Gemini CLI
- OpenCode
- Factory
- OpenAI Codex

## License

MIT

## Acknowledgments

- Inspired by [Vercel's React Best Practices](https://vercel.com/blog/introducing-react-best-practices)
- Based on the [Agent Skills](https://agentskills.io) specification from Anthropic
- Azure Cosmos DB team for [official documentation](https://learn.microsoft.com/azure/cosmos-db/)
