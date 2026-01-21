# 1. Data Modeling (model)

**Impact:** CRITICAL  
**Description:** Proper data modeling is foundational to Cosmos DB performance. Poor modeling leads to expensive queries, excessive RU consumption, and scalability issues that are difficult to fix later.

## 2. Partition Key Design (partition)

**Impact:** CRITICAL  
**Description:** Partition key choice determines data distribution, query efficiency, and scalability limits. A bad partition key creates hot partitions and cross-partition query overhead.

## 3. Query Optimization (query)

**Impact:** HIGH  
**Description:** Optimized queries minimize RU consumption and latency. Inefficient queries cause unnecessary cross-partition scans and index misses.

## 4. SDK Best Practices (sdk)

**Impact:** HIGH  
**Description:** Proper SDK usage ensures connection efficiency, retry handling, and optimal throughput. Common mistakes include creating multiple clients and ignoring throttling.

## 5. Indexing Strategies (index)

**Impact:** MEDIUM-HIGH  
**Description:** Strategic indexing reduces query costs while minimizing write overhead. Default indexing often includes unused paths.

## 6. Throughput & Scaling (throughput)

**Impact:** MEDIUM  
**Description:** Right-sizing throughput balances cost and performance. Over-provisioning wastes money; under-provisioning causes throttling.

## 7. Global Distribution (global)

**Impact:** MEDIUM  
**Description:** Multi-region configuration enables low-latency reads globally and disaster recovery. Consistency choices impact both.

## 8. Monitoring & Diagnostics (monitoring)

**Impact:** LOW-MEDIUM  
**Description:** Proactive monitoring catches issues before they impact users. Diagnostics enable root cause analysis.
