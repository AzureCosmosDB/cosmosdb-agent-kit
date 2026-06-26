---
title: Normalize Embeddings for Cosine Similarity
impact: MEDIUM
impactDescription: Ensures accurate similarity scores and consistent test results
tags: vector, embeddings, normalization, testing, cosine
---

## Normalize Embeddings for Cosine Similarity

When using cosine distance, normalize embeddings to unit length (L2 norm = 1). Cosine similarity measures angle, not magnitude — unnormalized vectors produce inconsistent scores.

**Incorrect (unnormalized mock embeddings):**

```python
import random
def generate_mock_embedding(dimensions=1536):
    return [random.uniform(-1, 1) for _ in range(dimensions)]
    # Magnitude varies — cosine scores inconsistent
```

**Correct (normalized to unit length):**


```python
import numpy as np

def generate_mock_embedding(text: str, dimensions: int = 1536) -> list:
    """Normalized mock embedding. Uses text hash as seed for reproducibility."""
    seed = hash(text) % (2**32)
    np.random.seed(seed)
```

```csharp
public static float[] GenerateMockEmbedding(string text, int dimensions = 1536)
{
    var random = new Random(Math.Abs(text.GetHashCode()));
    var vector = new float[dimensions];
    for (int i = 0; i < dimensions; i++)
    {
```
