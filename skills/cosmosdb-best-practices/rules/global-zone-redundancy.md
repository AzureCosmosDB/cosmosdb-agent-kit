---
title: Configure Zone Redundancy for High Availability
impact: HIGH
impactDescription: eliminates availability zone failures, increases SLA to 99.995%
tags: global, zone-redundancy, high-availability, availability-zones, resilience, sla
---

## Configure Zone Redundancy for High Availability

Enable zone redundancy to protect against availability zone failures. Zone-redundant accounts distribute replicas across multiple availability zones within a region.

**Incorrect (no zone redundancy):**

```json
// Single-region account without zone redundancy
// If an availability zone fails:
{
    "type": "Microsoft.DocumentDB/databaseAccounts",
    "properties": {
        "locations": [
```

**Correct (zone redundancy enabled):**


```json
// ARM template with zone redundancy
{
    "type": "Microsoft.DocumentDB/databaseAccounts",
    "apiVersion": "2023-04-15",
    "name": "my-cosmos-account",
    "properties": {
```

```bicep
// Bicep template with zone redundancy
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: 'my-cosmos-account'
  location: 'East US'
  properties: {
    locations: [
```
