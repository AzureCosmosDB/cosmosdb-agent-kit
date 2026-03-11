"""
Contract tests for the AI Chat with RAG scenario.

Every test references the API contract defined in ../api-contract.yaml.
Tests validate HTTP method, path, status codes, response structure, and field names.
"""

import math
import pytest


class TestHealth:
    """GET /health"""

    def test_health_returns_200(self, api):
        resp = api.request("GET", "/health")
        assert resp.status_code == 200

    def test_health_response_has_status(self, api):
        data = api.request("GET", "/health").json()
        assert "status" in data
        assert data["status"] in ("ok", "healthy", "UP")


class TestCreateSession:
    """POST /api/sessions"""

    def test_create_session_returns_201(self, api):
        resp = api.request("POST", "/api/sessions", json={
            "userId": "user-new-001",
            "title": "New test session"
        })
        assert resp.status_code == 201

    def test_create_session_response_fields(self, api):
        resp = api.request("POST", "/api/sessions", json={
            "userId": "user-new-002",
            "title": "Field check session"
        })
        data = resp.json()
        assert "sessionId" in data
        assert data["userId"] == "user-new-002"
        assert data["title"] == "Field check session"

    def test_create_session_generates_unique_ids(self, api):
        r1 = api.request("POST", "/api/sessions", json={
            "userId": "user-new-003",
            "title": "Session A"
        })
        r2 = api.request("POST", "/api/sessions", json={
            "userId": "user-new-003",
            "title": "Session B"
        })
        assert r1.json()["sessionId"] != r2.json()["sessionId"]

    def test_create_session_has_created_at(self, api):
        resp = api.request("POST", "/api/sessions", json={
            "userId": "user-new-004",
            "title": "Timestamp check"
        })
        data = resp.json()
        assert "createdAt" in data


class TestGetSession:
    """GET /api/sessions/{sessionId}"""

    def test_get_session_returns_200(self, api, seeded_data):
        sid = seeded_data["sessions"][0]["sessionId"]
        resp = api.request("GET", f"/api/sessions/{sid}")
        assert resp.status_code == 200

    def test_get_session_includes_messages(self, api, seeded_data):
        sid = seeded_data["sessions"][0]["sessionId"]
        data = api.request("GET", f"/api/sessions/{sid}").json()
        assert "messages" in data
        assert isinstance(data["messages"], list)
        # First session has 4 seeded messages
        assert len(data["messages"]) >= 4

    def test_get_session_message_structure(self, api, seeded_data):
        sid = seeded_data["sessions"][0]["sessionId"]
        data = api.request("GET", f"/api/sessions/{sid}").json()
        msg = data["messages"][0]
        assert "role" in msg
        assert "content" in msg
        assert msg["role"] in ("user", "assistant", "system")

    def test_get_nonexistent_session_returns_404(self, api):
        resp = api.request("GET", "/api/sessions/nonexistent-session-id")
        assert resp.status_code == 404

    def test_get_session_returns_correct_title(self, api, seeded_data):
        sid = seeded_data["sessions"][0]["sessionId"]
        data = api.request("GET", f"/api/sessions/{sid}").json()
        assert data["title"] == "Help with Python"


class TestListUserSessions:
    """GET /api/users/{userId}/sessions"""

    def test_list_sessions_returns_200(self, api, seeded_data):
        resp = api.request("GET", "/api/users/user-001/sessions")
        assert resp.status_code == 200

    def test_list_sessions_returns_array(self, api, seeded_data):
        data = api.request("GET", "/api/users/user-001/sessions").json()
        assert isinstance(data, list)

    def test_user_001_has_3_sessions(self, api, seeded_data):
        data = api.request("GET", "/api/users/user-001/sessions").json()
        assert len(data) >= 3  # 3 seeded sessions for user-001

    def test_user_002_has_2_sessions(self, api, seeded_data):
        data = api.request("GET", "/api/users/user-002/sessions").json()
        assert len(data) >= 2  # 2 seeded sessions for user-002

    def test_session_list_contains_session_ids(self, api, seeded_data):
        data = api.request("GET", "/api/users/user-001/sessions").json()
        for session in data:
            assert "sessionId" in session
            assert "title" in session

    def test_unknown_user_returns_empty_list(self, api, seeded_data):
        data = api.request("GET", "/api/users/user-nobody/sessions").json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestAddMessage:
    """POST /api/sessions/{sessionId}/messages"""

    def test_add_message_returns_201(self, api, seeded_data):
        sid = seeded_data["sessions"][1]["sessionId"]
        resp = api.request("POST", f"/api/sessions/{sid}/messages", json={
            "role": "user",
            "content": "What is a partition key?"
        })
        assert resp.status_code == 201

    def test_add_message_response_fields(self, api, seeded_data):
        sid = seeded_data["sessions"][1]["sessionId"]
        resp = api.request("POST", f"/api/sessions/{sid}/messages", json={
            "role": "assistant",
            "content": "A partition key determines data distribution."
        })
        data = resp.json()
        assert "role" in data
        assert "content" in data
        assert data["role"] == "assistant"

    def test_add_message_has_timestamp(self, api, seeded_data):
        sid = seeded_data["sessions"][1]["sessionId"]
        resp = api.request("POST", f"/api/sessions/{sid}/messages", json={
            "role": "user",
            "content": "Testing timestamp"
        })
        data = resp.json()
        assert "timestamp" in data or "createdAt" in data

    def test_messages_persist_in_session(self, api, seeded_data):
        sid = seeded_data["sessions"][2]["sessionId"]
        # Add two messages
        api.request("POST", f"/api/sessions/{sid}/messages", json={
            "role": "user", "content": "First message"
        })
        api.request("POST", f"/api/sessions/{sid}/messages", json={
            "role": "assistant", "content": "First reply"
        })
        # Retrieve session and verify messages
        data = api.request("GET", f"/api/sessions/{sid}").json()
        assert len(data["messages"]) >= 2

    def test_add_message_to_nonexistent_session_returns_404(self, api):
        resp = api.request("POST", "/api/sessions/fake-session/messages", json={
            "role": "user", "content": "Hello"
        })
        assert resp.status_code == 404


class TestStoreDocument:
    """POST /api/documents"""

    def test_store_document_returns_201(self, api):
        embedding = [0.1] * 1536
        resp = api.request("POST", "/api/documents", json={
            "content": "Test document content for validation",
            "embedding": embedding,
            "metadata": {"category": "test", "source": "unit-test"}
        })
        assert resp.status_code == 201

    def test_store_document_response_has_id(self, api):
        embedding = [0.2] * 1536
        resp = api.request("POST", "/api/documents", json={
            "content": "Document with ID check",
            "embedding": embedding,
            "metadata": {"category": "test"}
        })
        data = resp.json()
        assert "documentId" in data or "id" in data

    def test_store_document_preserves_metadata(self, api):
        embedding = [0.3] * 1536
        resp = api.request("POST", "/api/documents", json={
            "content": "Metadata preservation test",
            "embedding": embedding,
            "metadata": {"category": "science", "source": "journal"}
        })
        data = resp.json()
        if "metadata" in data:
            assert data["metadata"]["category"] == "science"

    def test_store_document_embedding_dimension(self, api):
        """Embedding must be accepted as a list of floats."""
        embedding = [0.01 * i for i in range(1536)]
        resp = api.request("POST", "/api/documents", json={
            "content": "Dimension check document",
            "embedding": embedding,
            "metadata": {}
        })
        assert resp.status_code == 201


class TestVectorSearch:
    """POST /api/search/vector"""

    def test_vector_search_returns_200(self, api, seeded_data, mock_embeddings):
        resp = api.request("POST", "/api/search/vector", json={
            "embedding": mock_embeddings["python-basics"],
            "topK": 3
        })
        assert resp.status_code == 200

    def test_vector_search_returns_array(self, api, seeded_data, mock_embeddings):
        resp = api.request("POST", "/api/search/vector", json={
            "embedding": mock_embeddings["python-basics"],
            "topK": 5
        })
        data = resp.json()
        assert isinstance(data, list)

    def test_vector_search_respects_top_k(self, api, seeded_data, mock_embeddings):
        resp = api.request("POST", "/api/search/vector", json={
            "embedding": mock_embeddings["cosmos-modeling"],
            "topK": 2
        })
        data = resp.json()
        assert len(data) <= 2

    def test_vector_search_result_has_content(self, api, seeded_data, mock_embeddings):
        resp = api.request("POST", "/api/search/vector", json={
            "embedding": mock_embeddings["python-basics"],
            "topK": 3
        })
        data = resp.json()
        assert len(data) > 0
        result = data[0]
        assert "content" in result

    def test_vector_search_result_has_score(self, api, seeded_data, mock_embeddings):
        resp = api.request("POST", "/api/search/vector", json={
            "embedding": mock_embeddings["python-basics"],
            "topK": 3
        })
        data = resp.json()
        assert len(data) > 0
        result = data[0]
        assert "score" in result or "similarity" in result

    def test_vector_search_similar_docs_ranked_higher(self, api, seeded_data, mock_embeddings):
        """
        Searching with the python-basics embedding should return python-related
        documents ranked higher than cloud documents.
        """
        resp = api.request("POST", "/api/search/vector", json={
            "embedding": mock_embeddings["python-basics"],
            "topK": 5
        })
        data = resp.json()
        contents = [r["content"] for r in data]
        # The first result should be about Python (most similar)
        assert any("Python" in c or "python" in c for c in contents[:2])


class TestHybridSearch:
    """POST /api/search/hybrid"""

    def test_hybrid_search_returns_200(self, api, seeded_data, mock_embeddings):
        resp = api.request("POST", "/api/search/hybrid", json={
            "embedding": mock_embeddings["cosmos-modeling"],
            "filter": {"category": "database"},
            "topK": 3
        })
        assert resp.status_code == 200

    def test_hybrid_search_filters_by_metadata(self, api, seeded_data, mock_embeddings):
        resp = api.request("POST", "/api/search/hybrid", json={
            "embedding": mock_embeddings["cosmos-modeling"],
            "filter": {"category": "database"},
            "topK": 5
        })
        data = resp.json()
        assert isinstance(data, list)
        # All returned documents should be in the "database" category
        for result in data:
            if "metadata" in result:
                assert result["metadata"]["category"] == "database"

    def test_hybrid_search_result_structure(self, api, seeded_data, mock_embeddings):
        resp = api.request("POST", "/api/search/hybrid", json={
            "embedding": mock_embeddings["python-basics"],
            "filter": {"category": "programming"},
            "topK": 3
        })
        data = resp.json()
        assert len(data) > 0
        result = data[0]
        assert "content" in result

    def test_hybrid_search_empty_filter_returns_results(self, api, seeded_data, mock_embeddings):
        resp = api.request("POST", "/api/search/hybrid", json={
            "embedding": mock_embeddings["azure-deploy"],
            "filter": {},
            "topK": 3
        })
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_hybrid_search_no_match_filter_returns_empty(self, api, seeded_data, mock_embeddings):
        resp = api.request("POST", "/api/search/hybrid", json={
            "embedding": mock_embeddings["azure-deploy"],
            "filter": {"category": "nonexistent-category"},
            "topK": 3
        })
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0
