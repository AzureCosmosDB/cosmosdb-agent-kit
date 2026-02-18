# Scenario: Multi-tenant SaaS Application

> **Important**: This file defines the fixed requirements for this test scenario. 
> Do NOT modify this file between iterations - the point is to measure improvement 
> with the same requirements.

## Overview

Build an API for a multi-tenant SaaS project management application. Each tenant (company) has isolated data, with users, projects, and tasks. The system must ensure tenant isolation while efficiently sharing infrastructure.

## Language Suitability

| Language | Suitability | Notes |
|----------|-------------|-------|
| .NET | ✅ Recommended | Full hierarchical partition key support, enterprise standard |
| Java | ✅ Recommended | Full support, common for enterprise SaaS |
| Python | ✅ Suitable | Full support, good for smaller SaaS |
| Node.js | ✅ Suitable | Full support, good for startup SaaS |
| Go | ✅ Suitable | Full support, excellent for microservices |
| Rust | 🔬 Experimental | SDK in preview, verify hierarchical PK support |

## Requirements

### Functional Requirements

1. Tenant (company) management - create, configure tenants
2. Users belong to a tenant and can be assigned to projects
3. Projects belong to a tenant with multiple tasks
4. Tasks have status, assignee, due dates, and comments
5. Query tasks by project, by assignee, by status
6. Cross-project queries within a tenant (e.g., "all my tasks")
7. Tenant-level analytics (task counts, completion rates)

### Technical Requirements

- **Language/Framework**: Any supported Cosmos DB SDK language
  - .NET 8 (ASP.NET Core) - recommended
  - Java 17+ (Spring Boot 3) - recommended
  - Python 3.10+ (FastAPI)
  - Node.js 18+ (Express.js)
  - Go 1.21+ (Gin)
  - Rust (Axum) - experimental
- **Cosmos DB API**: NoSQL
- **Authentication**: Connection string (for simplicity in testing)
- **Deployment Target**: Local development only
- **Tenant Isolation**: Logical (shared container with partition isolation)

### Data Model

The system should handle:
- **Tenants**: Company/organization configuration
- **Users**: Users within a tenant
- **Projects**: Projects within a tenant
- **Tasks**: Tasks within projects

Expected volume:
- ~1,000 tenants
- ~100 users per tenant average (varies: 10 to 10,000)
- ~50 projects per tenant average
- ~500 tasks per project average
- Largest tenants: 10,000 users, 1,000 projects

### Expected Operations

- [x] CRUD operations for tenants, users, projects, tasks
- [x] Query tasks by project
- [x] Query all tasks assigned to a user (across projects)
- [x] Query tasks by status within a tenant
- [x] Get project with all tasks
- [x] Tenant-level aggregations
- [ ] Cross-tenant queries (explicitly NOT supported - isolation)

## Prompt to Give Agent

> Copy the appropriate prompt for the language being tested:

### .NET Prompt
```
I need to build a .NET 8 Web API for a multi-tenant SaaS project management system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Support multiple tenants (companies) with complete data isolation
2. Each tenant has users, projects, and tasks
3. Tasks belong to projects and can be assigned to users
4. Query tasks by project, by assignee, or by status
5. Users can see all their tasks across all projects in their tenant
6. Tenant-level analytics (task counts by status)

Expected scale:
- ~1,000 tenants (companies)
- Tenant sizes vary: 10 to 10,000 users
- ~50 projects per tenant, ~500 tasks per project
- Largest tenants have millions of tasks

Please create:
1. The data model with proper multi-tenant design
2. The Cosmos DB container configuration (consider hierarchical partition keys)
3. A repository layer that enforces tenant isolation
4. REST API endpoints for the required operations

Use best practices for Cosmos DB throughout, especially for multi-tenant patterns and hierarchical partition keys.
```

### Java Prompt
```
I need to build a Spring Boot 3 REST API for a multi-tenant SaaS project management system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Support multiple tenants (companies) with complete data isolation
2. Each tenant has users, projects, and tasks
3. Tasks belong to projects and can be assigned to users
4. Query tasks by project, by assignee, or by status
5. Users can see all their tasks across all projects in their tenant
6. Tenant-level analytics (task counts by status)

Expected scale:
- ~1,000 tenants (companies)
- Tenant sizes vary: 10 to 10,000 users
- ~50 projects per tenant, ~500 tasks per project
- Largest tenants have millions of tasks

Please create:
1. The data model with proper multi-tenant design
2. The Cosmos DB container configuration (consider hierarchical partition keys)
3. A repository layer that enforces tenant isolation
4. REST API endpoints for the required operations

Use best practices for Cosmos DB throughout, especially for multi-tenant patterns and hierarchical partition keys.
```

### Python Prompt
```
I need to build a FastAPI REST API for a multi-tenant SaaS project management system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Support multiple tenants (companies) with complete data isolation
2. Each tenant has users, projects, and tasks
3. Tasks belong to projects and can be assigned to users
4. Query tasks by project, by assignee, or by status
5. Users can see all their tasks across all projects in their tenant
6. Tenant-level analytics (task counts by status)

Expected scale:
- ~1,000 tenants (companies)
- Tenant sizes vary: 10 to 10,000 users
- ~50 projects per tenant, ~500 tasks per project
- Largest tenants have millions of tasks

Please create:
1. The data model with proper multi-tenant design
2. The Cosmos DB container configuration (consider hierarchical partition keys)
3. A repository layer that enforces tenant isolation
4. REST API endpoints for the required operations

Use best practices for Cosmos DB throughout, especially for multi-tenant patterns and hierarchical partition keys.
```

### Node.js Prompt
```
I need to build an Express.js REST API for a multi-tenant SaaS project management system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Support multiple tenants (companies) with complete data isolation
2. Each tenant has users, projects, and tasks
3. Tasks belong to projects and can be assigned to users
4. Query tasks by project, by assignee, or by status
5. Users can see all their tasks across all projects in their tenant
6. Tenant-level analytics (task counts by status)

Expected scale:
- ~1,000 tenants (companies)
- Tenant sizes vary: 10 to 10,000 users
- ~50 projects per tenant, ~500 tasks per project
- Largest tenants have millions of tasks

Please create:
1. The data model with proper multi-tenant design
2. The Cosmos DB container configuration (consider hierarchical partition keys)
3. A repository layer that enforces tenant isolation
4. REST API routes for the required operations

Use best practices for Cosmos DB throughout, especially for multi-tenant patterns and hierarchical partition keys.
```

### Go Prompt
```
I need to build a Go REST API (using Gin) for a multi-tenant SaaS project management system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Support multiple tenants (companies) with complete data isolation
2. Each tenant has users, projects, and tasks
3. Tasks belong to projects and can be assigned to users
4. Query tasks by project, by assignee, or by status
5. Users can see all their tasks across all projects in their tenant
6. Tenant-level analytics (task counts by status)

Expected scale:
- ~1,000 tenants (companies)
- Tenant sizes vary: 10 to 10,000 users
- ~50 projects per tenant, ~500 tasks per project
- Largest tenants have millions of tasks

Please create:
1. The data model with proper multi-tenant design
2. The Cosmos DB container configuration (consider hierarchical partition keys)
3. A repository layer that enforces tenant isolation
4. REST API handlers for the required operations

Use best practices for Cosmos DB throughout, especially for multi-tenant patterns and hierarchical partition keys.
```

## Success Criteria

What does "done" look like for this scenario?

- [ ] API compiles and runs locally
- [ ] Tenant isolation is enforced (no cross-tenant data leakage)
- [ ] Partition key strategy handles varying tenant sizes
- [ ] Hierarchical partition keys used appropriately
- [ ] Cross-project queries within tenant are efficient
- [ ] Large tenants don't hit partition size limits

## Notes

- This scenario tests hierarchical partition keys (subpartitioning)
- Tests understanding of multi-tenant patterns in Cosmos DB
- Common mistakes: flat partition key that doesn't scale for large tenants
- Validates tenant isolation in repository layer
- Tests query patterns that span multiple partition key values within a tenant
- May reveal need for composite indexes on status/assignee within tenant
