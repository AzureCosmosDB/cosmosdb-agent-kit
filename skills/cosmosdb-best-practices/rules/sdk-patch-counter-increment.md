---
title: Use the Patch API for atomic counter increments
impact: HIGH
impactDescription: eliminates read-modify-write for counters; reduces RU cost and eliminates concurrency conflicts
tags:
  - sdk
  - patch
  - java
  - counter
  - atomic
  - ru-cost
---

## Use the Patch API for atomic counter increments

**Impact: HIGH (eliminates read-modify-write for counters; reduces RU cost and eliminates concurrency conflicts)**

For fields that act as counters (view counts, rating totals, like counts), `patchItem` with `CosmosPatchOperations.incr()` performs a server-side atomic increment without a prior read. This is cheaper (no read RU), faster, and free of the ETag conflict/retry cycle.

**Incorrect (read-modify-write for counters):**

```java
// ❌ Read-modify-write: 1 read RU + 1 write RU, subject to ETag conflicts at scale
CosmosItemResponse<Video> resp = container.readItem(videoId,
    new PartitionKey(videoId), Video.class).block();
Video video = resp.getItem();
video.setViews(video.getViews() + 1);
container.upsertItem(video, new PartitionKey(videoId), null).block();
```

**Correct (Patch API — server-side atomic increment):**


```java
// ✅ Atomic increment — no read required, no ETag conflict possible
CosmosPatchOperations ops = CosmosPatchOperations.create()
    .increment("/views", 1);      // Atomic add, server-side

container.patchItem(
    videoId,
```

```java
// ✅ Patch multiple counters in one round-trip (e.g., rate-video: two fields)
CosmosPatchOperations ratingOps = CosmosPatchOperations.create()
    .increment("/ratingsCount", 1)
    .increment("/ratingsTotal", ratingValue);

videosContainer.patchItem(
```
