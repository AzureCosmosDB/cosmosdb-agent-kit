# Azure Cosmos DB Gemini Extension

This extension provides best practice skills for Azure Cosmos DB (NoSQL) — covering data modeling, partition key design, query optimization, SDK usage, indexing strategies, vector search, full-text search, global distribution, security, monitoring, and design patterns.

## Installation

Install via the skills CLI:

```bash
npx skills add AzureCosmosDB/cosmosdb-agent-kit
```

Or copy the extension file into your Gemini configuration directory.

## Usage

Once installed, the skills are automatically available when Gemini detects tasks related to Azure Cosmos DB. Example prompts:

- "Review my Cosmos DB data model for performance issues"
- "Help me choose a partition key for my e-commerce orders"
- "Optimize this query to reduce RU consumption"
- "Set up vector search on my Cosmos DB container"
- "What security do I need for a new Cosmos DB app?"

## Skill Categories

| Priority | Category | Impact |
|----------|----------|--------|
| 1 | Data Modeling | CRITICAL |
| 2 | Partition Key Design | CRITICAL |
| 3 | Query Optimization | HIGH |
| 4 | SDK Best Practices | HIGH |
| 5 | Design Patterns | HIGH |
| 6 | Vector Search | HIGH |
| 7 | Full-Text Search | HIGH |
| 8 | Security | HIGH |
| 9 | Indexing Strategies | MEDIUM-HIGH |
| 10 | Throughput & Scaling | MEDIUM |
| 11 | Global Distribution | MEDIUM |
| 12 | Developer Tooling | MEDIUM |
| 13 | Monitoring & Diagnostics | LOW-MEDIUM |
