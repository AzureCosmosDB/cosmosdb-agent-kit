"""
Scenario-level conftest for ai-chat-rag tests.

Imports shared harness fixtures and adds scenario-specific helpers.

NOTE: This scenario uses mock embeddings (small fixed-dimension arrays).
In production, embeddings would be 1536 dimensions (text-embedding-ada-002).
For testing, we use shorter vectors that still exercise the vector search API.
"""

import sys
import math
from pathlib import Path

# Add harness to path so shared fixtures are importable
harness_dir = Path(__file__).resolve().parent.parent.parent.parent / "harness"
sys.path.insert(0, str(harness_dir))

from conftest_base import *  # noqa: F401,F403 — re-export all shared fixtures

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_embedding(seed_value, dimensions=1536):
    """
    Generate a deterministic mock embedding vector.
    Uses simple math to create vectors that have knowable similarity relationships.
    """
    vec = [0.0] * dimensions
    for i in range(dimensions):
        vec[i] = math.sin(seed_value * (i + 1) * 0.01) * 0.5
    # Normalize to unit length
    magnitude = math.sqrt(sum(x * x for x in vec))
    if magnitude > 0:
        vec = [x / magnitude for x in vec]
    return vec


# ---------------------------------------------------------------------------
# Scenario-specific fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_sessions():
    """Standard set of test chat sessions."""
    return [
        {"userId": "user-001", "title": "Help with Python"},
        {"userId": "user-001", "title": "Cosmos DB questions"},
        {"userId": "user-001", "title": "Azure deployment"},
        {"userId": "user-002", "title": "Getting started"},
        {"userId": "user-002", "title": "Data modeling help"},
    ]


@pytest.fixture(scope="session")
def test_messages():
    """Messages to add to the first session after creation."""
    return [
        {"role": "user", "content": "How do I connect to Cosmos DB from Python?"},
        {"role": "assistant", "content": "You can use the azure-cosmos package. Install it with pip install azure-cosmos."},
        {"role": "user", "content": "How do I create a database?"},
        {"role": "assistant", "content": "Use client.create_database_if_not_exists('mydb') to create a database."},
    ]


@pytest.fixture(scope="session")
def mock_embeddings():
    """
    Pre-computed mock embeddings for test documents.
    Seed values are chosen so documents in the same category
    have more similar vectors than documents in different categories.
    """
    return {
        "python-basics": _make_embedding(1.0),
        "python-advanced": _make_embedding(1.2),
        "cosmos-modeling": _make_embedding(5.0),
        "cosmos-queries": _make_embedding(5.3),
        "azure-deploy": _make_embedding(10.0),
    }


@pytest.fixture(scope="session")
def test_documents(mock_embeddings):
    """Standard set of test documents with embeddings and metadata."""
    return [
        {
            "content": "Python is a versatile programming language used for web development, data science, and AI.",
            "embedding": mock_embeddings["python-basics"],
            "metadata": {"category": "programming", "source": "docs"},
        },
        {
            "content": "Advanced Python features include decorators, generators, context managers, and metaclasses.",
            "embedding": mock_embeddings["python-advanced"],
            "metadata": {"category": "programming", "source": "docs"},
        },
        {
            "content": "Cosmos DB data modeling: embed related data in the same document for read-heavy workloads.",
            "embedding": mock_embeddings["cosmos-modeling"],
            "metadata": {"category": "database", "source": "best-practices"},
        },
        {
            "content": "Cosmos DB queries should avoid cross-partition scans. Use the partition key in WHERE clauses.",
            "embedding": mock_embeddings["cosmos-queries"],
            "metadata": {"category": "database", "source": "best-practices"},
        },
        {
            "content": "Deploy Azure resources using Bicep templates or ARM templates for infrastructure as code.",
            "embedding": mock_embeddings["azure-deploy"],
            "metadata": {"category": "cloud", "source": "tutorials"},
        },
    ]


@pytest.fixture(scope="session")
def seeded_data(api, test_sessions, test_messages, test_documents):
    """
    Create sessions, add messages, and store documents.
    Returns a dict with the created data for reference.
    """
    # Create sessions
    created_sessions = []
    for session in test_sessions:
        resp = api.request("POST", "/api/sessions", json=session)
        assert resp.status_code == 201, (
            f"Failed to create session '{session['title']}': "
            f"{resp.status_code} {resp.text}"
        )
        created_sessions.append(resp.json())

    # Add messages to the first session
    first_session_id = created_sessions[0]["sessionId"]
    created_messages = []
    for msg in test_messages:
        resp = api.request("POST", f"/api/sessions/{first_session_id}/messages", json=msg)
        assert resp.status_code == 201, (
            f"Failed to add message to session: "
            f"{resp.status_code} {resp.text}"
        )
        created_messages.append(resp.json())

    # Store documents
    created_documents = []
    for doc in test_documents:
        resp = api.request("POST", "/api/documents", json=doc)
        assert resp.status_code == 201, (
            f"Failed to store document: {resp.status_code} {resp.text}"
        )
        created_documents.append(resp.json())

    return {
        "sessions": created_sessions,
        "messages": created_messages,
        "documents": created_documents,
    }
