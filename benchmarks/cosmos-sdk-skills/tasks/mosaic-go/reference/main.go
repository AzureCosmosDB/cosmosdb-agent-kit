package main

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/Azure/azure-sdk-for-go/sdk/azcore"
	"github.com/Azure/azure-sdk-for-go/sdk/azcore/policy"
	"github.com/Azure/azure-sdk-for-go/sdk/data/azcosmos"
)

// UserInput is the POST /users payload.
type UserInput struct {
	ID        string   `json:"id"`
	Name      string   `json:"name"`
	Email     string   `json:"email"`
	City      string   `json:"city"`
	Interests []string `json:"interests"`
}

// UserDoc is what we persist.
type UserDoc struct {
	ID            string   `json:"id"`
	UserID        string   `json:"userId"`
	Name          string   `json:"name"`
	Email         string   `json:"email"`
	City          string   `json:"city"`
	Interests     []string `json:"interests"`
	CreatedAt     string   `json:"createdAt"`
	Type          string   `json:"type"`
	SchemaVersion int      `json:"schemaVersion"`
}

var (
	client    *azcosmos.Client
	container *azcosmos.ContainerClient
)

func mustEnv(k string) string {
	v := os.Getenv(k)
	if v == "" {
		log.Fatalf("env var %s must be set", k)
	}
	return v
}

func main() {
	endpoint := mustEnv("COSMOS_ENDPOINT")
	key := mustEnv("COSMOS_KEY")
	dbName := envOr("COSMOS_DATABASE", "mosaic")
	containerName := envOr("COSMOS_USERS_CONTAINER", "users")
	port := envOr("APP_PORT", "8080")

	cred, err := azcosmos.NewKeyCredential(key)
	if err != nil {
		log.Fatalf("KeyCredential: %v", err)
	}

	// HTTP transport that accepts the emulator's self-signed cert.
	httpClient := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		},
	}

	opts := &azcosmos.ClientOptions{
		ClientOptions: azcore.ClientOptions{
			Transport: httpClient,
			// Borrowed from the .NET / Java retry guidance bundled with
			// this skill set: 9 attempts is a reasonable upper bound for
			// 429 retries on a userland service. The Go SDK only exposes
			// the azcore retry policy here, not a Cosmos-specific
			// throttling option.
			Retry: policy.RetryOptions{
				MaxRetries: 9,
				RetryDelay: 1 * time.Second,
			},
			// "mosaic-users" tagging via Telemetry — equivalent to
			// userAgentSuffix in Node / ApplicationName in .NET.
			Telemetry: policy.TelemetryOptions{
				ApplicationID: "mosaic-users",
			},
		},
		// preferredLocations equivalent: PreferredRegions field. Inferred
		// from the .NET ApplicationPreferredRegions / Java
		// preferredRegions rule — no Go-specific local guidance.
		PreferredRegions: splitCSV(envOr("COSMOS_PREFERRED_REGIONS", "West US 2,East US 2")),
	}

	// Singleton client — constructed exactly once at process start.
	var cerr error
	client, cerr = azcosmos.NewClientWithKey(endpoint, cred, opts)
	if cerr != nil {
		log.Fatalf("NewClientWithKey: %v", cerr)
	}

	if err := ensureDatabaseAndContainer(client, dbName, containerName); err != nil {
		log.Fatalf("provision: %v", err)
	}
	container, err = client.NewContainer(dbName, containerName)
	if err != nil {
		log.Fatalf("NewContainer: %v", err)
	}

	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", health)
	mux.HandleFunc("POST /users", createUser)
	mux.HandleFunc("GET /users/{id}", getUser)
	mux.HandleFunc("GET /users", listUsersByCity)

	addr := "0.0.0.0:" + port
	log.Printf("mosaic-users listening on http://%s", addr)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatal(err)
	}
}

func envOr(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}

func splitCSV(s string) []string {
	parts := strings.Split(s, ",")
	out := parts[:0]
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			out = append(out, p)
		}
	}
	return out
}

func ensureDatabaseAndContainer(c *azcosmos.Client, dbName, containerName string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	throughput := azcosmos.NewManualThroughputProperties(400)
	_, err := c.CreateDatabase(ctx, azcosmos.DatabaseProperties{ID: dbName}, &azcosmos.CreateDatabaseOptions{
		ThroughputProperties: &throughput,
	})
	if err != nil && !isAlreadyExists(err) {
		return fmt.Errorf("CreateDatabase: %w", err)
	}

	db, err := c.NewDatabase(dbName)
	if err != nil {
		return err
	}

	props := azcosmos.ContainerProperties{
		ID: containerName,
		PartitionKeyDefinition: azcosmos.PartitionKeyDefinition{
			Paths: []string{"/userId"},
		},
		IndexingPolicy: &azcosmos.IndexingPolicy{
			IndexingMode: azcosmos.IndexingModeConsistent,
			Automatic:    true,
			IncludedPaths: []azcosmos.IncludedPath{{Path: "/*"}},
			ExcludedPaths: []azcosmos.ExcludedPath{
				{Path: "/\"_etag\"/?"},
				{Path: "/email/?"},
				{Path: "/interests/*"},
			},
			CompositeIndexes: [][]azcosmos.CompositeIndex{
				{
					{Path: "/city", Order: azcosmos.CompositeIndexAscending},
					{Path: "/id", Order: azcosmos.CompositeIndexAscending},
				},
			},
		},
	}
	_, err = db.CreateContainer(ctx, props, nil)
	if err != nil && !isAlreadyExists(err) {
		return fmt.Errorf("CreateContainer: %w", err)
	}
	return nil
}

func isAlreadyExists(err error) bool {
	var rerr *azcore.ResponseError
	if errors.As(err, &rerr) {
		return rerr.StatusCode == http.StatusConflict
	}
	return false
}

// --- handlers ---

func health(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func createUser(w http.ResponseWriter, r *http.Request) {
	var in UserInput
	if err := json.NewDecoder(r.Body).Decode(&in); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid json"})
		return
	}
	if in.ID == "" || in.Name == "" || in.Email == "" || in.City == "" || in.Interests == nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "id, name, email, city, interests required"})
		return
	}
	doc := UserDoc{
		ID:            in.ID,
		UserID:        in.ID,
		Name:          in.Name,
		Email:         in.Email,
		City:          in.City,
		Interests:     append([]string(nil), in.Interests...),
		CreatedAt:     time.Now().UTC().Format(time.RFC3339Nano),
		Type:          "user",
		SchemaVersion: 1,
	}
	body, _ := json.Marshal(doc)
	pk := azcosmos.NewPartitionKeyString(doc.ID)
	_, err := container.CreateItem(r.Context(), pk, body, nil)
	if err != nil {
		var rerr *azcore.ResponseError
		if errors.As(err, &rerr) && rerr.StatusCode == http.StatusConflict {
			writeJSON(w, http.StatusConflict, map[string]string{"error": fmt.Sprintf("user %s already exists", in.ID)})
			return
		}
		log.Printf("create failed: %v", err)
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, http.StatusCreated, doc)
}

func getUser(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	pk := azcosmos.NewPartitionKeyString(id)
	resp, err := container.ReadItem(r.Context(), pk, id, nil)
	if err != nil {
		var rerr *azcore.ResponseError
		if errors.As(err, &rerr) && rerr.StatusCode == http.StatusNotFound {
			writeJSON(w, http.StatusNotFound, map[string]string{"error": fmt.Sprintf("user %s not found", id)})
			return
		}
		log.Printf("read failed: %v", err)
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
		return
	}
	var doc UserDoc
	if err := json.Unmarshal(resp.Value, &doc); err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": "decode"})
		return
	}
	writeJSON(w, http.StatusOK, doc)
}

func listUsersByCity(w http.ResponseWriter, r *http.Request) {
	city := r.URL.Query().Get("city")
	if city == "" {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "city query param required"})
		return
	}
	query := "SELECT * FROM c WHERE c.city = @city"
	opts := &azcosmos.QueryOptions{
		QueryParameters: []azcosmos.QueryParameter{{Name: "@city", Value: city}},
	}
	pager := container.NewQueryItemsPager(query, azcosmos.NewPartitionKey(), opts)
	results := []UserDoc{}
	for pager.More() {
		page, err := pager.NextPage(r.Context())
		if err != nil {
			log.Printf("query failed: %v", err)
			writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
			return
		}
		for _, raw := range page.Items {
			var doc UserDoc
			if err := json.Unmarshal(raw, &doc); err == nil {
				results = append(results, doc)
			}
		}
	}
	writeJSON(w, http.StatusOK, results)
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}
