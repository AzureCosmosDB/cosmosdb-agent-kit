# cosmosdb-agent-kit

A collection of skills for AI coding agents working with Azure Cosmos DB. Skills are packaged instructions and scripts that extend agent capabilities.

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
npx add-skill AzureCosmosDB/cosmosdb-agent-kit
```

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

## License

MIT
