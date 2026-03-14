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

## API Contract (V2)

This scenario has a **fixed API contract** defined in `api-contract.yaml`. All iterations must implement this exact interface. Tests in `tests/` validate conformance automatically.

| Endpoint | Method | Path |
|----------|--------|------|
| Health check | GET | `/health` |
| Register device | POST | `/api/devices` |
| Get device | GET | `/api/devices/{deviceId}` |
| Update device | PATCH | `/api/devices/{deviceId}` |
| Delete device | DELETE | `/api/devices/{deviceId}` |
| Get devices by location | GET | `/api/devices?location=X` |
| Ingest telemetry | POST | `/api/telemetry` |
| Batch ingest | POST | `/api/telemetry/batch` |
| Latest reading | GET | `/api/devices/{deviceId}/telemetry/latest` |
| Time range query | GET | `/api/devices/{deviceId}/telemetry?start=X&end=Y` |
| Device stats | GET | `/api/devices/{deviceId}/telemetry/stats?period=24h` |
| Location summary | GET | `/api/locations/{location}/telemetry/latest` |

Each language prompt below includes the contract requirements and an `iteration-config.yaml` block.

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

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                                              → Returns 200 when app is ready
- POST /api/devices                                         → Body: {deviceId, name, location, deviceType} → 201 with device object
- GET  /api/devices/{deviceId}                              → 200 with device object or 404
- PATCH /api/devices/{deviceId}                             → Body: {name?, location?, deviceType?} → 200 with updated device or 404
- DELETE /api/devices/{deviceId}                            → 204 on success, 404 if not found
- GET  /api/devices?location=X                              → 200 with array of devices at location
- POST /api/telemetry                                       → Body: {deviceId, temperature, humidity, batteryLevel, timestamp?} → 201 with {readingId, deviceId, temperature, humidity, batteryLevel, timestamp}
- POST /api/telemetry/batch                                 → Body: array of readings → 201 with {ingested: count}
- GET  /api/devices/{deviceId}/telemetry/latest              → 200 with latest reading or 404
- GET  /api/devices/{deviceId}/telemetry?start=X&end=Y       → 200 with array of readings in time range (ISO-8601)
- GET  /api/devices/{deviceId}/telemetry/stats?period=24h    → 200 with {deviceId, period, temperature:{min,max,avg}, humidity:{min,max,avg}, batteryLevel:{min,max,avg}}
- GET  /api/locations/{location}/telemetry/latest            → 200 with array of {deviceId, temperature, humidity, batteryLevel, timestamp} (latest reading per device at location)

Field naming: use camelCase (deviceId, deviceType, readingId, temperature, humidity, batteryLevel, timestamp).
If no timestamp is provided on ingestion, the server MUST generate one (ISO-8601).
TTL: configure 30-day automatic expiration on telemetry readings.
Deleting a device must also make its telemetry inaccessible (latest returns 404).
Location summary: returns the most recent reading for each device at the specified location.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: dotnet
database: iot-device-telemetry
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

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                                              → Returns 200 when app is ready
- POST /api/devices                                         → Body: {deviceId, name, location, deviceType} → 201 with device object
- GET  /api/devices/{deviceId}                              → 200 with device object or 404
- PATCH /api/devices/{deviceId}                             → Body: {name?, location?, deviceType?} → 200 with updated device or 404
- DELETE /api/devices/{deviceId}                            → 204 on success, 404 if not found
- GET  /api/devices?location=X                              → 200 with array of devices at location
- POST /api/telemetry                                       → Body: {deviceId, temperature, humidity, batteryLevel, timestamp?} → 201 with {readingId, deviceId, temperature, humidity, batteryLevel, timestamp}
- POST /api/telemetry/batch                                 → Body: array of readings → 201 with {ingested: count}
- GET  /api/devices/{deviceId}/telemetry/latest              → 200 with latest reading or 404
- GET  /api/devices/{deviceId}/telemetry?start=X&end=Y       → 200 with array of readings in time range (ISO-8601)
- GET  /api/devices/{deviceId}/telemetry/stats?period=24h    → 200 with {deviceId, period, temperature:{min,max,avg}, humidity:{min,max,avg}, batteryLevel:{min,max,avg}}
- GET  /api/locations/{location}/telemetry/latest            → 200 with array of {deviceId, temperature, humidity, batteryLevel, timestamp} (latest reading per device at location)

Field naming: use camelCase (deviceId, deviceType, readingId, temperature, humidity, batteryLevel, timestamp).
If no timestamp is provided on ingestion, the server MUST generate one (ISO-8601).
TTL: configure 30-day automatic expiration on telemetry readings.
Deleting a device must also make its telemetry inaccessible (latest returns 404).
Location summary: returns the most recent reading for each device at the specified location.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: java
database: iot-device-telemetry
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

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                                              → Returns 200 when app is ready
- POST /api/devices                                         → Body: {deviceId, name, location, deviceType} → 201 with device object
- GET  /api/devices/{deviceId}                              → 200 with device object or 404
- PATCH /api/devices/{deviceId}                             → Body: {name?, location?, deviceType?} → 200 with updated device or 404
- DELETE /api/devices/{deviceId}                            → 204 on success, 404 if not found
- GET  /api/devices?location=X                              → 200 with array of devices at location
- POST /api/telemetry                                       → Body: {deviceId, temperature, humidity, batteryLevel, timestamp?} → 201 with {readingId, deviceId, temperature, humidity, batteryLevel, timestamp}
- POST /api/telemetry/batch                                 → Body: array of readings → 201 with {ingested: count}
- GET  /api/devices/{deviceId}/telemetry/latest              → 200 with latest reading or 404
- GET  /api/devices/{deviceId}/telemetry?start=X&end=Y       → 200 with array of readings in time range (ISO-8601)
- GET  /api/devices/{deviceId}/telemetry/stats?period=24h    → 200 with {deviceId, period, temperature:{min,max,avg}, humidity:{min,max,avg}, batteryLevel:{min,max,avg}}
- GET  /api/locations/{location}/telemetry/latest            → 200 with array of {deviceId, temperature, humidity, batteryLevel, timestamp} (latest reading per device at location)

Field naming: use camelCase (deviceId, deviceType, readingId, temperature, humidity, batteryLevel, timestamp).
If no timestamp is provided on ingestion, the server MUST generate one (ISO-8601).
TTL: configure 30-day automatic expiration on telemetry readings.
Deleting a device must also make its telemetry inaccessible (latest returns 404).
Location summary: returns the most recent reading for each device at the specified location.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: python
database: iot-device-telemetry
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

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                                              → Returns 200 when app is ready
- POST /api/devices                                         → Body: {deviceId, name, location, deviceType} → 201 with device object
- GET  /api/devices/{deviceId}                              → 200 with device object or 404
- PATCH /api/devices/{deviceId}                             → Body: {name?, location?, deviceType?} → 200 with updated device or 404
- DELETE /api/devices/{deviceId}                            → 204 on success, 404 if not found
- GET  /api/devices?location=X                              → 200 with array of devices at location
- POST /api/telemetry                                       → Body: {deviceId, temperature, humidity, batteryLevel, timestamp?} → 201 with {readingId, deviceId, temperature, humidity, batteryLevel, timestamp}
- POST /api/telemetry/batch                                 → Body: array of readings → 201 with {ingested: count}
- GET  /api/devices/{deviceId}/telemetry/latest              → 200 with latest reading or 404
- GET  /api/devices/{deviceId}/telemetry?start=X&end=Y       → 200 with array of readings in time range (ISO-8601)
- GET  /api/devices/{deviceId}/telemetry/stats?period=24h    → 200 with {deviceId, period, temperature:{min,max,avg}, humidity:{min,max,avg}, batteryLevel:{min,max,avg}}
- GET  /api/locations/{location}/telemetry/latest            → 200 with array of {deviceId, temperature, humidity, batteryLevel, timestamp} (latest reading per device at location)

Field naming: use camelCase (deviceId, deviceType, readingId, temperature, humidity, batteryLevel, timestamp).
If no timestamp is provided on ingestion, the server MUST generate one (ISO-8601).
TTL: configure 30-day automatic expiration on telemetry readings.
Deleting a device must also make its telemetry inaccessible (latest returns 404).
Location summary: returns the most recent reading for each device at the specified location.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: nodejs
database: iot-device-telemetry
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

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                                              → Returns 200 when app is ready
- POST /api/devices                                         → Body: {deviceId, name, location, deviceType} → 201 with device object
- GET  /api/devices/{deviceId}                              → 200 with device object or 404
- PATCH /api/devices/{deviceId}                             → Body: {name?, location?, deviceType?} → 200 with updated device or 404
- DELETE /api/devices/{deviceId}                            → 204 on success, 404 if not found
- GET  /api/devices?location=X                              → 200 with array of devices at location
- POST /api/telemetry                                       → Body: {deviceId, temperature, humidity, batteryLevel, timestamp?} → 201 with {readingId, deviceId, temperature, humidity, batteryLevel, timestamp}
- POST /api/telemetry/batch                                 → Body: array of readings → 201 with {ingested: count}
- GET  /api/devices/{deviceId}/telemetry/latest              → 200 with latest reading or 404
- GET  /api/devices/{deviceId}/telemetry?start=X&end=Y       → 200 with array of readings in time range (ISO-8601)
- GET  /api/devices/{deviceId}/telemetry/stats?period=24h    → 200 with {deviceId, period, temperature:{min,max,avg}, humidity:{min,max,avg}, batteryLevel:{min,max,avg}}
- GET  /api/locations/{location}/telemetry/latest            → 200 with array of {deviceId, temperature, humidity, batteryLevel, timestamp} (latest reading per device at location)

Field naming: use camelCase (deviceId, deviceType, readingId, temperature, humidity, batteryLevel, timestamp).
If no timestamp is provided on ingestion, the server MUST generate one (ISO-8601).
TTL: configure 30-day automatic expiration on telemetry readings.
Deleting a device must also make its telemetry inaccessible (latest returns 404).
Location summary: returns the most recent reading for each device at the specified location.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: go
database: iot-device-telemetry
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
- [ ] Partition key handles time-series data efficiently (not timestamp alone!)
- [ ] TTL is configured correctly for 30-day retention
- [ ] Bulk operations use SDK batch capabilities
- [ ] Queries for device + time range are efficient (single partition)
- [ ] No hot partition issues with high-volume writes
- [ ] All tests in `test_api_contract.py` pass (API contract conformance)
- [ ] All tests in `test_data_integrity.py` pass (data persistence, partition keys, TTL, indexing)
- [ ] `iteration-config.yaml` is present and valid

## Notes

- This scenario specifically tests time-series data patterns
- Common mistakes: using timestamp as partition key (hot partition), not using TTL
- Tests understanding of synthetic/composite partition keys
- High write volume tests bulk ingestion patterns
- Tests are language-agnostic Python HTTP tests — the API under test can be in any language
- See `api-contract.yaml` for the full contract specification
- See `tests/` directory for the complete test suite
