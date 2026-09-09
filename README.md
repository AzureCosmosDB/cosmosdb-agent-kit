# cosmosdb-agent-kit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Good First Issues](https://img.shields.io/github/issues/AzureCosmosDB/cosmosdb-agent-kit/good-first-issue?color=7057ff&label=good%20first%20issues)](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
[![Discussions](https://img.shields.io/github/discussions/AzureCosmosDB/cosmosdb-agent-kit)](https://github.com/AzureCosmosDB/cosmosdb-agent-kit/discussions)

A collection of skills for AI coding agents working with Azure Cosmos DB. Skills are packaged instructions and scripts that extend agent capabilities.

![agent-kit-cosmosdb (1)](https://github.com/user-attachments/assets/0a2c2e5f-62ee-4741-adda-9af790980761)

Skills follow the [Agent Skills](https://agentskills.io/) format and the kit ships with plugin manifests for **Claude Code**, **Codex**, **Cursor**, **Gemini CLI**, **Grok Build**, **Kimi Code**, and **GitHub Copilot**.

## Where this works best

This agent kit is designed for **progressive (on-demand) skill delivery**: hosts that load a relevant skill only when it is needed, rather than injecting the entire skill set into every prompt. For the best results:

- **Recommended:** Agent hosts that support progressive or on-demand skill loading (for example, GitHub Copilot in VS Code), **or** models with a large context window (roughly **200K+ tokens**).
- **Use with caution:** Hosts that inject the **entire** skill set as always-on context (some IDE agents and CLI tools) **combined with** models that have a smaller usable prompt budget (roughly **128K tokens or less**). In this configuration the full skill payload can consume, or overflow, the context window, which degrades output quality or causes the agent to stop making progress.

**If you are in a constrained setup** (always-on injection plus a smaller-context model), prefer one of the following:

- Load a **single, focused skill** for the task at hand instead of the full set, or
- Switch to a **larger-context model**, or
- Use a host that supports **on-demand skill discovery**.

> These recommendations are based on internal skill-efficacy testing across multiple models and delivery mechanisms. Exact context limits vary by model and host.

## Recommended models

We evaluate agent builds on Azure Cosmos DB with an **execution-graded** benchmark on Microsoft Bench: a realistic *AI Chat with RAG* task (Python / FastAPI) built against a **live** Azure Cosmos DB account (Entra ID, no keys) and scored by hidden integration tests. `reward` is the fraction of checks passed, averaged over roughly **100 independent attempts per model**. Based on this, for building non-trivial Cosmos DB applications we recommend:

| Tier | Models (as tested) | Avg reward | Guidance |
|------|--------------------|-----------|----------|
| **Recommended** | GPT-5.4, Claude Opus 4.8 | 0.79 – 0.82 | Strongest Cosmos DB build quality; the best default choice. |
| **Capable** | Claude Sonnet 4.5, Claude Opus 4.5, GPT-5.2, Claude Sonnet 4.6 | 0.59 – 0.68 | Solid results; pair with the kit and a clear specification. |
| **Best for simpler tasks** | Claude Haiku 4.5, GPT-4.1 | 0.11 – 0.15 | Fine for individual operations; struggle with full application builds regardless of how skills are delivered. |

**How to read this:** the ranking reflects intrinsic model capability on Cosmos DB build tasks, measured *without* any skill injected. Model capability is the dominant factor in outcome quality — **choose a Recommended-tier model first**, then apply the kit.

### Delivery mechanism matters as much as the model

The same testing measured *how* the skill is delivered, and this is where the results are strongest:

- **Always-on injection can hurt — including the strongest models.** Injecting the **entire** skill set as always-on context (~500&nbsp;KB) **overflowed the context window and scored 0** on every model whose usable prompt budget is roughly **130K tokens or less**. And a multi-file always-on variant **significantly reduced quality on large-context, capable models too** (for example Claude Opus 4.8 and GPT-5.2 both dropped by roughly **0.3**). In other words, forcing the full skill payload into every prompt is counter-productive.
- **Progressive / on-demand delivery is the safe mode.** It avoided both failure modes — no overflow, no regression on strong models — and **matched no-skill quality**. It also costs **roughly 5–13× fewer input tokens than always-on injection** (progressive sends about as many tokens as a no-skill run, because it loads a skill only when needed; always-on re-sends the full payload on every call).

So the combined recommendation is simple: **use a Recommended-tier model *and* deliver skills on demand.** This is exactly what the kit is designed for (see [Where this works best](#where-this-works-best)).

> On this well-specified build task, progressive delivery *matches* a no-skill baseline rather than beating it — the strong models already know a lot. The measurable win today is avoiding the harm of always-on injection at a fraction of the token cost; benefits on *under-specified* prompts and additional scenarios are still being measured.

### Scope & caveats

- Results come from a single build scenario (AI Chat + RAG), a single language (Python), and a single agent host, graded by hidden integration tests over ~100 attempts per model per configuration.
- These tiers are **directional and specific to this evaluation** (one scenario, one language, one host). Model names reflect the versions exposed by the evaluation harness at test time (mid-2026); exact scores will shift as models evolve and may not transfer to other tasks.
- On this well-specified task, Recommended-tier models already score well **without** the skill; the kit's role is to encode Cosmos DB-specific best practices and steer agents away from common anti-patterns. Testing is being extended to under-specified prompts and additional scenarios.

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

Installs the skill across GitHub Copilot, Claude Code, Cursor, Codex, Gemini, and Kimi Code in one command.

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

### Grok Build

Add the Agent Kit marketplace, install the plugin, then verify that Grok discovered its skills:

```bash
grok plugin marketplace add AzureCosmosDB/cosmosdb-agent-kit
grok plugin install cosmosdb --trust
grok inspect
```

The marketplace catalog lives at `.grok-plugin/marketplace.json`, and the plugin uses the root
`plugin.json` manifest. Only install trusted plugin sources; Grok requires `--trust` before
activating a remote plugin's skills and MCP servers.

### Kimi Code CLI

Install directly from GitHub (recommended):

```
/plugins install https://github.com/AzureCosmosDB/cosmosdb-agent-kit
/reload
```

Or add the custom marketplace catalog, then install from the plugin manager (`/plugins`):

```
/plugins marketplace https://raw.githubusercontent.com/AzureCosmosDB/cosmosdb-agent-kit/main/kimi-marketplace.json
```

The plugin manifest lives at `.kimi-plugin/plugin.json` and the catalog at `kimi-marketplace.json`.

### OpenAI Codex CLI

Add the repo marketplace, then install from the Plugins Directory in the ChatGPT desktop app:

```
codex plugin marketplace add AzureCosmosDB/cosmosdb-agent-kit
```

The plugin manifest lives at `.codex-plugin/plugin.json` and the marketplace catalog at `.agents/plugins/marketplace.json` (Codex also reads the legacy `.claude-plugin/marketplace.json`).

### Per-agent plugin directories

The repository includes ready-made plugin manifests:

| Agent | Manifest |
|-------|----------|
| Claude Code | `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` |
| OpenAI Codex | `.codex-plugin/plugin.json` + `.agents/plugins/marketplace.json` |
| Cursor | `.cursor-plugin/plugin.json` |
| Gemini CLI | `gemini-extension.json` + `GEMINI.md` |
| Grok Build | `.grok-plugin/marketplace.json` + `plugin.json` |
| Kimi Code | `.kimi-plugin/plugin.json` |
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
- `SKILL.md` - Instructions and index for the agent (what agents read; links to rules)
- `rules/` - Individual rule files
- `metadata.json` - Version and metadata

## Compatibility

Works with Claude Code, Codex, Cursor, Gemini CLI, Grok Build, Kimi Code, GitHub Copilot, and other Agent Skills-compatible tools.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Evaluation (Local Only)

This project includes a [Vally](https://github.com/microsoft/vally) eval framework for local skill testing. Evals are not enforced in CI today (the mock executor cannot validate response content), but you can run them locally to sanity-check your changes:

```bash
# Install Vally by following the instructions at https://github.com/microsoft/vally

# Validate split eval specs (PowerShell)
$files = @('modeling.eval.yaml','query.eval.yaml','sdk.eval.yaml','throughput.eval.yaml','security.eval.yaml','vector.eval.yaml','guardrails.eval.yaml'); foreach ($f in $files) { vally lint -e (Join-Path './evals/cosmosdb-best-practices' $f) }

# Run all Cosmos DB eval suites
vally eval --suite cosmosdb-all

# Run only serverless-focused throughput checks
vally eval --suite cosmosdb-serverless --workers 1

# Lint skill references and frontmatter
vally lint ./skills
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

## Evaluation with Vally

This project uses [Vally](https://github.com/microsoft/vally) to evaluate skill quality, testing that the agent produces correct Cosmos DB guidance across data modeling, partitioning, queries, SDK usage, and throughput scenarios.

```bash
# Install Vally by following the instructions at https://github.com/microsoft/vally

# Validate split eval specs (PowerShell)
$files = @('modeling.eval.yaml','query.eval.yaml','sdk.eval.yaml','throughput.eval.yaml','security.eval.yaml','vector.eval.yaml','guardrails.eval.yaml'); foreach ($f in $files) { vally lint -e (Join-Path './evals/cosmosdb-best-practices' $f) }

# Lint skill definitions
vally lint ./skills

# Run all split evals
vally eval --suite cosmosdb-all

# Run by area
vally eval --suite cosmosdb-throughput
vally eval --suite cosmosdb-serverless --workers 1
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a dated history of updates to the agent kit, including the `cosmosdb-best-practices` skill and the testing framework. Each entry links to the PR that introduced the change.

When you merge a PR, add a new dated entry at the top of `CHANGELOG.md`.

## License

MIT
