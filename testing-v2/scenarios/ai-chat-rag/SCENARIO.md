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

## API Contract (V2)

This scenario has a **fixed API contract** defined in `api-contract.yaml`. All iterations must implement this exact interface. Tests in `tests/` validate conformance automatically.

| Endpoint | Method | Path |
|----------|--------|------|
| Health check | GET | `/health` |
| Create session | POST | `/api/sessions` |
| Get session | GET | `/api/sessions/{sessionId}` |
| List user sessions | GET | `/api/users/{userId}/sessions` |
| Add message | POST | `/api/sessions/{sessionId}/messages` |
| Store document | POST | `/api/documents` |
| Vector search | POST | `/api/search/vector` |
| Hybrid search | POST | `/api/search/hybrid` |

Vector search tests use **mock embeddings** (1536-dimension float arrays). The app does NOT need a real embedding model.

Each language prompt below includes the contract requirements and an `iteration-config.yaml` block.

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

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                                → Returns 200 when app is ready
- POST /api/sessions                          → Body: {userId, title} → 201 with {sessionId, userId, title, createdAt}
- GET  /api/sessions/{sessionId}              → 200 with {sessionId, userId, title, messages[], createdAt} or 404
- GET  /api/users/{userId}/sessions           → 200 with array of sessions
- POST /api/sessions/{sessionId}/messages     → Body: {role, content} → 201 with {sessionId, role, content, timestamp} or 404
- POST /api/documents                         → Body: {content, embedding[1536 floats], metadata:{category?, source?}} → 201 with {documentId, content, metadata}
- POST /api/search/vector                     → Body: {embedding[1536 floats], topK?} → 200 with array of {documentId, content, score, metadata?}
- POST /api/search/hybrid                     → Body: {embedding[1536 floats], filters:{category?, source?}, topK?} → 200 with filtered results

Field naming: use camelCase (sessionId, userId, createdAt, documentId, topK).
Role values: "user" or "assistant".
Embeddings are arrays of 1536 floats — the app stores and searches pre-computed vectors (no embedding model needed).
Vector index: configure DiskANN or flat index for the embedding property.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: dotnet
database: ai-chat-rag
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

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                                → Returns 200 when app is ready
- POST /api/sessions                          → Body: {userId, title} → 201 with {sessionId, userId, title, createdAt}
- GET  /api/sessions/{sessionId}              → 200 with {sessionId, userId, title, messages[], createdAt} or 404
- GET  /api/users/{userId}/sessions           → 200 with array of sessions
- POST /api/sessions/{sessionId}/messages     → Body: {role, content} → 201 with {sessionId, role, content, timestamp} or 404
- POST /api/documents                         → Body: {content, embedding[1536 floats], metadata:{category?, source?}} → 201 with {documentId, content, metadata}
- POST /api/search/vector                     → Body: {embedding[1536 floats], topK?} → 200 with array of {documentId, content, score, metadata?}
- POST /api/search/hybrid                     → Body: {embedding[1536 floats], filters:{category?, source?}, topK?} → 200 with filtered results

Field naming: use camelCase (sessionId, userId, createdAt, documentId, topK).
Role values: "user" or "assistant".
Embeddings are arrays of 1536 floats — the app stores and searches pre-computed vectors (no embedding model needed).
Vector index: configure DiskANN or flat index for the embedding property.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: java
database: ai-chat-rag
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

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                                → Returns 200 when app is ready
- POST /api/sessions                          → Body: {userId, title} → 201 with {sessionId, userId, title, createdAt}
- GET  /api/sessions/{sessionId}              → 200 with {sessionId, userId, title, messages[], createdAt} or 404
- GET  /api/users/{userId}/sessions           → 200 with array of sessions
- POST /api/sessions/{sessionId}/messages     → Body: {role, content} → 201 with {sessionId, role, content, timestamp} or 404
- POST /api/documents                         → Body: {content, embedding[1536 floats], metadata:{category?, source?}} → 201 with {documentId, content, metadata}
- POST /api/search/vector                     → Body: {embedding[1536 floats], topK?} → 200 with array of {documentId, content, score, metadata?}
- POST /api/search/hybrid                     → Body: {embedding[1536 floats], filters:{category?, source?}, topK?} → 200 with filtered results

Field naming: use camelCase (sessionId, userId, createdAt, documentId, topK).
Role values: "user" or "assistant".
Embeddings are arrays of 1536 floats — the app stores and searches pre-computed vectors (no embedding model needed).
Vector index: configure DiskANN or flat index for the embedding property.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: python
database: ai-chat-rag
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

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                                → Returns 200 when app is ready
- POST /api/sessions                          → Body: {userId, title} → 201 with {sessionId, userId, title, createdAt}
- GET  /api/sessions/{sessionId}              → 200 with {sessionId, userId, title, messages[], createdAt} or 404
- GET  /api/users/{userId}/sessions           → 200 with array of sessions
- POST /api/sessions/{sessionId}/messages     → Body: {role, content} → 201 with {sessionId, role, content, timestamp} or 404
- POST /api/documents                         → Body: {content, embedding[1536 floats], metadata:{category?, source?}} → 201 with {documentId, content, metadata}
- POST /api/search/vector                     → Body: {embedding[1536 floats], topK?} → 200 with array of {documentId, content, score, metadata?}
- POST /api/search/hybrid                     → Body: {embedding[1536 floats], filters:{category?, source?}, topK?} → 200 with filtered results

Field naming: use camelCase (sessionId, userId, createdAt, documentId, topK).
Role values: "user" or "assistant".
Embeddings are arrays of 1536 floats — the app stores and searches pre-computed vectors (no embedding model needed).
Vector index: configure DiskANN or flat index for the embedding property.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: nodejs
database: ai-chat-rag
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

---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                                → Returns 200 when app is ready
- POST /api/sessions                          → Body: {userId, title} → 201 with {sessionId, userId, title, createdAt}
- GET  /api/sessions/{sessionId}              → 200 with {sessionId, userId, title, messages[], createdAt} or 404
- GET  /api/users/{userId}/sessions           → 200 with array of sessions
- POST /api/sessions/{sessionId}/messages     → Body: {role, content} → 201 with {sessionId, role, content, timestamp} or 404
- POST /api/documents                         → Body: {content, embedding[1536 floats], metadata:{category?, source?}} → 201 with {documentId, content, metadata}
- POST /api/search/vector                     → Body: {embedding[1536 floats], topK?} → 200 with array of {documentId, content, score, metadata?}
- POST /api/search/hybrid                     → Body: {embedding[1536 floats], filters:{category?, source?}, topK?} → 200 with filtered results

Field naming: use camelCase (sessionId, userId, createdAt, documentId, topK).
Role values: "user" or "assistant".
Embeddings are arrays of 1536 floats — the app stores and searches pre-computed vectors (no embedding model needed).
Vector index: configure DiskANN or flat index for the embedding property.
Note: If Go SDK lacks native vector search, use raw SQL queries with VectorDistance() function.

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: go
database: ai-chat-rag
port: 8080
health: /health
build: go build -o server.exe .
run: .\server.exe
```

The Cosmos DB connection uses environment variables:
- COSMOS_ENDPOINT (default: https://localhost:8081)
- COSMOS_KEY (default: the standard emulator key)

Do NOT hardcode connection strings. Read them from environment variables or configuration.
```

## Success Criteria

What does "done" look like for this scenario?

- [ ] API compiles and runs locally
- [ ] Vector index is configured correctly (DiskANN or similar)
- [ ] Embedding property correctly defined in container
- [ ] Vector search queries use proper SDK methods
- [ ] Chat history is partitioned by session/user efficiently
- [ ] Hybrid search combines vector + filters correctly
- [ ] All tests in `test_api_contract.py` pass (API contract conformance)
- [ ] All tests in `test_data_integrity.py` pass (data persistence, partition keys, vector index, indexing)
- [ ] `iteration-config.yaml` is present and valid

## Notes

- This scenario tests newer Cosmos DB vector search capabilities
- Validates agent's knowledge of vector indexing configuration
- Tests understanding of embedding storage patterns
- Common mistakes: wrong vector index type, missing vector policy
- May reveal gaps in skills around vector search (newer feature)
- Tests are language-agnostic Python HTTP tests — the API under test can be in any language
- See `api-contract.yaml` for the full contract specification
- See `tests/` directory for the complete test suite
