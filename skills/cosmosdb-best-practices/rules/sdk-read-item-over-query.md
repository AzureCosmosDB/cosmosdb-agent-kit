---
title: Prefer ReadItem (point read) over query for single-document lookup
impact: HIGH
impactDescription: 1 RU vs ~3+ RU per single-document lookup
tags: query, point-read, ReadItem, performance, optimization
---

## Prefer ReadItem (point read) over query for single-document lookup

**Impact: HIGH (reduces RU consumption and improves performance for single-document reads)**

When both the document `id` and partition key value are known, prefer **ReadItem (point read)** instead of querying using:

```sql
SELECT * FROM c WHERE c.id = @id
```

A point read consumes approximately **1 RU** for a 1 KB document and bypasses the query engine entirely. An equivalent query typically consumes **3+ RUs** because Cosmos DB must still parse, optimize, and execute the query.

---

### RU cost comparison

| Operation | Example | Typical RU Cost |
|------------|---------|----------------|
| Point Read | `ReadItemAsync(id, partitionKey)` | ~1 RU |
| Query | `SELECT * FROM c WHERE c.id = @id` | ~3+ RU |

Point reads bypass the query engine and are the most efficient way to retrieve a single document when both the `id` and partition key are known.

---

### .NET / C#

**Incorrect (query when both id and partition key are known):**

```csharp
var querySpec = new QueryDefinition(
    "SELECT * FROM c WHERE c.id = @id")
    .WithParameter("@id", myId);

var iterator = container.GetItemQueryIterator<MyItem>(
    querySpec,
    requestOptions: new QueryRequestOptions
    {
        PartitionKey = new PartitionKey(partitionKeyValue)
    });

while (iterator.HasMoreResults)
{
    foreach (var item in await iterator.ReadNextAsync())
    {
        Console.WriteLine(item.Id);
    }
}
```

**Correct (point read using ReadItemAsync):**

```csharp
var response = await container.ReadItemAsync<MyItem>(
    myId,
    new PartitionKey(partitionKeyValue));

Console.WriteLine(response.Resource.Id);
```

---

### Java

**Incorrect (query when both id and partition key are known):**

```java
String query = "SELECT * FROM c WHERE c.id = @id";
SqlParameter param = new SqlParameter("@id", myId);
SqlQuerySpec querySpec = new SqlQuerySpec(query, Arrays.asList(param));

CosmosPagedIterable<MyItem> items = container.queryItems(
    querySpec, new CosmosQueryRequestOptions().setPartitionKey(new PartitionKey(partitionKeyValue)),
    MyItem.class);

for (MyItem item : items) {
    System.out.println(item.getId());
}
```

**Correct (point read using readItem):**

```java
CosmosItemResponse<MyItem> response = container.readItem(
    myId, new PartitionKey(partitionKeyValue), MyItem.class);
System.out.println(response.getItem().getId());
```

---

### Python

**Incorrect (query when both id and partition key are known):**

```python
query = "SELECT * FROM c WHERE c.id=@id"
parameters = [{"name": "@id", "value": my_id}]
items = container.query_items(
    query=query,
    parameters=parameters,
    partition_key=partition_key_value
)

for item in items:
    print(item["id"])
```

**Correct (point read using read_item):**

```python
response = container.read_item(item=my_id, partition_key=partition_key_value)
print(response["id"])
```

---

### Node.js

**Incorrect (query when both id and partition key are known):**

```javascript
const querySpec = {
    query: "SELECT * FROM c WHERE c.id = @id",
    parameters: [{ name: "@id", value: myId }]
};

const { resources: items } = await container.items.query(querySpec, { partitionKey: partitionKeyValue }).fetchAll();
items.forEach(item => console.log(item.id));
```

**Correct (point read using readItem):**

```javascript
const { resource: item } = await container.item(myId, partitionKeyValue).read();
console.log(item.id);
```

---

### Additional considerations

- Use point reads whenever both the `id` and partition key are known.
- Point reads consume fewer RUs and have lower latency than queries.
- Queries should be reserved for cases where the document identity is not fully known.
- Applies across all SDKs (.NET, Java, Python, Node.js).

Reference: [Read items in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-read-item)
