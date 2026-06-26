---
title: Configure local development environment to avoid cloud connection conflicts
impact: MEDIUM
impactDescription: prevents accidental connections to production instead of emulator
tags: sdk, local-development, emulator, configuration, environment-variables
---

## Configure local development environment to avoid cloud connection conflicts

## Configure Local Development Environment Properly

When developing locally with the Cosmos DB Emulator, system-level environment variables pointing to Azure cloud accounts can override your local configuration, causing unexpected connections to production resources instead of the emulator.

**Incorrect:**

```python
# Your .env file (local config)
COSMOS_ENDPOINT=https://localhost:8081
COSMOS_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==

# But system environment has (from Azure CLI or other tools):
# COSMOS_ENDPOINT=https://my-prod-account.documents.azure.com:443/

```

**Correct:**


```python
from dotenv import load_dotenv
import os

# Force .env values to override system environment variables
load_dotenv(override=True)  # ✅ .env values take precedence

# Or use explicit defaults for emulator
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "https://localhost:8081")
```

```javascript
// dotenv also has override option
require('dotenv').config({ override: true });

// Or with explicit defaults
const endpoint = process.env.COSMOS_ENDPOINT || 'https://localhost:8081';
const key = process.env.COSMOS_KEY || 
    'C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==';
```
