# AI Chat RAG API - Python Implementation

AI-powered chat application with Retrieval-Augmented Generation (RAG) using Azure Cosmos DB vector search.

## Features

- ✅ Chat session management with embedded messages
- ✅ Vector similarity search for document retrieval
- ✅ Hybrid search (vector + metadata filters)
- ✅ Azure AD authentication (DefaultAzureCredential)
- ✅ Full Cosmos DB best practices applied

## Cosmos DB Best Practices Applied

### Data Modeling (CRITICAL)
- **Rule 1.3**: Messages embedded within sessions for single-document retrieval
- **Rule 1.6**: Type discriminators for polymorphic queries

### Partition Key Design (CRITICAL)
- **Rule 2.4**: High-cardinality partition keys (userId, category)
- **Rule 2.5**: Partition keys aligned with query patterns

### Query Optimization (HIGH)
- **Rule 3.1**: Single-partition queries for user sessions
- **Rule 3.5**: Parameterized queries for plan caching

### SDK Best Practices (HIGH)
- **Rule 4.4**: Direct connection mode (default in Python SDK)
- **Rule 4.10**: Explicit environment variable loading with override
- **Rule 4.14**: Singleton CosmosClient instance

### Throughput & Scaling (MEDIUM)
- **Rule 6.1**: Autoscale throughput (1000-4000 RU/s) for variable workloads

### Vector Search (CRITICAL - NEW)
- **Rule 10.1**: Vector embedding policy (1536 dimensions, cosine distance)
- **Rule 10.2**: QuantizedFlat vector indexes for <50K documents
- **Rule 10.3**: Embedding paths excluded from regular indexing
- **Rule 10.4**: VectorDistance() queries with ORDER BY

## Setup

### Prerequisites

- Python 3.10+
- Azure Cosmos DB account with vector search enabled
- Azure CLI logged in (`az login`) for DefaultAzureCredential

### Installation

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Configuration

The application uses DefaultAzureCredential (Azure AD) for authentication.

Configure `.env`:
```env
COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_DATABASE=ai-chat-rag-db
```

## Running the Application

```bash
python main.py
```

Application will start on `http://0.0.0.0:8000`

## API Endpoints

### Health Check
```
GET /health
```

### Chat Sessions
```
POST /api/chat/sessions
Body: {"userId": "user-001", "title": "My Chat"}

GET /api/chat/users/{userId}/sessions
Returns: List of sessions for user

GET /api/chat/sessions/{sessionId}?user_id={userId}
Returns: Session with all messages
```

### Messages
```
POST /api/chat/messages
Body: {"sessionId": "...", "role": "user", "content": "Hello"}
```

### Documents
```
POST /api/documents
Body: {
  "category": "technical",
  "title": "Azure Cosmos DB Guide",
  "content": "...",
  "embedding": [0.1, 0.2, ..., 0.5],  # 1536 floats
  "metadata": {"author": "..."}
}
```

### Vector Search
```
POST /api/documents/search
Body: {
  "embedding": [0.1, 0.2, ..., 0.5],  # 1536 floats
  "top_k": 10,
  "category": "technical"  # Optional: hybrid search
}
```

## Testing with Mock Embeddings

For testing without an embedding model:

```python
import random

# Generate mock embedding (1536 dimensions)
mock_embedding = [random.random() for _ in range(1536)]
```

```bash
# Example: Create session
curl -X POST http://localhost:8000/api/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"userId":"test-user","title":"Test Chat"}'

# Example: Store document with mock embedding
curl -X POST http://localhost:8000/api/documents \
  -H "Content-Type: application/json" \
  -d '{
    "category": "test",
    "title": "Test Document",
    "content": "This is a test",
    "embedding": [0.1, 0.2, ...],
    "metadata": {}
  }'
```

## Architecture

```
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── models.py            # Pydantic models
├── cosmos_service.py    # Cosmos DB service layer
├── requirements.txt     # Dependencies
└── .env                 # Configuration (not in git)
```

## Cosmos DB Containers

### sessions
- **Partition Key**: `/userId`
- **Throughput**: Autoscale 1000-4000 RU/s
- **Pattern**: Embedded messages for single-document reads

### documents
- **Partition Key**: `/category`
- **Throughput**: Autoscale 1000-4000 RU/s
- **Vector Search**: Enabled with QuantizedFlat index
- **Embedding**: 1536 dimensions, cosine distance
- **Indexing**: Vector path excluded for performance

## Notes

- Using Azure AD (DefaultAzureCredential) - no connection string needed
- Containers are created automatically on first run
- Vector embeddings are mock data for testing
- In production, integrate with Azure OpenAI for real embeddings
