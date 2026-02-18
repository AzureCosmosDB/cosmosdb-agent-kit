# Scenario: AI Chat Application with RAG

> **Important**: This file defines the fixed requirements for this test scenario. 
> Do NOT modify this file between iterations - the point is to measure improvement 
> with the same requirements.

## Overview

Build an API for an AI-powered chat application that uses Retrieval-Augmented Generation (RAG). The system stores chat history, user sessions, and document embeddings for semantic search.

## Language Suitability

| Language | Suitability | Notes |
|----------|-------------|-------|
| .NET | ✅ Recommended | Full vector search support, excellent AI integration |
| Java | ✅ Recommended | Full vector search support, good for enterprise AI |
| Python | ✅ Recommended | Dominant in AI/ML, full vector search support |
| Node.js | ✅ Suitable | Vector search supported, good for chat interfaces |
| Go | ⚠️ Limited | Vector search SDK support may be limited |
| Rust | 🔬 Experimental | SDK in preview, vector search not guaranteed |

## Requirements

### Functional Requirements

1. Store and retrieve chat conversations (messages with role: user/assistant)
2. Maintain user sessions with context
3. Store document chunks with vector embeddings
4. Perform vector similarity search to find relevant documents
5. Hybrid search: combine vector search with metadata filters
6. Session management (create, continue, list user's sessions)
7. Configurable chat history length per session

### Technical Requirements

- **Language/Framework**: Any supported Cosmos DB SDK language (with vector search support)
  - .NET 8 (ASP.NET Core) - recommended for AI
  - Java 17+ (Spring Boot 3) - full support
  - Python 3.10+ (FastAPI) - recommended for AI/ML
  - Node.js 18+ (Express.js) - supported
  - Go 1.21+ (Gin) - limited vector support
  - Rust (Axum) - experimental, verify vector support
- **Cosmos DB API**: NoSQL with vector search
- **Embedding Model**: text-embedding-ada-002 (1536 dimensions) - mock for testing
- **Authentication**: Connection string (for simplicity in testing)
- **Deployment Target**: Local development only

### Data Model

The system should handle:
- **Sessions**: Chat sessions with metadata (user, title, created date)
- **Messages**: Individual chat messages within sessions
- **Documents**: Document chunks with embeddings for RAG

Expected volume:
- ~100,000 users
- ~10 sessions per user average
- ~50 messages per session average
- ~1 million document chunks with embeddings

### Expected Operations

- [x] Create new chat session
- [x] Add message to session
- [x] Get session history (with pagination)
- [x] List user's sessions
- [x] Store document with embedding
- [x] Vector similarity search (top K similar documents)
- [x] Hybrid search (vector + metadata filter)
- [ ] Bulk document ingestion (optional)

## Prompt to Give Agent

> Copy the appropriate prompt for the language being tested:

### .NET Prompt
```
I need to build a .NET 8 Web API for an AI chat application with RAG (Retrieval-Augmented Generation) using Azure Cosmos DB (NoSQL API).

Requirements:
1. Store chat sessions and messages (user/assistant messages)
2. Create, continue, and list chat sessions per user
3. Store document chunks with vector embeddings (1536 dimensions)
4. Perform vector similarity search to find relevant documents for RAG
5. Support hybrid search: vector similarity + metadata filters (e.g., by category)
6. Paginated retrieval of chat history

Expected scale:
- ~100,000 users
- ~10 sessions per user, ~50 messages per session
- ~1 million document chunks with embeddings

Please create:
1. The data model for sessions, messages, and documents with embeddings
2. The Cosmos DB container configuration with vector indexing
3. A repository layer for data access including vector search
4. REST API endpoints for chat and search operations

Use best practices for Cosmos DB throughout, especially for vector search configuration.
```

### Java Prompt
```
I need to build a Spring Boot 3 REST API for an AI chat application with RAG (Retrieval-Augmented Generation) using Azure Cosmos DB (NoSQL API).

Requirements:
1. Store chat sessions and messages (user/assistant messages)
2. Create, continue, and list chat sessions per user
3. Store document chunks with vector embeddings (1536 dimensions)
4. Perform vector similarity search to find relevant documents for RAG
5. Support hybrid search: vector similarity + metadata filters (e.g., by category)
6. Paginated retrieval of chat history

Expected scale:
- ~100,000 users
- ~10 sessions per user, ~50 messages per session
- ~1 million document chunks with embeddings

Please create:
1. The data model for sessions, messages, and documents with embeddings
2. The Cosmos DB container configuration with vector indexing
3. A repository layer for data access including vector search
4. REST API endpoints for chat and search operations

Use best practices for Cosmos DB throughout, especially for vector search configuration.
```

### Python Prompt
```
I need to build a FastAPI REST API for an AI chat application with RAG (Retrieval-Augmented Generation) using Azure Cosmos DB (NoSQL API).

Requirements:
1. Store chat sessions and messages (user/assistant messages)
2. Create, continue, and list chat sessions per user
3. Store document chunks with vector embeddings (1536 dimensions)
4. Perform vector similarity search to find relevant documents for RAG
5. Support hybrid search: vector similarity + metadata filters (e.g., by category)
6. Paginated retrieval of chat history

Expected scale:
- ~100,000 users
- ~10 sessions per user, ~50 messages per session
- ~1 million document chunks with embeddings

Please create:
1. The data model for sessions, messages, and documents with embeddings
2. The Cosmos DB container configuration with vector indexing
3. A repository layer for data access including vector search
4. REST API endpoints for chat and search operations

Use best practices for Cosmos DB throughout, especially for vector search configuration.
```

### Node.js Prompt
```
I need to build an Express.js REST API for an AI chat application with RAG (Retrieval-Augmented Generation) using Azure Cosmos DB (NoSQL API).

Requirements:
1. Store chat sessions and messages (user/assistant messages)
2. Create, continue, and list chat sessions per user
3. Store document chunks with vector embeddings (1536 dimensions)
4. Perform vector similarity search to find relevant documents for RAG
5. Support hybrid search: vector similarity + metadata filters (e.g., by category)
6. Paginated retrieval of chat history

Expected scale:
- ~100,000 users
- ~10 sessions per user, ~50 messages per session
- ~1 million document chunks with embeddings

Please create:
1. The data model for sessions, messages, and documents with embeddings
2. The Cosmos DB container configuration with vector indexing
3. A repository layer for data access including vector search
4. REST API routes for chat and search operations

Use best practices for Cosmos DB throughout, especially for vector search configuration.
```

### Go Prompt (Limited Vector Support)
```
I need to build a Go REST API (using Gin) for an AI chat application with RAG (Retrieval-Augmented Generation) using Azure Cosmos DB (NoSQL API).

Note: The Go SDK may have limited vector search support. Please indicate if any features are not available.

Requirements:
1. Store chat sessions and messages (user/assistant messages)
2. Create, continue, and list chat sessions per user
3. Store document chunks with vector embeddings (1536 dimensions)
4. Perform vector similarity search to find relevant documents for RAG
5. Support hybrid search: vector similarity + metadata filters (e.g., by category)
6. Paginated retrieval of chat history

Expected scale:
- ~100,000 users
- ~10 sessions per user, ~50 messages per session
- ~1 million document chunks with embeddings

Please create:
1. The data model for sessions, messages, and documents with embeddings
2. The Cosmos DB container configuration with vector indexing
3. A repository layer for data access including vector search
4. REST API handlers for chat and search operations

Use best practices for Cosmos DB throughout, especially for vector search configuration.
```

## Success Criteria

What does "done" look like for this scenario?

- [ ] API compiles and runs locally
- [ ] Vector index is configured correctly (DiskANN or similar)
- [ ] Embedding property correctly defined in container
- [ ] Vector search queries use proper SDK methods
- [ ] Chat history is partitioned by session/user efficiently
- [ ] Hybrid search combines vector + filters correctly

## Notes

- This scenario tests newer Cosmos DB vector search capabilities
- Validates agent's knowledge of vector indexing configuration
- Tests understanding of embedding storage patterns
- Common mistakes: wrong vector index type, missing vector policy
- May reveal gaps in skills around vector search (newer feature)
