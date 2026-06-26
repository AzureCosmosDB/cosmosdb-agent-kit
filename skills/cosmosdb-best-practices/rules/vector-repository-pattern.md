---
title: Implement Repository Pattern for Vector Search
impact: HIGH
impactDescription: Provides clean abstraction for vector operations and data access
tags: vector, repository, pattern, architecture, vector-search
---

## Implement Repository Pattern for Vector Search

Encapsulate Cosmos DB vector operations in a repository to separate data access from business logic. Key methods: `upsert_document`, `vector_search`, `get_document`, `delete_document`.

**Incorrect (direct container access scattered throughout app):**

```python
# BAD: Vector search logic mixed with API logic, no abstraction
@app.post("/api/search")
async def search(request: SearchRequest):
    query = f"""SELECT TOP {request.limit} c.title,
        VectorDistance(c.embedding, @embedding) AS score FROM c
        ORDER BY VectorDistance(c.embedding, @embedding)"""
```

**Correct (repository pattern):**


```python
class DocumentRepository:
    def __init__(self, container: ContainerProxy):
        self.container = container

    async def vector_search(self, query_embedding: List[float], limit: int = 5,
                            similarity_threshold: float = 0.0,
```

```csharp
// .NET repository
public class DocumentRepository
{
    private readonly Container _container;
    public DocumentRepository(Container container) => _container = container;

```

> Cross-ref: See `query-parameterize` for parameterized queries.
