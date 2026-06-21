# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Best practices for Azure Cosmos DB vector search: enabling the feature, embedding policies, vector index types, embedding normalization, distance queries, and repository patterns for RAG.

---

## Table of Contents

1. [Vector Search](#1-vector-search) — **HIGH**
   - 1.1 [Use VectorDistance for Similarity Search](#11-use-vectordistance-for-similarity-search)
   - 1.2 [Define Vector Embedding Policy](#12-define-vector-embedding-policy)
   - 1.3 [Enable Vector Search Feature on Account](#13-enable-vector-search-feature-on-account)
   - 1.4 [Configure Vector Indexes in Indexing Policy](#14-configure-vector-indexes-in-indexing-policy)
   - 1.5 [Normalize Embeddings for Cosine Similarity](#15-normalize-embeddings-for-cosine-similarity)
   - 1.6 [Implement Repository Pattern for Vector Search](#16-implement-repository-pattern-for-vector-search)

---

## 1. Vector Search

**Impact: HIGH**

### 1.1 Use VectorDistance for Similarity Search

**Impact: HIGH** (Enables semantic search and RAG patterns)

## Use VectorDistance for Similarity Search

**Impact: HIGH (Enables semantic search and RAG patterns)**

Use the VectorDistance() system function to perform vector similarity searches. This function computes the distance between a query vector and stored vectors using the distance function specified in the vector embedding policy.

**Query Pattern:**
```sql
SELECT TOP N c.property, VectorDistance(c.vectorPath, @embedding) AS SimilarityScore
FROM c
ORDER BY VectorDistance(c.vectorPath, @embedding)
```

**Incorrect (missing ORDER BY or parameterization):**

```csharp
// .NET - Not parameterized, no ORDER BY
var query = "SELECT c.title FROM c WHERE VectorDistance(c.embedding, [0.1, 0.2, ...]) < 0.5";
// Issues: 
// 1. Hard-coded embedding array (query plan cache misses)
// 2. No ORDER BY (doesn't return most similar first)
// 3. Using WHERE instead of ORDER BY (less efficient)
```

```python
# Python - Missing TOP/LIMIT
query = "SELECT c.title, VectorDistance(c.embedding, @embedding) AS score FROM c"
# Missing ORDER BY and TOP - returns all items unsorted
```

**Correct (parameterized with ORDER BY):**

```csharp
// .NET - SDK 3.45.0+
float[] queryEmbedding = await GetEmbeddingAsync("search query");

var queryDef = new QueryDefinition(
    query: "SELECT TOP 10 c.title, VectorDistance(c.embedding, @embedding) AS SimilarityScore " +
           "FROM c ORDER BY VectorDistance(c.embedding, @embedding)"
).WithParameter("@embedding", queryEmbedding);

using FeedIterator<SearchResult> feed = container.GetItemQueryIterator<SearchResult>(
    queryDefinition: queryDef
);

while (feed.HasMoreResults) 
{
    FeedResponse<SearchResult> response = await feed.ReadNextAsync();
    foreach (var item in response)
    {
        Console.WriteLine($"{item.Title}: {item.SimilarityScore}");
    }
}
```

```python
# Python
query_embedding = get_embedding("search query")  # Returns list of floats

for item in container.query_items( 
    query='SELECT TOP 10 c.title, VectorDistance(c.embedding, @embedding) AS SimilarityScore ' +
          'FROM c ORDER BY VectorDistance(c.embedding, @embedding)', 
    parameters=[
        {"name": "@embedding", "value": query_embedding}
    ], 
    enable_cross_partition_query=True
):
    print(f"{item['title']}: {item['SimilarityScore']}")
```

```javascript
// JavaScript - SDK 4.1.0+
const queryEmbedding = await getEmbedding("search query");

const { resources } = await container.items
  .query({
    query: "SELECT TOP 10 c.title, VectorDistance(c.embedding, @embedding) AS SimilarityScore " +
           "FROM c ORDER BY VectorDistance(c.embedding, @embedding)",
    parameters: [{ name: "@embedding", value: queryEmbedding }]
  })
  .fetchAll();

for (const item of resources) {
  console.log(`${item.title}: ${item.SimilarityScore}`);
}
```

```java
// Java
float[] queryEmbedding = getEmbedding("search query");

ArrayList<SqlParameter> paramList = new ArrayList<>();
paramList.add(new SqlParameter("@embedding", queryEmbedding));

SqlQuerySpec querySpec = new SqlQuerySpec(
    "SELECT TOP 10 c.title, VectorDistance(c.embedding, @embedding) AS SimilarityScore " +
    "FROM c ORDER BY VectorDistance(c.embedding, @embedding)", 
    paramList
);

CosmosPagedIterable<SearchResult> results = container.queryItems(
    querySpec, 
    new CosmosQueryRequestOptions(), 
    SearchResult.class
);

for (SearchResult result : results) {
    System.out.println(result.getTitle() + ": " + result.getSimilarityScore());
}
```

**Best Practices:**
- Always use `@parameters` for embeddings (enables query plan caching)
- Include `ORDER BY VectorDistance()` to get most similar results first
- Use `TOP N` to limit results (reduces RU consumption)
- Consider combining with WHERE clauses for filtered vector search
- Enable cross-partition queries when partition key is not in WHERE clause

**Hybrid Search Example (Vector + Filters):**
```sql
SELECT TOP 10 c.title, VectorDistance(c.embedding, @embedding) AS score
FROM c
WHERE c.category = @category AND c.publishYear >= @minYear
ORDER BY VectorDistance(c.embedding, @embedding)
```

Reference: [VectorDistance](https://learn.microsoft.com/en-us/cosmos-db/query/vectordistance) | [.NET](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-dotnet-vector-index-query#run-a-vector-similarity-search-query) | [Python](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-python-vector-index-query#run-a-vector-similarity-search-query) | [JavaScript](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-javascript-vector-index-query#run-a-vector-similarity-search-query) | [Java](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-java-vector-index-query#run-a-vector-similarity-search-query)

### 1.2 Define Vector Embedding Policy

**Impact: CRITICAL** (Required for vector search functionality)

## Define Vector Embedding Policy

**Impact: CRITICAL (Required for vector search functionality)**

The vector embedding policy provides essential information to the Azure Cosmos DB query engine about how to handle vector properties in the VectorDistance system functions. This policy is required and cannot be modified after container creation.

**Vector Embedding Policy Properties:**
- `path`: The property path that contains vectors (e.g., `/embedding`, `/contentVector`)
- `dataType`: The type of the elements of the vector (default: Float32)
- `dimensions`: The length of each vector in the path (default: 1536)
- `distanceFunction`: The metric used to compute distance/similarity (default: Cosine, options: Cosine, DotProduct, Euclidean)

**Incorrect (no vector embedding policy):**

```csharp
// .NET - Missing vector embedding policy
var containerProperties = new ContainerProperties("mycontainer", "/partitionKey");
await database.CreateContainerAsync(containerProperties);
```

```python
# Python - Missing vector embedding policy
container = db.create_container(
    id="mycontainer",
    partition_key=PartitionKey(path='/id')
)
```

**Correct (with vector embedding policy):**

```csharp
// .NET - SDK 3.45.0+
List<Embedding> embeddings = new List<Embedding>()
{
    new Embedding()
    {
        Path = "/embedding",
        DataType = VectorDataType.Float32,
        DistanceFunction = DistanceFunction.Cosine,
        Dimensions = 1536,
    }
};

Collection<Embedding> collection = new Collection<Embedding>(embeddings);
ContainerProperties properties = new ContainerProperties(
    id: "documents", 
    partitionKeyPath: "/category")
{   
    VectorEmbeddingPolicy = new(collection)
};
```

```python
# Python
vector_embedding_policy = { 
    "vectorEmbeddings": [ 
        { 
            "path": "/embedding", 
            "dataType": "float32", 
            "distanceFunction": "cosine", 
            "dimensions": 1536
        }
    ]    
}

container = db.create_container_if_not_exists( 
    id="documents", 
    partition_key=PartitionKey(path='/category'), 
    vector_embedding_policy=vector_embedding_policy
)
```

```javascript
// JavaScript - SDK 4.1.0+
const vectorEmbeddingPolicy = {
  vectorEmbeddings: [
    {
      path: "/embedding",
      dataType: VectorEmbeddingDataType.Float32,
      dimensions: 1536,
      distanceFunction: VectorEmbeddingDistanceFunction.Cosine,
    }
  ],
};

const { resource: containerdef } = await database.containers.createIfNotExists({
  id: "documents",
  partitionKey: { paths: ["/category"] },
  vectorEmbeddingPolicy: vectorEmbeddingPolicy
});
```

```java
// Java
CosmosVectorEmbeddingPolicy cosmosVectorEmbeddingPolicy = new CosmosVectorEmbeddingPolicy();

CosmosVectorEmbedding embedding = new CosmosVectorEmbedding();
embedding.setPath("/embedding");
embedding.setDataType(CosmosVectorDataType.FLOAT32);
embedding.setDimensions(1536L);
embedding.setDistanceFunction(CosmosVectorDistanceFunction.COSINE);

cosmosVectorEmbeddingPolicy.setCosmosVectorEmbeddings(Arrays.asList(embedding));

CosmosContainerProperties containerProperties = new CosmosContainerProperties("documents", "/category");
containerProperties.setVectorEmbeddingPolicy(cosmosVectorEmbeddingPolicy);

database.createContainer(containerProperties).block();
```

Reference: [.NET](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-dotnet-vector-index-query) | [Python](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-python-vector-index-query) | [JavaScript](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-javascript-vector-index-query) | [Java](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-java-vector-index-query)

### 1.3 Enable Vector Search Feature on Account

**Impact: CRITICAL** (Required before using vector search)

## Enable Vector Search Feature on Account

**Impact: CRITICAL (Required before using vector search)**

Vector search must be explicitly enabled on the Azure Cosmos DB account before creating containers with vector policies. The feature can be enabled via Azure Portal or Azure CLI. Activation is auto-approved but may take up to 15 minutes to take effect.

**Important Notes:**
- Must be enabled **before** creating containers with vector policies
- Only supported on **new containers** (cannot modify existing containers)
- Feature activation takes up to 15 minutes
- Vector policies cannot be modified after container creation

**Enable via Azure Portal:**

1. Navigate to Azure Cosmos DB for NoSQL account
2. Select "Features" under Settings
3. Select "Vector Search for NoSQL API"
4. Review feature description
5. Click "Enable"

**Enable via Azure CLI:**

```bash
# Enable vector search capability on account
az cosmosdb update \
    --resource-group <resource-group-name> \
    --name <account-name> \
    --capabilities EnableNoSQLVectorSearch
```

**Verify Feature is Enabled (before creating containers):**

Wait 15 minutes after enabling, then verify:

```bash
# Check account capabilities
az cosmosdb show \
    --resource-group <resource-group-name> \
    --name <account-name> \
    --query "capabilities[?name=='EnableNoSQLVectorSearch']"
```

**Incorrect (attempting to use vectors without enabling feature):**

```csharp
// .NET - This will FAIL if feature not enabled
var embeddings = new List<Embedding>() { /* ... */ };
var properties = new ContainerProperties("docs", "/id")
{
    VectorEmbeddingPolicy = new(new Collection<Embedding>(embeddings))
};

await database.CreateContainerAsync(properties);
// Error: Vector search feature not enabled on account
```

**Correct (enable feature first, wait, then create):**

```bash
# Step 1: Enable feature
az cosmosdb update \
    --resource-group myResourceGroup \
    --name myCosmosAccount \
    --capabilities EnableNoSQLVectorSearch

# Step 2: Wait 15 minutes for feature to activate

# Step 3: Verify enabled
az cosmosdb show \
    --resource-group myResourceGroup \
    --name myCosmosAccount \
    --query "capabilities"

# Step 4: Now create containers with vector policies (see other rules)
```

**SDK Version Requirements:**
- **.NET**: SDK 3.45.0+ (release) or 3.46.0-preview.0+ (preview)
- **Python**: Latest Python SDK
- **JavaScript**: SDK 4.1.0+
- **Java**: Latest Java SDK v4

Reference: [.NET](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-dotnet-vector-index-query#enable-the-feature) | [Python](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-python-vector-index-query#enable-the-feature) | [JavaScript](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-javascript-vector-index-query#enable-the-feature) | [Java](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-java-vector-index-query#enable-the-feature)

### 1.4 Configure Vector Indexes in Indexing Policy

**Impact: CRITICAL** (Required for vector search performance)

## Configure Vector Indexes in Indexing Policy

**Impact: CRITICAL (Required for vector search performance)**

Vector indexes must be added to the indexing policy to enable efficient vector similarity search. Choose between QuantizedFlat (faster builds, good for smaller datasets) or DiskANN (better for larger datasets, requires more memory).

**Vector Index Types:**
- `QuantizedFlat`: Quantized flat index - faster to build, good for datasets < 50K vectors
- `DiskANN`: Disk-based approximate nearest neighbor - better for larger datasets, optimized for scale

**CRITICAL: Exclude vector paths from regular indexing** to avoid high RU charges and latency on inserts.

**Incorrect (no vector indexes or missing excludedPaths):**

```csharp
// .NET - Missing vector indexes
var properties = new ContainerProperties("documents", "/category")
{
    VectorEmbeddingPolicy = new(embeddings)
};
// No VectorIndexes configured!
```

```python
# Python - Missing excluded paths for vectors
indexing_policy = { 
    "includedPaths": [{"path": "/*"}],
    "vectorIndexes": [
        {"path": "/embedding", "type": "quantizedFlat"}
    ]
    # Missing excludedPaths - will cause high RU consumption!
}
```

**Correct (with vector indexes and excluded paths):**

```csharp
// .NET - SDK 3.45.0+
ContainerProperties properties = new ContainerProperties(
    id: "documents", 
    partitionKeyPath: "/category")
{   
    VectorEmbeddingPolicy = new(collection),
    IndexingPolicy = new IndexingPolicy()
    {
        VectorIndexes = new()
        {
            new VectorIndexPath()
            {
                Path = "/embedding",
                Type = VectorIndexType.QuantizedFlat,
            }
        }
    },
};

// CRITICAL: Exclude vector paths from regular indexing
properties.IndexingPolicy.IncludedPaths.Add(new IncludedPath { Path = "/*" });
properties.IndexingPolicy.ExcludedPaths.Add(new ExcludedPath { Path = "/embedding/*" });
```

```python
# Python
indexing_policy = { 
    "includedPaths": [{"path": "/*"}], 
    "excludedPaths": [
        {"path": "/\"_etag\"/?"},
        {"path": "/embedding/*"}  # CRITICAL: Exclude vector path
    ], 
    "vectorIndexes": [
        {
            "path": "/embedding", 
            "type": "quantizedFlat"  # or "diskANN" for larger datasets
        }
    ] 
}

container = db.create_container_if_not_exists( 
    id="documents", 
    partition_key=PartitionKey(path='/category'), 
    indexing_policy=indexing_policy, 
    vector_embedding_policy=vector_embedding_policy
)
```

```javascript
// JavaScript - SDK 4.1.0+
const indexingPolicy = {
  vectorIndexes: [
    { path: "/embedding", type: VectorIndexType.QuantizedFlat }
  ],
  includedPaths: [{ path: "/*" }],
  excludedPaths: [
    { path: "/embedding/*" }  // CRITICAL: Exclude vector path
  ]
};

const { resource: containerdef } = await database.containers.createIfNotExists({
  id: "documents",
  partitionKey: { paths: ["/category"] },
  vectorEmbeddingPolicy: vectorEmbeddingPolicy,
  indexingPolicy: indexingPolicy
});
```

```java
// Java
IndexingPolicy indexingPolicy = new IndexingPolicy();
indexingPolicy.setIndexingMode(IndexingMode.CONSISTENT);

// CRITICAL: Exclude vector path
ExcludedPath excludedPath = new ExcludedPath("/embedding/*");
indexingPolicy.setExcludedPaths(Collections.singletonList(excludedPath));

IncludedPath includedPath = new IncludedPath("/*");
indexingPolicy.setIncludedPaths(Collections.singletonList(includedPath));

// Vector index configuration
CosmosVectorIndexSpec vectorIndexSpec = new CosmosVectorIndexSpec();
vectorIndexSpec.setPath("/embedding");
vectorIndexSpec.setType(CosmosVectorIndexType.QUANTIZED_FLAT.toString());

indexingPolicy.setVectorIndexes(Collections.singletonList(vectorIndexSpec));

containerProperties.setIndexingPolicy(indexingPolicy);
database.createContainer(containerProperties).block();
```

**Index Type Selection Guide:**
- Use `QuantizedFlat` for: < 50K vectors, faster builds, lower memory
- Use `DiskANN` for: > 50K vectors, better recall, production workloads

Reference: [.NET](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-dotnet-vector-index-query#create-a-vector-index-in-the-indexing-policy) | [Python](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-python-vector-index-query#create-a-vector-index-in-the-indexing-policy) | [JavaScript](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-javascript-vector-index-query#create-a-vector-index-in-the-indexing-policy) | [Java](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-java-vector-index-query#create-a-vector-index-in-the-indexing-policy)

### 1.5 Normalize Embeddings for Cosine Similarity

**Impact: MEDIUM** (Ensures accurate similarity scores and consistent test results)

## Normalize Embeddings for Cosine Similarity

**Impact: MEDIUM (Accurate similarity scores)**

When using cosine distance (the most common choice for vector search), normalize embeddings to unit length (L2 norm = 1). This ensures consistent similarity scores and enables accurate testing with mock embeddings.

**Why Normalize:**
- Cosine similarity measures the angle between vectors, not magnitude
- Unnormalized embeddings can produce inconsistent scores
- Most embedding models (Azure OpenAI, etc.) return normalized vectors
- Essential for generating mock embeddings for testing

**Formula:**
```
normalized_vector = vector / ||vector||₂
where ||vector||₂ = sqrt(sum(x² for x in vector))
```

**Incorrect (unnormalized embeddings):**

```python
# Python - BAD: Random vectors without normalization
import random

def generate_mock_embedding(dimensions=1536):
    # Returns unnormalized random vector
    return [random.uniform(-1, 1) for _ in range(dimensions)]
    # Problem: Magnitude varies, affects cosine similarity scores
```

```csharp
// .NET - BAD: Unnormalized test embeddings
public float[] GenerateMockEmbedding(int dimensions = 1536)
{
    var random = new Random();
    var embedding = new float[dimensions];
    for (int i = 0; i < dimensions; i++)
    {
        embedding[i] = (float)(random.NextDouble() * 2 - 1);
    }
    return embedding; // Not normalized - scores will be inconsistent
}
```

**Correct (normalized to unit length):**

```python
# Python - GOOD: Normalized embeddings
import numpy as np

def generate_mock_embedding(text: str, dimensions: int = 1536) -> list:
    """
    Generate normalized mock embedding for testing.
    Uses text hash as seed for reproducibility.
    """
    # Use text hash as seed for deterministic results
    seed = hash(text) % (2**32)
    np.random.seed(seed)
    
    # Generate random vector
    vector = np.random.randn(dimensions).astype(np.float32)
    
    # Normalize to unit length (critical for cosine similarity)
    vector = vector / np.linalg.norm(vector)
    
    return vector.tolist()

# Verify normalization
embedding = generate_mock_embedding("test document")
magnitude = np.linalg.norm(embedding)
assert abs(magnitude - 1.0) < 1e-6, f"Not normalized: {magnitude}"

# Use in tests
documents = [
    {
        "id": "doc1",
        "content": "Azure Cosmos DB vector search",
        "embedding": generate_mock_embedding("Azure Cosmos DB vector search")
    }
]
```

```csharp
// .NET - GOOD: Normalized embeddings
using System;
using System.Linq;

public class EmbeddingHelper
{
    public static float[] GenerateMockEmbedding(string text, int dimensions = 1536)
    {
        // Use text hash as seed for reproducibility
        var seed = Math.Abs(text.GetHashCode());
        var random = new Random(seed);
        
        // Generate random vector
        var vector = new float[dimensions];
        for (int i = 0; i < dimensions; i++)
        {
            // Box-Muller transform for normal distribution
            double u1 = random.NextDouble();
            double u2 = random.NextDouble();
            vector[i] = (float)(Math.Sqrt(-2.0 * Math.Log(u1)) * Math.Cos(2.0 * Math.PI * u2));
        }
        
        // Normalize to unit length (L2 norm = 1)
        var magnitude = Math.Sqrt(vector.Sum(x => x * x));
        for (int i = 0; i < dimensions; i++)
        {
            vector[i] /= (float)magnitude;
        }
        
        return vector;
    }
    
    public static double CalculateMagnitude(float[] vector)
    {
        return Math.Sqrt(vector.Sum(x => x * x));
    }
}

// Usage
var embedding = EmbeddingHelper.GenerateMockEmbedding("test document");
var magnitude = EmbeddingHelper.CalculateMagnitude(embedding);
Console.WriteLine($"Magnitude: {magnitude}"); // Should be ~1.0

var document = new Document
{
    Id = "doc1",
    Content = "Azure Cosmos DB",
    Embedding = embedding
};
```

```javascript
// JavaScript - GOOD: Normalized embeddings
function generateMockEmbedding(text, dimensions = 1536) {
    // Simple hash for seed
    let seed = 0;
    for (let i = 0; i < text.length; i++) {
        seed = ((seed << 5) - seed) + text.charCodeAt(i);
        seed = seed & seed; // Convert to 32-bit integer
    }
    
    // Seeded random number generator
    const random = (function(seed) {
        let state = seed;
        return function() {
            state = (state * 1103515245 + 12345) & 0x7fffffff;
            return state / 0x7fffffff;
        };
    })(Math.abs(seed));
    
    // Generate random vector with normal distribution (Box-Muller)
    const vector = [];
    for (let i = 0; i < dimensions; i++) {
        const u1 = random();
        const u2 = random();
        const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
        vector.push(z);
    }
    
    // Normalize to unit length
    const magnitude = Math.sqrt(vector.reduce((sum, x) => sum + x * x, 0));
    return vector.map(x => x / magnitude);
}

// Verify
const embedding = generateMockEmbedding("test document");
const magnitude = Math.sqrt(embedding.reduce((sum, x) => sum + x * x, 0));
console.log(`Magnitude: ${magnitude}`); // Should be ~1.0

const document = {
    id: "doc1",
    content: "Azure Cosmos DB",
    embedding: embedding
};
```

```java
// Java - GOOD: Normalized embeddings
import java.util.Random;

public class EmbeddingHelper {
    public static float[] generateMockEmbedding(String text, int dimensions) {
        // Use text hash as seed for reproducibility
        int seed = Math.abs(text.hashCode());
        Random random = new Random(seed);
        
        // Generate random vector with normal distribution
        float[] vector = new float[dimensions];
        for (int i = 0; i < dimensions; i++) {
            vector[i] = (float) random.nextGaussian();
        }
        
        // Normalize to unit length
        double magnitude = 0.0;
        for (float v : vector) {
            magnitude += v * v;
        }
        magnitude = Math.sqrt(magnitude);
        
        for (int i = 0; i < dimensions; i++) {
            vector[i] /= magnitude;
        }
        
        return vector;
    }
    
    public static double calculateMagnitude(float[] vector) {
        double sum = 0.0;
        for (float v : vector) {
            sum += v * v;
        }
        return Math.sqrt(sum);
    }
}

// Usage
float[] embedding = EmbeddingHelper.generateMockEmbedding("test document", 1536);
double magnitude = EmbeddingHelper.calculateMagnitude(embedding);
System.out.println("Magnitude: " + magnitude); // Should be ~1.0
```

**Production Embeddings:**

Most embedding APIs return normalized vectors automatically, but verify:

```python
# Azure OpenAI - typically normalized
from openai import AzureOpenAI

client = AzureOpenAI(...)
response = client.embeddings.create(
    input="search query",
    model="text-embedding-ada-002"
)
embedding = response.data[0].embedding

# Verify normalization (optional, for debugging)
import numpy as np
magnitude = np.linalg.norm(embedding)
print(f"Magnitude: {magnitude}")  # Should be ~1.0

# If not normalized (rare), normalize:
if abs(magnitude - 1.0) > 0.01:
    embedding = (np.array(embedding) / magnitude).tolist()
```

**Testing Best Practices:**

1. **Deterministic Mock Embeddings** - Use text/content hash as random seed
   ```python
   seed = hash(text) % (2**32)  # Reproducible results
   ```

2. **Verify Normalization** - Assert magnitude is ~1.0 in tests
   ```python
   assert abs(np.linalg.norm(embedding) - 1.0) < 1e-6
   ```

3. **Realistic Dimensions** - Use actual dimensions (1536 for Ada-002, 3072 for text-embedding-3-large)

4. **Similarity Score Ranges** - With normalized vectors and cosine distance:
   - Identical vectors: score = 1.0
   - Orthogonal vectors: score = 0.0
   - Opposite vectors: score = -1.0 (rare in embeddings)

**When NOT to Normalize:**

- If using **Euclidean** or **Dot Product** distance functions (check your embedding policy)
- When magnitude carries semantic meaning (very rare)
- If embedding model explicitly states vectors are not normalized

**Common Mistake:**

```python
# BAD: Comparing normalized query to unnormalized documents
query_embedding = normalize(get_embedding(query))  # Normalized
documents = [
    {"embedding": [random.random() for _ in range(1536)]}  # NOT normalized
]
# Results: Inconsistent similarity scores
```

**Related Rules:**
- vector-embedding-policy.md - Choose cosine distance function
- vector-distance-query.md - VectorDistance() queries return similarity scores

### 1.6 Implement Repository Pattern for Vector Search

**Impact: HIGH** (Provides clean abstraction for vector operations and data access)

## Implement Repository Pattern for Vector Search

**Impact: HIGH (Clean abstraction for vector operations)**

When implementing vector search, use a repository pattern to encapsulate Cosmos DB operations. This separates data access logic from business logic and makes vector search operations testable and maintainable. For FastAPI or REST-based RAG APIs, pair this guidance with `cosmosdb-sdk` for SDK-correct writes/client configuration and `cosmosdb-design-patterns` for FastAPI startup, chat history, and response DTO mapping. If using `azure.cosmos.aio`, also check the SDK version before copying sync-only query kwargs such as `enable_cross_partition_query`.

**RAG API critical path:** configure vector policy/index, write documents with partition-key fields in the body, query with parameterized `VectorDistance`, use a literal bounded `TOP N`, project only public fields, and map Cosmos documents to API DTOs before returning them.

**Key Methods to Implement:**
1. **insert_document/upsert_document** - Store documents with embeddings
2. **vector_search** - Perform similarity search with VectorDistance()
3. **get_document** - Point read by ID and partition key
4. **delete_document** - Remove documents

**Incorrect (direct container access in application code):**

```python
# Python - BAD: Direct container access scattered throughout app
@app.post("/api/search")
async def search(request: SearchRequest):
    # Vector search logic mixed with API logic
    query = f"""
        SELECT TOP {request.limit} c.title, 
               VectorDistance(c.embedding, @embedding) AS score
        FROM c ORDER BY VectorDistance(c.embedding, @embedding)
    """
    results = container.query_items(query, parameters=[...])
    # No abstraction, hard to test, tightly coupled
```

```csharp
// .NET - BAD: No separation of concerns
public class DocumentService {
    public async Task<List<Doc>> Search(float[] embedding) {
        // Direct container access, no abstraction
        var query = new QueryDefinition(...);
        var iterator = _container.GetItemQueryIterator<Doc>(query);
        // Mixing infrastructure concerns with business logic
    }
}
```

**Correct (repository pattern with clean abstraction):**

```python
# Python - GOOD: Repository pattern
class DocumentRepository:
    """Repository for documents with vector search capabilities"""
    
    def __init__(self, container: ContainerProxy):
        self.container = container
    
    async def insert_document(self, document: DocumentChunk) -> DocumentChunk:
        """Insert document with vector embedding."""
        try:
            doc_dict = document.dict()
            created_item = self.container.upsert_item(body=doc_dict)
            return DocumentChunk(**created_item)
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to insert document: {e.message}")
            raise
    
    async def vector_search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        similarity_threshold: float = 0.0,
        category_filter: Optional[str] = None
    ) -> List[DocumentChunk]:
        """Perform vector similarity search with VectorDistance()."""
        try:
            # Build parameterized query
            safe_limit = max(1, min(int(limit), 50))
            query = f"""
                SELECT TOP {safe_limit} 
                    c.id, c.title, c.content, c.category, c.metadata,
                    VectorDistance(c.embedding, @queryVector) AS similarityScore
                FROM c
                WHERE VectorDistance(c.embedding, @queryVector) > @threshold
            """
            
            # Add optional filters
            if category_filter:
                query += " AND c.category = @category"
            
            query += " ORDER BY VectorDistance(c.embedding, @queryVector)"
            
            # Build parameters
            parameters = [
                {"name": "@queryVector", "value": query_embedding},
                {"name": "@threshold", "value": similarity_threshold}
            ]
            
            if category_filter:
                parameters.append({"name": "@category", "value": category_filter})
            
            # Execute query
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
                populate_query_metrics=True
            ))
            
            # Convert to domain models
            results = []
            for item in items:
                score = item.pop('similarityScore', 0.0)
                if 'metadata' not in item:
                    item['metadata'] = {}
                item['metadata']['similarityScore'] = score
                item.pop('embedding', None)  # Keep raw embeddings out of API responses
                results.append(DocumentChunk(**item))
            
            return results
            
        except CosmosHttpResponseError as e:
            logger.error(f"Vector search failed: {e.message}")
            raise
    
    async def get_document(self, document_id: str, category: str) -> Optional[DocumentChunk]:
        """Point read with partition key."""
        try:
            item = self.container.read_item(
                item=document_id,
                partition_key=category
            )
            return DocumentChunk(**item)
        except CosmosHttpResponseError as e:
            if e.status_code == 404:
                return None
            raise

# Usage in application
@app.post("/api/search")
async def search(request: SearchRequest):
    results = await document_repo.vector_search(
        query_embedding=request.embedding,
        limit=request.top_k,
        category_filter=request.category
    )
    return {"results": results}
```

```csharp
// .NET - GOOD: Repository pattern
public interface IDocumentRepository
{
    Task<DocumentChunk> InsertDocumentAsync(DocumentChunk document);
    Task<List<DocumentChunk>> VectorSearchAsync(
        float[] queryEmbedding, 
        int limit = 5, 
        double similarityThreshold = 0.0, 
        string? categoryFilter = null);
    Task<DocumentChunk?> GetDocumentAsync(string id, string category);
}

public class DocumentRepository : IDocumentRepository
{
    private readonly Container _container;
    private readonly ILogger<DocumentRepository> _logger;

    public DocumentRepository(Container container, ILogger<DocumentRepository> logger)
    {
        _container = container;
        _logger = logger;
    }

    public async Task<DocumentChunk> InsertDocumentAsync(DocumentChunk document)
    {
        try
        {
            var response = await _container.UpsertItemAsync(
                item: document,
                partitionKey: new PartitionKey(document.Category)
            );
            _logger.LogInformation("Inserted document {Id}", document.Id);
            return response.Resource;
        }
        catch (CosmosException ex)
        {
            _logger.LogError(ex, "Failed to insert document {Id}", document.Id);
            throw;
        }
    }

    public async Task<List<DocumentChunk>> VectorSearchAsync(
        float[] queryEmbedding, 
        int limit = 5,
        double similarityThreshold = 0.0, 
        string? categoryFilter = null)
    {
        try
        {
            var safeLimit = Math.Clamp(limit, 1, 50);

            // Build query. TOP requires a literal integer in Cosmos DB SQL.
            var queryText = $@"
                SELECT TOP {safeLimit} 
                    c.id, c.title, c.content, c.category, c.metadata,
                    VectorDistance(c.embedding, @queryVector) AS similarityScore
                FROM c
                WHERE VectorDistance(c.embedding, @queryVector) > @threshold";

            if (!string.IsNullOrEmpty(categoryFilter))
            {
                queryText += " AND c.category = @category";
            }

            queryText += " ORDER BY VectorDistance(c.embedding, @queryVector)";

            // Build query definition
            var queryDef = new QueryDefinition(queryText)
                .WithParameter("@queryVector", queryEmbedding)
                .WithParameter("@threshold", similarityThreshold);

            if (!string.IsNullOrEmpty(categoryFilter))
            {
                queryDef = queryDef.WithParameter("@category", categoryFilter);
            }

            // Execute query
            var results = new List<DocumentChunk>();
            using var iterator = _container.GetItemQueryIterator<DocumentChunk>(queryDef);

            while (iterator.HasMoreResults)
            {
                var response = await iterator.ReadNextAsync();
                results.AddRange(response);
                
                // Log RU consumption
                _logger.LogDebug("Vector search consumed {RU} RUs", 
                    response.RequestCharge);
            }

            return results;
        }
        catch (CosmosException ex)
        {
            _logger.LogError(ex, "Vector search failed");
            throw;
        }
    }

    public async Task<DocumentChunk?> GetDocumentAsync(string id, string category)
    {
        try
        {
            var response = await _container.ReadItemAsync<DocumentChunk>(
                id: id,
                partitionKey: new PartitionKey(category)
            );
            return response.Resource;
        }
        catch (CosmosException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return null;
        }
    }
}

// Usage in service/controller
public class SearchService
{
    private readonly IDocumentRepository _repository;

    public SearchService(IDocumentRepository repository)
    {
        _repository = repository;
    }

    public async Task<List<DocumentChunk>> SearchAsync(SearchRequest request)
    {
        return await _repository.VectorSearchAsync(
            queryEmbedding: request.Embedding,
            limit: request.TopK,
            categoryFilter: request.Category
        );
    }
}
```

```javascript
// JavaScript/TypeScript - GOOD: Repository pattern
class DocumentRepository {
    constructor(private container: Container) {}

    async insertDocument(document: DocumentChunk): Promise<DocumentChunk> {
        try {
            const { resource } = await this.container.items.upsert(document);
            console.log(`Inserted document ${resource.id}`);
            return resource;
        } catch (error) {
            console.error('Failed to insert document:', error);
            throw error;
        }
    }

    async vectorSearch(
        queryEmbedding: number[],
        options: {
            limit?: number;
            similarityThreshold?: number;
            categoryFilter?: string;
        } = {}
    ): Promise<DocumentChunk[]> {
        const { limit = 5, similarityThreshold = 0.0, categoryFilter } = options;

        try {
            const safeLimit = Math.max(1, Math.min(Number(limit), 50));
            let query = `
                SELECT TOP ${safeLimit} 
                    c.id, c.title, c.content, c.category, c.metadata,
                    VectorDistance(c.embedding, @queryVector) AS similarityScore
                FROM c
                WHERE VectorDistance(c.embedding, @queryVector) > @threshold
            `;

            const parameters = [
                { name: '@queryVector', value: queryEmbedding },
                { name: '@threshold', value: similarityThreshold }
            ];

            if (categoryFilter) {
                query += ' AND c.category = @category';
                parameters.push({ name: '@category', value: categoryFilter });
            }

            query += ' ORDER BY VectorDistance(c.embedding, @queryVector)';

            const { resources } = await this.container.items
                .query({
                    query,
                    parameters
                })
                .fetchAll();

            return resources.map(item => ({
                ...item,
                embedding: undefined // Exclude from public API responses
            }));
        } catch (error) {
            console.error('Vector search failed:', error);
            throw error;
        }
    }

    async getDocument(id: string, category: string): Promise<DocumentChunk | null> {
        try {
            const { resource } = await this.container.item(id, category).read();
            return resource;
        } catch (error: any) {
            if (error.code === 404) {
                return null;
            }
            throw error;
        }
    }
}

// Usage
const documentRepo = new DocumentRepository(container);
const results = await documentRepo.vectorSearch(embedding, { 
    limit: 10, 
    categoryFilter: 'ai' 
});
```

**Benefits:**
- ✅ Testable - Mock repository in unit tests
- ✅ Maintainable - Vector search logic in one place
- ✅ Reusable - Use repository across multiple services
- ✅ Clean separation - Infrastructure vs business logic
- ✅ Easier to optimize - Centralized query performance tuning

**Best Practices:**
1. Use `upsert_item` for idempotent inserts
2. Always parameterize queries (never concatenate embeddings)
3. Include `ORDER BY VectorDistance()` for ranked results
4. Exclude embeddings from SELECT when not needed (performance)
5. Log RU consumption for monitoring
6. Handle 404 errors gracefully (return null, not exception)
7. Use domain models (not raw dictionaries/dynamic)

**Related Rules:**
- vector-distance-query.md - VectorDistance() usage
- query-parameterize.md - Always use parameters
- query-use-projections.md - Exclude unnecessary fields

---

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
