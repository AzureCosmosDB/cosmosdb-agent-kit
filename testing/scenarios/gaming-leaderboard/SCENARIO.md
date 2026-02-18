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

## Prompt to Give Agent

> Copy the appropriate prompt for the language being tested:

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
```

## Success Criteria

What does "done" look like for this scenario?

- [ ] API compiles and runs locally
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
