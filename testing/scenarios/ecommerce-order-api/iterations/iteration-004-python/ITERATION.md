# Iteration 004 - Python (WITH Skills) - IN PROGRESS

**Date**: January 28, 2026  
**Agent**: GitHub Copilot (Claude Opus 4.5)  
**Skills Loaded**: ✅ YES - Read `skills/cosmosdb-best-practices/AGENTS.md` before building
**SDK Version**: azure-cosmos (Python SDK) / FastAPI

## Skills Verification

- [x] Read AGENTS.md before starting implementation
- [x] Applied rules during implementation
- **Status**: 🔄 **IN PROGRESS**

## Summary

This iteration demonstrates applying Cosmos DB best practices in a **Python/FastAPI** implementation. Key focus is validating that **enum serialization works correctly as strings** using the `class OrderStatus(str, Enum)` pattern per Rule 4.10.

## Test Plan

| # | Test | Expected | Status |
|---|------|----------|--------|
| 1 | POST /api/orders - Create order | Order created with totals, status="Pending" | ⏳ |
| 2 | GET /api/orders/{id} - Get by ID | Point read returns order | ⏳ |
| 3 | GET /api/orders/customer/{customerId} | Single-partition query | ⏳ |
| 4 | PATCH /api/orders/{id}/status | Status updated to "Shipped" | ⏳ |
| 5 | GET /api/orders/status/{status} | Cross-partition query finds orders | ⏳ |
| 6 | GET /api/orders/daterange | Date range query | ⏳ |

### Critical Test: Enum Serialization (Rule 4.10)

The key validation is that status values are stored and queried as **strings** (e.g., "Pending", "Shipped") not integers.

## Rules to Apply

| Rule | Description | Target |
|------|-------------|--------|
| 1.1 | Embed Related Data | OrderItems embedded in Order |
| 1.5 | Version Document Schemas | schemaVersion property |
| 1.6 | Use Type Discriminators | type = "order" |
| 2.1 | High-Cardinality Partition Keys | customerId |
| 3.1 | Minimize Cross-Partition Queries | Customer queries use partition key |
| 3.2 | Project Only Needed Fields | OrderSummary projection |
| 3.3 | Use Continuation Tokens | PagedResult with continuationToken |
| 3.5 | Use Parameterized Queries | Query with parameters |
| 4.1 | Singleton Client | Single CosmosClient instance |
| 4.10 | **Enum String Serialization** | `class OrderStatus(str, Enum)` |
| 5.2 | Composite Indexes | status+createdAt, customerId+createdAt |
| 7.2 | Session Consistency | ConsistencyLevel.Session |

## Implementation

Building FastAPI application with:
- Python 3.11+
- FastAPI
- azure-cosmos SDK
- Pydantic for models

## Files

- `source-code.zip` - FastAPI project (to be created)
