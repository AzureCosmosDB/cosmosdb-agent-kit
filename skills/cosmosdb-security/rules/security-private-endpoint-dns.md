---
title: Configure Private Endpoints with Correct DNS Resolution
impact: HIGH
impactDescription: prevents connection failures and portal access issues
tags: connectivity, private-endpoint, dns, vnet, security, portal
---

Private endpoints route Cosmos DB traffic through your VNet instead of the public internet, but they require correct DNS configuration to work. The most common connectivity failures after enabling private endpoints are DNS misconfigurations, VNet peering without private DNS integration, and portal access blocked by browser Private Network Access (PNA) policies.

### Common Issue: DNS Not Resolving to Private IP

**Incorrect (private endpoint created but DNS still resolves to public IP):**

```bash
# WRONG: Private endpoint created without private DNS zone integration
az network private-endpoint create \
  --name myaccount-pe \
  --resource-group myrg \
  --vnet-name myvnet \
  --subnet default \
  --private-connection-resource-id <cosmos-resource-id> \
  --group-id Sql \
  --connection-name myaccount-connection
  # Missing: DNS zone integration

# Result: myaccount.documents.azure.com still resolves to public IP (104.x.x.x)
# Applications fail with connection timeout or "unable to reach" errors
```

**Correct (private endpoint with automatic DNS integration):**

```bash
# Create private DNS zone for Cosmos DB
az network private-dns zone create \
  --resource-group myrg \
  --name privatelink.documents.azure.com

# Link DNS zone to your VNet
az network private-dns link vnet create \
  --resource-group myrg \
  --zone-name privatelink.documents.azure.com \
  --name myaccount-dnslink \
  --virtual-network myvnet \
  --registration-enabled false

# Create private endpoint WITH DNS integration
az network private-endpoint create \
  --name myaccount-pe \
  --resource-group myrg \
  --vnet-name myvnet \
  --subnet default \
  --private-connection-resource-id <cosmos-resource-id> \
  --group-id Sql \
  --connection-name myaccount-connection

# Associate the private endpoint with the Private DNS zone (DNS zone group)
az network private-endpoint dns-zone-group create \
  --resource-group myrg \
  --endpoint-name myaccount-pe \
  --name myaccount-zonegroup \
  --private-dns-zone /subscriptions/<sub>/resourceGroups/myrg/providers/Microsoft.Network/privateDnsZones/privatelink.documents.azure.com

# Verify DNS resolution from a VM in the VNet:
# nslookup myaccount.documents.azure.com
# Should return private IP (10.x.x.x), not public (104.x.x.x)
```

### Customer-Managed DNS Configuration

If your organization uses custom DNS servers (not Azure-provided DNS), you must configure DNS forwarding:

```bash
# Your custom DNS servers must forward *.privatelink.documents.azure.com queries
# to Azure DNS (168.63.129.16)

# Option 1: Conditional forwarder on your DNS servers
# Forward privatelink.documents.azure.com → 168.63.129.16

# Option 2: DNS A records (manual approach, not recommended)
# Create A record: myaccount.privatelink.documents.azure.com → <private-endpoint-ip>
# Must update manually if private endpoint IP changes
```

**Verify DNS resolution from your application host:**

```bash
# Windows
nslookup myaccount.documents.azure.com

# Linux
dig myaccount.documents.azure.com

# Expected: 
# - Public DNS disabled: resolves to private IP (10.x.x.x)
# - Public DNS enabled: may resolve to public IP (applications must reach via private route)
```

### VNet Peering and Hub-Spoke Topologies

Private endpoint DNS integration is **per-VNet**. If you have hub-spoke or peered VNets:

```bash
# Scenario: Private endpoint in Hub VNet, applications in Spoke VNets

# Link the private DNS zone to ALL VNets that need access
az network private-dns link vnet create \
  --resource-group myrg \
  --zone-name privatelink.documents.azure.com \
  --name spoke1-dnslink \
  --virtual-network spoke1-vnet \
  --registration-enabled false

az network private-dns link vnet create \
  --resource-group myrg \
  --zone-name privatelink.documents.azure.com \
  --name spoke2-dnslink \
  --virtual-network spoke2-vnet \
  --registration-enabled false

# VNet peering must allow forwarded traffic:
az network vnet peering update \
  --name hub-to-spoke1 \
  --resource-group myrg \
  --vnet-name hub-vnet \
  --allow-forwarded-traffic true
```

### Portal and Data Explorer Access with Private Endpoints

When you **disable public network access** and use only private endpoints, the Azure Portal and Data Explorer cannot reach your account from your browser (they run client-side, outside your VNet).

**Symptoms:**
- Portal shows "Unable to load containers" or "Connection timeout"
- Data Explorer queries fail with network errors
- Chromium browsers block with **Private Network Access (PNA)** CORS errors

**Solutions:**

```bash
# Option 1: Allow Azure portal access exception
# Keeps private endpoint but allows portal IP ranges
az cosmosdb update \
  --name myaccount \
  --resource-group myrg \
  --public-network-access ENABLED \
  --ip-range-filter "0.0.0.0"  # Special value: allows Azure Portal only

# Option 2: Use Azure CLI or SDK from within VNet
# From a VM, Azure Cloud Shell, or developer workstation connected to VNet via VPN/Bastion
az cosmosdb sql database list --account-name myaccount --resource-group myrg

# Option 3: VS Code with Remote extension
# Connect to a VM in the VNet via Remote-SSH or Bastion
# Use Cosmos DB extension from within the VNet
```

**Chromium Private Network Access (PNA) blocking:**
- Affects Chrome, Edge, Brave when portal tries to access private endpoint from public internet
- Browser blocks "public-to-private" requests as a security policy
- Solution: use portal exception (Option 1) or CLI/SDK from within VNet (Option 2/3)

### Disable Public Access (Production Best Practice)

After private endpoint and DNS are working:

```bash
# Fully disable public internet access
az cosmosdb update \
  --name myaccount \
  --resource-group myrg \
  --public-network-access DISABLED

# All traffic must flow through private endpoints
# Portal access will require Option 2 or 3 above
```

### Troubleshooting Checklist

| Symptom | Likely Cause | Solution |
|---|---|---|
| Connection timeout from application | DNS not configured | Link private DNS zone to VNet |
| Resolves to public IP (104.x.x.x) | Missing DNS integration | Re-create private endpoint with DNS zone |
| Works from one VNet, not another | DNS zone not linked to spoke | Link DNS zone to all peered VNets |
| Portal shows "Unable to load" | Public access disabled | Enable portal exception or use CLI from VNet |
| Chromium PNA CORS error | Browser blocks public→private | Use portal exception or access from VNet |
| Custom DNS servers: no resolution | DNS not forwarding to Azure | Configure conditional forwarder to 168.63.129.16 |

### Connection String Unchanged

**Important:** Your connection string does NOT change when using private endpoints. Applications still use `myaccount.documents.azure.com` — DNS resolution handles routing to the private IP.

```csharp
// Same connection string before and after private endpoint
var client = new CosmosClient(
    "https://myaccount.documents.azure.com:443/",
    tokenCredential: new DefaultAzureCredential()
);
// DNS automatically resolves to private IP when query originates from VNet
```

References:
- [Configure private endpoints for Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/how-to-configure-private-endpoints)
- [Azure Private Endpoint DNS configuration](https://learn.microsoft.com/azure/private-link/private-endpoint-dns)
- [Troubleshoot Azure Private Endpoint connectivity](https://learn.microsoft.com/azure/private-link/troubleshoot-private-endpoint-connectivity)