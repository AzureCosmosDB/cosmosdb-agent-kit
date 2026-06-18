# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Security best practices for Azure Cosmos DB: disabling local authentication, managed identity with DefaultAzureCredential, network access restrictions, RBAC least privilege, and continuous backup.

---

## Table of Contents

1. [Security](#1-security) — **HIGH**
   - 1.1 [Enable Continuous Backup for Point-in-Time Restore](#11-enable-continuous-backup-for-point-in-time-restore)
   - 1.2 [Disable Local Authentication (Keys)](#12-disable-local-authentication-keys-)
   - 1.3 [Use Managed Identity with DefaultAzureCredential](#13-use-managed-identity-with-defaultazurecredential)
   - 1.4 [Restrict Network Access](#14-restrict-network-access)
   - 1.5 [Assign Minimum RBAC Roles with Narrow Scope](#15-assign-minimum-rbac-roles-with-narrow-scope)

---

## 1. Security

**Impact: HIGH**

### 1.1 Enable Continuous Backup for Point-in-Time Restore

**Impact: MEDIUM** (enables recovery from accidental data loss)

## Enable Continuous Backup for Point-in-Time Restore

**Impact: MEDIUM (enables recovery from accidental data loss)**

Data loss is more often caused by mistakes than by attackers. Enable continuous backup (7 or 30 days) to allow point-in-time restore. Enable it at account creation if possible — switching from periodic to continuous is supported but is a one-way change.

**Incorrect (relying on default periodic backup):**

```bash
# Default periodic backup:
# - 4 hour intervals between backups
# - Only 2 copies retained
# - Recovery requires a support ticket
# - Cannot restore to a specific point in time
# - Data written between backups can be lost permanently

az cosmosdb create \
  --name myaccount \
  --resource-group myrg
  # Default periodic backup — limited recovery options
```

**Correct (continuous backup enabled):**

```bash
# Enable at account creation (preferred)
az cosmosdb create \
  --name myaccount \
  --resource-group myrg \
  --backup-policy-type Continuous \
  --continuous-tier Continuous7Days

# Or upgrade an existing account (one-way change)
az cosmosdb update \
  --name myaccount \
  --resource-group myrg \
  --backup-policy-type Continuous \
  --continuous-tier Continuous7Days

# Tiers available:
# Continuous7Days  — 7-day retention, lower cost
# Continuous30Days — 30-day retention, for compliance-sensitive workloads
```

```bash
# Restore to a specific point in time (self-service, no support ticket)
az cosmosdb restore \
  --account-name myaccount \
  --resource-group myrg \
  --target-database-account-name myaccount-restored \
  --restore-timestamp "2026-05-29T10:00:00Z" \
  --location "East US"
```

Continuous backup protects against:
- Accidental deletion of containers or databases
- Buggy deployments that corrupt data
- Unintended bulk updates or deletes
- Ransomware or malicious data modification (when combined with audit logs to identify the point of compromise)

Reference: [Continuous backup with point-in-time restore in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/continuous-backup-restore-introduction)

### 1.2 Disable Local Authentication (Keys)

**Impact: CRITICAL** (eliminates credential leakage risk)

## Disable Local Authentication (Keys)

**Impact: CRITICAL (eliminates credential leakage risk)**

Disable local authentication (shared keys and connection strings) on your Cosmos DB account. Keys are bearer tokens — anyone who has one can read, modify, or delete all data. If a key leaks, the only option is to regenerate it and update every dependent system. Disabling keys forces all access through Entra ID, eliminating this entire class of risk.

**Incorrect (using connection string with keys):**

```csharp
// WRONG: Connection string contains a master key
// If this leaks via source control, logs, or config, all data is exposed
var connectionString = "AccountEndpoint=https://myaccount.documents.azure.com:443/;AccountKey=abc123...==;";
var client = new CosmosClient(connectionString);

// Risks:
// - Key in source control (even in .env files that get committed)
// - Key in CI/CD logs or screenshots
// - Key shared across teams with no audit trail
// - No way to attribute access to a specific identity
// - Rotation requires updating every system simultaneously
```

**Correct (disable keys, use Entra ID exclusively):**

```bash
# Disable local authentication on the account
az cosmosdb update \
  --name <your-account> \
  --resource-group <your-rg> \
  --disable-local-auth true
```

```csharp
// Connect using Entra ID — no keys or connection strings needed
using Azure.Identity;
using Microsoft.Azure.Cosmos;

var client = new CosmosClient(
    accountEndpoint: "https://myaccount.documents.azure.com:443/",
    tokenCredential: new DefaultAzureCredential()
);

// Benefits:
// - No secrets to leak
// - Access is auditable per identity
// - Revocation is instant and targeted
// - Works in dev (az login), Azure (managed identity), and CI/CD (service principal)
```

If you cannot disable keys immediately, at minimum: never store connection strings in source control, use Azure Key Vault for secret storage, and enable secret scanning in your repository.

Reference: [Disable local authentication in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/how-to-setup-rbac#disable-local-auth)

### 1.3 Use Managed Identity with DefaultAzureCredential

**Impact: CRITICAL** (zero-secret authentication for all environments)

## Use Managed Identity with DefaultAzureCredential

**Impact: CRITICAL (zero-secret authentication for all environments)**

Authenticate to Cosmos DB using managed identity and `DefaultAzureCredential`. This provides a single code path that works in local development (via `az login`), Azure compute (via system-assigned managed identity), and CI/CD (via service principal or federated identity) — with no secrets in code or configuration.

**Incorrect (hard-coded keys or environment-specific auth):**

```csharp
// WRONG: Key stored in configuration
var client = new CosmosClient(
    "https://myaccount.documents.azure.com:443/",
    "abc123masterkey=="
);

// WRONG: Connection string in environment variable still contains a secret
var connectionString = Environment.GetEnvironmentVariable("COSMOS_CONNECTION_STRING");
var client = new CosmosClient(connectionString);

// WRONG: Different auth code per environment
if (isDevelopment)
    client = new CosmosClient(connectionString);  // key-based
else
    client = new CosmosClient(endpoint, new ManagedIdentityCredential());  // identity
```

**Correct (DefaultAzureCredential everywhere):**

```csharp
using Azure.Identity;
using Microsoft.Azure.Cosmos;

// Same code works in all environments:
// - Local dev: uses az login / Visual Studio / VS Code credentials
// - Azure (App Service, Functions, Container Apps, AKS): uses managed identity
// - CI/CD: uses service principal or workload identity federation
var client = new CosmosClient(
    accountEndpoint: "https://myaccount.documents.azure.com:443/",
    tokenCredential: new DefaultAzureCredential()
);
```

```python
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient

credential = DefaultAzureCredential()
client = CosmosClient("https://myaccount.documents.azure.com:443/", credential)
```

```javascript
const { DefaultAzureCredential } = require("@azure/identity");
const { CosmosClient } = require("@azure/cosmos");

const credential = new DefaultAzureCredential();
const client = new CosmosClient({
    endpoint: "https://myaccount.documents.azure.com:443/",
    aadCredentials: credential
});
```

```java
import com.azure.identity.DefaultAzureCredentialBuilder;
import com.azure.cosmos.CosmosClientBuilder;

CosmosClient client = new CosmosClientBuilder()
    .endpoint("https://myaccount.documents.azure.com:443/")
    .credential(new DefaultAzureCredentialBuilder().build())
    .buildClient();
```

For Azure compute, assign a system-assigned managed identity:

```bash
# App Service
az webapp identity assign --name <your-app> --resource-group <your-rg>

# Azure Functions
az functionapp identity assign --name <your-app> --resource-group <your-rg>

# Container Apps
az containerapp identity assign --name <your-app> --resource-group <your-rg> --system-assigned
```

Starting with `DefaultAzureCredential` from day one avoids a painful migration later — moving from keys to managed identity means touching every deployment, every environment, and potentially every SDK call.

Reference: [DefaultAzureCredential Class](https://learn.microsoft.com/dotnet/api/azure.identity.defaultazurecredential)

### 1.4 Restrict Network Access

**Impact: HIGH** (reduces attack surface from public internet)

## Restrict Network Access

**Impact: HIGH (reduces attack surface from public internet)**

By default, a Cosmos DB endpoint is publicly reachable from anywhere on the internet. If a credential leaks, nothing stands between an attacker and your data. Restrict access to known IP ranges as a baseline, and plan to move to private endpoints for production workloads.

**Incorrect (unrestricted public access):**

```bash
# WRONG: Default configuration — account is accessible from any IP address worldwide
# No --ip-range-filter means open to the internet

az cosmosdb create \
  --name myaccount \
  --resource-group myrg
  # No network restrictions = reachable from anywhere
```

**Correct (restrict to known IPs as baseline):**

```bash
# Restrict access to known IP addresses (office, CI/CD egress, developer IPs)
az cosmosdb update \
  --name myaccount \
  --resource-group myrg \
  --ip-range-filter "203.0.113.10,198.51.100.0/24"

# For production: use private endpoints (no public internet exposure)
az cosmosdb update \
  --name myaccount \
  --resource-group myrg \
  --public-network-access DISABLED

# Create a private endpoint in your VNet
az network private-endpoint create \
  --name myaccount-pe \
  --resource-group myrg \
  --vnet-name myvnet \
  --subnet default \
  --private-connection-resource-id <cosmos-account-resource-id> \
  --group-id Sql \
  --connection-name myaccount-connection
```

Network restriction tiers (from minimum to most secure):
1. **IP allowlisting** (day one minimum): restrict to office, CI/CD, and developer IPs
2. **Service endpoints**: allow access from specific Azure VNet subnets
3. **Private endpoints** (production goal): no public exposure, traffic stays on Microsoft backbone

Even with Entra ID authentication, network restrictions add defense-in-depth — a compromised token is useless if the attacker cannot reach the endpoint.

Reference: [Configure IP firewall in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/how-to-configure-firewall)

### 1.5 Assign Minimum RBAC Roles with Narrow Scope

**Impact: HIGH** (limits blast radius of compromised identities)

## Assign Minimum RBAC Roles with Narrow Scope

**Impact: HIGH (limits blast radius of compromised identities)**

Grant each identity only the Cosmos DB data plane role it needs, scoped to the narrowest resource level possible. Avoid account-wide contributor access when an app only reads from a single container. Separate data plane access (read/write data) from control plane access (manage account settings).

**Incorrect (over-privileged access):**

```bash
# WRONG: Granting full Contributor at account scope to an app that only reads data
az cosmosdb sql role assignment create \
  --account-name myaccount \
  --resource-group myrg \
  --role-definition-id "00000000-0000-0000-0000-000000000002" \
  --principal-id <app-principal-id> \
  --scope "/"

# WRONG: Giving the app control plane access (can delete containers, change settings)
az role assignment create \
  --role "Contributor" \
  --assignee <app-principal-id> \
  --scope "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.DocumentDB/databaseAccounts/myaccount"

# WRONG: Sharing one identity across multiple services
# If one service is compromised, attacker gets access to everything
```

**Correct (least privilege, narrowly scoped):**

```bash
# Built-in data plane roles:
# Cosmos DB Built-in Data Reader:      00000000-0000-0000-0000-000000000001
# Cosmos DB Built-in Data Contributor: 00000000-0000-0000-0000-000000000002

# Read-only app: grant Reader scoped to specific container
az cosmosdb sql role assignment create \
  --account-name myaccount \
  --resource-group myrg \
  --role-definition-id "00000000-0000-0000-0000-000000000001" \
  --principal-id <reader-app-principal-id> \
  --scope "/dbs/mydb/colls/products"

# Read-write app: grant Contributor scoped to specific database
az cosmosdb sql role assignment create \
  --account-name myaccount \
  --resource-group myrg \
  --role-definition-id "00000000-0000-0000-0000-000000000002" \
  --principal-id <writer-app-principal-id> \
  --scope "/dbs/mydb"

# CI/CD pipeline: only data plane write for schema migrations
az cosmosdb sql role assignment create \
  --account-name myaccount \
  --resource-group myrg \
  --role-definition-id "00000000-0000-0000-0000-000000000002" \
  --principal-id <cicd-principal-id> \
  --scope "/dbs/mydb"
```

Guidelines for role assignment:
- **Application**: Data plane only, minimum role (Reader vs Contributor), scoped to its database or container
- **Developers**: Data plane access on dev accounts, scoped narrowly, using their own Entra ID identity
- **CI/CD pipeline**: Only permissions required to deploy — often just data plane write, sometimes control plane for container management
- **Each identity gets its own access** — never share a single credential across users, environments, or systems

Reference: [Use data plane role-based access control with Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/security/how-to-grant-data-plane-role-based-access)

---

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
