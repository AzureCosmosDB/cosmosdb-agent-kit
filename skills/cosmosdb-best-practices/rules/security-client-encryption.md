---
title: Encrypt sensitive fields with Always Encrypted client-side encryption
impact: MEDIUM
impactDescription: sensitive fields stay unreadable to anyone without key access, including operators with full account permissions
tags: security, always-encrypted, client-side-encryption, key-vault, compliance
---

## Encrypt Sensitive Fields with Always Encrypted Client-Side Encryption

**Impact: MEDIUM (sensitive fields stay unreadable to anyone without key access, including operators with full account permissions)**

Cosmos DB encrypts all data at rest by default, but that only protects the storage media. Anyone with account keys, RBAC read access, or portal access still sees documents in plaintext. For regulated data such as PII, health records, or payment details, use Always Encrypted: marked fields are encrypted inside the client SDK before the document leaves your process, and the service only ever stores ciphertext. Decryption requires access to the key in Azure Key Vault, which you control separately from database access.

**When to use it:**

- Compliance requirements like GDPR, HIPAA, or PCI DSS
- Fields such as national IDs, card numbers, salaries, or diagnoses
- Separating duties: database operators can administer data they cannot read

**Limitations to plan around:**

- Encrypted paths are not indexed; randomized encryption cannot be filtered on at all, deterministic encryption supports equality filters only
- The `id` and partition key paths cannot be encrypted
- The encryption policy is set at container creation and cannot be changed later, so decide the paths up front
- Key wrap and unwrap calls add latency on first use per key (cached afterwards)

**Incorrect (plaintext PII, relying on encryption at rest):**

```csharp
// Encryption at rest is always on, but it is transparent: anyone who can
// read the container sees the SSN in plaintext, portal included
var patient = new Patient { Id = "p1", HospitalId = "h1", Ssn = "123-45-6789" };
await container.CreateItemAsync(patient, new PartitionKey(patient.HospitalId));
```

**Correct (client-side encryption backed by Azure Key Vault):**

```csharp
// Package: Microsoft.Azure.Cosmos.Encryption
using Azure.Identity;
using Azure.Security.KeyVault.Keys.Cryptography;
using Microsoft.Azure.Cosmos.Encryption;

var credential = new DefaultAzureCredential();
var client = new CosmosClient(endpoint, credential)
    .WithEncryption(new KeyResolver(credential), KeyEncryptionKeyResolverName.AzureKeyVault);

// One-time setup: a data encryption key, wrapped by a key you own in Key Vault
var database = client.GetDatabase("hospital");
await database.CreateClientEncryptionKeyAsync(
    "patient-cek",
    DataEncryptionAlgorithm.AeadAes256CbcHmacSha256,
    new EncryptionKeyWrapMetadata(
        KeyEncryptionKeyResolverName.AzureKeyVault,
        "cosmos-kek",
        "https://myvault.vault.azure.net/keys/cosmos-kek",
        EncryptionAlgorithm.RsaOaep.ToString()));

// One-time setup: declare which paths are encrypted, and how
var paths = new List<ClientEncryptionIncludedPath>
{
    new ClientEncryptionIncludedPath
    {
        Path = "/ssn",
        ClientEncryptionKeyId = "patient-cek",
        EncryptionType = EncryptionType.Deterministic,  // allows equality filters
        EncryptionAlgorithm = "AEAD_AES_256_CBC_HMAC_SHA256"
    },
    new ClientEncryptionIncludedPath
    {
        Path = "/diagnosis",
        ClientEncryptionKeyId = "patient-cek",
        EncryptionType = EncryptionType.Randomized,  // stronger, never filtered on
        EncryptionAlgorithm = "AEAD_AES_256_CBC_HMAC_SHA256"
    }
};

await database.CreateContainerAsync(new ContainerProperties("patients", "/hospitalId")
{
    ClientEncryptionPolicy = new ClientEncryptionPolicy(paths)
});
```

Reads and writes stay the same; the SDK encrypts and decrypts the declared paths transparently:

```csharp
// Stored as ciphertext, returned decrypted to callers holding key access
await container.CreateItemAsync(patient, new PartitionKey(patient.HospitalId));
```

Querying a deterministically encrypted field requires the parameter to be encrypted too:

```csharp
var query = new QueryDefinition("SELECT * FROM c WHERE c.ssn = @ssn");
await query.AddParameterAsync("@ssn", "123-45-6789", "/ssn");
```

**Choosing an encryption type per field:**

- Deterministic: the same plaintext always produces the same ciphertext, so equality lookups work. Use for fields you must search by, like an SSN.
- Randomized: stronger protection, no querying at all. Use for fields you only read back, like a diagnosis or card number.
- No encryption: anything you index, sort, aggregate, or use as a partition key.

**How this differs from encryption at rest:**

- Encryption at rest is always on, managed by the service, and protects disks and backups. It does nothing against a leaked key or an over-permissioned reader, because data is decrypted for every authorized request.
- Always Encrypted is opt-in per field, the keys live in your Key Vault, and ciphertext is all the service ever holds. Revoking key access makes the fields unreadable even for the account owner.

Reference: [Use client-side encryption with Always Encrypted for Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-always-encrypted)
