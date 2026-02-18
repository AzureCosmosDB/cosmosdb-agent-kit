# AI Chat RAG API - .NET Implementation

## Overview

This is a .NET 8 Web API for an AI-powered chat application with RAG (Retrieval-Augmented Generation) using Azure Cosmos DB NoSQL API with vector search.

## Prerequisites

- .NET 8 SDK
- Azure Cosmos DB Emulator (running on https://localhost:8081)

## Build & Run

```bash
cd AIChatRAG.Api
dotnet restore
dotnet build
dotnet run
```

The API will start on `https://localhost:7000` (or configured port).

## API Endpoints

### Chat Sessions

- `POST /api/chat/sessions` - Create new chat session
- `GET /api/chat/sessions/{sessionId}?userId={userId}` - Get session details
- `POST /api/chat/messages` - Add message to session
- `GET /api/chat/sessions?userId={userId}&maxItems=20` - List user's sessions
- `GET /api/chat/sessions/{sessionId}/history?userId={userId}&maxMessages=50` - Get session history

### Documents & Vector Search

- `POST /api/documents` - Store document chunk with embedding
- `POST /api/documents/bulk` - Bulk store document chunks
- `GET /api/documents/{documentId}?category={category}` - Get all chunks for a document
- `POST /api/documents/search` - Vector similarity search

## Vector Search Example

```json
POST /api/documents/search
{
  "queryEmbedding": [0.1, 0.2, ..., 0.5],  // 1536 dimensions
  "topK": 5,
  "category": "technical-docs"  // Optional: hybrid search
}
```

## Best Practices Applied

- Rule 1.2: Denormalized message count
- Rule 1.3: Embedded messages for read efficiency
- Rule 1.5: Schema versioning
- Rule 1.6: Type discriminators
- Rule 2.5: Partition key aligned with access patterns
- Rule 3.1: Single-partition queries
- Rule 3.4: Pagination with continuation tokens
- Rule 3.5: Parameterized queries
- Rule 3.6: ORDER BY with composite indexes
- Rule 4.1: Async operations
- Rule 4.3: Direct connection mode
- Rule 4.13: Singleton CosmosClient
- Rule 5.1: Composite indexes
- Rule 5.2: Exclude large arrays from indexing
- Rule 6.1: Autoscale throughput

## Vector Search Configuration

The documents container is configured with:
- **Vector Embedding Policy**: Defines `/embedding` property (1536 dimensions, Float32, Cosine distance)
- **Vector Index**: DiskANN index type (recommended for production)
- **Indexing Policy**: Excludes `/embedding` array from regular indexing (critical for performance)

## Testing

Use Swagger UI at `https://localhost:7000/swagger` or test with curl:

```bash
# Create session
curl -X POST https://localhost:7000/api/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"userId":"user1","title":"My Chat"}'

# Add message
curl -X POST https://localhost:7000/api/chat/messages \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"...","userId":"user1","role":"user","content":"Hello!"}'
```
