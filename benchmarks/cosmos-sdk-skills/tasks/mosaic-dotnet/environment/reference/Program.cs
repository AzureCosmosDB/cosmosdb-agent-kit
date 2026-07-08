using System.Net;
using System.Text.Json.Serialization;
using Microsoft.Azure.Cosmos;
using Microsoft.AspNetCore.Mvc;

var builder = WebApplication.CreateBuilder(args);

// Configuration: env vars take precedence; appsettings.json could also be used.
var endpoint = Environment.GetEnvironmentVariable("COSMOS_ENDPOINT")
               ?? throw new InvalidOperationException("COSMOS_ENDPOINT not set");
var key      = Environment.GetEnvironmentVariable("COSMOS_KEY")
               ?? throw new InvalidOperationException("COSMOS_KEY not set");
var dbName   = Environment.GetEnvironmentVariable("COSMOS_DATABASE") ?? "mosaic";
var containerName = Environment.GetEnvironmentVariable("COSMOS_USERS_CONTAINER") ?? "users";
var preferred = (Environment.GetEnvironmentVariable("COSMOS_PREFERRED_REGIONS") ?? "West US 2,East US 2")
    .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);

// Rule sdk-singleton-client: one CosmosClient registered as a singleton.
// Rule sdk-connection-mode: Direct is the production default for .NET.
//   The vnext Cosmos emulator only speaks the Gateway protocol (it has no
//   rntbd/Direct backend endpoints), so fall back to Gateway when pointed at
//   a local emulator while keeping Direct for real accounts.
// Rule sdk-preferred-regions: ApplicationPreferredRegions tells the SDK
//   which region(s) to prefer for reads/writes.
// Rule sdk-retry-throttled: tune retry attempts + wait time on 429s.
// Rule sdk-diagnostics: ApplicationName tags telemetry; this is the
//   minimal hook the diagnostics rule requires.
var isEmulator = endpoint.Contains("localhost", StringComparison.OrdinalIgnoreCase)
                 || endpoint.Contains("127.0.0.1", StringComparison.OrdinalIgnoreCase);
builder.Services.AddSingleton<CosmosClient>(_ =>
{
    var options = new CosmosClientOptions
    {
        ConnectionMode = isEmulator ? ConnectionMode.Gateway : ConnectionMode.Direct,
        ApplicationName = "mosaic-users",
        ApplicationPreferredRegions = preferred,
        MaxRetryAttemptsOnRateLimitedRequests = 9,
        MaxRetryWaitTimeOnRateLimitedRequests = TimeSpan.FromSeconds(30),
        // Rule sdk-end-to-end-timeouts: cap a single attempt; the
        // handler also passes ctx.RequestAborted so the OVERALL
        // operation is bounded by the request deadline.
        RequestTimeout = TimeSpan.FromSeconds(10),
        SerializerOptions = new CosmosSerializationOptions
        {
            PropertyNamingPolicy = CosmosPropertyNamingPolicy.CamelCase,
        },
        // Emulator self-signed cert: trust everything in this container only.
        HttpClientFactory = () =>
        {
            var handler = new HttpClientHandler
            {
                ServerCertificateCustomValidationCallback = HttpClientHandler.DangerousAcceptAnyServerCertificateValidator,
            };
            return new HttpClient(handler);
        },
    };
    return new CosmosClient(endpoint, key, options);
});

builder.Services.AddSingleton<UserStore>();

var app = builder.Build();
var port = Environment.GetEnvironmentVariable("APP_PORT") ?? "8080";
app.Urls.Add($"http://0.0.0.0:{port}");

// Bootstrap database + container at startup.
await app.Services.GetRequiredService<UserStore>().InitAsync(dbName, containerName);

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));

app.MapPost("/users", async ([FromBody] User input, UserStore store, HttpContext ctx) =>
{
    if (string.IsNullOrWhiteSpace(input.Id)
        || string.IsNullOrWhiteSpace(input.Name)
        || string.IsNullOrWhiteSpace(input.Email)
        || string.IsNullOrWhiteSpace(input.City)
        || input.Interests is null)
    {
        return Results.BadRequest(new { error = "id, name, email, city, interests required" });
    }
    try
    {
        var created = await store.CreateAsync(input, ctx.RequestAborted);
        return Results.Created($"/users/{created.Id}", created);
    }
    catch (CosmosException e) when (e.StatusCode == HttpStatusCode.Conflict)
    {
        return Results.Conflict(new { error = $"user {input.Id} already exists" });
    }
});

app.MapGet("/users/{id}", async (string id, UserStore store, HttpContext ctx) =>
{
    var user = await store.GetAsync(id, ctx.RequestAborted);
    return user is null ? Results.NotFound(new { error = $"user {id} not found" }) : Results.Ok(user);
});

app.MapGet("/users", async ([FromQuery] string city, UserStore store, HttpContext ctx) =>
{
    var users = await store.ListByCityAsync(city, ctx.RequestAborted);
    return Results.Ok(users);
});

app.Run();

public record User(
    [property: JsonPropertyName("id")] string Id,
    [property: JsonPropertyName("name")] string Name,
    [property: JsonPropertyName("email")] string Email,
    [property: JsonPropertyName("city")] string City,
    [property: JsonPropertyName("interests")] List<string> Interests,
    [property: JsonPropertyName("createdAt")] string? CreatedAt = null,
    [property: JsonPropertyName("type")] string Type = "user",
    [property: JsonPropertyName("schemaVersion")] int SchemaVersion = 1,
    [property: JsonPropertyName("userId")] string? UserId = null
);

public sealed class UserStore
{
    private readonly CosmosClient _client;
    private Container _container = default!;

    public UserStore(CosmosClient client) { _client = client; }

    public async Task InitAsync(string dbName, string containerName)
    {
        var dbResponse = await _client.CreateDatabaseIfNotExistsAsync(dbName, throughput: 400);
        var indexing = new IndexingPolicy
        {
            IndexingMode = IndexingMode.Consistent,
            Automatic = true,
        };
        indexing.IncludedPaths.Add(new IncludedPath { Path = "/*" });
        indexing.ExcludedPaths.Add(new ExcludedPath { Path = "/\"_etag\"/?" });
        // Rule index-exclude-unused: drop indexes from fields we never filter on.
        indexing.ExcludedPaths.Add(new ExcludedPath { Path = "/email/?" });
        indexing.ExcludedPaths.Add(new ExcludedPath { Path = "/interests/*" });
        indexing.CompositeIndexes.Add(new System.Collections.ObjectModel.Collection<CompositePath>
        {
            new() { Path = "/city", Order = CompositePathSortOrder.Ascending },
            new() { Path = "/id",   Order = CompositePathSortOrder.Ascending },
        });

        var containerProps = new ContainerProperties(containerName, "/userId")
        {
            IndexingPolicy = indexing,
        };
        var resp = await dbResponse.Database.CreateContainerIfNotExistsAsync(containerProps);
        _container = resp.Container;
    }

    // Rule sdk-end-to-end-timeouts: every SDK call accepts and forwards
    // a CancellationToken so the OVERALL operation is bounded by the
    // caller's deadline (typically HttpContext.RequestAborted).
    public async Task<User> CreateAsync(User input, CancellationToken ct = default)
    {
        var now = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ");
        var doc = input with
        {
            CreatedAt = now,
            UserId = input.Id,
            Type = "user",
            SchemaVersion = 1,
        };
        var resp = await _container.CreateItemAsync(doc, new PartitionKey(doc.Id), cancellationToken: ct);
        return resp.Resource;
    }

    public async Task<User?> GetAsync(string id, CancellationToken ct = default)
    {
        try
        {
            var resp = await _container.ReadItemAsync<User>(id, new PartitionKey(id), cancellationToken: ct);
            return resp.Resource;
        }
        catch (CosmosException e) when (e.StatusCode == HttpStatusCode.NotFound)
        {
            return null;
        }
    }

    public async Task<List<User>> ListByCityAsync(string city, CancellationToken ct = default)
    {
        var query = new QueryDefinition("SELECT * FROM c WHERE c.city = @city")
            .WithParameter("@city", city);
        using var iter = _container.GetItemQueryIterator<User>(query);
        var results = new List<User>();
        while (iter.HasMoreResults)
        {
            foreach (var item in await iter.ReadNextAsync(ct))
            {
                results.Add(item);
            }
        }
        return results;
    }
}
