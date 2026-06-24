# cosmosdb-agent-kit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Good First Issues](https://img.shields.io/github/issues/AzureCosmosDB/cosmosdb-agent-kit/good-first-issue?color=7057ff&label=good%20first%20issues)](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
[![Discussions](https://img.shields.io/github/discussions/AzureCosmosDB/cosmosdb-agent-kit)](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/discussions)

A collection of skills for AI coding agents working with Azure Cosmos DB. Skills are packaged instructions and scripts that extend agent capabilities.

![agent-kit-cosmosdb (1)](https://github.com/user-attachments/assets/0a2c2e5f-62ee-4741-adda-9af790980761)

Skills follow the [Agent Skills](https://agentskills.io/) format and the kit ships with plugin manifests for Claude Code, Codex, Cursor, Gemini CLI, and GitHub Copilot.

## Available Skills

The repository currently ships a monolith skill plus focused topic skills.

| Skill | Focus | Rules |
|-------|-------|-------|
| [cosmosdb-best-practices](skills/cosmosdb-best-practices/) | Full Cosmos DB guidance (catch-all) | 127 |
| [cosmosdb-data-modeling](skills/cosmosdb-data-modeling/) | Data modeling | 11 |
| [cosmosdb-partition-key](skills/cosmosdb-partition-key/) | Partition key design | 8 |
| [cosmosdb-query-optimization](skills/cosmosdb-query-optimization/) | Query optimization | 12 |
| [cosmosdb-sdk](skills/cosmosdb-sdk/) | SDK patterns and framework integration | 40 |
| [cosmosdb-indexing](skills/cosmosdb-indexing/) | Indexing policy and composite indexes | 7 |
| [cosmosdb-throughput](skills/cosmosdb-throughput/) | Throughput and scaling | 5 |
| [cosmosdb-global-distribution](skills/cosmosdb-global-distribution/) | Multi-region and consistency | 6 |
| [cosmosdb-monitoring](skills/cosmosdb-monitoring/) | Monitoring and diagnostics | 5 |
| [cosmosdb-design-patterns](skills/cosmosdb-design-patterns/) | Architecture and app patterns | 14 |
| [cosmosdb-tooling](skills/cosmosdb-tooling/) | Emulator and developer tooling | 2 |
| [cosmosdb-vector-search](skills/cosmosdb-vector-search/) | Vector search guidance | 6 |
| [cosmosdb-full-text-search](skills/cosmosdb-full-text-search/) | Full-text search guidance | 6 |
| [cosmosdb-security](skills/cosmosdb-security/) | Security and hardening | 5 |

## Current Structure

The repository ships both the monolith and focused skills:

- The monolith skill is available as a broad catch-all.
- Focused skills are available for narrower prompts and lower-context loading.
- Each skill is self-contained and compiles its own AGENTS.md from its own rules directory.

## Installation

### APM (recommended: all harnesses at once)

```bash
apm install AzureCosmosDB/cosmosdb-agent-kit
```

Installs the skill catalog across GitHub Copilot, Claude Code, Cursor, Codex, and Gemini in one command.

### Universal one-liner (all agents)

```bash
npx skills add AzureCosmosDB/cosmosdb-agent-kit
```

### GitHub Copilot CLI

```text
/plugin marketplace add AzureCosmosDB/cosmosdb-agent-kit
/plugin install cosmosdb@cosmosdb-agent-kit
```

### Claude Code

```text
/plugin install cosmosdb@claude-plugins-official
```

### Gemini CLI

```bash
gemini extensions install https://github.com/AzureCosmosDB/cosmosdb-agent-kit
```

### Per-agent plugin directories

| Agent | Manifest |
|-------|----------|
| Claude Code | .claude-plugin/plugin.json |
| OpenAI Codex | .codex-plugin/plugin.json |
| Cursor | .cursor-plugin/plugin.json |
| Gemini CLI | gemini-extension.json + GEMINI.md |
| GitHub Copilot | skills/*/SKILL.md (auto-detected) |

## Build and Validate

Compile all skills:

```bash
npm run build
```

Compile one skill:

```bash
npm run build:skill -- cosmosdb-sdk
```

Validate all rules:

```bash
npm run validate
```

Validate one skill:

```bash
npm run validate:skill -- cosmosdb-sdk
```

## Usage

Skills are automatically available once installed. The agent will choose the most relevant skill for the prompt.

Example prompts:

```text
Review my Cosmos DB data model
```

```text
Help me choose a partition key for my orders collection
```

```text
Optimize this Cosmos DB query
```

```text
Set up vector search for my RAG app in Cosmos DB
```

## Skill Package Layout

Each skill contains:

- SKILL.md: trigger and guidance index
- AGENTS.md: compiled guidance output
- rules/: individual rule files (source of truth)
- metadata.json: skill metadata and version info

## Evaluation (Local)

This project uses [Waza](https://github.com/microsoft/waza) for local evaluation runs.

```bash
# Install waza (one-time)
irm https://raw.githubusercontent.com/microsoft/waza/main/install.ps1 | iex   # Windows
curl -fsSL https://raw.githubusercontent.com/microsoft/waza/main/install.sh | bash  # macOS/Linux

# Run evaluations
waza run evals/cosmosdb-best-practices/eval.yaml -v

# Check skill readiness
waza check skills/cosmosdb-best-practices
```

## Website

A project website is available in docs/ and is designed for GitHub Pages publishing.

- Main page: docs/index.html
- Styles: docs/styles.css
- Interactions + survey flow: docs/app.js

Preview locally:

```bash
python -m http.server 8080 --directory docs
```

Then open http://localhost:8080.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

Looking for a place to help? Check [good first issues](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) or join [Discussions](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/discussions).

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a dated history of updates.

## License

MIT
