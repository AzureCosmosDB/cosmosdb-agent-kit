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

## Prompt to Give Agent

> Copy the appropriate prompt for the language being tested:

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
```

## Success Criteria

What does "done" look like for this scenario?

- [ ] API compiles and runs locally
- [ ] Data model follows Cosmos DB best practices (embedding, partition key choice)
- [ ] Partition key enables efficient queries for the main access patterns
- [ ] SDK is used correctly (singleton client, async, proper error handling)
- [ ] No obvious query anti-patterns (cross-partition when avoidable, full scans)
- [ ] Code is production-quality (not just a prototype)

## Notes

- This scenario tests multiple skill areas: data modeling, partition key design, query optimization, and SDK usage
- The tension between "query by customer" and "query by status" tests whether the agent handles multiple access patterns correctly
- Time-based queries test awareness of partition key + date range query patterns
