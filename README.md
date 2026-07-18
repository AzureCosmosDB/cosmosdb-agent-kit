# cosmosdb-agent-kit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Good First Issues](https://img.shields.io/github/issues/AzureCosmosDB/cosmosdb-agent-kit/good-first-issue?color=7057ff&label=good%20first%20issues)](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
[![Discussions](https://img.shields.io/github/discussions/AzureCosmosDB/cosmosdb-agent-kit)](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/discussions)

A collection of skills for AI coding agents working with Azure Cosmos DB. Skills are packaged instructions and scripts that extend agent capabilities.

![agent-kit-cosmosdb (1)](https://github.com/user-attachments/assets/0a2c2e5f-62ee-4741-adda-9af790980761)

Skills follow the [Agent Skills](https://agentskills.io/) format and the kit ships with plugin manifests for **Claude Code**, **Codex**, **Cursor**, **Gemini CLI**, and **GitHub Copilot**.

## Where this works best

This agent kit is designed for **progressive (on-demand) skill delivery**: hosts that load a relevant skill only when it is needed, rather than injecting the entire skill set into every prompt. For the best results:

- **Recommended:** Agent hosts that support progressive or on-demand skill loading (for example, GitHub Copilot in VS Code), **or** models with a large context window (roughly **200K+ tokens**).
- **Use with caution:** Hosts that inject the **entire** skill set as always-on context (some IDE agents and CLI tools) **combined with** models that have a smaller usable prompt budget (roughly **128K tokens or less**). In this configuration the full skill payload can consume, or overflow, the context window, which degrades output quality or causes the agent to stop making progress.

**If you are in a constrained setup** (always-on injection plus a smaller-context model), prefer one of the following:

- Load a **single, focused skill** for the task at hand instead of the full set, or
- Switch to a **larger-context model**, or
- Use a host that supports **on-demand skill discovery**.

> These recommendations are based on internal skill-efficacy testing across multiple models and delivery mechanisms. Exact context limits vary by model and host.

## Available Skills

| Skill | Description | Status |
|-------|-------------|--------|
| [cosmosdb-best-practices](skills/cosmosdb-best-practices/) | Performance optimization (111 rules, 12 categories) | ✅ Stable |
| migration-capacity-planning | RU calculation, data sizing, pre-split partitions | 🚧 Planned |

### cosmosdb-best-practices

Azure Cosmos DB performance optimization guidelines containing 111 rules across 12 categories, prioritized by impact.

**Use when:**
- Writing new code that interacts with Cosmos DB
- Designing data models or choosing partition keys
- Reviewing code for performance issues
- Optimizing queries or throughput configuration

**Categories covered:**
- Data Modeling (Critical)
- Partition Key Design (Critical)
- Query Optimization (High)
- SDK Best Practices (High)
- Design Patterns (High)
- Vector Search (High)
- Full-Text Search (High)
- Security (High)
- Indexing Strategies (Medium-High)
- Throughput & Scaling (Medium)
- Global Distribution (Medium)
- Developer Tooling (Medium)
- Monitoring & Diagnostics (Low-Medium)

## Installation

### APM (recommended — all harnesses at once)

```bash
apm install AzureCosmosDB/cosmosdb-agent-kit
```

Installs the skill across GitHub Copilot, Claude Code, Cursor, Codex, and Gemini in one command.

### Universal one-liner (all agents)

```bash
npx skills add AzureCosmosDB/cosmosdb-agent-kit
```

This drops the skill catalog into whichever agent you're using.

### GitHub Copilot CLI

```
/plugin marketplace add AzureCosmosDB/cosmosdb-agent-kit
/plugin install cosmosdb@cosmosdb-agent-kit
```

### Claude Code

```
/plugin install cosmosdb@claude-plugins-official
```

### Gemini CLI

```bash
gemini extensions install https://github.com/AzureCosmosDB/cosmosdb-agent-kit
```

### Per-agent plugin directories

The repository includes ready-made plugin manifests:

| Agent | Manifest |
|-------|----------|
| Claude Code | `.claude-plugin/plugin.json` |
| OpenAI Codex | `.codex-plugin/plugin.json` |
| Cursor | `.cursor-plugin/plugin.json` |
| Gemini CLI | `gemini-extension.json` + `GEMINI.md` |
| GitHub Copilot | `skills/cosmosdb-best-practices/SKILL.md` (auto-detected) |

## Website

A project website is available in `docs/` and is designed for GitHub Pages publishing.

- Main page: `docs/index.html`
- Styles: `docs/styles.css`
- Interactions + survey flow: `docs/app.js`

The website includes a feedback survey that opens a prefilled GitHub issue so users can share improvements for Agent Kit without requiring a backend service.

### Preview locally

```bash
# Option 1: VS Code Live Server
# open docs/index.html with Live Server

# Option 2: Python static server
python -m http.server 8080 --directory docs
```

Then open `http://localhost:8080`.

### Publish with GitHub Pages

In repository settings, set Pages source to `Deploy from a branch`, branch `main`, folder `/docs`.

## Usage

Skills are automatically available once installed. The agent will use them when relevant tasks are detected.

**Examples:**
```
Review my Cosmos DB data model
```
```
Help me choose a partition key for my orders collection
```
```
Optimize this Cosmos DB query
```

## Skill Structure

Each skill contains:
- `SKILL.md` - Instructions for the agent (triggers activation)
- `AGENTS.md` - Compiled rules (what agents read)
- `rules/` - Individual rule files
- `metadata.json` - Version and metadata

## Compatibility

Works with Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, and other Agent Skills-compatible tools.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Evaluation (Local Only)

This project includes a [Waza](https://github.com/microsoft/waza) eval framework for local skill testing. Evals are not enforced in CI today (the mock executor cannot validate response content), but you can run them locally to sanity-check your changes:

```bash
# Install waza (one-time)
irm https://raw.githubusercontent.com/microsoft/waza/main/install.ps1 | iex   # Windows
curl -fsSL https://raw.githubusercontent.com/microsoft/waza/main/install.sh | bash  # macOS/Linux

# Run evaluations
waza run evals/cosmosdb-best-practices/eval.yaml -v

# Check skill readiness
waza check skills/cosmosdb-best-practices
```

**Looking for a way to help?** Check out our [good first issues](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) or browse the [Discussions](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/discussions) board to share ideas.

## Contributors

Thanks to everyone who has contributed rules, fixes, and ideas!

<!-- ALL-CONTRIBUTORS-LIST:START -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

Contributions of any kind welcome! See the [contributing guide](CONTRIBUTING.md) to get started.

## Evaluation with Waza

This project uses [Waza](https://github.com/microsoft/waza) to evaluate skill quality — testing that the agent produces correct Cosmos DB guidance across data modeling, partitioning, queries, SDK usage, and throughput scenarios.

```bash
# Install waza
irm https://raw.githubusercontent.com/microsoft/waza/main/install.ps1 | iex  # Windows
curl -fsSL https://raw.githubusercontent.com/microsoft/waza/main/install.sh | bash  # macOS/Linux

# Run evaluations (mock executor, no API key needed)
waza run evals/cosmosdb-best-practices/eval.yaml -v

# Check skill readiness
waza check skills/cosmosdb-best-practices

# Run with a real model (requires Copilot auth)
waza run evals/cosmosdb-best-practices/eval.yaml --executor copilot-sdk --model claude-sonnet-4.6
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a dated history of updates to the agent kit, including the `cosmosdb-best-practices` skill and the testing framework. Each entry links to the PR that introduced the change.

When you merge a PR, add a new dated entry at the top of `CHANGELOG.md`.

## License

MIT
