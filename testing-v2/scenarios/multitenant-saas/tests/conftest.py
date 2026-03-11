"""
Scenario-level conftest for multitenant-saas tests.

Imports shared harness fixtures and adds scenario-specific helpers.
Sets up two tenants with users, projects, and tasks for deterministic testing.
"""

import sys
from pathlib import Path

# Add harness to path so shared fixtures are importable
harness_dir = Path(__file__).resolve().parent.parent.parent.parent / "harness"
sys.path.insert(0, str(harness_dir))

from conftest_base import *  # noqa: F401,F403 — re-export all shared fixtures

import pytest


# ---------------------------------------------------------------------------
# Scenario-specific fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_tenants():
    """Standard set of test tenants."""
    return [
        {"name": "Acme Corp", "plan": "premium"},
        {"name": "Startup Inc", "plan": "standard"},
        {"name": "Solo Dev", "plan": "free"},
    ]


@pytest.fixture(scope="session")
def test_users_per_tenant():
    """Users to create within each tenant. Keyed by tenant index."""
    return {
        0: [  # Acme Corp
            {"name": "Alice Admin", "email": "alice@acme.com", "role": "admin"},
            {"name": "Bob Member", "email": "bob@acme.com", "role": "member"},
            {"name": "Charlie Viewer", "email": "charlie@acme.com", "role": "viewer"},
        ],
        1: [  # Startup Inc
            {"name": "Dana Admin", "email": "dana@startup.com", "role": "admin"},
            {"name": "Eve Member", "email": "eve@startup.com", "role": "member"},
        ],
    }


@pytest.fixture(scope="session")
def test_projects_per_tenant():
    """Projects to create within each tenant. Keyed by tenant index."""
    return {
        0: [  # Acme Corp
            {"name": "Website Redesign", "description": "Redesign the company website"},
            {"name": "Mobile App", "description": "Build a mobile application"},
        ],
        1: [  # Startup Inc
            {"name": "MVP Launch", "description": "Build the minimum viable product"},
        ],
    }


@pytest.fixture(scope="session")
def test_tasks_blueprint():
    """
    Tasks to create. Keyed by (tenant_index, project_index).
    assignee_index refers to the user index within that tenant.
    """
    return {
        (0, 0): [  # Acme Corp → Website Redesign
            {"title": "Design mockups", "assignee_index": 1, "priority": "high", "status": "done"},
            {"title": "Implement frontend", "assignee_index": 1, "priority": "high", "status": "in-progress"},
            {"title": "Write content", "assignee_index": 2, "priority": "medium", "status": "todo"},
        ],
        (0, 1): [  # Acme Corp → Mobile App
            {"title": "Setup CI/CD", "assignee_index": 0, "priority": "critical", "status": "done"},
            {"title": "Build auth module", "assignee_index": 1, "priority": "high", "status": "in-progress"},
            {"title": "Create API endpoints", "assignee_index": 1, "priority": "medium", "status": "todo"},
            {"title": "Design database schema", "assignee_index": 0, "priority": "high", "status": "blocked"},
        ],
        (1, 0): [  # Startup Inc → MVP Launch
            {"title": "User research", "assignee_index": 0, "priority": "high", "status": "done"},
            {"title": "Build landing page", "assignee_index": 1, "priority": "medium", "status": "in-progress"},
            {"title": "Setup payments", "assignee_index": 0, "priority": "critical", "status": "todo"},
        ],
    }


@pytest.fixture(scope="session")
def seeded_data(
    api,
    test_tenants,
    test_users_per_tenant,
    test_projects_per_tenant,
    test_tasks_blueprint,
):
    """
    Create tenants, users, projects, and tasks deterministically.
    Returns a dict with all created entities for test reference.
    """
    # Create tenants
    created_tenants = []
    for tenant in test_tenants:
        resp = api.request("POST", "/api/tenants", json=tenant)
        assert resp.status_code == 201, (
            f"Failed to create tenant '{tenant['name']}': "
            f"{resp.status_code} {resp.text}"
        )
        created_tenants.append(resp.json())

    # Create users per tenant
    created_users = {}  # {tenant_index: [user_dicts]}
    for t_idx, users in test_users_per_tenant.items():
        tenant_id = created_tenants[t_idx]["tenantId"]
        created_users[t_idx] = []
        for user in users:
            resp = api.request("POST", f"/api/tenants/{tenant_id}/users", json=user)
            assert resp.status_code == 201, (
                f"Failed to create user '{user['name']}' in tenant {tenant_id}: "
                f"{resp.status_code} {resp.text}"
            )
            created_users[t_idx].append(resp.json())

    # Create projects per tenant
    created_projects = {}  # {tenant_index: [project_dicts]}
    for t_idx, projects in test_projects_per_tenant.items():
        tenant_id = created_tenants[t_idx]["tenantId"]
        created_projects[t_idx] = []
        for project in projects:
            resp = api.request("POST", f"/api/tenants/{tenant_id}/projects", json=project)
            assert resp.status_code == 201, (
                f"Failed to create project '{project['name']}' in tenant {tenant_id}: "
                f"{resp.status_code} {resp.text}"
            )
            created_projects[t_idx].append(resp.json())

    # Create tasks
    created_tasks = {}  # {(tenant_index, project_index): [task_dicts]}
    for (t_idx, p_idx), tasks in test_tasks_blueprint.items():
        tenant_id = created_tenants[t_idx]["tenantId"]
        project_id = created_projects[t_idx][p_idx]["projectId"]
        created_tasks[(t_idx, p_idx)] = []
        for task in tasks:
            assignee_id = created_users[t_idx][task["assignee_index"]]["userId"]
            payload = {
                "title": task["title"],
                "assigneeId": assignee_id,
                "priority": task["priority"],
                "status": task["status"],
            }
            resp = api.request(
                "POST",
                f"/api/tenants/{tenant_id}/projects/{project_id}/tasks",
                json=payload,
            )
            assert resp.status_code == 201, (
                f"Failed to create task '{task['title']}': "
                f"{resp.status_code} {resp.text}"
            )
            created_tasks[(t_idx, p_idx)].append(resp.json())

    return {
        "tenants": created_tenants,
        "users": created_users,
        "projects": created_projects,
        "tasks": created_tasks,
    }
