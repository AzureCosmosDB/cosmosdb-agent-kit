---
title: Follow ID Value Length and Character Constraints
impact: HIGH
impactDescription: prevents write failures, 401 auth errors, and cross-SDK interoperability issues
tags: model, id, limits, interoperability, design, auth, url-reserved
---

## Follow ID Value Length and Character Constraints

Max `id` length: 1,023 bytes. URL-reserved characters in `id` cause 401 auth errors or 404 routing failures on read/update/delete (not create — the bug hides until first read).

**Incorrect (problematic IDs):**

```python
# ❌ '#' causes 401 on read/update/delete (HTTP fragment delimiter)
doc_id = f"best#{player_id}#{week}#{region}"
await container.upsert_item(body={"id": doc_id, ...})    # succeeds
await container.read_item(item=doc_id, partition_key=pk)  # 💥 401
```

**Correct (safe, bounded IDs):**


```python
# ✅ Use ':' or '_' or '-' as separators
doc_id = f"best:{player_id}:{week}:{region}"
await container.read_item(item=doc_id, partition_key=pk)  # ✅ 200 OK
```

```csharp
// ✅ GUID or bounded deterministic ID
Id = Guid.NewGuid().ToString();
Id = $"report-{tenantId}-{DateTime.UtcNow:yyyyMMdd}-{seq}";
// ✅ Base64 for non-ASCII sources
Id = Convert.ToBase64String(Encoding.UTF8.GetBytes(rawId)).Replace('/', '_').Replace('+', '-');
```
