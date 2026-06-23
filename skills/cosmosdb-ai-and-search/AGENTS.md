# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Best practices for AI, RAG, and search on Azure Cosmos DB: vector search, full-text search, LangChain/LangGraph integration, and AI-agent design patterns.

---

## Table of Contents

1. [Vector Search](#1-vector-search) — **HIGH**
   - 1.1 [Use VectorDistance for Similarity Search](#11-use-vectordistance-for-similarity-search)
   - 1.2 [Define Vector Embedding Policy](#12-define-vector-embedding-policy)
   - 1.3 [Enable Vector Search Feature on Account](#13-enable-vector-search-feature-on-account)
   - 1.4 [Configure Vector Indexes in Indexing Policy](#14-configure-vector-indexes-in-indexing-policy)
   - 1.5 [Normalize Embeddings for Cosine Similarity](#15-normalize-embeddings-for-cosine-similarity)
   - 1.6 [Implement Repository Pattern for Vector Search](#16-implement-repository-pattern-for-vector-search)
2. [Full-Text Search](#2-full-text-search) — **HIGH**
   - 2.1 [Add Full-Text Index in the Indexing Policy](#21-add-full-text-index-in-the-indexing-policy)
   - 2.2 [Define Full-Text Policy on the Container](#22-define-full-text-policy-on-the-container)
   - 2.3 [Enable Full-Text Search Capability on Account](#23-enable-full-text-search-capability-on-account)
   - 2.4 [Combine FTS predicates with range or equality filters for hybrid queries](#24-combine-fts-predicates-with-range-or-equality-filters-for-hybrid-queries)
   - 2.5 [Use FullTextContains for keyword matching on indexed text fields](#25-use-fulltextcontains-for-keyword-matching-on-indexed-text-fields)
   - 2.6 [Use FullTextScore with ORDER BY RANK for BM25 relevance ranking](#26-use-fulltextscore-with-order-by-rank-for-bm25-relevance-ranking)
3. [SDK Best Practices](#3-sdk-best-practices) — **HIGH**
   - 3.1 [Initialize Async Cosmos DB Container Before CosmosDBSaver](#31-initialize-async-cosmos-db-container-before-cosmosdbsaver)
   - 3.2 [Use CosmosDBSaver for LangGraph Checkpointing](#32-use-cosmosdbsaver-for-langgraph-checkpointing)
   - 3.3 [Use AzureCosmosDBNoSQLChatMessageHistory for Persistent Conversations in JS/TS](#33-use-azurecosmosdbnosqlchatmessagehistory-for-persistent-conversations-in-js-ts)
   - 3.4 [Configure Azure OpenAI Embedding Deployment Name for JS/TS LangChain](#34-configure-azure-openai-embedding-deployment-name-for-js-ts-langchain)
   - 3.5 [Prevent Filter Injection in JS/TS LangChain Vector Store Queries](#35-prevent-filter-injection-in-js-ts-langchain-vector-store-queries)
   - 3.6 [Configure Full-Text Prerequisites Before JS/TS LangChain Hybrid Search](#36-configure-full-text-prerequisites-before-js-ts-langchain-hybrid-search)
   - 3.7 [Use Managed Identity for JS/TS LangChain Cosmos DB Integration](#37-use-managed-identity-for-js-ts-langchain-cosmos-db-integration)
   - 3.8 [Choose the Correct Search Type for JS/TS LangChain Vector Store](#38-choose-the-correct-search-type-for-js-ts-langchain-vector-store)
   - 3.9 [Use AzureCosmosDBNoSQLSemanticCache for LLM Cost Reduction in JS/TS](#39-use-azurecosmosdbnosqlsemanticcache-for-llm-cost-reduction-in-js-ts)
   - 3.10 [Correctly Initialize AzureCosmosDBNoSQLVectorStore in JavaScript/TypeScript](#310-correctly-initialize-azurecosmosdbnosqlvectorstore-in-javascript-typescript)
   - 3.11 [Use Persistent MCP Client Sessions for Multi-Agent Applications](#311-use-persistent-mcp-client-sessions-for-multi-agent-applications)
   - 3.12 [Handle MCP ToolMessage Content Format Variations](#312-handle-mcp-toolmessage-content-format-variations)
   - 3.13 [Filter MCP Tools by Name Prefix for Agent Assignment](#313-filter-mcp-tools-by-name-prefix-for-agent-assignment)
4. [Design Patterns](#4-design-patterns) — **HIGH**
   - 4.1 [Use Point Reads for AI-Grounding and RAG Retrieval When ID Is Known](#41-use-point-reads-for-ai-grounding-and-rag-retrieval-when-id-is-known)
   - 4.2 [Use Background Tasks for Non-Blocking Chat History Storage](#42-use-background-tasks-for-non-blocking-chat-history-storage)
   - 4.3 [Tag AI Messages with Agent Name for API Response Attribution](#43-tag-ai-messages-with-agent-name-for-api-response-attribution)
   - 4.4 [Persist Active Agent in Cosmos DB for Deterministic Routing](#44-persist-active-agent-in-cosmos-db-for-deterministic-routing)
   - 4.5 [Wrap Cosmos DB Sync Calls in asyncio.to_thread for LangGraph Routing Functions](#45-wrap-cosmos-db-sync-calls-in-asyncio-to-thread-for-langgraph-routing-functions)
   - 4.6 [Use asyncio.to_thread for Active Agent Writes in LangGraph Node Functions](#46-use-asyncio-to-thread-for-active-agent-writes-in-langgraph-node-functions)
   - 4.7 [Store Chat History Separately from LangGraph Checkpoints](#47-store-chat-history-separately-from-langgraph-checkpoints)
   - 4.8 [Initialize LangGraph Agents in FastAPI Startup with Retry](#48-initialize-langgraph-agents-in-fastapi-startup-with-retry)
   - 4.9 [Use LangGraph Interrupt for Human-in-the-Loop Confirmation](#49-use-langgraph-interrupt-for-human-in-the-loop-confirmation)
   - 4.10 [Use StateGraph with Conditional Edges for Multi-Agent Routing](#410-use-stategraph-with-conditional-edges-for-multi-agent-routing)
   - 4.11 [Resume LangGraph from Checkpoint After Interrupt](#411-resume-langgraph-from-checkpoint-after-interrupt)

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

When implementing vector search, use a repository pattern to encapsulate Cosmos DB operations. This separates data access logic from business logic and makes vector search operations testable and maintainable.

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
            query = """
                SELECT TOP @limit 
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
                {"name": "@limit", "value": limit},
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
                item['embedding'] = []  # Exclude from response for performance
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
            // Build query
            var queryText = @"
                SELECT TOP @limit 
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
                .WithParameter("@limit", limit)
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
            let query = `
                SELECT TOP @limit 
                    c.id, c.title, c.content, c.category, c.metadata,
                    VectorDistance(c.embedding, @queryVector) AS similarityScore
                FROM c
                WHERE VectorDistance(c.embedding, @queryVector) > @threshold
            `;

            const parameters = [
                { name: '@queryVector', value: queryEmbedding },
                { name: '@limit', value: limit },
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
                embedding: [] // Exclude for performance
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

## 2. Full-Text Search

**Impact: HIGH**

### 2.1 Add Full-Text Index in the Indexing Policy

**Impact: HIGH** (without the index, FTS functions fall back to a full scan)

## Add Full-Text Index in the Indexing Policy

**Impact: HIGH (without the index, FTS functions fall back to a full scan)**

The `fullTextIndexes` array in the `indexingPolicy` tells Cosmos DB to build an inverted index for the corresponding path. This is separate from the range index — a field can have both. Fields covered by a full-text index should **not** also appear in `excludedPaths`.

**Incorrect (field excluded from range index but no FTS index — slow scan):**

```bicep
excludedPaths: [
  { path: '/description/?' }   // excluded from range index...
]                               // ...but no fullTextIndexes entry → full scan
```

**Correct (Bicep):**

```bicep
indexingPolicy: {
  indexingMode: 'consistent'
  includedPaths: [
    { path: '/name/?' }
    { path: '/userid/?' }
  ]
  excludedPaths: [
    { path: '/*' }             // root wildcard
    // description NOT listed here — managed by FTS index below
  ]
  #disable-next-line BCP037
  fullTextIndexes: [
    { path: '/description' }   // inverted index — case-insensitive, tokenized
  ]
}
```

> A field under `fullTextIndexes` incurs **extra write RU** for index maintenance. Only index fields that are actually queried with `FullTextContains` or `FullTextScore`.

Reference: [Indexing policy for full-text search](https://learn.microsoft.com/azure/cosmos-db/gen-ai/full-text-search)

### 2.2 Define Full-Text Policy on the Container

**Impact: HIGH** (required for tokenizer and stop-word configuration)

## Define Full-Text Policy on the Container

**Impact: HIGH (required for tokenizer and stop-word configuration)**

The `fullTextPolicy` declares which paths are full-text searchable and their language. Supported languages: `en-US`, `de-DE` (preview), `fr-FR` (preview), `it-IT` (preview), `pt-BR` (preview), `pt-PT` (preview), `es-ES` (preview). Language codes are **case-sensitive** — use the exact casing shown (e.g., `en-US` not `en-us`).

**Incorrect (wrong language casing causes ARM BadRequest):**

```bicep
fullTextPolicy: {
  defaultLanguage: 'en-us'       // ❌ lowercase — rejected by ARM
  fullTextPaths: [
    { path: '/description', language: 'en-us' }  // ❌
  ]
}
```

**Correct (Bicep):**

```bicep
#disable-next-line BCP037
fullTextPolicy: {
  defaultLanguage: 'en-US'       // ✅ exact casing required
  fullTextPaths: [
    {
      path: '/description'
      language: 'en-US'          // ✅
    }
  ]
}
```

**Correct — Java SDK (container creation):**

```java
FullTextPolicy ftsPolicy = new FullTextPolicy()
    .setDefaultLanguage("en-US")
    .setFullTextPaths(List.of(
        new FullTextPath().setPath("/description").setLanguage("en-US")
    ));

CosmosContainerProperties props = new CosmosContainerProperties("videos", "/videoid");
props.setFullTextPolicy(ftsPolicy);
database.createContainerIfNotExists(props).block();
```

Reference: [Configure full-text policy](https://learn.microsoft.com/azure/cosmos-db/gen-ai/full-text-search)

### 2.3 Enable Full-Text Search Capability on Account

**Impact: HIGH** (prerequisite — FTS SQL functions fail without it)

## Enable Full-Text Search Capability on Account

**Impact: HIGH (prerequisite — FTS SQL functions fail without it)**

Full-text search is an opt-in account-level capability. The SQL functions `FullTextContains`, `FullTextContainsAll`, `FullTextContainsAny`, and `FullTextScore` all return an error if this capability is not enabled.

**Incorrect (capability absent — FTS queries fail at runtime):**

```sql
-- This query fails with "Function 'FullTextContains' is not supported"
-- when EnableNoSQLFullTextSearch capability is missing on the account
SELECT * FROM c WHERE FullTextContains(c.description, 'cosmos')
```

**Correct — enable via Azure CLI:**

```bash
az cosmosdb update \
  --resource-group <rg> \
  --name <account-name> \
  --capabilities EnableNoSQLFullTextSearch
```

**Correct — enable via Bicep (account resource):**

```bicep
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosAccountName
  properties: {
    // ... other properties ...
    capabilities: [
      { name: 'EnableNoSQLFullTextSearch' }
    ]
  }
}
```

> **Note:** As of Bicep type library v0.41, `fullTextIndexes` and `fullTextPolicy` may emit `BCP037` warnings. Suppress with `#disable-next-line BCP037` — the properties are valid at the ARM REST API level.

Reference: [Full-text search in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/gen-ai/full-text-search)

### 2.4 Combine FTS predicates with range or equality filters for hybrid queries

**Impact: MEDIUM** (avoids full-container scans when combined with equality/range filters)

## Combine FTS with Range Filters for Hybrid Queries

**Impact: MEDIUM (avoids full-container scans when combined with equality/range filters)**

FTS predicates can be combined with standard SQL predicates. Cosmos DB uses the most selective predicate first. Put the most restrictive filter (e.g., equality on a high-cardinality property) before the FTS predicate to reduce the candidate set.

**Incorrect (FTS-only query — no range filters, scans all partitions):**

```sql
-- ❌ No equality filter — Cosmos DB must scan every partition before ranking
SELECT * FROM c
WHERE FullTextContains(c.description, @q)
ORDER BY RANK FullTextScore(c.description, @q)
```

**Correct — filter by partition + FTS:**

```sql
SELECT * FROM c
WHERE c.type = 'video'
  AND c.userid = @userid
  AND FullTextContains(c.description, @q)
ORDER BY RANK FullTextScore(c.description, @q)
```

```java
// Hybrid: exact field filters narrow partition, FTS ranks within results
String sql = "SELECT * FROM c " +
    "WHERE c.type = 'video' " +
    "AND FullTextContains(c.description, @q) " +
    "ORDER BY RANK FullTextScore(c.description, @q)";

CosmosQueryRequestOptions opts = new CosmosQueryRequestOptions();
// enableCrossPartitionQuery is true by default for FTS ORDER BY RANK

return container.queryItems(
    new SqlQuerySpec(sql, new SqlParameter("@q", term)),
    opts, Video.class
).byPage(pageSize).next().toFuture();
```

**Fields that should NOT use FTS:**
- Short identifiers (`id`, `userid`) — use point read or range index equality
- Numeric fields — use range index with `=`, `>`, `<`
- Array elements already indexed with `[]/?` — `CONTAINS(LOWER(t), @q)` via EXISTS is fine

Reference: [Full-text search queries](https://learn.microsoft.com/azure/cosmos-db/gen-ai/full-text-search)

### 2.5 Use FullTextContains for keyword matching on indexed text fields

**Impact: HIGH** (replaces expensive CONTAINS(LOWER(...)) string scans with O(log n) inverted index lookup)

## Use FullTextContains for Keyword Matching

**Impact: HIGH (replaces expensive CONTAINS(LOWER(...)) string scans with O(log n) inverted index lookup)**

`FullTextContains(path, term)` performs a single-keyword lookup against the inverted index and is case-insensitive by design. It is dramatically faster than `CONTAINS(LOWER(c.field), @q)` on large containers because it does an `O(log n)` index lookup instead of a full document scan.

**Incorrect (scan-based — avoid for long text fields with FTS index):**

```sql
-- Full document scan, case folding at query time
SELECT * FROM c
WHERE CONTAINS(LOWER(c.description), @q)
```

```java
String sql = "SELECT * FROM c WHERE CONTAINS(LOWER(c.description), @q)";
```

**Correct:**

```sql
-- Inverted index lookup — no LOWER() needed, FTS tokenizer handles casing
SELECT * FROM c
WHERE FullTextContains(c.description, @q)
```

```java
// Java SDK — parameterized query with FullTextContains
String sql = "SELECT * FROM c WHERE c.type = 'video' " +
    "AND (CONTAINS(LOWER(c.name), @q) " +          // short field — range index OK
    "OR FullTextContains(c.description, @q) " +    // long text — FTS index
    "OR EXISTS(SELECT VALUE t FROM t IN c.tags WHERE CONTAINS(LOWER(t), @q)))";

SqlQuerySpec querySpec = new SqlQuerySpec(sql,
    new SqlParameter("@q", query.trim().toLowerCase()));

return container.queryItems(querySpec, opts, Video.class)
    .byPage(continuationToken, pageSize)
    .next()
    .map(page -> new ResultListPage<>(page.getResults(), page.getContinuationToken()))
    .toFuture();
```

**Variants:**
- `FullTextContains(path, term)` — document contains the term
- `FullTextContainsAll(path, term1, term2, ...)` — document contains ALL terms (AND)
- `FullTextContainsAny(path, term1, term2, ...)` — document contains ANY term (OR)

Reference: [FullTextContains function](https://learn.microsoft.com/azure/cosmos-db/nosql/query/fulltextcontains)

### 2.6 Use FullTextScore with ORDER BY RANK for BM25 relevance ranking

**Impact: MEDIUM-HIGH** (enables BM25-based ranked results instead of arbitrary order)

## Use FullTextScore for Relevance Ranking

**Impact: MEDIUM-HIGH (enables BM25-based ranked results instead of arbitrary order)**

`FullTextScore(path, term)` returns a BM25 relevance score. Use it in `ORDER BY` to surface the most relevant documents first. It **requires** `FullTextContains` in the WHERE clause on the same path.

**Incorrect (FullTextScore without FullTextContains — parse error):**

```sql
SELECT * FROM c
ORDER BY FullTextScore(c.description, 'cosmos')  -- ❌ missing WHERE FullTextContains
```

**Correct:**

```sql
SELECT c.name, c.description, c.addedDate
FROM c
WHERE FullTextContains(c.description, @q)
ORDER BY RANK FullTextScore(c.description, @q)
```

```java
String sql = "SELECT c.name, c.description, c.addedDate FROM c " +
    "WHERE FullTextContains(c.description, @q) " +
    "ORDER BY RANK FullTextScore(c.description, @q)";

SqlQuerySpec querySpec = new SqlQuerySpec(sql, new SqlParameter("@q", searchTerm));
```

> `RANK FullTextScore(...)` is cross-partition — Cosmos DB merges and re-ranks results from all partitions before returning the page.

Reference: [FullTextScore function](https://learn.microsoft.com/azure/cosmos-db/nosql/query/fulltextscore)

---

## 3. SDK Best Practices

**Impact: HIGH**

### 3.1 Initialize Async Cosmos DB Container Before CosmosDBSaver

**Impact: HIGH** (prevents credential and event-loop errors in async applications)

## Initialize Async Cosmos DB Container Before CosmosDBSaver

**Impact: HIGH (prevents credential and event-loop errors in async applications)**

When using `CosmosDBSaver` with the async Cosmos DB SDK, the container client must be created within an active async context (e.g., inside an `async def` function). Creating it at module level causes event-loop errors because the async credential and client require a running loop. Always initialize the async client inside your application's startup routine and recompile the LangGraph graph afterward.

**Incorrect (module-level initialization — event loop not running):**

```python
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from langchain_azure_cosmosdb import CosmosDBSaver

# BAD: No event loop running at module import time
credential = AsyncDefaultAzureCredential()
client = AsyncCosmosClient(url, credential=credential)
container = client.get_database_client("db").get_container_client("Checkpoints")
checkpointer = CosmosDBSaver(container)  # May raise RuntimeError
```

**Incorrect (mixing sync credential with async client):**

```python
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.identity import DefaultAzureCredential  # sync credential

# BAD: Sync credential cannot be used with async CosmosClient
credential = DefaultAzureCredential()
client = AsyncCosmosClient(url, credential=credential)
```

**Correct (initialize in async startup function):**

```python
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from langchain_azure_cosmosdb import CosmosDBSaver
from langgraph.graph import StateGraph, MessagesState

builder = StateGraph(MessagesState)
# ... add nodes and edges ...
graph = builder.compile(checkpointer=None)  # initial compile without persistence

async def setup():
    """Call during application startup (e.g., FastAPI lifespan)."""
    global graph
    credential = AsyncDefaultAzureCredential()
    client = AsyncCosmosClient(cosmos_url, credential=credential)
    database = client.get_database_client("MyDatabase")
    container = database.get_container_client("Checkpoints")
    checkpointer = CosmosDBSaver(container)
    graph = builder.compile(checkpointer=checkpointer)
```

**Tip:** Keep a reference to the `AsyncCosmosClient` so you can close it gracefully on shutdown with `await client.close()`.

Reference: [Azure Cosmos DB async Python SDK](https://learn.microsoft.com/python/api/azure-cosmos/azure.cosmos.aio?view=azure-python)

### 3.2 Use CosmosDBSaver for LangGraph Checkpointing

**Impact: HIGH** (enables persistent multi-turn conversation state across restarts)

## Use CosmosDBSaver for LangGraph Checkpointing

**Impact: HIGH (enables persistent multi-turn conversation state across restarts)**

When building LangGraph agents that require multi-turn conversation persistence, use `CosmosDBSaver` from `langchain-azure-cosmosdb` as the checkpointer. This stores graph state in Cosmos DB, enabling conversations to survive process restarts and scale across multiple instances. The checkpointer requires an **async** container client — using a sync client will raise runtime errors.

**Incorrect (using in-memory checkpointer — state lost on restart):**

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState

builder = StateGraph(MessagesState)
# ... add nodes and edges ...

# BAD: State is lost when the process restarts
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

**Incorrect (passing a sync container client — will fail at runtime):**

```python
from azure.cosmos import CosmosClient
from langchain_azure_cosmosdb import CosmosDBSaver

# BAD: CosmosDBSaver requires an async container client
sync_client = CosmosClient(url, credential=credential)
sync_container = sync_client.get_database_client("db").get_container_client("Checkpoints")
checkpointer = CosmosDBSaver(sync_container)  # RuntimeError
```

**Correct (async container client with CosmosDBSaver):**

```python
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from langchain_azure_cosmosdb import CosmosDBSaver
from langgraph.graph import StateGraph, MessagesState

builder = StateGraph(MessagesState)
# ... add nodes and edges ...

# Compile initially without checkpointer (setup may be async)
graph = builder.compile(checkpointer=None)

async def initialize_checkpointer():
    credential = AsyncDefaultAzureCredential()
    client = AsyncCosmosClient(cosmos_url, credential=credential)
    database = client.get_database_client("MyDatabase")
    container = database.get_container_client("Checkpoints")
    checkpointer = CosmosDBSaver(container)
    # Recompile graph with persistent checkpointer
    return builder.compile(checkpointer=checkpointer)
```

Reference: [langchain-azure-cosmosdb documentation](https://python.langchain.com/docs/integrations/providers/azure_cosmos_db/)

### 3.3 Use AzureCosmosDBNoSQLChatMessageHistory for Persistent Conversations in JS/TS

**Impact: HIGH** (enables persistent multi-turn conversations that survive restarts and scale horizontally)

## Use AzureCosmosDBNoSQLChatMessageHistory for Persistent Conversations in JS/TS

**Impact: HIGH (enables persistent multi-turn conversations that survive restarts and scale horizontally)**

When building conversational AI applications with LangChain.js, use `AzureCosmosDBNoSQLChatMessageHistory` to persist chat messages in Cosmos DB. This ensures conversations survive process restarts, enables horizontal scaling across multiple instances, and provides a queryable audit trail. Each conversation session is stored as a document identified by a `sessionId`, with the partition key enabling efficient retrieval.

**Incorrect (in-memory history — lost on restart, no horizontal scaling):**

```typescript
import { ChatMessageHistory } from "langchain/memory";

// BAD: Messages lost when process restarts or user hits different instance
const history = new ChatMessageHistory();
await history.addUserMessage("Hello");
await history.addAIMessage("Hi there!");
// Process restarts... conversation is gone
```

**Incorrect (wrong partition key — cross-partition queries for session lookup):**

```typescript
import { AzureCosmosDBNoSQLChatMessageHistory } from "@langchain/azure-cosmosdb";

// BAD: If container partition key is /userId but you query by sessionId,
// lookups become cross-partition scans
const history = new AzureCosmosDBNoSQLChatMessageHistory({
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
  databaseName: "mydb",
  containerName: "chat-history", // partitioned by /userId
  sessionId: "session-123",     // queries will fan out across partitions
});
```

**Correct (persistent chat history with proper session isolation):**

```typescript
import { AzureCosmosDBNoSQLChatMessageHistory } from "@langchain/azure-cosmosdb";
import { DefaultAzureCredential } from "@azure/identity";
import { RunnableWithMessageHistory } from "@langchain/core/runnables";
import { ChatOpenAI } from "@langchain/openai";

const credential = new DefaultAzureCredential();

const model = new ChatOpenAI({
  azureOpenAIApiDeploymentName: "gpt-4o",
});

// Factory function creates history per session
function getMessageHistory(sessionId: string) {
  return new AzureCosmosDBNoSQLChatMessageHistory({
    endpoint: process.env.COSMOS_ENDPOINT,
    credential,
    databaseName: "mydb",
    containerName: "chat-history", // partition key should be /sessionId
    sessionId,
  });
}

// Wrap model with persistent history
const withHistory = new RunnableWithMessageHistory({
  runnable: model,
  getMessageHistory,
  inputMessagesKey: "input",
  historyMessagesKey: "history",
});

// Invoke with session tracking — messages persist across restarts
const response = await withHistory.invoke(
  { input: "What did we discuss earlier?" },
  { configurable: { sessionId: "user-123-session-456" } }
);
```

**Container design tips:**
- Use `/sessionId` as partition key for efficient single-session retrieval
- Enable TTL to auto-expire old conversations (e.g., 30 days)
- Use a composite index on `sessionId` + `_ts` if you query history by time range

Reference: [LangChain.js Azure Cosmos DB Chat History](https://js.langchain.com/docs/integrations/chat_memory/azure_cosmosdb_nosql/)

### 3.4 Configure Azure OpenAI Embedding Deployment Name for JS/TS LangChain

**Impact: MEDIUM** (incorrect deployment name causes 404 errors or uses wrong model)

## Configure Azure OpenAI Embedding Deployment Name for JS/TS LangChain

**Impact: MEDIUM (incorrect deployment name causes 404 errors or uses wrong model)**

When using `AzureOpenAIEmbeddings` with `@langchain/openai` in JavaScript/TypeScript, you must specify the Azure OpenAI **deployment name** (the name you chose when deploying the model in Azure AI Studio or via CLI) — not the bare model name. Azure OpenAI uses deployment names to route requests, and these can differ from the underlying model name. Passing a bare model name like `"text-embedding-3-small"` only works if your deployment happens to use that exact name.

**Incorrect (using bare model name or wrong property):**

```typescript
import { AzureOpenAIEmbeddings } from "@langchain/openai";

// BAD: "model" property is for OpenAI API, not Azure OpenAI
const embeddings = new AzureOpenAIEmbeddings({
  model: "text-embedding-3-small",  // Wrong property for Azure
});

// BAD: Using model name instead of deployment name
const embeddings2 = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small", // Only works if deployment has this exact name
  azureOpenAIApiVersion: "2024-06-01",
});

// BAD: Missing API version — will use an outdated default
const embeddings3 = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "my-embeddings",
});
```

**Correct (explicit deployment name and API version):**

```typescript
import { AzureOpenAIEmbeddings } from "@langchain/openai";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "my-embedding-deployment", // Your actual deployment name
  azureOpenAIApiVersion: "2024-06-01",
  // Endpoint and key from environment variables:
  // AZURE_OPENAI_API_INSTANCE_NAME or azureOpenAIApiInstanceName
  // AZURE_OPENAI_API_KEY or azureOpenAIApiKey (if not using managed identity)
});
```

**Correct (with managed identity — no API key needed):**

```typescript
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const credential = new DefaultAzureCredential();

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "my-embedding-deployment",
  azureOpenAIApiVersion: "2024-06-01",
  azureOpenAIApiInstanceName: "my-openai-resource", // just the resource name, not full URL
  credentials: credential,
});
```

**Tip:** Verify your deployment name with `az cognitiveservices account deployment list --name <resource> --resource-group <rg> --query "[].name"`.

Reference: [LangChain.js Azure OpenAI Embeddings](https://js.langchain.com/docs/integrations/text_embedding/azure_openai/)

### 3.5 Prevent Filter Injection in JS/TS LangChain Vector Store Queries

**Impact: CRITICAL** (prevents NoSQL injection attacks that can exfiltrate or corrupt data)

## Prevent Filter Injection in JS/TS LangChain Vector Store Queries

**Impact: CRITICAL (prevents NoSQL injection attacks that can exfiltrate or corrupt data)**

When passing filter clauses to `AzureCosmosDBNoSQLVectorStore` similarity searches, **never** concatenate user input directly into the filter string. Cosmos DB NoSQL queries support parameterized queries with `@param` placeholders — always use these to safely inject user-provided values. Concatenated filters allow attackers to manipulate query logic, bypass tenant isolation, or extract unauthorized data.

**Incorrect (string concatenation — SQL injection vulnerability):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

async function searchByCategory(store: AzureCosmosDBNoSQLVectorStore, userInput: string) {
  // CRITICAL VULNERABILITY: User can inject arbitrary SQL predicates
  // e.g., userInput = "electronics' OR c.secret != '"
  const results = await store.similaritySearch("find products", 10, {
    filter: `c.category = '${userInput}'`,
  });
  return results;
}

// Also BAD: Template literals are just string concatenation
async function searchByTenant(store: AzureCosmosDBNoSQLVectorStore, tenantId: string) {
  const results = await store.similaritySearch("query", 10, {
    filter: `c.tenantId = "${tenantId}"`,  // STILL INJECTABLE
  });
  return results;
}
```

**Correct (parameterized queries with @param placeholders):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

async function searchByCategory(store: AzureCosmosDBNoSQLVectorStore, userInput: string) {
  // SAFE: Parameters are escaped by the SDK — no injection possible
  const results = await store.similaritySearch("find products", 10, {
    filter: "c.category = @category",
    filterParams: [{ name: "@category", value: userInput }],
  });
  return results;
}

async function searchByTenant(store: AzureCosmosDBNoSQLVectorStore, tenantId: string) {
  // SAFE: Multi-tenant isolation with parameterized filter
  const results = await store.similaritySearch("query", 10, {
    filter: "c.tenantId = @tenantId AND c.isActive = true",
    filterParams: [{ name: "@tenantId", value: tenantId }],
  });
  return results;
}

// Multiple parameters
async function searchFiltered(
  store: AzureCosmosDBNoSQLVectorStore,
  category: string,
  minPrice: number
) {
  const results = await store.similaritySearch("query", 10, {
    filter: "c.category = @category AND c.price >= @minPrice",
    filterParams: [
      { name: "@category", value: category },
      { name: "@minPrice", value: minPrice },
    ],
  });
  return results;
}
```

**Why this matters:** In multi-tenant RAG applications, filter injection can bypass tenant isolation. An attacker providing `tenantA' OR '1'='1` as a tenant ID would access all tenants' data if the filter is concatenated.

Reference: [Azure Cosmos DB Parameterized Queries](https://learn.microsoft.com/azure/cosmos-db/nosql/query/parameterized-queries)

### 3.6 Configure Full-Text Prerequisites Before JS/TS LangChain Hybrid Search

**Impact: HIGH** (full-text and hybrid queries fail at runtime without container-level configuration)

## Configure Full-Text Prerequisites Before JS/TS LangChain Hybrid Search

**Impact: HIGH (full-text and hybrid queries fail at runtime without container-level configuration)**

Before using `FullTextSearch`, `Hybrid`, or `HybridScoreThreshold` search types with `AzureCosmosDBNoSQLVectorStore` in JavaScript/TypeScript, you must configure three things on your Cosmos DB container: (1) enable the full-text search capability on the account, (2) define a `fullTextPolicy` specifying which properties to index and their language, and (3) add `fullTextIndexes` entries to the indexing policy. Without all three, queries will fail with opaque errors.

**Incorrect (attempting hybrid search on unconfigured container):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

// Container created with only vector embedding policy — no full-text config
const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
  databaseName: "mydb",
  containerName: "docs",
});

// FAILS: "Full-text search is not enabled" or similar runtime error
const results = await store.similaritySearch("query", 10, {
  searchType: "Hybrid",
});
```

**Correct (container configured with full-text policy and indexes):**

First, configure the container (via ARM/Bicep/Terraform or CLI):

```json
{
  "containerProperties": {
    "id": "docs",
    "partitionKey": { "paths": ["/tenantId"], "kind": "Hash" },
    "fullTextPolicy": {
      "defaultLanguage": "en-US",
      "fullTextPaths": [
        { "path": "/content", "language": "en-US" },
        { "path": "/title", "language": "en-US" }
      ]
    },
    "indexingPolicy": {
      "includedPaths": [{ "path": "/*" }],
      "excludedPaths": [{ "path": "/embedding/*" }],
      "fullTextIndexes": [
        { "path": "/content" },
        { "path": "/title" }
      ],
      "vectorIndexes": [
        { "path": "/embedding", "type": "diskANN" }
      ]
    },
    "vectorEmbeddingPolicy": {
      "vectorEmbeddings": [
        {
          "path": "/embedding",
          "dataType": "float32",
          "distanceFunction": "cosine",
          "dimensions": 1536
        }
      ]
    }
  }
}
```

Then use hybrid search in your application:

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
});

const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential: new DefaultAzureCredential(),
  databaseName: "mydb",
  containerName: "docs",  // container has fullTextPolicy + fullTextIndexes
});

// Now hybrid search works — combines vector similarity with BM25 keyword matching
const results = await store.similaritySearch("specific keyword plus semantic meaning", 10, {
  searchType: "Hybrid",
});
```

**Checklist before enabling full-text/hybrid search:**
1. Account has full-text search capability enabled (`az cosmosdb update --capabilities EnableNoSQLFullTextSearch`)
2. Container has `fullTextPolicy` with paths and languages defined
3. Container indexing policy has `fullTextIndexes` for the same paths
4. Container has `vectorEmbeddingPolicy` and `vectorIndexes` (for hybrid)

Reference: [Azure Cosmos DB Full-Text Search](https://learn.microsoft.com/azure/cosmos-db/nosql/query/full-text-search)

### 3.7 Use Managed Identity for JS/TS LangChain Cosmos DB Integration

**Impact: CRITICAL** (zero-secret authentication eliminates credential leakage risk)

## Use Managed Identity for JS/TS LangChain Cosmos DB Integration

**Impact: CRITICAL (zero-secret authentication eliminates credential leakage risk)**

In production JavaScript/TypeScript applications using `@langchain/azure-cosmosdb`, always authenticate with `DefaultAzureCredential` from `@azure/identity` instead of connection strings. Connection strings contain master keys that grant full access — if leaked, they compromise the entire account. Managed identity provides automatic credential rotation and least-privilege access via RBAC roles.

**Incorrect (connection string in production):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
});

// BAD: Connection string contains master key — full account access if leaked
const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  connectionString: process.env.COSMOS_CONNECTION_STRING,
  databaseName: "mydb",
  containerName: "vectors",
});
```

**Correct (endpoint + DefaultAzureCredential):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
});

// GOOD: No secrets in code or config; works with system/user-assigned managed identity
const credential = new DefaultAzureCredential();
const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT, // e.g., "https://myaccount.documents.azure.com:443/"
  credential,
  databaseName: "mydb",
  containerName: "vectors",
});
```

**Required RBAC setup:** Assign the `Cosmos DB Built-in Data Contributor` role to your app's managed identity:

```bash
az cosmosdb sql role assignment create \
  --account-name myaccount \
  --resource-group myrg \
  --role-definition-id 00000000-0000-0000-0000-000000000002 \
  --principal-id <managed-identity-object-id> \
  --scope "/"
```

**Note:** When using RBAC, the database and container must be pre-created (via Bicep, Terraform, or CLI) — the SDK cannot create resources with data-plane-only permissions.

Reference: [Azure Cosmos DB RBAC with Azure Identity](https://learn.microsoft.com/azure/cosmos-db/nosql/security/how-to-grant-data-plane-role-based-access)

### 3.8 Choose the Correct Search Type for JS/TS LangChain Vector Store

**Impact: HIGH** (selecting wrong search type returns irrelevant results or causes errors)

## Choose the Correct Search Type for JS/TS LangChain Vector Store

**Impact: HIGH (selecting wrong search type returns irrelevant results or causes errors)**

The `@langchain/azure-cosmosdb` package supports multiple search types via `AzureCosmosDBNoSQLVectorStore`. Choose the appropriate type based on your retrieval needs. Using full-text or hybrid search requires pre-configured `fullTextPolicy` and `fullTextIndexes` on the container — otherwise queries will fail at runtime.

| Search Type | Use Case | Requires Full-Text Config |
|---|---|---|
| `Vector` | Pure semantic similarity (default) | No |
| `VectorScoreThreshold` | Semantic with minimum relevance cutoff | No |
| `FullTextSearch` | Keyword/BM25 matching only | Yes |
| `Hybrid` | Vector + full-text combined (RRF fusion) | Yes |
| `HybridScoreThreshold` | Hybrid with minimum score cutoff | Yes |

**Incorrect (using hybrid search without full-text configuration):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
  databaseName: "mydb",
  containerName: "vectors", // container has NO fullTextPolicy configured
});

// BAD: Will fail — container doesn't have full-text indexes
const results = await store.similaritySearch("query", 10, {
  searchType: "Hybrid",
});
```

**Correct (vector search — no special container config needed):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
  databaseName: "mydb",
  containerName: "vectors",
});

// Pure vector similarity search
const results = await store.similaritySearch("semantic query", 5);

// With score threshold — only return results above 0.7 similarity
const filtered = await store.similaritySearchWithScore("semantic query", 10, {
  searchType: "VectorScoreThreshold",
  scoreThreshold: 0.7,
});
```

**Correct (hybrid search — container has fullTextPolicy and fullTextIndexes):**

```typescript
// Container must have fullTextPolicy and fullTextIndexes configured FIRST
const results = await store.similaritySearch("keyword and semantic query", 10, {
  searchType: "Hybrid",
});
```

Reference: [LangChain.js Azure Cosmos DB NoSQL Vector Store](https://js.langchain.com/docs/integrations/vectorstores/azure_cosmosdb_nosql/)

### 3.9 Use AzureCosmosDBNoSQLSemanticCache for LLM Cost Reduction in JS/TS

**Impact: MEDIUM** (reduces LLM API costs and latency by caching semantically similar queries)

## Use AzureCosmosDBNoSQLSemanticCache for LLM Cost Reduction in JS/TS

**Impact: MEDIUM (reduces LLM API costs and latency by caching semantically similar queries)**

When building LLM-powered applications with LangChain.js, use `AzureCosmosDBNoSQLSemanticCache` to cache LLM responses in Cosmos DB. Unlike exact-match caches, semantic cache uses vector similarity to return cached responses for queries that are semantically similar (not just identical). This reduces LLM API costs for repeated or paraphrased queries and cuts response latency from seconds to milliseconds.

**Incorrect (no caching — every request hits the LLM):**

```typescript
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  azureOpenAIApiDeploymentName: "gpt-4o",
});

// BAD: Every call pays full LLM cost, even for repeated/similar questions
const response1 = await model.invoke("What is Azure Cosmos DB?");
const response2 = await model.invoke("Tell me about Azure Cosmos DB"); // Pays again
```

**Incorrect (exact-match cache misses paraphrased queries):**

```typescript
import { InMemoryCache } from "langchain/cache";

const model = new ChatOpenAI({
  azureOpenAIApiDeploymentName: "gpt-4o",
  cache: new InMemoryCache(), // Only matches exact string — misses paraphrases
});
```

**Correct (semantic cache with Cosmos DB):**

```typescript
import { AzureCosmosDBNoSQLSemanticCache } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings, ChatOpenAI } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const credential = new DefaultAzureCredential();

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
  azureOpenAIApiVersion: "2024-06-01",
});

const cache = new AzureCosmosDBNoSQLSemanticCache(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
  databaseName: "mydb",
  containerName: "semantic-cache",
  similarityScoreThreshold: 0.8, // Only return cache hits above 80% similarity
});

const model = new ChatOpenAI({
  azureOpenAIApiDeploymentName: "gpt-4o",
  cache, // Semantically similar queries return cached responses
});

// Second call with paraphrased question hits cache — no LLM API call
const response1 = await model.invoke("What is Azure Cosmos DB?");
const response2 = await model.invoke("Tell me about Azure Cosmos DB"); // Cache hit!
```

**Container requirements:** The cache container needs a vector embedding policy configured for the embedding dimension (e.g., 1536 for text-embedding-3-small). Use TTL on the container to auto-expire stale cache entries.

Reference: [LangChain.js Azure Cosmos DB Semantic Cache](https://js.langchain.com/docs/integrations/llm_caching/azure_cosmosdb_nosql/)

### 3.10 Correctly Initialize AzureCosmosDBNoSQLVectorStore in JavaScript/TypeScript

**Impact: HIGH** (prevents runtime connection failures and misconfigured vector stores)

## Correctly Initialize AzureCosmosDBNoSQLVectorStore in JavaScript/TypeScript

**Impact: HIGH (prevents runtime connection failures and misconfigured vector stores)**

When using `@langchain/azure-cosmosdb` in JavaScript/TypeScript, initialize `AzureCosmosDBNoSQLVectorStore` with either a connection string (development) or endpoint + `DefaultAzureCredential` (production). The target database and container must already exist when using RBAC/managed identity — the SDK will not auto-create them. Always pass the embedding model instance at construction time.

**Incorrect (missing embedding model, relying on auto-create with RBAC):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

// BAD: No embedding model provided — store cannot generate vectors
const store = new AzureCosmosDBNoSQLVectorStore({
  connectionString: process.env.COSMOS_CONNECTION_STRING,
  databaseName: "mydb",
  containerName: "vectors",
});

// BAD: With RBAC, database/container must pre-exist — SDK cannot create them
const store2 = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  databaseName: "nonexistent-db",
  containerName: "nonexistent-container",
});
```

**Correct (connection string for development):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
});

const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  connectionString: process.env.COSMOS_CONNECTION_STRING,
  databaseName: "mydb",
  containerName: "vectors",
});
```

**Correct (managed identity for production — database/container pre-created):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
});

const credential = new DefaultAzureCredential();
const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
  databaseName: "mydb",       // must already exist
  containerName: "vectors",   // must already exist with vector policy
});
```

Reference: [LangChain.js Azure Cosmos DB Integration](https://js.langchain.com/docs/integrations/vectorstores/azure_cosmosdb_nosql/)

### 3.11 Use Persistent MCP Client Sessions for Multi-Agent Applications

**Impact: HIGH** (prevents session initialization overhead and connection churn)

## Use Persistent MCP Client Sessions for Multi-Agent Applications

**Impact: HIGH (prevents session initialization overhead and connection churn)**

When using `MultiServerMCPClient` with LangGraph agents, avoid creating a new client instance per request. MCP sessions involve transport negotiation, tool discovery, and server handshakes. Creating a client per request adds latency and may exhaust server connection limits.

**Note:** The API changed significantly in `langchain-mcp-adapters >= 0.2.0`. The persistent session pattern (manual `__aenter__`/`__aexit__`) only applies to versions `< 0.2.0`. In `>= 0.2.0`, sessions are managed internally per call via `get_tools()`.

**Incorrect (new client per request — high overhead, applies to all versions):**

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

async def handle_request(user_input):
    # BAD: Creates a new client (and underlying sessions) for every single request
    client = MultiServerMCPClient({
        "my_server": {"transport": "streamable_http", "url": "http://localhost:8080/mcp"}
    })
    tools = await client.get_tools()
    # ... invoke agent ...
    # Client discarded, next request pays setup cost again
```

**Correct (>= 0.2.0 — single client instance, get_tools() manages sessions internally):**

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

_mcp_client: MultiServerMCPClient | None = None

async def setup_mcp():
    """Call once during application startup."""
    global _mcp_client
    _mcp_client = MultiServerMCPClient({
        "my_server": {
            "transport": "streamable_http",
            "url": f"{MCP_SERVER_BASE_URL}/mcp",
        }
    })
    # get_tools() creates a per-call session under the hood
    tools = await _mcp_client.get_tools()
    return tools

# No explicit cleanup needed — sessions are per-call in >= 0.2.0
```

**Correct (< 0.2.0 only — persistent session initialized once at startup):**

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

_mcp_client = None
_session_context = None
_persistent_session = None

async def setup_mcp():
    """Call once during application startup (< 0.2.0 API only)."""
    global _mcp_client, _session_context, _persistent_session

    _mcp_client = MultiServerMCPClient({
        "my_server": {"transport": "streamable_http", "url": mcp_server_url}
    })
    _session_context = _mcp_client.session("my_server")
    _persistent_session = await _session_context.__aenter__()

    # Load tools once — they remain valid for the session lifetime
    tools = await load_mcp_tools(_persistent_session)
    return tools

async def cleanup_mcp():
    """Call during application shutdown (< 0.2.0 API only)."""
    global _session_context, _persistent_session
    if _session_context and _persistent_session:
        await _session_context.__aexit__(None, None, None)
        _session_context = None
        _persistent_session = None
```

**Tip:** Wrap the session setup in retry logic with exponential backoff for production deployments where the MCP server may take time to become ready.

Reference: [langchain-mcp-adapters documentation](https://github.com/langchain-ai/langchain-mcp-adapters)

### 3.12 Handle MCP ToolMessage Content Format Variations

**Impact: HIGH** (prevents JSON parse failures from langchain-mcp-adapters >= 0.2.0)

## Handle MCP ToolMessage Content Format Variations

**Impact: HIGH (prevents JSON parse failures from langchain-mcp-adapters >= 0.2.0)**

Starting with `langchain-mcp-adapters` 0.2.0, `ToolMessage.content` changed from a plain JSON string to a list of content blocks (e.g., `[{"type": "text", "text": "..."}]`). Any code that parses `ToolMessage.content` must handle both formats to remain compatible across versions and avoid `json.JSONDecodeError` or `TypeError`.

**Incorrect (assumes content is always a string):**

```python
import json
from langchain_core.messages import ToolMessage

def extract_routing_info(message: ToolMessage):
    # BAD: Fails when content is a list (langchain-mcp-adapters >= 0.2.0)
    data = json.loads(message.content)
    return data.get("goto")
```

Error with newer adapter versions:
```
TypeError: the JSON object must be str, bytes or bytearray, not list
```

**Correct (handles both string and list formats):**

```python
import json
from langchain_core.messages import ToolMessage

def extract_routing_info(message: ToolMessage):
    content = message.content

    # Handle list-of-blocks format (langchain-mcp-adapters >= 0.2.0)
    if isinstance(content, list):
        text_parts = [block["text"] for block in content if block.get("type") == "text"]
        content = text_parts[0] if text_parts else ""

    # Now content is a plain string — safe to parse
    data = json.loads(content)
    return data.get("goto")
```

**When this matters:** Any time you inspect tool call results programmatically — for example, to extract routing decisions, parse structured responses, or implement conditional logic based on tool outputs.

Reference: [langchain-mcp-adapters changelog](https://github.com/langchain-ai/langchain-mcp-adapters)

### 3.13 Filter MCP Tools by Name Prefix for Agent Assignment

**Impact: MEDIUM** (reduces agent confusion and improves routing accuracy)

## Filter MCP Tools by Name Prefix for Agent Assignment

**Impact: MEDIUM (reduces agent confusion and improves routing accuracy)**

When a single MCP server exposes tools for multiple domains, assign each LangGraph agent only the subset of tools it needs. Use a name-prefix convention on the server side (e.g., `get_transaction_history`, `get_offer_information`, `transfer_to_sales_agent`) and filter client-side by prefix. This prevents agents from calling tools outside their domain and reduces prompt confusion from irrelevant tool descriptions.

**Incorrect (all agents receive all tools):**

```python
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

all_tools = await load_mcp_tools(session)

# BAD: Every agent sees every tool — leads to wrong tool calls
support_agent = create_react_agent(model, all_tools, prompt=support_prompt)
sales_agent = create_react_agent(model, all_tools, prompt=sales_prompt)
transactions_agent = create_react_agent(model, all_tools, prompt=transactions_prompt)
```

**Correct (filter tools by prefix per agent):**

```python
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

all_tools = await load_mcp_tools(session)

def filter_tools_by_prefix(tools, prefixes):
    """Return only tools whose name starts with one of the given prefixes."""
    return [t for t in tools if any(t.name.startswith(p) for p in prefixes)]

# Each agent gets only the tools relevant to its domain
support_tools = filter_tools_by_prefix(all_tools, [
    "service_request", "get_branch_location", "transfer_to_"
])
sales_tools = filter_tools_by_prefix(all_tools, [
    "get_offer_information", "create_account", "calculate_monthly_payment", "transfer_to_"
])
transactions_tools = filter_tools_by_prefix(all_tools, [
    "bank_transfer", "get_transaction_history", "bank_balance", "transfer_to_"
])

support_agent = create_react_agent(model, support_tools, prompt=support_prompt)
sales_agent = create_react_agent(model, sales_tools, prompt=sales_prompt)
transactions_agent = create_react_agent(model, transactions_tools, prompt=transactions_prompt)
```

**Naming convention tip:** Include `transfer_to_` prefixed tools in each agent's set so agents can hand off conversations to other agents via the routing mechanism.

Reference: [LangGraph prebuilt agents](https://langchain-ai.github.io/langgraph/reference/prebuilt/)

---

## 4. Design Patterns

**Impact: HIGH**

### 4.1 Use Point Reads for AI-Grounding and RAG Retrieval When ID Is Known

**Impact: HIGH** (1 RU point read vs ~2.5+ RU query per grounding fetch; reduces tool-call latency in LLM loops)

## Use Point Reads for AI-Grounding and RAG Retrieval When ID Is Known

In AI-grounded workloads an LLM tool-use loop typically resolves a concrete entity id (e.g., `orderId`, `sessionId`, `documentId`) from the user turn or tool-call arguments, then fetches the full document from Cosmos DB to build the grounding context for the model. Because the id and partition key are both known at call time, a point read should always be used instead of a query. This applies to any retrieval step that feeds data into an LLM context window — RAG retrieval, tool-call handlers, grounding functions, or agent data-fetching steps.

**How to recognize this pattern — static tell-tales:**

- An LLM / AI client import in the same module (e.g., `OpenAI`, `AzureOpenAI`, `ChatCompletionClient`, Semantic Kernel, LangChain)
- A function that parses tool-call arguments or assembles a `messages` array
- A Cosmos DB call using a single-id equality filter where the id was extracted from user input or a tool-call response

**Incorrect (query when id and partition key are both available from the tool call):**

```typescript
// ❌ Generic query — id is already known from the user turn / tool call
export async function groundOrderContext(orderId: string, userId: string) {
  const { resources: orders } = await ordersContainer.items
    .query<Order>({
      query: "SELECT * FROM c WHERE c.orderId = @o",
      parameters: [{ name: "@o", value: orderId }],
    })
    .fetchAll();

  const { resources: events } = await eventsContainer.items
    .query<DeliveryEvent>({
      query: "SELECT * FROM c WHERE c.orderId = @o ORDER BY c.timestamp DESC",
      parameters: [{ name: "@o", value: orderId }],
    })
    .fetchAll();

  return buildGroundingContext(orders[0], events);
}
```

```python
# ❌ Query instead of point read — id and partition key both known
def ground_order_context(order_id: str, user_id: str):
    orders = list(orders_container.query_items(
        query="SELECT * FROM c WHERE c.id = @id",
        parameters=[{"name": "@id", "value": order_id}],
        partition_key=user_id,
    ))
    return build_grounding_context(orders[0]) if orders else None
```

**Correct (point read for the primary document, partition-scoped projection for related items):**

```typescript
// ✅ Point read for the order (id + partition key both known from tool call)
export async function groundOrderContext(orderId: string, userId: string) {
  const orderResp = await ordersContainer.item(orderId, userId).read<Order>();
  const order = orderResp.resource;
  if (!order) return null;

  // ✅ Partition-key-scoped projection for related event list
  const { resources: events } = await eventsContainer.items
    .query<DeliveryEvent>(
      {
        query:
          "SELECT c.id, c.orderId, c.timestamp, c.status, c.note FROM c WHERE c.orderId = @o ORDER BY c.timestamp DESC",
        parameters: [{ name: "@o", value: orderId }],
      },
      { partitionKey: orderId }
    )
    .fetchAll();

  return buildGroundingContext(order, events);
}
```

```python
# ✅ Point read — 1 RU, no query engine overhead
def ground_order_context(order_id: str, user_id: str):
    order = orders_container.read_item(item=order_id, partition_key=user_id)
    return build_grounding_context(order)
```

**Why this matters for AI workloads:**

1. **Latency-sensitive** — each tool call adds to perceived LLM response time; a point read (1 RU, single backend hop) is the fastest possible retrieval
2. **Throughput-sensitive** — hot conversations drive the same partition key repeatedly; cross-partition fan-out under load hot-spots a single logical partition fastest
3. **ID is known by construction** — the LLM tool-use loop hands the agent an id parsed from the user turn or a prior tool result; agents should recognise this signal and reach for the point read

See also: `query-point-reads` (general point-read guidance), `query-use-projections` (select only needed fields), `query-avoid-cross-partition` (avoid cross-partition fan-out).

Reference: [Request Units — point reads cost fewer RUs than queries](https://learn.microsoft.com/azure/cosmos-db/request-units#request-unit-considerations)

### 4.2 Use Background Tasks for Non-Blocking Chat History Storage

**Impact: MEDIUM** (reduces API response latency by 50-200ms per request)

## Use Background Tasks for Non-Blocking Chat History Storage

**Impact: MEDIUM (reduces API response latency by 50-200ms per request)**

After a LangGraph agent produces a response, storing chat history and debug logs in Cosmos DB is important for the UI but not for the immediate API response. Use FastAPI's `BackgroundTasks` to defer these writes, returning the agent response to the user immediately. This avoids adding Cosmos DB write latency (typically 5-20ms per write, more with multiple writes) to the user-facing response time.

**Incorrect (blocking writes before returning response):**

```python
from fastapi import FastAPI

@app.post("/chat/{session_id}")
async def chat(session_id: str, user_message: str):
    response = await graph.ainvoke(state, config, stream_mode="updates")
    messages = extract_response(response)

    # BAD: User waits for all these DB writes to complete before seeing the response
    for msg in messages:
        store_chat_history(msg)  # 5-20ms each
    store_debug_log(session_id, response)  # Another 10-20ms
    update_active_agent(session_id, last_agent)  # Another 5-10ms

    return messages  # User waited an extra 50-200ms unnecessarily
```

**Correct (defer writes with BackgroundTasks):**

```python
from fastapi import FastAPI, BackgroundTasks

def process_post_response(messages, session_id, tenant_id, user_id, active_agent):
    """Runs after the response is sent to the client."""
    for msg in messages:
        store_chat_history(msg)
    update_active_agent_in_latest_message(session_id, active_agent)

@app.post("/chat/{session_id}")
async def chat(
    session_id: str,
    user_message: str,
    background_tasks: BackgroundTasks
):
    response = await graph.ainvoke(state, config, stream_mode="updates")
    messages = extract_response(response)

    # Schedule writes to run after the response is sent
    background_tasks.add_task(
        process_post_response, messages, session_id, tenant_id, user_id, active_agent
    )

    # Response returned immediately — user sees it while writes happen in background
    return messages
```

**When to use background tasks vs. blocking:**
- **Background:** Chat history storage, debug log writes, session name updates, analytics
- **Blocking:** Active agent patch (if needed for the *current* response routing), session creation, critical state that the next request depends on

**Note:** Background tasks in FastAPI run in the same process after the response. For truly fire-and-forget workloads at scale, consider Azure Cosmos DB change feed triggers or message queues.

Reference: [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

### 4.3 Tag AI Messages with Agent Name for API Response Attribution

**Impact: MEDIUM** (enables API layer to report which agent generated a response for UI display and logging)

## Tag AI Messages with Agent Name for API Response Attribution

**Impact: MEDIUM (enables API layer to report which agent generated a response for UI display and logging)**

`create_react_agent` does not set the `name` field on AI messages it produces. If the API layer needs to report which agent generated a response (e.g., for UI display or logging), it has no way to determine this from the message itself. Tag the last AI message with the agent name before returning from each node function.

**Incorrect (no attribution — API cannot determine which agent responded):**

```python
async def call_product_search(state, config):
    response = await product_search_agent.ainvoke(state)
    # BAD: No way to tell which agent produced this response at the API layer
    return Command(update=response, goto=END)
```

**Correct (tag last AI message with agent name):**

```python
def _tag_last_ai_message(response: dict, agent_name: str) -> dict:
    """Set `name` on the last AI message for API-layer attribution."""
    msgs = response.get("messages", [])
    for msg in reversed(msgs):
        if hasattr(msg, "type") and msg.type == "ai" and msg.content:
            msg.name = agent_name
            break
    return response

async def call_product_search(state, config):
    response = await product_search_agent.ainvoke(state)
    # Tag the response so the API layer knows which agent answered
    _tag_last_ai_message(response, "product_search_agent")
    return Command(update=response, goto=END)
```

**Key points:**
1. Iterate in reverse to find the last AI message with content (skip empty tool-call messages)
2. Set `msg.name = agent_name` — LangGraph preserves this field through state updates
3. Apply tagging in every node function before returning the `Command`
4. The API layer can then read `message.name` to display agent attribution in the UI

Reference: [LangGraph multi-agent patterns](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)

### 4.4 Persist Active Agent in Cosmos DB for Deterministic Routing

**Impact: HIGH** (eliminates LLM re-classification overhead and prevents routing drift)

## Persist Active Agent in Cosmos DB for Deterministic Routing

**Impact: HIGH (eliminates LLM re-classification overhead and prevents routing drift)**

In multi-agent systems, once a user has been routed to a specialist agent, persist the active agent name in Cosmos DB alongside the conversation session. On subsequent messages, perform a point read to retrieve the active agent instead of re-invoking the coordinator LLM to classify intent. This is faster (single-digit millisecond point read vs. hundreds of milliseconds for LLM inference), deterministic, and avoids mid-conversation routing flip-flops.

**Incorrect (re-classify every message through the coordinator):**

```python
async def route_message(state, config):
    # BAD: Every user message goes through the coordinator LLM for classification
    # Adds latency and may incorrectly re-route mid-conversation
    response = await coordinator_agent.ainvoke(state)
    return determine_agent_from_response(response)
```

**Correct (async point read for active agent, coordinator only for new conversations):**

```python
import asyncio
from azure.cosmos import CosmosClient

def _read_active_agent_from_db(tenant_id: str, user_id: str, thread_id: str) -> str:
    """Synchronous helper — runs in a thread pool."""
    try:
        item = container.read_item(
            item=thread_id,
            partition_key=[tenant_id, user_id, thread_id]
        )
        return item.get("activeAgent", "unknown")
    except Exception:
        return "unknown"

async def get_active_agent(state, config) -> str:
    """Routing function — must be async and must NEVER raise."""
    thread_id = config.get("configurable", {}).get("thread_id", "")
    user_id = config.get("configurable", {}).get("userId", "")
    tenant_id = config.get("configurable", {}).get("tenantId", "")

    # O(1) point read — single-digit ms latency, 1 RU cost
    # Wrapped in asyncio.to_thread to avoid blocking the event loop
    try:
        active_agent = await asyncio.wait_for(
            asyncio.to_thread(_read_active_agent_from_db, tenant_id, user_id, thread_id),
            timeout=5.0,
        )
    except Exception:
        # Covers: CosmosResourceNotFoundError (new session),
        # asyncio.TimeoutError (cold start / slow DB),
        # CredentialUnavailableError (auth not ready)
        return "coordinator"

    # If an agent is already assigned, route directly — skip coordinator
    if active_agent not in [None, "unknown", "coordinator"]:
        return active_agent

    # Only invoke coordinator for new/unrouted conversations
    return "coordinator"
```

**Updating the active agent:** When a transfer tool is called (e.g., `transfer_to_sales_agent`), patch the Cosmos DB document with the new active agent name:

```python
from azure.cosmos import PartitionKey

def patch_active_agent(tenant_id, user_id, thread_id, new_agent):
    """Partial update — only modifies the activeAgent field (minimal RU cost)."""
    container.patch_item(
        item=thread_id,
        partition_key=[tenant_id, user_id, thread_id],
        patch_operations=[
            {"op": "set", "path": "/activeAgent", "value": new_agent}
        ]
    )
```

**Key design points:**
1. Use hierarchical partition key (`/tenantId`, `/userId`, `/sessionId`) for efficient multi-tenant lookups
2. The point read costs 1 RU regardless of document size
3. Use patch operations (not full replace) to update the active agent — costs fewer RUs
4. Fall back to the coordinator only when `activeAgent` is `null` or `"unknown"`
5. The routing function must NEVER raise — any exception (404, timeout, credential error) should fall through to the coordinator
6. Always use `asyncio.to_thread()` for sync Cosmos DB calls in routing functions to avoid blocking the event loop

Reference: [Azure Cosmos DB point reads](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-read-item)

### 4.5 Wrap Cosmos DB Sync Calls in asyncio.to_thread for LangGraph Routing Functions

**Impact: CRITICAL** (prevents event loop blocking that causes all concurrent requests to hang)

## Wrap Cosmos DB Sync Calls in asyncio.to_thread for LangGraph Routing Functions

**Impact: CRITICAL (prevents event loop blocking that causes all concurrent requests to hang)**

LangGraph's `add_conditional_edges` routing function runs inside the async event loop. If the routing function calls `DefaultAzureCredential` or `container.read_item()` synchronously, it blocks the entire event loop — causing all concurrent requests to hang and potentially triggering timeouts. Always wrap synchronous Cosmos DB SDK calls in `asyncio.to_thread()` and add a timeout to prevent hung routing if Cosmos DB is slow or unreachable.

**Incorrect (synchronous Cosmos DB call blocks the event loop):**

```python
from azure.cosmos import CosmosClient

def get_active_agent(state, config) -> str:
    thread_id = config["configurable"]["thread_id"]
    # BAD: Blocks the event loop when called from LangGraph's async runtime
    item = container.read_item(item=thread_id, partition_key=thread_id)
    active_agent = item.get("activeAgent", "unknown")
    if active_agent not in [None, "unknown", "coordinator"]:
        return active_agent
    return "coordinator"
```

**Correct (async wrapper with timeout and fallback):**

```python
import asyncio
from azure.cosmos import CosmosClient

def _read_active_agent_from_db(thread_id: str) -> str:
    """Synchronous helper — runs in a thread pool."""
    container = get_sync_container("ChatSessions")
    item = container.read_item(item=thread_id, partition_key=thread_id)
    return item.get("activeAgent", "unknown")

async def get_active_agent_from_db(thread_id: str) -> str:
    """Non-blocking wrapper with timeout for reading active agent from Cosmos DB."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_read_active_agent_from_db, thread_id),
            timeout=5.0,
        )
    except Exception:
        # Covers: CosmosResourceNotFoundError (new session),
        # asyncio.TimeoutError (cold start / slow DB),
        # CredentialUnavailableError (auth not ready)
        return "unknown"

async def get_active_agent(state, config) -> str:
    """Routing function for add_conditional_edges — must be async def."""
    thread_id = config.get("configurable", {}).get("thread_id", "")
    active_agent = await get_active_agent_from_db(thread_id)
    if active_agent not in [None, "unknown", "coordinator"]:
        return active_agent
    return "coordinator"
```

**Key points:**
1. The routing function MUST be `async def` when using Cosmos DB lookups
2. Always wrap `DefaultAzureCredential` and `read_item()` in `asyncio.to_thread()`
3. Add a timeout (5s) to prevent hung routing if Cosmos DB is slow or unreachable
4. Fall back to "coordinator" on any exception — never let a DB failure crash the graph
5. The routing function must NEVER raise — it runs on every single message as a graph entry point

Reference: [Python asyncio.to_thread documentation](https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread)

### 4.6 Use asyncio.to_thread for Active Agent Writes in LangGraph Node Functions

**Impact: HIGH** (prevents event loop blocking during Cosmos DB upserts in async node functions)

## Use asyncio.to_thread for Active Agent Writes in LangGraph Node Functions

**Impact: HIGH (prevents event loop blocking during Cosmos DB upserts in async node functions)**

When saving the active agent after a transfer (inside a LangGraph node function), using the sync Cosmos DB SDK also blocks the event loop. Node functions in LangGraph run as coroutines. Wrap synchronous write operations in `asyncio.to_thread()` to keep the event loop responsive.

**Incorrect (synchronous upsert blocks the event loop inside an async node):**

```python
async def call_agent(state, config):
    response = await agent.ainvoke(state)
    # BAD: Blocks the event loop during upsert
    container.upsert_item({
        "id": thread_id,
        "sessionId": thread_id,
        "activeAgent": "target_agent",
    })
    return Command(update=response, goto="target_agent")
```

**Correct (non-blocking write with asyncio.to_thread):**

```python
import asyncio
import logging

logger = logging.getLogger(__name__)

async def save_active_agent_to_db_async(
    thread_id: str, agent_name: str, tenant_id: str, user_id: str
):
    """Non-blocking upsert of active agent to Cosmos DB."""
    def _save():
        try:
            container = get_sync_container("ChatSessions")
            container.upsert_item({
                "id": thread_id,
                "sessionId": thread_id,
                "tenantId": tenant_id,
                "userId": user_id,
                "activeAgent": agent_name,
            })
        except Exception as e:
            logger.error(f"Failed to save active agent: {e}")
    await asyncio.to_thread(_save)

async def call_agent(state, config):
    response = await agent.ainvoke(state)
    thread_id = config.get("configurable", {}).get("thread_id", "")
    tenant_id = config.get("configurable", {}).get("tenantId", "")
    user_id = config.get("configurable", {}).get("userId", "")
    # Non-blocking write — errors logged but not propagated
    await save_active_agent_to_db_async(thread_id, "target_agent", tenant_id, user_id)
    return Command(update=response, goto="target_agent")
```

**Key points:**
1. Wrap all synchronous Cosmos DB write operations in `asyncio.to_thread()` inside async node functions
2. Writes can be fire-and-forget — errors are logged but not propagated, since failing to persist the active agent is not fatal to the current request
3. Keep the synchronous logic in a nested helper function for clarity and thread-safety
4. Use `upsert_item` (not `create_item`) to handle both new and existing sessions

Reference: [Python asyncio.to_thread documentation](https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread)

### 4.7 Store Chat History Separately from LangGraph Checkpoints

**Impact: MEDIUM** (enables efficient message retrieval and agent attribution)

## Store Chat History Separately from LangGraph Checkpoints

**Impact: MEDIUM (enables efficient message retrieval and agent attribution)**

LangGraph's checkpointer (CosmosDBSaver) stores full graph state for resumption, but it is not optimized for retrieving displayable chat history. Checkpoint data contains internal graph metadata, tool messages, system messages, and duplicate entries from each node execution. Instead, maintain a separate Cosmos DB container for chat history with only the fields your UI needs (sender, text, timestamp, which agent responded). This enables efficient queries, proper agent attribution, and avoids scanning checkpoint blobs.

**Incorrect (reading chat history from the checkpointer store):**

```python
@app.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str):
    config = {"configurable": {"thread_id": session_id, "checkpoint_ns": ""}}
    # BAD: Checkpointer stores ALL graph state — tool messages, system messages,
    # intermediate states, duplicates from each node. Expensive to scan and filter.
    checkpoints = [cp async for cp in checkpointer.alist(config)]
    if not checkpoints:
        return []
    
    # Must dig into checkpoint internals to extract displayable messages
    messages = checkpoints[-1].checkpoint["channel_values"]["messages"]
    # No record of which agent responded — lost in checkpoint format
    return filter_displayable(messages)
```

**Correct (store displayable history in a dedicated container):**

```python
from azure.cosmos import CosmosClient

# Dedicated container with partition key /sessionId for efficient retrieval
history_container = database.get_container_client("ChatHistory")

def store_chat_message(session_id: str, tenant_id: str, user_id: str, 
                       sender: str, text: str, agent_name: str):
    """Store a single displayable message after graph execution completes."""
    history_container.create_item({
        "id": str(uuid.uuid4()),
        "sessionId": session_id,
        "tenantId": tenant_id,
        "userId": user_id,
        "sender": sender,
        "agentName": agent_name,  # Which agent responded — not available in checkpoints
        "text": text,
        "timestamp": datetime.utcnow().isoformat(),
    })

@app.get("/sessions/{session_id}/messages")
def get_messages(session_id: str):
    # Single-partition query — fast and cheap (few RUs)
    return list(history_container.query_items(
        query="SELECT * FROM c WHERE c.sessionId = @sid ORDER BY c.timestamp",
        parameters=[{"name": "@sid", "value": session_id}],
        partition_key=session_id
    ))
```

**Why separate storage:**
1. **Agent attribution** — checkpoints don't track which agent produced each response
2. **Query efficiency** — dedicated container with `/sessionId` partition key enables single-partition queries
3. **Cleaner data** — no tool messages, system messages, or graph internal state
4. **Independent scaling** — chat history access patterns differ from checkpointing (read-heavy vs. write-heavy)

Reference: [Azure Cosmos DB container design](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-model-partition-example)

### 4.8 Initialize LangGraph Agents in FastAPI Startup with Retry

**Impact: HIGH** (prevents request failures when dependent services are not yet ready)

## Initialize LangGraph Agents in FastAPI Startup with Retry

**Impact: HIGH (prevents request failures when dependent services are not yet ready)**

LangGraph agents that depend on external services (MCP servers, Cosmos DB, Azure OpenAI) must be initialized asynchronously during application startup, not at module import time or on first request. Use FastAPI's startup event (or lifespan) with retry logic to handle cases where dependent services take time to become available (e.g., in container orchestration environments where services start in parallel).

**Incorrect (initialize at module level — blocks import, no retry):**

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

# BAD: Runs at import time, fails if MCP server isn't ready yet
client = MultiServerMCPClient({"server": {"transport": "streamable_http", "url": mcp_url}})
tools = asyncio.run(load_tools(client))  # Blocks and may fail
```

**Incorrect (initialize on first request — slow first response, no retry):**

```python
@app.post("/chat")
async def chat(message: str):
    global _initialized
    if not _initialized:
        # BAD: First user pays full initialization cost (seconds)
        # No retry if MCP server is temporarily unavailable
        await setup_agents()
        _initialized = True
    # ...
```

**Correct (startup event with retry and fallback):**

```python
import asyncio
from fastapi import FastAPI, HTTPException

app = FastAPI()
_agents_ready = False

@app.on_event("startup")
async def initialize_agents():
    global _agents_ready
    max_retries = 5
    retry_delay = 10  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            await setup_agents()  # Connects to MCP, loads tools, creates agents, inits checkpointer
            _agents_ready = True
            return
        except Exception as e:
            if attempt < max_retries:
                await asyncio.sleep(retry_delay)
            else:
                # Start anyway — will initialize on demand
                _agents_ready = False

async def ensure_ready():
    """Dependency that ensures agents are initialized before handling requests."""
    if not _agents_ready:
        try:
            await setup_agents()
        except Exception:
            raise HTTPException(status_code=503, detail="Service unavailable — agents not initialized")

@app.post("/chat")
async def chat(message: str):
    await ensure_ready()
    # ... handle request ...
```

**Production tips:**
- Set retry delay via environment variable (e.g., `STARTUP_DELAY_SECONDS`) for container orchestration tuning
- Add a `/health/ready` endpoint that returns 503 until `_agents_ready` is `True` — used by load balancers and container health probes
- For FastAPI >= 0.93, prefer `lifespan` context manager over deprecated `on_event`

Reference: [FastAPI lifespan events](https://fastapi.tiangolo.com/advanced/events/)

### 4.9 Use LangGraph Interrupt for Human-in-the-Loop Confirmation

**Impact: HIGH** (enables safe confirmation flows for sensitive operations)

## Use LangGraph Interrupt for Human-in-the-Loop Confirmation

**Impact: HIGH (enables safe confirmation flows for sensitive operations)**

When agents perform sensitive operations (e.g., money transfers, account creation, data deletion), use LangGraph's `interrupt()` mechanism to pause execution and wait for user confirmation. The graph state is persisted to Cosmos DB via the checkpointer, and execution resumes from the same point when the user responds. This avoids custom polling loops or separate confirmation APIs.

**Incorrect (no confirmation — agent executes sensitive action immediately):**

```python
from langgraph.graph import StateGraph, MessagesState

async def call_transactions_agent(state: MessagesState, config):
    # BAD: Agent may call bank_transfer without user confirmation
    response = await transactions_agent.ainvoke(state)
    return {"messages": response["messages"]}
```

**Incorrect (manual polling loop instead of interrupt):**

```python
async def call_transactions_agent(state: MessagesState, config):
    response = await transactions_agent.ainvoke(state)
    # BAD: Custom polling — reinvents what LangGraph interrupt provides
    while not await check_user_confirmed(config):
        await asyncio.sleep(1)
    return {"messages": response["messages"]}
```

**Correct (interrupt pauses graph, state saved to Cosmos DB):**

```python
from langgraph.types import Command, interrupt
from langgraph.graph import StateGraph, MessagesState
from langchain_azure_cosmosdb import CosmosDBSaver

def human_node(state: MessagesState, config) -> None:
    """Pauses the graph and waits for the next user message."""
    interrupt(value="Ready for user input.")
    return None

async def call_transactions_agent(state: MessagesState, config) -> Command:
    response = await transactions_agent.ainvoke(state)
    # Route to human node — graph pauses, state persisted to Cosmos DB
    return Command(update=response, goto="human")

builder = StateGraph(MessagesState)
builder.add_node("transactions_agent", call_transactions_agent)
builder.add_node("human", human_node)
# ... add edges ...

graph = builder.compile(checkpointer=CosmosDBSaver(async_container))
```

**How it works:**
1. Agent node returns `Command(goto="human")` after processing
2. The `human_node` calls `interrupt()`, which persists state and pauses
3. The caller receives a response indicating the graph is waiting
4. When the user sends a new message, the caller resumes the graph with `graph.stream(new_input, config)`
5. The checkpointer restores state from Cosmos DB and continues from where it paused

Reference: [LangGraph human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)

### 4.10 Use StateGraph with Conditional Edges for Multi-Agent Routing

**Impact: HIGH** (enables deterministic agent hand-off in multi-agent LangGraph applications)

## Use StateGraph with Conditional Edges for Multi-Agent Routing

**Impact: HIGH (enables deterministic agent hand-off in multi-agent LangGraph applications)**

When building multi-agent systems with LangGraph backed by Cosmos DB checkpointing, use `StateGraph` with `add_conditional_edges` to route between agents based on tool call results or persisted state. Each agent node should return a `Command` that updates state and directs the graph to the next node (e.g., a human-input node). A conditional edge function inspects the state (or Cosmos DB) to determine which agent handles the next turn.

**Incorrect (linear chain — no dynamic routing between agents):**

```python
from langgraph.graph import StateGraph, START, MessagesState

builder = StateGraph(MessagesState)
builder.add_node("agent_a", call_agent_a)
builder.add_node("agent_b", call_agent_b)

# BAD: Fixed linear flow — cannot route dynamically
builder.add_edge(START, "agent_a")
builder.add_edge("agent_a", "agent_b")
builder.add_edge("agent_b", END)
```

**Correct (conditional edges with dynamic routing):**

```python
from typing import Literal
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.types import Command
from langchain_azure_cosmosdb import CosmosDBSaver

async def call_agent_a(state: MessagesState, config) -> Command[Literal["agent_a", "human"]]:
    response = await agent_a.ainvoke(state)
    return Command(update=response, goto="human")

async def call_agent_b(state: MessagesState, config) -> Command[Literal["agent_b", "human"]]:
    response = await agent_b.ainvoke(state)
    return Command(update=response, goto="human")

def route_to_agent(state: MessagesState, config) -> str:
    """Determine which agent handles the next message based on state or DB lookup."""
    # Inspect tool messages for routing hints, or query Cosmos DB for active agent
    # Return the node name to route to
    return "agent_a"  # or "agent_b" based on logic

builder = StateGraph(MessagesState)
builder.add_node("coordinator", call_coordinator)
builder.add_node("agent_a", call_agent_a)
builder.add_node("agent_b", call_agent_b)
builder.add_node("human", human_node)

builder.add_edge(START, "coordinator")
builder.add_conditional_edges(
    "coordinator",
    route_to_agent,
    {"agent_a": "agent_a", "agent_b": "agent_b", "coordinator": "coordinator"}
)

graph = builder.compile(checkpointer=CosmosDBSaver(async_container))
```

**Critical: Only check NEW messages for routing decisions.** When a sub-agent is invoked with `await agent.ainvoke(state)`, the response contains ALL messages — both the existing conversation history AND new messages. If node functions iterate all messages to find routing ToolMessages, they will find old routing messages from previous turns and re-route infinitely, causing a `GraphRecursionError`.

```python
async def call_agent_a(state: MessagesState, config) -> Command[Literal["agent_a", "agent_b", "human"]]:
    response = await agent_a.ainvoke(state)

    # CRITICAL: Only check NEW messages added by this invocation
    existing_count = len(state.get("messages", []))
    new_messages = response.get("messages", [])[existing_count:]

    for msg in reversed(new_messages):
        if isinstance(msg, ToolMessage):
            goto = extract_routing_info(msg)
            if goto:
                return Command(update=response, goto=goto)

    return Command(update=response, goto="human")
```

**Key principles:**
1. Each agent node returns `Command(update=response, goto="human")` to yield control back for user input
2. After user input, the coordinator's conditional edge function decides which agent continues
3. Use Cosmos DB point reads in the routing function for O(1) active-agent lookups
4. Include a fallback route to the coordinator when the active agent is unknown
5. Always slice `response["messages"]` by `len(state["messages"])` to get only new messages — never iterate the full history for routing decisions

Reference: [LangGraph multi-agent patterns](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)

### 4.11 Resume LangGraph from Checkpoint After Interrupt

**Impact: HIGH** (enables multi-turn conversations with persistent state)

## Resume LangGraph from Checkpoint After Interrupt

**Impact: HIGH (enables multi-turn conversations with persistent state)**

When a LangGraph graph pauses at an `interrupt()` node, the next user message must resume from the last checkpoint rather than starting fresh. Retrieve the last checkpoint, append the new user message, inject `langgraph_triggers` to signal which node to resume, and call `ainvoke` with `stream_mode="updates"`. Without proper resume logic, each message starts a new conversation with no memory of prior turns.

**Incorrect (always starts a fresh graph invocation):**

```python
@app.post("/chat/{session_id}")
async def chat(session_id: str, user_message: str):
    config = {"configurable": {"thread_id": session_id}}
    # BAD: Always starts from scratch — ignores prior conversation state
    state = {"messages": [{"role": "user", "content": user_message}]}
    response = await graph.ainvoke(state, config, stream_mode="updates")
    return extract_response(response)
```

**Correct (resume from last checkpoint when one exists):**

```python
@app.post("/chat/{session_id}")
async def chat(session_id: str, user_message: str):
    config = {"configurable": {"thread_id": session_id, "checkpoint_ns": ""}}

    # Check for existing checkpoint (prior conversation state)
    checkpoints = [cp async for cp in checkpointer.alist(config)]

    if not checkpoints:
        # First message — start fresh
        state = {"messages": [{"role": "user", "content": user_message}]}
    else:
        # Resume from last checkpoint
        last_checkpoint = checkpoints[-1]
        state = last_checkpoint.checkpoint

        if "messages" not in state:
            state["messages"] = []
        state["messages"].append({"role": "user", "content": user_message})

        # Signal which node to resume from (required after interrupt)
        # Determine the last active agent from channel_versions or external state
        resume_node = determine_resume_node(state)
        state["langgraph_triggers"] = [f"resume:{resume_node}"]

    response = await graph.ainvoke(state, config, stream_mode="updates")
    return extract_response(response)
```

**Key details:**
1. `stream_mode="updates"` returns per-node state diffs, making it easy to extract only the final agent response
2. `langgraph_triggers` tells the graph which paused node to resume — without it, the graph may restart from START
3. The `checkpoint_ns` must match what was used when the checkpoint was written (typically `""`)
4. Use `checkpointer.alist(config)` to list checkpoints — this is an async generator

Reference: [LangGraph persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)

---

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
