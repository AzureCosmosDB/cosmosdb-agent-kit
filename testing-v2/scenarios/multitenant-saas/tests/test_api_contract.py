"""
Contract tests for the Multitenant SaaS (Project Management) scenario.

Every test references the API contract defined in ../api-contract.yaml.
Tests validate HTTP method, path, status codes, response structure,
field names, and tenant isolation.
"""

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


class TestCreateTenant:
    """POST /api/tenants"""

    def test_create_tenant_returns_201(self, api):
        resp = api.request("POST", "/api/tenants", json={
            "name": "Test Tenant",
            "plan": "free"
        })
        assert resp.status_code == 201

    def test_create_tenant_response_fields(self, api):
        resp = api.request("POST", "/api/tenants", json={
            "name": "Field Check Tenant",
            "plan": "standard"
        })
        data = resp.json()
        assert "tenantId" in data
        assert data["name"] == "Field Check Tenant"
        assert data["plan"] == "standard"

    def test_create_tenant_generates_unique_ids(self, api):
        r1 = api.request("POST", "/api/tenants", json={
            "name": "Tenant A", "plan": "free"
        })
        r2 = api.request("POST", "/api/tenants", json={
            "name": "Tenant B", "plan": "free"
        })
        assert r1.json()["tenantId"] != r2.json()["tenantId"]

    def test_create_tenant_has_created_at(self, api):
        resp = api.request("POST", "/api/tenants", json={
            "name": "Timestamp Tenant", "plan": "premium"
        })
        data = resp.json()
        assert "createdAt" in data


class TestGetTenant:
    """GET /api/tenants/{tenantId}"""

    def test_get_tenant_returns_200(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        resp = api.request("GET", f"/api/tenants/{tid}")
        assert resp.status_code == 200

    def test_get_tenant_returns_correct_name(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid}").json()
        assert data["name"] == "Acme Corp"
        assert data["plan"] == "premium"

    def test_get_nonexistent_tenant_returns_404(self, api):
        resp = api.request("GET", "/api/tenants/nonexistent-tenant-id")
        assert resp.status_code == 404


class TestCreateUser:
    """POST /api/tenants/{tenantId}/users"""

    def test_create_user_returns_201(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        resp = api.request("POST", f"/api/tenants/{tid}/users", json={
            "name": "New User",
            "email": "newuser@acme.com",
            "role": "member"
        })
        assert resp.status_code == 201

    def test_create_user_response_fields(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        resp = api.request("POST", f"/api/tenants/{tid}/users", json={
            "name": "Field User",
            "email": "fielduser@acme.com",
            "role": "viewer"
        })
        data = resp.json()
        assert "userId" in data
        assert data["tenantId"] == tid
        assert data["name"] == "Field User"
        assert data["email"] == "fielduser@acme.com"
        assert data["role"] == "viewer"

    def test_create_user_generates_unique_ids(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        r1 = api.request("POST", f"/api/tenants/{tid}/users", json={
            "name": "User A", "email": "a@acme.com", "role": "member"
        })
        r2 = api.request("POST", f"/api/tenants/{tid}/users", json={
            "name": "User B", "email": "b@acme.com", "role": "member"
        })
        assert r1.json()["userId"] != r2.json()["userId"]


class TestListUsers:
    """GET /api/tenants/{tenantId}/users"""

    def test_list_users_returns_200(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        resp = api.request("GET", f"/api/tenants/{tid}/users")
        assert resp.status_code == 200

    def test_list_users_returns_array(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid}/users").json()
        assert isinstance(data, list)

    def test_acme_has_at_least_3_seeded_users(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid}/users").json()
        assert len(data) >= 3  # 3 seeded users for Acme Corp

    def test_startup_has_at_least_2_seeded_users(self, api, seeded_data):
        tid = seeded_data["tenants"][1]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid}/users").json()
        assert len(data) >= 2  # 2 seeded users for Startup Inc


class TestCreateProject:
    """POST /api/tenants/{tenantId}/projects"""

    def test_create_project_returns_201(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        resp = api.request("POST", f"/api/tenants/{tid}/projects", json={
            "name": "New Project",
            "description": "A test project"
        })
        assert resp.status_code == 201

    def test_create_project_response_fields(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        resp = api.request("POST", f"/api/tenants/{tid}/projects", json={
            "name": "Field Project",
            "description": "Checking fields"
        })
        data = resp.json()
        assert "projectId" in data
        assert data["tenantId"] == tid
        assert data["name"] == "Field Project"


class TestListProjects:
    """GET /api/tenants/{tenantId}/projects"""

    def test_list_projects_returns_200(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        resp = api.request("GET", f"/api/tenants/{tid}/projects")
        assert resp.status_code == 200

    def test_acme_has_at_least_2_seeded_projects(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid}/projects").json()
        assert len(data) >= 2

    def test_startup_has_at_least_1_seeded_project(self, api, seeded_data):
        tid = seeded_data["tenants"][1]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid}/projects").json()
        assert len(data) >= 1


class TestGetProject:
    """GET /api/tenants/{tenantId}/projects/{projectId}"""

    def test_get_project_returns_200(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        pid = seeded_data["projects"][0][0]["projectId"]
        resp = api.request("GET", f"/api/tenants/{tid}/projects/{pid}")
        assert resp.status_code == 200

    def test_get_project_returns_correct_name(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        pid = seeded_data["projects"][0][0]["projectId"]
        data = api.request("GET", f"/api/tenants/{tid}/projects/{pid}").json()
        assert data["name"] == "Website Redesign"

    def test_get_nonexistent_project_returns_404(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        resp = api.request("GET", f"/api/tenants/{tid}/projects/nonexistent-project")
        assert resp.status_code == 404


class TestCreateTask:
    """POST /api/tenants/{tenantId}/projects/{projectId}/tasks"""

    def test_create_task_returns_201(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        pid = seeded_data["projects"][0][0]["projectId"]
        assignee_id = seeded_data["users"][0][0]["userId"]
        resp = api.request(
            "POST",
            f"/api/tenants/{tid}/projects/{pid}/tasks",
            json={
                "title": "New test task",
                "assigneeId": assignee_id,
                "priority": "low",
            },
        )
        assert resp.status_code == 201

    def test_create_task_response_fields(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        pid = seeded_data["projects"][0][0]["projectId"]
        assignee_id = seeded_data["users"][0][1]["userId"]
        resp = api.request(
            "POST",
            f"/api/tenants/{tid}/projects/{pid}/tasks",
            json={
                "title": "Field check task",
                "assigneeId": assignee_id,
                "priority": "high",
                "status": "in-progress",
            },
        )
        data = resp.json()
        assert "taskId" in data
        assert data["tenantId"] == tid
        assert data["projectId"] == pid
        assert data["title"] == "Field check task"
        assert data["assigneeId"] == assignee_id
        assert data["priority"] == "high"
        assert data["status"] == "in-progress"

    def test_create_task_default_status_is_todo(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        pid = seeded_data["projects"][0][0]["projectId"]
        assignee_id = seeded_data["users"][0][0]["userId"]
        resp = api.request(
            "POST",
            f"/api/tenants/{tid}/projects/{pid}/tasks",
            json={
                "title": "Default status task",
                "assigneeId": assignee_id,
                "priority": "medium",
            },
        )
        data = resp.json()
        assert data["status"] == "todo"


class TestListProjectTasks:
    """GET /api/tenants/{tenantId}/projects/{projectId}/tasks"""

    def test_list_tasks_returns_200(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        pid = seeded_data["projects"][0][0]["projectId"]
        resp = api.request("GET", f"/api/tenants/{tid}/projects/{pid}/tasks")
        assert resp.status_code == 200

    def test_list_tasks_returns_array(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        pid = seeded_data["projects"][0][0]["projectId"]
        data = api.request("GET", f"/api/tenants/{tid}/projects/{pid}/tasks").json()
        assert isinstance(data, list)

    def test_website_redesign_has_3_seeded_tasks(self, api, seeded_data):
        """Acme Corp > Website Redesign has 3 seeded tasks."""
        tid = seeded_data["tenants"][0]["tenantId"]
        pid = seeded_data["projects"][0][0]["projectId"]
        data = api.request("GET", f"/api/tenants/{tid}/projects/{pid}/tasks").json()
        assert len(data) >= 3

    def test_mobile_app_has_4_seeded_tasks(self, api, seeded_data):
        """Acme Corp > Mobile App has 4 seeded tasks."""
        tid = seeded_data["tenants"][0]["tenantId"]
        pid = seeded_data["projects"][0][1]["projectId"]
        data = api.request("GET", f"/api/tenants/{tid}/projects/{pid}/tasks").json()
        assert len(data) >= 4


class TestUserTasks:
    """GET /api/tenants/{tenantId}/users/{userId}/tasks"""

    def test_user_tasks_returns_200(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        uid = seeded_data["users"][0][1]["userId"]  # Bob Member
        resp = api.request("GET", f"/api/tenants/{tid}/users/{uid}/tasks")
        assert resp.status_code == 200

    def test_user_tasks_returns_array(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        uid = seeded_data["users"][0][1]["userId"]
        data = api.request("GET", f"/api/tenants/{tid}/users/{uid}/tasks").json()
        assert isinstance(data, list)

    def test_bob_has_tasks_across_projects(self, api, seeded_data):
        """
        Bob Member (user index 1 in Acme) is assigned:
        - Website Redesign: Design mockups, Implement frontend
        - Mobile App: Build auth module, Create API endpoints
        = at least 4 tasks total
        """
        tid = seeded_data["tenants"][0]["tenantId"]
        uid = seeded_data["users"][0][1]["userId"]
        data = api.request("GET", f"/api/tenants/{tid}/users/{uid}/tasks").json()
        assert len(data) >= 4

    def test_alice_has_tasks(self, api, seeded_data):
        """
        Alice Admin (user index 0 in Acme) is assigned:
        - Mobile App: Setup CI/CD, Design database schema
        = at least 2 tasks
        """
        tid = seeded_data["tenants"][0]["tenantId"]
        uid = seeded_data["users"][0][0]["userId"]
        data = api.request("GET", f"/api/tenants/{tid}/users/{uid}/tasks").json()
        assert len(data) >= 2

    def test_user_tasks_all_belong_to_user(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        uid = seeded_data["users"][0][1]["userId"]
        data = api.request("GET", f"/api/tenants/{tid}/users/{uid}/tasks").json()
        for task in data:
            assert task["assigneeId"] == uid


class TestQueryTasksByStatus:
    """GET /api/tenants/{tenantId}/tasks?status=X"""

    def test_query_by_status_returns_200(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        resp = api.request("GET", f"/api/tenants/{tid}/tasks", params={"status": "todo"})
        assert resp.status_code == 200

    def test_query_todo_tasks_in_acme(self, api, seeded_data):
        """
        Acme Corp has these 'todo' tasks:
        - Write content (Website Redesign)
        - Create API endpoints (Mobile App)
        = at least 2 'todo' tasks
        """
        tid = seeded_data["tenants"][0]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid}/tasks", params={"status": "todo"}).json()
        assert len(data) >= 2
        for task in data:
            assert task["status"] == "todo"

    def test_query_done_tasks_in_acme(self, api, seeded_data):
        """
        Acme Corp has these 'done' tasks:
        - Design mockups (Website Redesign)
        - Setup CI/CD (Mobile App)
        = at least 2 'done' tasks
        """
        tid = seeded_data["tenants"][0]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid}/tasks", params={"status": "done"}).json()
        assert len(data) >= 2
        for task in data:
            assert task["status"] == "done"

    def test_query_in_progress_tasks_in_acme(self, api, seeded_data):
        """
        Acme Corp 'in-progress' tasks:
        - Implement frontend
        - Build auth module
        = at least 2
        """
        tid = seeded_data["tenants"][0]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid}/tasks", params={"status": "in-progress"}).json()
        assert len(data) >= 2
        for task in data:
            assert task["status"] == "in-progress"

    def test_query_blocked_tasks_in_acme(self, api, seeded_data):
        """
        Acme Corp 'blocked' tasks:
        - Design database schema (Mobile App)
        = at least 1
        """
        tid = seeded_data["tenants"][0]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid}/tasks", params={"status": "blocked"}).json()
        assert len(data) >= 1
        for task in data:
            assert task["status"] == "blocked"


class TestTenantAnalytics:
    """GET /api/tenants/{tenantId}/analytics"""

    def test_analytics_returns_200(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        resp = api.request("GET", f"/api/tenants/{tid}/analytics")
        assert resp.status_code == 200

    def test_analytics_response_fields(self, api, seeded_data):
        tid = seeded_data["tenants"][0]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid}/analytics").json()
        assert "tenantId" in data
        assert "totalUsers" in data
        assert "totalProjects" in data
        assert "totalTasks" in data
        assert "tasksByStatus" in data
        assert "tasksByPriority" in data

    def test_acme_analytics_counts(self, api, seeded_data):
        """
        Acme Corp seeded data:
        - 3 users (Alice, Bob, Charlie)
        - 2 projects (Website Redesign, Mobile App)
        - 7 tasks (3 + 4)
        """
        tid = seeded_data["tenants"][0]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid}/analytics").json()
        assert data["totalUsers"] >= 3
        assert data["totalProjects"] >= 2
        assert data["totalTasks"] >= 7

    def test_acme_tasks_by_status_breakdown(self, api, seeded_data):
        """
        Acme Corp tasks by status:
        - todo: 2 (Write content, Create API endpoints)
        - in-progress: 2 (Implement frontend, Build auth module)
        - done: 2 (Design mockups, Setup CI/CD)
        - blocked: 1 (Design database schema)
        """
        tid = seeded_data["tenants"][0]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid}/analytics").json()
        status = data["tasksByStatus"]
        assert status.get("todo", 0) >= 2
        assert status.get("in-progress", 0) >= 2
        assert status.get("done", 0) >= 2
        assert status.get("blocked", 0) >= 1

    def test_acme_tasks_by_priority_breakdown(self, api, seeded_data):
        """
        Acme Corp tasks by priority:
        - low: 0
        - medium: 2 (Write content, Create API endpoints)
        - high: 4 (Design mockups, Implement frontend, Build auth module, Design database schema)
        - critical: 1 (Setup CI/CD)
        """
        tid = seeded_data["tenants"][0]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid}/analytics").json()
        priority = data["tasksByPriority"]
        assert priority.get("medium", 0) >= 2
        assert priority.get("high", 0) >= 4
        assert priority.get("critical", 0) >= 1


class TestTenantIsolation:
    """Verify strict data isolation between tenants."""

    def test_tenant_1_cannot_see_tenant_0_users(self, api, seeded_data):
        """Startup Inc should not see Acme Corp's users."""
        tid1 = seeded_data["tenants"][1]["tenantId"]
        users = api.request("GET", f"/api/tenants/{tid1}/users").json()
        acme_emails = ["alice@acme.com", "bob@acme.com", "charlie@acme.com"]
        for user in users:
            assert user.get("email") not in acme_emails, (
                f"Tenant isolation breach: Startup Inc returned Acme Corp user {user.get('email')}"
            )

    def test_tenant_0_cannot_see_tenant_1_projects(self, api, seeded_data):
        """Acme Corp should not see Startup Inc's projects."""
        tid0 = seeded_data["tenants"][0]["tenantId"]
        projects = api.request("GET", f"/api/tenants/{tid0}/projects").json()
        for proj in projects:
            assert proj["name"] != "MVP Launch", (
                "Tenant isolation breach: Acme Corp returned Startup Inc project"
            )

    def test_tenant_1_tasks_isolated(self, api, seeded_data):
        """Status query within Startup Inc should only return Startup tasks."""
        tid1 = seeded_data["tenants"][1]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid1}/tasks", params={"status": "done"}).json()
        acme_task_titles = [
            "Design mockups", "Setup CI/CD", "Implement frontend",
            "Write content", "Build auth module", "Create API endpoints",
            "Design database schema"
        ]
        for task in data:
            assert task["title"] not in acme_task_titles, (
                f"Tenant isolation breach: Startup Inc returned Acme Corp task '{task['title']}'"
            )

    def test_analytics_reflect_only_own_tenant(self, api, seeded_data):
        """Startup Inc analytics should not include Acme Corp data."""
        tid1 = seeded_data["tenants"][1]["tenantId"]
        data = api.request("GET", f"/api/tenants/{tid1}/analytics").json()
        # Startup Inc: 2 users, 1 project, 3 tasks
        assert data["totalUsers"] >= 2
        assert data["totalProjects"] >= 1
        assert data["totalTasks"] >= 3
        # Should NOT have Acme's 7+ tasks
        assert data["totalTasks"] <= 10, (
            "Tenant analytics returning too many tasks — possible isolation breach"
        )
