# Scenario: IoT Device Telemetry

> **Important**: This file defines the fixed requirements for this test scenario. 
> Do NOT modify this file between iterations - the point is to measure improvement 
> with the same requirements.

## Overview

Build an API for ingesting and querying IoT device telemetry data. The system should handle high-volume writes from thousands of devices and support time-range queries for analytics dashboards.

## Language Suitability

| Language | Suitable | Notes |
|----------|----------|-------|
| .NET | ✅ Yes | Strong for enterprise IoT backends |
| Java | ✅ Yes | Common in enterprise IoT, good async support |
| Python | ✅ Yes | Popular for IoT, great for data processing |
| Node.js | ✅ Yes | Event-driven, good for real-time ingestion |
| Go | ✅ Yes | Excellent for high-throughput ingestion services |
| Rust | ⚠️ Optional | Great performance, but less common for IoT APIs |

## Requirements

### Functional Requirements

1. Devices can send telemetry readings (temperature, humidity, battery level)
2. System should handle burst writes from many devices simultaneously
3. Query latest reading for a specific device
4. Query readings for a device within a time range
5. Query all devices in a specific location/facility
6. Automatic expiration of old data (retention policy)
7. Aggregate statistics per device (min/max/avg over time periods)

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
- **Devices**: Device metadata (id, name, location, device type)
- **Telemetry**: Time-series readings from devices

Expected volume:
- ~10,000 devices
- Each device sends readings every 5 minutes
- ~2.88 million readings per day
- 30-day retention (auto-expire old data)

### Expected Operations

- [x] Ingest telemetry readings (high volume)
- [x] Read latest reading for a device
- [x] Query readings by device + time range
- [x] Query devices by location
- [x] Bulk/batch ingestion
- [ ] Change feed processing (not required for this scenario)
- [ ] Transactions (not required)

## Prompt to Give Agent

> Copy the appropriate prompt for the language being tested:

### .NET Prompt
```
I need to build a .NET 8 Web API for an IoT telemetry system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Devices send telemetry readings (temperature, humidity, battery level) every 5 minutes
2. Query the latest reading for a specific device
3. Query readings for a device within a time range (e.g., last 24 hours)
4. Query all devices in a specific facility/location
5. Old data should automatically expire after 30 days
6. Support bulk ingestion of readings

Expected scale:
- ~10,000 devices
- ~2.88 million readings per day
- 30-day data retention

Please create:
1. The data model with appropriate Cosmos DB design for time-series data
2. The Cosmos DB container configuration (including TTL)
3. A repository layer for data access
4. REST API endpoints for the required operations

Use best practices for Cosmos DB throughout, especially for time-series data patterns.
```

### Java Prompt
```
I need to build a Spring Boot 3 REST API for an IoT telemetry system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Devices send telemetry readings (temperature, humidity, battery level) every 5 minutes
2. Query the latest reading for a specific device
3. Query readings for a device within a time range (e.g., last 24 hours)
4. Query all devices in a specific facility/location
5. Old data should automatically expire after 30 days
6. Support bulk ingestion of readings

Expected scale:
- ~10,000 devices
- ~2.88 million readings per day
- 30-day data retention

Please create:
1. The data model with appropriate Cosmos DB design for time-series data
2. The Cosmos DB container configuration (including TTL)
3. A repository layer for data access
4. REST API endpoints for the required operations

Use best practices for Cosmos DB throughout, especially for time-series data patterns.
```

### Python Prompt
```
I need to build a FastAPI REST API for an IoT telemetry system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Devices send telemetry readings (temperature, humidity, battery level) every 5 minutes
2. Query the latest reading for a specific device
3. Query readings for a device within a time range (e.g., last 24 hours)
4. Query all devices in a specific facility/location
5. Old data should automatically expire after 30 days
6. Support bulk ingestion of readings

Expected scale:
- ~10,000 devices
- ~2.88 million readings per day
- 30-day data retention

Please create:
1. The data model with appropriate Cosmos DB design for time-series data
2. The Cosmos DB container configuration (including TTL)
3. A repository layer for data access
4. REST API endpoints for the required operations

Use best practices for Cosmos DB throughout, especially for time-series data patterns.
```

### Node.js Prompt
```
I need to build an Express.js REST API for an IoT telemetry system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Devices send telemetry readings (temperature, humidity, battery level) every 5 minutes
2. Query the latest reading for a specific device
3. Query readings for a device within a time range (e.g., last 24 hours)
4. Query all devices in a specific facility/location
5. Old data should automatically expire after 30 days
6. Support bulk ingestion of readings

Expected scale:
- ~10,000 devices
- ~2.88 million readings per day
- 30-day data retention

Please create:
1. The data model with appropriate Cosmos DB design for time-series data
2. The Cosmos DB container configuration (including TTL)
3. A repository layer for data access
4. REST API routes for the required operations

Use best practices for Cosmos DB throughout, especially for time-series data patterns.
```

### Go Prompt
```
I need to build a Go REST API (using Gin) for an IoT telemetry system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Devices send telemetry readings (temperature, humidity, battery level) every 5 minutes
2. Query the latest reading for a specific device
3. Query readings for a device within a time range (e.g., last 24 hours)
4. Query all devices in a specific facility/location
5. Old data should automatically expire after 30 days
6. Support bulk ingestion of readings

Expected scale:
- ~10,000 devices
- ~2.88 million readings per day
- 30-day data retention

Please create:
1. The data model with appropriate Cosmos DB design for time-series data
2. The Cosmos DB container configuration (including TTL)
3. A repository layer for data access
4. REST API handlers for the required operations

Use best practices for Cosmos DB throughout, especially for time-series data patterns.
```

## Success Criteria

What does "done" look like for this scenario?

- [ ] API compiles and runs locally
- [ ] Partition key handles time-series data efficiently (not timestamp alone!)
- [ ] TTL is configured correctly for 30-day retention
- [ ] Bulk operations use SDK batch capabilities
- [ ] Queries for device + time range are efficient (single partition)
- [ ] No hot partition issues with high-volume writes

## Notes

- This scenario specifically tests time-series data patterns
- Common mistakes: using timestamp as partition key (hot partition), not using TTL
- Tests understanding of synthetic/composite partition keys
- High write volume tests bulk ingestion patterns
