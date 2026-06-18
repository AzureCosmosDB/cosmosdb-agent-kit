---
name: cosmosdb-security
description: |
  Azure Cosmos DB security best practices: disabling local authentication (keys),
  managed identity with DefaultAzureCredential, network access restrictions,
  RBAC least privilege, and continuous backup for point-in-time restore.
  USE FOR: Cosmos DB security, disable local auth, disable keys, managed identity,
  DefaultAzureCredential, Entra ID, network restrictions, IP firewall,
  private endpoints, RBAC roles, least privilege, data plane roles,
  continuous backup, point-in-time restore, PITR, zero-trust.
  DO NOT USE FOR: client-side encryption (pending), SDK authentication code (use cosmosdb-sdk).

license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.0.0"
---

# Azure Cosmos DB Security

Security best practices for Azure Cosmos DB accounts, covering authentication, network isolation, access control, and data protection.

## When to Apply

Reference these guidelines when:
- Setting up authentication for Cosmos DB
- Configuring network access restrictions
- Assigning RBAC roles for data plane access
- Enabling continuous backup
- Hardening a Cosmos DB account for production

## Rules

- [security-disable-local-auth](rules/security-disable-local-auth.md) - Disable local authentication (keys)
- [security-managed-identity](rules/security-managed-identity.md) - Use managed identity with DefaultAzureCredential
- [security-network-restrict](rules/security-network-restrict.md) - Restrict network access
- [security-rbac-least-privilege](rules/security-rbac-least-privilege.md) - Assign minimum RBAC roles
- [security-continuous-backup](rules/security-continuous-backup.md) - Enable continuous backup for PITR

## Full Compiled Document

For all rules expanded: [AGENTS.md](AGENTS.md)
