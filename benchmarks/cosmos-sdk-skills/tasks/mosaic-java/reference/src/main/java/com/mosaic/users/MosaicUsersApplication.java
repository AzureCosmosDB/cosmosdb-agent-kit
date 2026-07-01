package com.mosaic.users;

import com.azure.cosmos.ConsistencyLevel;
import com.azure.cosmos.CosmosClient;
import com.azure.cosmos.CosmosClientBuilder;
import com.azure.cosmos.CosmosContainer;
import com.azure.cosmos.CosmosDatabase;
import com.azure.cosmos.CosmosEndToEndOperationLatencyPolicyConfig;
import com.azure.cosmos.CosmosEndToEndOperationLatencyPolicyConfigBuilder;
import com.azure.cosmos.CosmosException;
import com.azure.cosmos.DirectConnectionConfig;
import com.azure.cosmos.ThrottlingRetryOptions;
import com.azure.cosmos.models.*;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;
import java.time.Instant;
import java.util.*;

@SpringBootApplication
@RestController
public class MosaicUsersApplication {

    public static void main(String[] args) {
        if (System.getenv("APP_PORT") != null) {
            System.setProperty("server.port", System.getenv("APP_PORT"));
        } else {
            System.setProperty("server.port", "8080");
        }
        SpringApplication.run(MosaicUsersApplication.class, args);
    }

    // Singleton CosmosClient (rule sdk-singleton-client). One @Bean,
    // owned by the Spring context.
    @Bean
    public CosmosClient cosmosClient(
            @Value("${COSMOS_ENDPOINT}") String endpoint,
            @Value("${COSMOS_KEY}") String key) {

        String preferred = Optional.ofNullable(System.getenv("COSMOS_PREFERRED_REGIONS"))
                .orElse("West US 2,East US 2");
        List<String> regions = new ArrayList<>();
        for (String r : preferred.split(",")) {
            String t = r.trim();
            if (!t.isEmpty()) regions.add(t);
        }

        ThrottlingRetryOptions retry = new ThrottlingRetryOptions()
                .setMaxRetryAttemptsOnThrottledRequests(9)
                .setMaxRetryWaitTime(Duration.ofSeconds(30));

        // Rule sdk-end-to-end-timeouts: cap the whole operation, not
        // just a single attempt.
        CosmosEndToEndOperationLatencyPolicyConfig e2e =
                new CosmosEndToEndOperationLatencyPolicyConfigBuilder(Duration.ofSeconds(5))
                        .enable(true)
                        .build();

        return new CosmosClientBuilder()
                .endpoint(endpoint)
                .key(key)
                .directMode(DirectConnectionConfig.getDefaultConfig())
                .preferredRegions(regions)
                .throttlingRetryOptions(retry)
                .endToEndOperationLatencyPolicyConfig(e2e)
                .userAgentSuffix("mosaic-users")
                .consistencyLevel(ConsistencyLevel.SESSION)
                .buildClient();
    }

    @Autowired
    private UserStore store;

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok");
    }

    @PostMapping("/users")
    public ResponseEntity<?> createUser(@RequestBody UserInput input) {
        if (input.id == null || input.id.isBlank()
                || input.name == null || input.email == null
                || input.city == null || input.interests == null) {
            return ResponseEntity.badRequest().body(Map.of("error", "missing fields"));
        }
        try {
            UserDoc doc = store.create(input);
            return ResponseEntity.status(HttpStatus.CREATED).body(doc);
        } catch (CosmosException e) {
            if (e.getStatusCode() == 409) {
                return ResponseEntity.status(HttpStatus.CONFLICT)
                        .body(Map.of("error", "user " + input.id + " already exists"));
            }
            throw new RuntimeException(e);
        }
    }

    @GetMapping("/users/{id}")
    public ResponseEntity<?> getUser(@PathVariable("id") String id) {
        UserDoc u = store.get(id);
        if (u == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("error", "user " + id + " not found"));
        }
        return ResponseEntity.ok(u);
    }

    @GetMapping("/users")
    public List<UserDoc> listByCity(@RequestParam("city") String city) {
        return store.listByCity(city);
    }

    // Models
    public static class UserInput {
        public String id;
        public String name;
        public String email;
        public String city;
        public List<String> interests;
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class UserDoc {
        public String id;
        public String userId;
        public String name;
        public String email;
        public String city;
        public List<String> interests;
        public String createdAt;
        public String type = "user";
        public int schemaVersion = 1;

        @JsonProperty("_etag") public String etag;
    }

    @Component
    public static class UserStore {
        private final CosmosClient client;
        private CosmosDatabase database;
        private CosmosContainer container;

        public UserStore(CosmosClient client) { this.client = client; }

        @PostConstruct
        public void init() {
            String dbName = Optional.ofNullable(System.getenv("COSMOS_DATABASE")).orElse("mosaic");
            String containerName = Optional.ofNullable(System.getenv("COSMOS_USERS_CONTAINER")).orElse("users");

            ThroughputProperties throughput = ThroughputProperties.createManualThroughput(400);
            client.createDatabaseIfNotExists(dbName, throughput);
            database = client.getDatabase(dbName);

            IndexingPolicy indexing = new IndexingPolicy();
            indexing.setIndexingMode(IndexingMode.CONSISTENT);
            indexing.setIncludedPaths(List.of(new IncludedPath("/*")));
            // Rule index-exclude-unused: exclude noisy / unused paths
            // beyond the system _etag field.
            indexing.setExcludedPaths(List.of(
                    new ExcludedPath("/\"_etag\"/?"),
                    new ExcludedPath("/email/?"),
                    new ExcludedPath("/interests/*")
            ));
            indexing.setCompositeIndexes(List.of(
                    List.of(
                            new CompositePath().setPath("/city").setOrder(CompositePathSortOrder.ASCENDING),
                            new CompositePath().setPath("/id").setOrder(CompositePathSortOrder.ASCENDING)
                    )
            ));
            CosmosContainerProperties props = new CosmosContainerProperties(containerName, "/userId")
                    .setIndexingPolicy(indexing);
            database.createContainerIfNotExists(props);
            container = database.getContainer(containerName);
        }

        public UserDoc create(UserInput input) {
            UserDoc doc = new UserDoc();
            doc.id = input.id;
            doc.userId = input.id;
            doc.name = input.name;
            doc.email = input.email;
            doc.city = input.city;
            doc.interests = new ArrayList<>(input.interests);
            doc.createdAt = Instant.now().toString();
            doc.type = "user";
            doc.schemaVersion = 1;
            container.createItem(doc, new PartitionKey(doc.id), new CosmosItemRequestOptions());
            return doc;
        }

        public UserDoc get(String id) {
            try {
                return container.readItem(id, new PartitionKey(id), UserDoc.class).getItem();
            } catch (CosmosException e) {
                if (e.getStatusCode() == 404) return null;
                throw e;
            }
        }

        public List<UserDoc> listByCity(String city) {
            String sql = "SELECT * FROM c WHERE c.city = @city";
            SqlQuerySpec spec = new SqlQuerySpec(sql,
                    List.of(new SqlParameter("@city", city)));
            List<UserDoc> out = new ArrayList<>();
            for (FeedResponse<UserDoc> page :
                    container.queryItems(spec, new CosmosQueryRequestOptions(), UserDoc.class)
                            .iterableByPage()) {
                out.addAll(page.getResults());
            }
            return out;
        }

        @PreDestroy
        public void shutdown() {
            if (client != null) client.close();
        }
    }
}
