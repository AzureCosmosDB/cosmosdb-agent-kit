# Scenario: E-Commerce Order API

> **Important**: This file defines the fixed requirements for this test scenario. 
> Do NOT modify this file between iterations - the point is to measure improvement 
> with the same requirements.

## Overview

Build a REST API for an e-commerce platform's order management system. The API should handle customer orders, order items, and provide efficient querying capabilities for both customers and administrators.

## Language Suitability

| Language | Suitable | Notes |
|----------|----------|-------|
| .NET | ✅ Yes | Excellent for enterprise APIs, mature SDK |
| Java | ✅ Yes | Strong enterprise choice, Spring Boot ecosystem |
| Python | ✅ Yes | Good for APIs (FastAPI/Flask), rapid development |
| Node.js | ✅ Yes | Great for REST APIs, Express/Fastify ecosystem |
| Go | ✅ Yes | Excellent for microservices, high performance |
| Rust | ⚠️ Optional | Less common for CRUD APIs, but viable with Actix/Axum |

## Requirements

### Functional Requirements

1. Customers can place orders with multiple items
2. Customers can view their order history
3. Customers can view a specific order's details
4. Administrators can query orders by status (pending, shipped, delivered, cancelled)
5. Administrators can query orders within a date range
6. Support for order status updates
7. Calculate order totals including tax

### Technical Requirements

- **Cosmos DB API**: NoSQL
- **Authentication**: Connection string (for simplicity in testing)
- **Deployment Target**: Local development only

**Language-specific frameworks:**
- **.NET**: ASP.NET Core 8 Web API
- **Java**: Spring Boot 3.x
- **Python**: FastAPI or Flask
- **Node.js**: Express.js or Fastify
- **Go**: Gin or Echo
- **Rust**: Actix-web or Axum

### Data Model

The system should handle:
- **Orders**: Order header with customer info, status, timestamps, totals
- **Order Items**: Line items within an order (products, quantities, prices)
- **Customers**: Customer information (can be embedded or referenced)

Expected volume:
- ~100,000 customers
- ~1 million orders per year
- Average 3-5 items per order

### Expected Operations

- [x] Create new orders with items
- [x] Read order by ID
- [x] Query orders by customer
- [x] Query orders by status
- [x] Query orders by date range
- [x] Update order status
- [ ] Delete orders (not required)
- [ ] Bulk operations (not required)
- [ ] Change feed processing (not required)
- [ ] Transactions (optional/bonus)

## API Contract (V2)

This scenario has a **fixed API contract** defined in [`api-contract.yaml`](api-contract.yaml).
Automated tests in the [`tests/`](tests/) directory validate implementations against this contract.

**The agent MUST implement these exact endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (returns 200 when ready) |
| POST | `/api/orders` | Create a new order with items (auto-calculates total) |
| GET | `/api/orders/{orderId}` | Get order by ID |
| GET | `/api/customers/{customerId}/orders` | Get all orders for a customer |
| GET | `/api/customers/{customerId}/orders/summary` | Customer order summary (totals, averages) |
| GET | `/api/orders?status=X` | Query orders by status |
| GET | `/api/orders?startDate=X&endDate=Y` | Query orders by date range |
| PATCH | `/api/orders/{orderId}/status` | Update order status (409 on invalid transition) |
| DELETE | `/api/orders/{orderId}` | Delete order (pending only, else 409) |

**The agent MUST also create `iteration-config.yaml`** in the iteration folder.
See `testing-v2/scenarios/_iteration-config-template.yaml` for the template.

## Prompt to Give Agent

> Copy the appropriate prompt for the language being tested.
> Each prompt includes the API contract requirements that the agent must follow.

### .NET Prompt
```
I need to build a .NET 8 Web API for an e-commerce order management system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Customers can place orders containing multiple items
2. Customers can view their order history and specific order details
3. Admins can query orders by status (pending, shipped, delivered, cancelled)
4. Admins can query orders by date range
5. Orders can have their status updated

Expected scale:
- ~100,000 customers
- ~1 million orders per year  
- 3-5 items per order on average

Please create:
1. The data model with appropriate Cosmos DB design
2. The Cosmos DB container configuration
3. A repository layer for data access
4. REST API controllers with the required endpoints

Use best practices for Cosmos DB throughout.

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                              → Returns 200 when app is ready
- POST /api/orders                          → Body: {customerId, items[{productId, productName, quantity, unitPrice}]} → 201 with {orderId, customerId, items, totalAmount, status, orderDate}
- GET  /api/orders/{orderId}                → 200 with full order object or 404
- GET  /api/customers/{customerId}/orders   → 200 with array of orders
- GET  /api/customers/{customerId}/orders/summary → 200 with {customerId, totalOrders, totalSpent, averageOrderValue}
- GET  /api/orders?status=X                 → 200 with array of orders matching status
- GET  /api/orders?startDate=X&endDate=Y    → 200 with array of orders in date range (ISO-8601)
- PATCH /api/orders/{orderId}/status        → Body: {status} → 200 with updated order, or 409 for invalid transition
- DELETE /api/orders/{orderId}              → 204 on success, 404 if not found, 409 if not pending

Field naming: use camelCase (orderId, customerId, productId, productName, unitPrice, totalAmount, orderDate).
Order totalAmount MUST be auto-calculated as sum of (quantity × unitPrice) for all items.
Status values: pending, shipped, delivered, cancelled. New orders default to "pending".
Status transitions: only pending→shipped, pending→cancelled, shipped→delivered are valid. All others return 409.
orderDate must be ISO-8601 format.
Only orders in "pending" status can be deleted; non-pending returns 409.
Customer summary: totalSpent = sum of totalAmount, averageOrderValue = totalSpent / totalOrders.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: dotnet
database: ecommerce-order-api
port: 5000
health: /health
build: dotnet build
run: dotnet run
```

The Cosmos DB connection uses environment variables:
- COSMOS_ENDPOINT (default: https://localhost:8081)
- COSMOS_KEY (default: the standard emulator key)

Do NOT hardcode connection strings. Read them from environment variables or configuration.
```

### Java Prompt
```
I need to build a Spring Boot 3 REST API for an e-commerce order management system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Customers can place orders containing multiple items
2. Customers can view their order history and specific order details
3. Admins can query orders by status (pending, shipped, delivered, cancelled)
4. Admins can query orders by date range
5. Orders can have their status updated

Expected scale:
- ~100,000 customers
- ~1 million orders per year  
- 3-5 items per order on average

Please create:
1. The data model with appropriate Cosmos DB design
2. The Cosmos DB container configuration
3. A repository layer for data access
4. REST API controllers with the required endpoints

Use best practices for Cosmos DB throughout.

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                              → Returns 200 when app is ready
- POST /api/orders                          → Body: {customerId, items[{productId, productName, quantity, unitPrice}]} → 201 with {orderId, customerId, items, totalAmount, status, orderDate}
- GET  /api/orders/{orderId}                → 200 with full order object or 404
- GET  /api/customers/{customerId}/orders   → 200 with array of orders
- GET  /api/customers/{customerId}/orders/summary → 200 with {customerId, totalOrders, totalSpent, averageOrderValue}
- GET  /api/orders?status=X                 → 200 with array of orders matching status
- GET  /api/orders?startDate=X&endDate=Y    → 200 with array of orders in date range (ISO-8601)
- PATCH /api/orders/{orderId}/status        → Body: {status} → 200 with updated order, or 409 for invalid transition
- DELETE /api/orders/{orderId}              → 204 on success, 404 if not found, 409 if not pending

Field naming: use camelCase (orderId, customerId, productId, productName, unitPrice, totalAmount, orderDate).
Order totalAmount MUST be auto-calculated as sum of (quantity × unitPrice) for all items.
Status values: pending, shipped, delivered, cancelled. New orders default to "pending".
Status transitions: only pending→shipped, pending→cancelled, shipped→delivered are valid. All others return 409.
orderDate must be ISO-8601 format.
Only orders in "pending" status can be deleted; non-pending returns 409.
Customer summary: totalSpent = sum of totalAmount, averageOrderValue = totalSpent / totalOrders.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: java
database: ecommerce-order-api
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
I need to build a FastAPI REST API for an e-commerce order management system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Customers can place orders containing multiple items
2. Customers can view their order history and specific order details
3. Admins can query orders by status (pending, shipped, delivered, cancelled)
4. Admins can query orders by date range
5. Orders can have their status updated

Expected scale:
- ~100,000 customers
- ~1 million orders per year  
- 3-5 items per order on average

Please create:
1. The data model with appropriate Cosmos DB design
2. The Cosmos DB container configuration
3. A repository layer for data access
4. REST API endpoints with the required operations

Use best practices for Cosmos DB throughout.

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                              → Returns 200 when app is ready
- POST /api/orders                          → Body: {customerId, items[{productId, productName, quantity, unitPrice}]} → 201 with {orderId, customerId, items, totalAmount, status, orderDate}
- GET  /api/orders/{orderId}                → 200 with full order object or 404
- GET  /api/customers/{customerId}/orders   → 200 with array of orders
- GET  /api/customers/{customerId}/orders/summary → 200 with {customerId, totalOrders, totalSpent, averageOrderValue}
- GET  /api/orders?status=X                 → 200 with array of orders matching status
- GET  /api/orders?startDate=X&endDate=Y    → 200 with array of orders in date range (ISO-8601)
- PATCH /api/orders/{orderId}/status        → Body: {status} → 200 with updated order, or 409 for invalid transition
- DELETE /api/orders/{orderId}              → 204 on success, 404 if not found, 409 if not pending

Field naming: use camelCase (orderId, customerId, productId, productName, unitPrice, totalAmount, orderDate).
Order totalAmount MUST be auto-calculated as sum of (quantity × unitPrice) for all items.
Status values: pending, shipped, delivered, cancelled. New orders default to "pending".
Status transitions: only pending→shipped, pending→cancelled, shipped→delivered are valid. All others return 409.
orderDate must be ISO-8601 format.
Only orders in "pending" status can be deleted; non-pending returns 409.
Customer summary: totalSpent = sum of totalAmount, averageOrderValue = totalSpent / totalOrders.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: python
database: ecommerce-order-api
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
I need to build an Express.js REST API for an e-commerce order management system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Customers can place orders containing multiple items
2. Customers can view their order history and specific order details
3. Admins can query orders by status (pending, shipped, delivered, cancelled)
4. Admins can query orders by date range
5. Orders can have their status updated

Expected scale:
- ~100,000 customers
- ~1 million orders per year  
- 3-5 items per order on average

Please create:
1. The data model with appropriate Cosmos DB design
2. The Cosmos DB container configuration
3. A repository layer for data access
4. REST API routes with the required endpoints

Use best practices for Cosmos DB throughout.

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                              → Returns 200 when app is ready
- POST /api/orders                          → Body: {customerId, items[{productId, productName, quantity, unitPrice}]} → 201 with {orderId, customerId, items, totalAmount, status, orderDate}
- GET  /api/orders/{orderId}                → 200 with full order object or 404
- GET  /api/customers/{customerId}/orders   → 200 with array of orders
- GET  /api/customers/{customerId}/orders/summary → 200 with {customerId, totalOrders, totalSpent, averageOrderValue}
- GET  /api/orders?status=X                 → 200 with array of orders matching status
- GET  /api/orders?startDate=X&endDate=Y    → 200 with array of orders in date range (ISO-8601)
- PATCH /api/orders/{orderId}/status        → Body: {status} → 200 with updated order, or 409 for invalid transition
- DELETE /api/orders/{orderId}              → 204 on success, 404 if not found, 409 if not pending

Field naming: use camelCase (orderId, customerId, productId, productName, unitPrice, totalAmount, orderDate).
Order totalAmount MUST be auto-calculated as sum of (quantity × unitPrice) for all items.
Status values: pending, shipped, delivered, cancelled. New orders default to "pending".
Status transitions: only pending→shipped, pending→cancelled, shipped→delivered are valid. All others return 409.
orderDate must be ISO-8601 format.
Only orders in "pending" status can be deleted; non-pending returns 409.
Customer summary: totalSpent = sum of totalAmount, averageOrderValue = totalSpent / totalOrders.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: nodejs
database: ecommerce-order-api
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
I need to build a Go REST API (using Gin) for an e-commerce order management system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Customers can place orders containing multiple items
2. Customers can view their order history and specific order details
3. Admins can query orders by status (pending, shipped, delivered, cancelled)
4. Admins can query orders by date range
5. Orders can have their status updated

Expected scale:
- ~100,000 customers
- ~1 million orders per year  
- 3-5 items per order on average

Please create:
1. The data model with appropriate Cosmos DB design
2. The Cosmos DB container configuration
3. A repository layer for data access
4. REST API handlers with the required endpoints

Use best practices for Cosmos DB throughout.

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                              → Returns 200 when app is ready
- POST /api/orders                          → Body: {customerId, items[{productId, productName, quantity, unitPrice}]} → 201 with {orderId, customerId, items, totalAmount, status, orderDate}
- GET  /api/orders/{orderId}                → 200 with full order object or 404
- GET  /api/customers/{customerId}/orders   → 200 with array of orders
- GET  /api/customers/{customerId}/orders/summary → 200 with {customerId, totalOrders, totalSpent, averageOrderValue}
- GET  /api/orders?status=X                 → 200 with array of orders matching status
- GET  /api/orders?startDate=X&endDate=Y    → 200 with array of orders in date range (ISO-8601)
- PATCH /api/orders/{orderId}/status        → Body: {status} → 200 with updated order, or 409 for invalid transition
- DELETE /api/orders/{orderId}              → 204 on success, 404 if not found, 409 if not pending

Field naming: use camelCase (orderId, customerId, productId, productName, unitPrice, totalAmount, orderDate).
Order totalAmount MUST be auto-calculated as sum of (quantity × unitPrice) for all items.
Status values: pending, shipped, delivered, cancelled. New orders default to "pending".
Status transitions: only pending→shipped, pending→cancelled, shipped→delivered are valid. All others return 409.
orderDate must be ISO-8601 format.
Only orders in "pending" status can be deleted; non-pending returns 409.
Customer summary: totalSpent = sum of totalAmount, averageOrderValue = totalSpent / totalOrders.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: go
database: ecommerce-order-api
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
- [ ] Data model follows Cosmos DB best practices (embedding, partition key choice)
- [ ] Partition key enables efficient queries for the main access patterns
- [ ] SDK is used correctly (singleton client, async, proper error handling)
- [ ] No obvious query anti-patterns (cross-partition when avoidable, full scans)
- [ ] Code is production-quality (not just a prototype)
- [ ] All tests in `test_api_contract.py` pass (API contract conformance)
- [ ] All tests in `test_data_integrity.py` pass (data persistence, partition keys, indexing)
- [ ] `iteration-config.yaml` is present and valid

## Notes

- This scenario tests multiple skill areas: data modeling, partition key design, query optimization, and SDK usage
- The tension between "query by customer" and "query by status" tests whether the agent handles multiple access patterns correctly
- Time-based queries test awareness of partition key + date range query patterns
- Tests are language-agnostic Python HTTP tests — the API under test can be in any language
- See `api-contract.yaml` for the full contract specification
- See `tests/` directory for the complete test suite
