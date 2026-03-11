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

## API Contract (V2)

This scenario has a **fixed API contract** defined in `api-contract.yaml`. All iterations must implement this exact interface. Tests in `tests/` validate conformance automatically.

| Endpoint | Method | Path |
|----------|--------|------|
| Health check | GET | `/health` |
| Create tenant | POST | `/api/tenants` |
| Get tenant | GET | `/api/tenants/{tenantId}` |
| Create user | POST | `/api/tenants/{tenantId}/users` |
| List users | GET | `/api/tenants/{tenantId}/users` |
| Create project | POST | `/api/tenants/{tenantId}/projects` |
| List projects | GET | `/api/tenants/{tenantId}/projects` |
| Get project | GET | `/api/tenants/{tenantId}/projects/{projectId}` |
| Create task | POST | `/api/tenants/{tenantId}/projects/{projectId}/tasks` |
| List project tasks | GET | `/api/tenants/{tenantId}/projects/{projectId}/tasks` |
| User tasks | GET | `/api/tenants/{tenantId}/users/{userId}/tasks` |
| Tasks by status | GET | `/api/tenants/{tenantId}/tasks?status=X` |
| Tenant analytics | GET | `/api/tenants/{tenantId}/analytics` |

Each language prompt below includes the contract requirements and an `iteration-config.yaml` block.

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

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                                                        → Returns 200 when app is ready
- POST /api/tenants                                                   → Body: {name, plan} → 201 with {tenantId, name, plan, createdAt}
- GET  /api/tenants/{tenantId}                                        → 200 with tenant object or 404
- POST /api/tenants/{tenantId}/users                                  → Body: {name, email, role} → 201 with {userId, tenantId, name, email, role}
- GET  /api/tenants/{tenantId}/users                                  → 200 with array of users
- POST /api/tenants/{tenantId}/projects                               → Body: {name, description?} → 201 with {projectId, tenantId, name, description, createdAt}
- GET  /api/tenants/{tenantId}/projects                               → 200 with array of projects
- GET  /api/tenants/{tenantId}/projects/{projectId}                   → 200 with project object or 404
- POST /api/tenants/{tenantId}/projects/{projectId}/tasks             → Body: {title, assigneeId, priority, status?} → 201 with {taskId, tenantId, projectId, title, assigneeId, priority, status, createdAt}
- GET  /api/tenants/{tenantId}/projects/{projectId}/tasks             → 200 with array of tasks in project
- GET  /api/tenants/{tenantId}/users/{userId}/tasks                   → 200 with array of tasks assigned to user
- GET  /api/tenants/{tenantId}/tasks?status=X                         → 200 with tasks matching status
- GET  /api/tenants/{tenantId}/analytics                              → 200 with {tenantId, totalUsers, totalProjects, totalTasks, tasksByStatus:{todo,in-progress,done,blocked}, tasksByPriority:{low,medium,high,critical}}

Field naming: use camelCase (tenantId, userId, projectId, taskId, assigneeId, createdAt).
Status values: todo, in-progress, done, blocked. New tasks default to "todo".
Priority values: low, medium, high, critical.
Role values: admin, member, viewer.
Plan values: free, standard, premium.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: dotnet
database: multitenant-saas
port: 5000
health: /health
build: dotnet build
run: dotnet run --urls http://0.0.0.0:5000
```

The Cosmos DB connection uses environment variables:
- COSMOS_ENDPOINT (default: https://localhost:8081)
- COSMOS_KEY (default: the standard emulator key)

Do NOT hardcode connection strings. Read them from environment variables or configuration.
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

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                                                        → Returns 200 when app is ready
- POST /api/tenants                                                   → Body: {name, plan} → 201 with {tenantId, name, plan, createdAt}
- GET  /api/tenants/{tenantId}                                        → 200 with tenant object or 404
- POST /api/tenants/{tenantId}/users                                  → Body: {name, email, role} → 201 with {userId, tenantId, name, email, role}
- GET  /api/tenants/{tenantId}/users                                  → 200 with array of users
- POST /api/tenants/{tenantId}/projects                               → Body: {name, description?} → 201 with {projectId, tenantId, name, description, createdAt}
- GET  /api/tenants/{tenantId}/projects                               → 200 with array of projects
- GET  /api/tenants/{tenantId}/projects/{projectId}                   → 200 with project object or 404
- POST /api/tenants/{tenantId}/projects/{projectId}/tasks             → Body: {title, assigneeId, priority, status?} → 201 with {taskId, tenantId, projectId, title, assigneeId, priority, status, createdAt}
- GET  /api/tenants/{tenantId}/projects/{projectId}/tasks             → 200 with array of tasks in project
- GET  /api/tenants/{tenantId}/users/{userId}/tasks                   → 200 with array of tasks assigned to user
- GET  /api/tenants/{tenantId}/tasks?status=X                         → 200 with tasks matching status
- GET  /api/tenants/{tenantId}/analytics                              → 200 with {tenantId, totalUsers, totalProjects, totalTasks, tasksByStatus:{todo,in-progress,done,blocked}, tasksByPriority:{low,medium,high,critical}}

Field naming: use camelCase (tenantId, userId, projectId, taskId, assigneeId, createdAt).
Status values: todo, in-progress, done, blocked. New tasks default to "todo".
Priority values: low, medium, high, critical.
Role values: admin, member, viewer.
Plan values: free, standard, premium.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: java
database: multitenant-saas
port: 8080
health: /health
build: mvn package -DskipTests
run: java -jar target/*.jar
```

The Cosmos DB connection uses environment variables:
- COSMOS_ENDPOINT (default: https://localhost:8081)
- COSMOS_KEY (default: the standard emulator key)

Do NOT hardcode connection strings. Read them from environment variables or configuration.
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

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                                                        → Returns 200 when app is ready
- POST /api/tenants                                                   → Body: {name, plan} → 201 with {tenantId, name, plan, createdAt}
- GET  /api/tenants/{tenantId}                                        → 200 with tenant object or 404
- POST /api/tenants/{tenantId}/users                                  → Body: {name, email, role} → 201 with {userId, tenantId, name, email, role}
- GET  /api/tenants/{tenantId}/users                                  → 200 with array of users
- POST /api/tenants/{tenantId}/projects                               → Body: {name, description?} → 201 with {projectId, tenantId, name, description, createdAt}
- GET  /api/tenants/{tenantId}/projects                               → 200 with array of projects
- GET  /api/tenants/{tenantId}/projects/{projectId}                   → 200 with project object or 404
- POST /api/tenants/{tenantId}/projects/{projectId}/tasks             → Body: {title, assigneeId, priority, status?} → 201 with {taskId, tenantId, projectId, title, assigneeId, priority, status, createdAt}
- GET  /api/tenants/{tenantId}/projects/{projectId}/tasks             → 200 with array of tasks in project
- GET  /api/tenants/{tenantId}/users/{userId}/tasks                   → 200 with array of tasks assigned to user
- GET  /api/tenants/{tenantId}/tasks?status=X                         → 200 with tasks matching status
- GET  /api/tenants/{tenantId}/analytics                              → 200 with {tenantId, totalUsers, totalProjects, totalTasks, tasksByStatus:{todo,in-progress,done,blocked}, tasksByPriority:{low,medium,high,critical}}

Field naming: use camelCase (tenantId, userId, projectId, taskId, assigneeId, createdAt).
Status values: todo, in-progress, done, blocked. New tasks default to "todo".
Priority values: low, medium, high, critical.
Role values: admin, member, viewer.
Plan values: free, standard, premium.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: python
database: multitenant-saas
port: 8000
health: /health
build: pip install -r requirements.txt
run: uvicorn main:app --host 0.0.0.0 --port 8000
```

The Cosmos DB connection uses environment variables:
- COSMOS_ENDPOINT (default: https://localhost:8081)
- COSMOS_KEY (default: the standard emulator key)

Do NOT hardcode connection strings. Read them from environment variables or configuration.
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

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                                                        → Returns 200 when app is ready
- POST /api/tenants                                                   → Body: {name, plan} → 201 with {tenantId, name, plan, createdAt}
- GET  /api/tenants/{tenantId}                                        → 200 with tenant object or 404
- POST /api/tenants/{tenantId}/users                                  → Body: {name, email, role} → 201 with {userId, tenantId, name, email, role}
- GET  /api/tenants/{tenantId}/users                                  → 200 with array of users
- POST /api/tenants/{tenantId}/projects                               → Body: {name, description?} → 201 with {projectId, tenantId, name, description, createdAt}
- GET  /api/tenants/{tenantId}/projects                               → 200 with array of projects
- GET  /api/tenants/{tenantId}/projects/{projectId}                   → 200 with project object or 404
- POST /api/tenants/{tenantId}/projects/{projectId}/tasks             → Body: {title, assigneeId, priority, status?} → 201 with {taskId, tenantId, projectId, title, assigneeId, priority, status, createdAt}
- GET  /api/tenants/{tenantId}/projects/{projectId}/tasks             → 200 with array of tasks in project
- GET  /api/tenants/{tenantId}/users/{userId}/tasks                   → 200 with array of tasks assigned to user
- GET  /api/tenants/{tenantId}/tasks?status=X                         → 200 with tasks matching status
- GET  /api/tenants/{tenantId}/analytics                              → 200 with {tenantId, totalUsers, totalProjects, totalTasks, tasksByStatus:{todo,in-progress,done,blocked}, tasksByPriority:{low,medium,high,critical}}

Field naming: use camelCase (tenantId, userId, projectId, taskId, assigneeId, createdAt).
Status values: todo, in-progress, done, blocked. New tasks default to "todo".
Priority values: low, medium, high, critical.
Role values: admin, member, viewer.
Plan values: free, standard, premium.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: nodejs
database: multitenant-saas
port: 3000
health: /health
build: npm install
run: node server.js
```

The Cosmos DB connection uses environment variables:
- COSMOS_ENDPOINT (default: https://localhost:8081)
- COSMOS_KEY (default: the standard emulator key)

Do NOT hardcode connection strings. Read them from environment variables or configuration.
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

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                                                        → Returns 200 when app is ready
- POST /api/tenants                                                   → Body: {name, plan} → 201 with {tenantId, name, plan, createdAt}
- GET  /api/tenants/{tenantId}                                        → 200 with tenant object or 404
- POST /api/tenants/{tenantId}/users                                  → Body: {name, email, role} → 201 with {userId, tenantId, name, email, role}
- GET  /api/tenants/{tenantId}/users                                  → 200 with array of users
- POST /api/tenants/{tenantId}/projects                               → Body: {name, description?} → 201 with {projectId, tenantId, name, description, createdAt}
- GET  /api/tenants/{tenantId}/projects                               → 200 with array of projects
- GET  /api/tenants/{tenantId}/projects/{projectId}                   → 200 with project object or 404
- POST /api/tenants/{tenantId}/projects/{projectId}/tasks             → Body: {title, assigneeId, priority, status?} → 201 with {taskId, tenantId, projectId, title, assigneeId, priority, status, createdAt}
- GET  /api/tenants/{tenantId}/projects/{projectId}/tasks             → 200 with array of tasks in project
- GET  /api/tenants/{tenantId}/users/{userId}/tasks                   → 200 with array of tasks assigned to user
- GET  /api/tenants/{tenantId}/tasks?status=X                         → 200 with tasks matching status
- GET  /api/tenants/{tenantId}/analytics                              → 200 with {tenantId, totalUsers, totalProjects, totalTasks, tasksByStatus:{todo,in-progress,done,blocked}, tasksByPriority:{low,medium,high,critical}}

Field naming: use camelCase (tenantId, userId, projectId, taskId, assigneeId, createdAt).
Status values: todo, in-progress, done, blocked. New tasks default to "todo".
Priority values: low, medium, high, critical.
Role values: admin, member, viewer.
Plan values: free, standard, premium.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: go
database: multitenant-saas
port: 8080
health: /health
build: go build -o server .
run: ./server
```

The Cosmos DB connection uses environment variables:
- COSMOS_ENDPOINT (default: https://localhost:8081)
- COSMOS_KEY (default: the standard emulator key)

Do NOT hardcode connection strings. Read them from environment variables or configuration.
```

## Success Criteria

What does "done" look like for this scenario?

- [ ] API compiles and runs locally
- [ ] Tenant isolation is enforced (no cross-tenant data leakage)
- [ ] Partition key strategy handles varying tenant sizes
- [ ] Hierarchical partition keys used appropriately
- [ ] Cross-project queries within tenant are efficient
- [ ] Large tenants don't hit partition size limits
- [ ] All tests in `test_api_contract.py` pass (API contract conformance)
- [ ] All tests in `test_data_integrity.py` pass (data persistence, partition keys, hierarchical PKs, indexing)
- [ ] `iteration-config.yaml` is present and valid

## Notes

- This scenario tests hierarchical partition keys (subpartitioning)
- Tests understanding of multi-tenant patterns in Cosmos DB
- Common mistakes: flat partition key that doesn't scale for large tenants
- Validates tenant isolation in repository layer
- Tests query patterns that span multiple partition key values within a tenant
- May reveal need for composite indexes on status/assignee within tenant
- Tests are language-agnostic Python HTTP tests — the API under test can be in any language
- See `api-contract.yaml` for the full contract specification
- See `tests/` directory for the complete test suite
