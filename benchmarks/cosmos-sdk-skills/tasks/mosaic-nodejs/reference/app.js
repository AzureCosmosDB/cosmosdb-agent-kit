import express from "express";
import { CosmosClient } from "@azure/cosmos";

// --- Config (env-driven, no hardcoded literals) ---
const endpoint = process.env.COSMOS_ENDPOINT;
const key = process.env.COSMOS_KEY;
const dbName = process.env.COSMOS_DATABASE || "mosaic";
const containerName = process.env.COSMOS_USERS_CONTAINER || "users";
const port = parseInt(process.env.APP_PORT || "8080", 10);
const preferredLocations = (process.env.COSMOS_PREFERRED_REGIONS || "West US 2,East US 2")
    .split(",").map(s => s.trim()).filter(Boolean);

if (!endpoint || !key) {
    console.error("COSMOS_ENDPOINT and COSMOS_KEY must be set");
    process.exit(1);
}

// Singleton CosmosClient (rule sdk-singleton-client). One construction
// for the lifetime of the process.
const client = new CosmosClient({
    endpoint,
    key,
    connectionPolicy: {
        // Rule sdk-preferred-regions
        preferredLocations,
        // Rule sdk-retry-throttled
        retryOptions: {
            maxRetryAttemptCount: 9,
            maxWaitTimeInSeconds: 30,
            fixedRetryIntervalInMilliseconds: 0,
        },
    },
    // Rule sdk-diagnostics: tagging requests with a user-agent suffix
    // surfaces this app in Cosmos server-side metrics.
    userAgentSuffix: "mosaic-users",
});

// Provision database + container.
const { database } = await client.databases.createIfNotExists({
    id: dbName,
    throughput: 400,
});

const { container } = await database.containers.createIfNotExists({
    id: containerName,
    partitionKey: { paths: ["/userId"] },
    indexingPolicy: {
        indexingMode: "consistent",
        automatic: true,
        includedPaths: [{ path: "/*" }],
        excludedPaths: [
            { path: "/\"_etag\"/?" },
            { path: "/email/?" },
            { path: "/interests/*" },
        ],
        compositeIndexes: [[
            { path: "/city", order: "ascending" },
            { path: "/id",   order: "ascending" },
        ]],
    },
});

// --- HTTP ---

const app = express();
app.use(express.json());

app.get("/health", (_req, res) => res.status(200).json({ status: "ok" }));

app.post("/users", async (req, res) => {
    const { id, name, email, city, interests } = req.body || {};
    if (!id || !name || !email || !city || !Array.isArray(interests)) {
        return res.status(400).json({ error: "id, name, email, city, interests required" });
    }
    const doc = {
        id,
        userId: id,
        name,
        email,
        city,
        interests: [...interests],
        createdAt: new Date().toISOString(),
        type: "user",
        schemaVersion: 1,
    };
    try {
        const { resource } = await container.items.create(doc);
        return res.status(201).json(resource);
    } catch (e) {
        if (e.code === 409) return res.status(409).json({ error: `user ${id} already exists` });
        console.error("cosmos create failed", e);
        return res.status(500).json({ error: String(e) });
    }
});

app.get("/users/:id", async (req, res) => {
    const id = req.params.id;
    try {
        const { resource } = await container.item(id, id).read();
        if (!resource) return res.status(404).json({ error: `user ${id} not found` });
        return res.status(200).json(resource);
    } catch (e) {
        if (e.code === 404) return res.status(404).json({ error: `user ${id} not found` });
        throw e;
    }
});

app.get("/users", async (req, res) => {
    const city = req.query.city;
    if (!city) return res.status(400).json({ error: "city query param required" });
    const { resources } = await container.items.query({
        query: "SELECT * FROM c WHERE c.city = @city",
        parameters: [{ name: "@city", value: city }],
    }).fetchAll();
    return res.status(200).json(resources);
});

app.listen(port, "0.0.0.0", () => {
    console.log(`mosaic-users listening on http://0.0.0.0:${port}`);
});
