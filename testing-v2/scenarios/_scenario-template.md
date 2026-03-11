# Scenario: [Scenario Name]

> **Important**: This file defines the fixed requirements for this test scenario. 
> Do NOT modify this file between iterations - the point is to measure improvement 
> with the same requirements.

## Overview

[Brief description of what the agent should build]

## Language Suitability

| Language | Suitable | Notes |
|----------|----------|-------|
| .NET | ✅ / ❌ | [Why or why not] |
| Java | ✅ / ❌ | [Why or why not] |
| Python | ✅ / ❌ | [Why or why not] |
| Node.js | ✅ / ❌ | [Why or why not] |
| Go | ✅ / ❌ | [Why or why not] |
| Rust | ✅ / ❌ | [Why or why not] |

## Requirements

### Functional Requirements

1. [Requirement 1]
2. [Requirement 2]
3. [Requirement 3]

### Technical Requirements

- **Language/Framework**: [e.g., C# .NET 8, Node.js, Python]
- **Cosmos DB API**: [NoSQL, MongoDB, etc.]
- **Authentication**: [Managed Identity, Connection String, etc.]
- **Deployment Target**: [Local only, Azure, etc.]

### Data Model

[Describe the entities and their relationships]

```json
// Example document structure (if applicable)
{
  "id": "",
  "partitionKey": ""
}
```

### Expected Operations

- [ ] Create/insert items
- [ ] Read by ID + partition key
- [ ] Query with filters
- [ ] Update items
- [ ] Delete items
- [ ] Bulk operations
- [ ] Change feed processing
- [ ] Transactions (if applicable)

## Prompt to Give Agent

> Copy this prompt exactly when starting each iteration:

```
[Write the exact prompt to give the agent here. Be specific but don't 
include hints about Cosmos DB best practices - let the skills guide that.]
```

## Success Criteria

What does "done" look like for this scenario?

- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

## Notes

[Any additional context or constraints]
