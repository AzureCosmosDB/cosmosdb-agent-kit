# cosmosdb-agent-kit

A collection of skills for AI coding agents working with Azure Cosmos DB. Skills are packaged instructions and scripts that extend agent capabilities.

![agent-kit-cosmosdb (1)](https://github.com/user-attachments/assets/0a2c2e5f-62ee-4741-adda-9af790980761)

Skills follow the [Agent Skills](https://agentskills.io/) format.

## Available Skills

### cosmosdb-best-practices

Azure Cosmos DB performance optimization guidelines containing 45+ rules across 8 categories, prioritized by impact.

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
- Indexing Strategies (Medium-High)
- Throughput & Scaling (Medium)
- Global Distribution (Medium)
- Monitoring & Diagnostics (Low-Medium)

## Installation

```bash
npx skills add AzureCosmosDB/cosmosdb-agent-kit
```

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

Works with Claude Code, GitHub Copilot, Gemini CLI, and other Agent Skills-compatible tools.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a dated history of updates to the agent kit, including the `cosmosdb-best-practices` skill and the testing framework. Each entry links to the PR that introduced the change.

When you merge a PR, add a new dated entry at the top of `CHANGELOG.md`.

## License

MIT
