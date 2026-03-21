# Scenario: Gaming Leaderboard

> **Important**: This file defines the fixed requirements for this test scenario. 
> Do NOT modify this file between iterations - the point is to measure improvement 
> with the same requirements.

## Overview

Build an API for a mobile game's leaderboard system. The system needs to handle real-time score updates, display global and regional leaderboards, and support player profile queries.

## Language Suitability

| Language | Suitability | Notes |
|----------|-------------|-------|
| .NET | ✅ Recommended | Excellent for real-time game backends, strong async support |
| Java | ✅ Recommended | Popular for game backends, good async capabilities |
| Python | ⚠️ Suitable | Less common for real-time gaming due to GIL limitations |
| Node.js | ✅ Recommended | Great for real-time updates, high concurrency |
| Go | ✅ Recommended | Excellent performance for high-throughput scenarios |
| Rust | 🔬 Experimental | High performance, but SDK is in preview |

## Requirements

### Functional Requirements

1. Players can submit scores after completing a game
2. Display global top 100 leaderboard
3. Display regional leaderboards (by country)
4. Get a player's rank and nearby players (±10 positions)
5. Get a player's profile with stats (total games, best score, etc.)
6. Weekly leaderboard reset (historical data kept)
7. Real-time score updates reflected immediately

### Technical Requirements

- **Language/Framework**: Any supported Cosmos DB SDK language
  - .NET 8 (ASP.NET Core)
  - Java 17+ (Spring Boot 3)
  - Python 3.10+ (FastAPI)
  - Node.js 18+ (Express.js)
  - Go 1.21+ (Gin)
  - Rust (Axum) - experimental
- **Cosmos DB API**: NoSQL
- **Authentication**: Connection string (for simplicity in testing)
- **Deployment Target**: Local development only

### Data Model

The system should handle:
- **Players**: Player profiles with cumulative stats
- **Scores**: Individual game scores with timestamps
- **Leaderboards**: Aggregated ranking data

Expected volume:
- ~500,000 active players
- ~50,000 concurrent players at peak
- ~1 million scores submitted per day
- Leaderboard queries: very high read volume

### Expected Operations

- [x] Submit a new score
- [x] Get global top 100
- [x] Get regional top 100
- [x] Get player rank + surrounding players
- [x] Get player profile/stats
- [x] Update player cumulative stats
- [ ] Bulk operations (not required)
- [ ] Transactions (optional for score + stats update)

## API Contract (V2)

This scenario has a **fixed API contract** defined in [`api-contract.yaml`](api-contract.yaml).
Automated tests in the [`tests/`](tests/) directory validate implementations against this contract.

**The agent MUST implement these exact endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (returns 200 when ready) |
| POST | `/api/players` | Create a player profile |
| GET | `/api/players/{playerId}` | Get player profile with stats |
| PATCH | `/api/players/{playerId}` | Update player profile |
| DELETE | `/api/players/{playerId}` | Delete player and associated data |
| POST | `/api/scores` | Submit a game score |
| GET | `/api/players/{playerId}/scores?limit=N` | Player score history (most recent first) |
| GET | `/api/leaderboards/global?top=N` | Global top N leaderboard (tiebreak: displayName asc) |
| GET | `/api/leaderboards/regional/{region}?top=N` | Regional top N leaderboard (same tiebreak) |
| GET | `/api/players/{playerId}/rank` | Player rank + ±10 neighbors |

**The agent MUST also create `iteration-config.yaml`** in the iteration folder.
See `testing-v2/scenarios/_iteration-config-template.yaml` for the template.

## Prompt to Give Agent

> Copy the appropriate prompt for the language being tested.
> Each prompt includes the API contract requirements that the agent must follow.

### .NET Prompt
```
I need to build a .NET 8 Web API for a mobile game leaderboard system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Players submit scores after completing games
2. Display global top 100 leaderboard (sorted by high score)
3. Display regional leaderboards by country
4. Get a specific player's rank and the 10 players above/below them
5. Get player profiles with stats (total games played, best score, average score)
6. Support weekly leaderboard periods (keep historical data)

Expected scale:
- ~500,000 active players
- ~1 million score submissions per day
- Very high read volume on leaderboard queries
- Low latency requirements (< 50ms for leaderboard reads)

Please create:
1. The data model optimized for leaderboard queries
2. The Cosmos DB container configuration
3. A repository layer for data access
4. REST API endpoints for the required operations

Use best practices for Cosmos DB throughout. Consider how to efficiently handle "top N" queries and player ranking.

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                              → Returns 200 when app is ready
- POST /api/players                         → Body: {playerId, displayName, region} → 201 with {playerId, displayName, region, totalGames, bestScore, averageScore}
- GET  /api/players/{playerId}              → 200 with {playerId, displayName, region, totalGames, bestScore, averageScore} or 404
- PATCH /api/players/{playerId}             → Body: {displayName?, region?} → 200 with updated player or 404
- DELETE /api/players/{playerId}            → 204 on success, 404 if not found
- POST /api/scores                          → Body: {playerId, score, gameMode?} → 201 with {scoreId, playerId, score}
- GET  /api/players/{playerId}/scores?limit=N → 200 with array of {scoreId, playerId, score, gameMode, timestamp} most recent first (default limit=10)
- GET  /api/leaderboards/global?top=N       → 200 with array of {rank, playerId, displayName, score} sorted by score desc, then displayName asc for ties
- GET  /api/leaderboards/regional/{region}?top=N → 200 with array of {rank, playerId, displayName, score} for that region, same tiebreaking
- GET  /api/players/{playerId}/rank          → 200 with {playerId, rank, score, neighbors[]} or 404

Field naming: use camelCase (playerId, displayName, totalGames, bestScore, averageScore, scoreId, gameMode).
New players must have totalGames=0, bestScore=0, averageScore=0.
Leaderboard rank is 1-based. Global leaderboard default top=100.
Leaderboard tiebreaking: when two players have the same score, sort by displayName ascending.
Score history default limit=10, sorted most-recent-first. GET /api/players/{playerId}/scores returns 404 for deleted players.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: dotnet
database: gaming-leaderboard
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
I need to build a Spring Boot 3 REST API for a mobile game leaderboard system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Players submit scores after completing games
2. Display global top 100 leaderboard (sorted by high score)
3. Display regional leaderboards by country
4. Get a specific player's rank and the 10 players above/below them
5. Get player profiles with stats (total games played, best score, average score)
6. Support weekly leaderboard periods (keep historical data)

Expected scale:
- ~500,000 active players
- ~1 million score submissions per day
- Very high read volume on leaderboard queries
- Low latency requirements (< 50ms for leaderboard reads)

Please create:
1. The data model optimized for leaderboard queries
2. The Cosmos DB container configuration
3. A repository layer for data access
4. REST API endpoints for the required operations

Use best practices for Cosmos DB throughout. Consider how to efficiently handle "top N" queries and player ranking.

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                              → Returns 200 when app is ready
- POST /api/players                         → Body: {playerId, displayName, region} → 201 with {playerId, displayName, region, totalGames, bestScore, averageScore}
- GET  /api/players/{playerId}              → 200 with {playerId, displayName, region, totalGames, bestScore, averageScore} or 404
- PATCH /api/players/{playerId}             → Body: {displayName?, region?} → 200 with updated player or 404
- DELETE /api/players/{playerId}            → 204 on success, 404 if not found
- POST /api/scores                          → Body: {playerId, score, gameMode?} → 201 with {scoreId, playerId, score}
- GET  /api/players/{playerId}/scores?limit=N → 200 with array of {scoreId, playerId, score, gameMode, timestamp} most recent first (default limit=10)
- GET  /api/leaderboards/global?top=N       → 200 with array of {rank, playerId, displayName, score} sorted by score desc, then displayName asc for ties
- GET  /api/leaderboards/regional/{region}?top=N → 200 with array of {rank, playerId, displayName, score} for that region, same tiebreaking
- GET  /api/players/{playerId}/rank          → 200 with {playerId, rank, score, neighbors[]} or 404

Field naming: use camelCase (playerId, displayName, totalGames, bestScore, averageScore, scoreId, gameMode).
New players must have totalGames=0, bestScore=0, averageScore=0.
Leaderboard rank is 1-based. Global leaderboard default top=100.
Leaderboard tiebreaking: when two players have the same score, sort by displayName ascending.
Score history default limit=10, sorted most-recent-first. GET /api/players/{playerId}/scores returns 404 for deleted players.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: java
database: gaming-leaderboard
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
I need to build a FastAPI REST API for a mobile game leaderboard system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Players submit scores after completing games
2. Display global top 100 leaderboard (sorted by high score)
3. Display regional leaderboards by country
4. Get a specific player's rank and the 10 players above/below them
5. Get player profiles with stats (total games played, best score, average score)
6. Support weekly leaderboard periods (keep historical data)

Expected scale:
- ~500,000 active players
- ~1 million score submissions per day
- Very high read volume on leaderboard queries
- Low latency requirements (< 50ms for leaderboard reads)

Please create:
1. The data model optimized for leaderboard queries
2. The Cosmos DB container configuration
3. A repository layer for data access
4. REST API endpoints for the required operations

Use best practices for Cosmos DB throughout. Consider how to efficiently handle "top N" queries and player ranking.

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                              → Returns 200 when app is ready
- POST /api/players                         → Body: {playerId, displayName, region} → 201 with {playerId, displayName, region, totalGames, bestScore, averageScore}
- GET  /api/players/{playerId}              → 200 with {playerId, displayName, region, totalGames, bestScore, averageScore} or 404
- PATCH /api/players/{playerId}             → Body: {displayName?, region?} → 200 with updated player or 404
- DELETE /api/players/{playerId}            → 204 on success, 404 if not found
- POST /api/scores                          → Body: {playerId, score, gameMode?} → 201 with {scoreId, playerId, score}
- GET  /api/players/{playerId}/scores?limit=N → 200 with array of {scoreId, playerId, score, gameMode, timestamp} most recent first (default limit=10)
- GET  /api/leaderboards/global?top=N       → 200 with array of {rank, playerId, displayName, score} sorted by score desc, then displayName asc for ties
- GET  /api/leaderboards/regional/{region}?top=N → 200 with array of {rank, playerId, displayName, score} for that region, same tiebreaking
- GET  /api/players/{playerId}/rank          → 200 with {playerId, rank, score, neighbors[]} or 404

Field naming: use camelCase (playerId, displayName, totalGames, bestScore, averageScore, scoreId, gameMode).
New players must have totalGames=0, bestScore=0, averageScore=0.
Leaderboard rank is 1-based. Global leaderboard default top=100.
Leaderboard tiebreaking: when two players have the same score, sort by displayName ascending.
Score history default limit=10, sorted most-recent-first. GET /api/players/{playerId}/scores returns 404 for deleted players.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: python
database: gaming-leaderboard
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
I need to build an Express.js REST API for a mobile game leaderboard system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Players submit scores after completing games
2. Display global top 100 leaderboard (sorted by high score)
3. Display regional leaderboards by country
4. Get a specific player's rank and the 10 players above/below them
5. Get player profiles with stats (total games played, best score, average score)
6. Support weekly leaderboard periods (keep historical data)

Expected scale:
- ~500,000 active players
- ~1 million score submissions per day
- Very high read volume on leaderboard queries
- Low latency requirements (< 50ms for leaderboard reads)

Please create:
1. The data model optimized for leaderboard queries
2. The Cosmos DB container configuration
3. A repository layer for data access
4. REST API routes for the required operations

Use best practices for Cosmos DB throughout. Consider how to efficiently handle "top N" queries and player ranking.

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                              → Returns 200 when app is ready
- POST /api/players                         → Body: {playerId, displayName, region} → 201 with {playerId, displayName, region, totalGames, bestScore, averageScore}
- GET  /api/players/{playerId}              → 200 with {playerId, displayName, region, totalGames, bestScore, averageScore} or 404
- PATCH /api/players/{playerId}             → Body: {displayName?, region?} → 200 with updated player or 404
- DELETE /api/players/{playerId}            → 204 on success, 404 if not found
- POST /api/scores                          → Body: {playerId, score, gameMode?} → 201 with {scoreId, playerId, score}
- GET  /api/players/{playerId}/scores?limit=N → 200 with array of {scoreId, playerId, score, gameMode, timestamp} most recent first (default limit=10)
- GET  /api/leaderboards/global?top=N       → 200 with array of {rank, playerId, displayName, score} sorted by score desc, then displayName asc for ties
- GET  /api/leaderboards/regional/{region}?top=N → 200 with array of {rank, playerId, displayName, score} for that region, same tiebreaking
- GET  /api/players/{playerId}/rank          → 200 with {playerId, rank, score, neighbors[]} or 404

Field naming: use camelCase (playerId, displayName, totalGames, bestScore, averageScore, scoreId, gameMode).
New players must have totalGames=0, bestScore=0, averageScore=0.
Leaderboard rank is 1-based. Global leaderboard default top=100.
Leaderboard tiebreaking: when two players have the same score, sort by displayName ascending.
Score history default limit=10, sorted most-recent-first. GET /api/players/{playerId}/scores returns 404 for deleted players.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: nodejs
database: gaming-leaderboard
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
I need to build a Go REST API (using Gin) for a mobile game leaderboard system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Players submit scores after completing games
2. Display global top 100 leaderboard (sorted by high score)
3. Display regional leaderboards by country
4. Get a specific player's rank and the 10 players above/below them
5. Get player profiles with stats (total games played, best score, average score)
6. Support weekly leaderboard periods (keep historical data)

Expected scale:
- ~500,000 active players
- ~1 million score submissions per day
- Very high read volume on leaderboard queries
- Low latency requirements (< 50ms for leaderboard reads)

Please create:
1. The data model optimized for leaderboard queries
2. The Cosmos DB container configuration
3. A repository layer for data access
4. REST API handlers for the required operations

Use best practices for Cosmos DB throughout. Consider how to efficiently handle "top N" queries and player ranking.

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                              → Returns 200 when app is ready
- POST /api/players                         → Body: {playerId, displayName, region} → 201 with {playerId, displayName, region, totalGames, bestScore, averageScore}
- GET  /api/players/{playerId}              → 200 with {playerId, displayName, region, totalGames, bestScore, averageScore} or 404
- PATCH /api/players/{playerId}             → Body: {displayName?, region?} → 200 with updated player or 404
- DELETE /api/players/{playerId}            → 204 on success, 404 if not found
- POST /api/scores                          → Body: {playerId, score, gameMode?} → 201 with {scoreId, playerId, score}
- GET  /api/players/{playerId}/scores?limit=N → 200 with array of {scoreId, playerId, score, gameMode, timestamp} most recent first (default limit=10)
- GET  /api/leaderboards/global?top=N       → 200 with array of {rank, playerId, displayName, score} sorted by score desc, then displayName asc for ties
- GET  /api/leaderboards/regional/{region}?top=N → 200 with array of {rank, playerId, displayName, score} for that region, same tiebreaking
- GET  /api/players/{playerId}/rank          → 200 with {playerId, rank, score, neighbors[]} or 404

Field naming: use camelCase (playerId, displayName, totalGames, bestScore, averageScore, scoreId, gameMode).
New players must have totalGames=0, bestScore=0, averageScore=0.
Leaderboard rank is 1-based. Global leaderboard default top=100.
Leaderboard tiebreaking: when two players have the same score, sort by displayName ascending.
Score history default limit=10, sorted most-recent-first. GET /api/players/{playerId}/scores returns 404 for deleted players.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: go
database: gaming-leaderboard
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

- [ ] API compiles and runs (`iteration-config.yaml` build/run commands succeed)
- [ ] All API contract tests pass (`test_api_contract.py`)
- [ ] All data integrity tests pass (`test_data_integrity.py`)
- [ ] Leaderboard reads are efficient (consider materialized views or caching strategy)
- [ ] Player score submission doesn't create hot partitions
- [ ] Player rank lookup is reasonably efficient
- [ ] Data model handles both current and historical leaderboards
- [ ] Regional partitioning is handled correctly

## Notes

- This scenario tests read-heavy patterns and sorting challenges
- Common mistakes: trying to sort across partitions, hot partitions for global leaderboard
- May require discussion of materialized views or change feed for leaderboard aggregation
- Tests understanding of denormalization for read performance
- "Top N" queries across all data is an anti-pattern - tests if agent recognizes this
