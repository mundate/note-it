"""Projects: belong to a team, outlive it, and carry their lists along when they move."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import NotFoundError
from app.main import create_app


def test_project_lifecycle(svc) -> None:  # noqa: ANN001
    team = svc.teams.create_team("Platform").id
    billing = svc.projects.create_project(team, "Billing", "Invoices v2", date(2026, 12, 15))
    assert (billing.team_id, billing.description, billing.deadline, billing.status, billing.daily_enabled) == (
        team, "Invoices v2", "2026-12-15", "active", False,
    )
    onboarding = svc.projects.create_project(team, "Onboarding")
    svc.projects.update_project(billing.id, status="inactive")
    # Active first, then done.
    assert [p.name for p in svc.projects.list_for_team(team)] == ["Onboarding", "Billing"]

    updated = svc.projects.update_project(onboarding.id, name="Welcome", deadline=date(2027, 1, 1), daily_enabled=True)
    assert (updated.name, updated.deadline, updated.daily_enabled) == ("Welcome", "2027-01-01", True)
    assert svc.projects.update_project(onboarding.id, deadline=None).deadline is None
    assert svc.projects.update_project(onboarding.id, description="").name == "Welcome"  # others untouched

    svc.projects.delete_project(billing.id)
    assert [p.name for p in svc.projects.list_for_team(team)] == ["Welcome"]


def test_projects_outlive_their_team_and_can_join_another(svc) -> None:  # noqa: ANN001
    a, b = svc.teams.create_team("A").id, svc.teams.create_team("B").id
    project = svc.projects.create_project(a, "P")
    lst = svc.todos.create_list("L", project_id=project.id)
    assert lst.team_id == a

    svc.projects.update_project(project.id, team_id=b)  # its lists move with it
    assert svc.todos.get_list(lst.id).team_id == b

    svc.teams.delete_team(b)
    assert svc.projects.get_project(project.id).team_id is None
    assert [p.id for p in svc.projects.list_teamless()] == [project.id]
    assert (svc.todos.get_list(lst.id).team_id, svc.todos.get_list(lst.id).project_id) == (None, project.id)

    svc.projects.update_project(project.id, team_id=a)
    assert svc.projects.list_teamless() == []
    assert svc.todos.get_list(lst.id).team_id == a


def test_missing_project_or_team(svc) -> None:  # noqa: ANN001
    team = svc.teams.create_team("T").id
    project = svc.projects.create_project(team, "P")
    for call, message in (
        (lambda: svc.projects.get_project(999), "Project not found"),
        (lambda: svc.projects.update_project(999, name="x"), "Project not found"),
        (lambda: svc.projects.delete_project(999), "Project not found"),
        (lambda: svc.projects.create_project(999, "x"), "Team not found"),
        (lambda: svc.projects.list_for_team(999), "Team not found"),
        (lambda: svc.projects.update_project(project.id, team_id=999), "Team not found"),
    ):
        with pytest.raises(NotFoundError, match=message):
            call()


def test_project_routes(client: TestClient) -> None:
    tid = client.post("/api/teams", json={"name": "Platform"}).json()["id"]
    base = f"/api/teams/{tid}/projects"
    for bad in ({"name": " "}, {"name": "x" * 101}, {}, {"name": "P", "deadline": "soon"}, {"name": "P", "deadline": "2026-02-31"},
                {"name": "P", "description": "x" * 2001}):
        res = client.post(base, json=bad)
        assert res.status_code == 400, bad
        assert "error" in res.json()
    assert client.post("/api/teams/999/projects", json={"name": "P"}).json() == {"error": "Team not found"}

    res = client.post(base, json={"name": "  Billing ", "deadline": "2026-12-15"})
    assert res.status_code == 201
    project = res.json()
    assert set(project) == {"id", "teamId", "name", "description", "deadline", "status", "dailyEnabled", "createdAt", "updatedAt"}
    assert (project["name"], project["deadline"], project["description"]) == ("Billing", "2026-12-15", "")
    pid = project["id"]

    assert [p["id"] for p in client.get(base).json()] == [pid]
    assert client.get(f"/api/projects/{pid}").json()["name"] == "Billing"
    assert client.get("/api/projects/999").json() == {"error": "Project not found"}
    assert client.get("/api/projects/teamless").json() == []

    patch = lambda body: client.patch(f"/api/projects/{pid}", json=body)  # noqa: E731
    assert patch({}).json() == {"error": "Nothing to update"}
    for bad in ({"name": None}, {"status": "paused"}, {"status": None}, {"dailyEnabled": "yes"}, {"dailyEnabled": None},
                {"deadline": "nope"}, {"teamId": 0}):
        assert patch(bad).status_code == 400, bad
    assert patch({"teamId": 999}).status_code == 404
    assert patch({"status": "inactive", "dailyEnabled": True, "deadline": None}).json()["status"] == "inactive"
    got = client.get(f"/api/projects/{pid}").json()
    assert (got["status"], got["dailyEnabled"], got["deadline"]) == ("inactive", True, None)
    assert patch({"teamId": None}).json()["teamId"] is None
    assert [p["id"] for p in client.get("/api/projects/teamless").json()] == [pid]

    res = client.delete(f"/api/projects/{pid}")
    assert res.status_code == 204 and res.content == b""
    assert client.delete(f"/api/projects/{pid}").status_code == 404


def test_openapi_project_schemas() -> None:
    schemas = create_app(":memory:").openapi()["components"]["schemas"]
    assert {"Project", "ProjectCreate", "ProjectPatch"} <= set(schemas)
    patch = schemas["ProjectPatch"]["properties"]
    assert patch["name"]["type"] == "string" and patch["dailyEnabled"]["type"] == "boolean"  # never null
    assert {t.get("type") for t in patch["teamId"]["anyOf"]} == {"integer", "null"}
