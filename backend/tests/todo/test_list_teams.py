"""Assigning todo lists to teams: optional, movable, and kept when a team is deleted."""

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import NotFoundError
from app.main import create_app
from app.team import TeamService
from app.todo import TodoService


@pytest.fixture
def services(svc) -> tuple[TodoService, TeamService]:  # noqa: ANN001
    return svc.todos, svc.teams


def test_lists_move_between_teams(services: tuple[TodoService, TeamService]) -> None:
    todos, teams = services
    platform, personal = teams.create_team("Platform"), teams.create_team("Personal")
    lst = todos.create_list("Sprint", team_id=platform.id)
    assert lst.team_id == platform.id

    assert todos.update_list(lst.id, team_id=personal.id).team_id == personal.id
    # Renaming alone leaves the team alone; team_id=None takes the list off its team.
    assert todos.update_list(lst.id, name="Sprint 2").team_id == personal.id
    assert todos.update_list(lst.id, team_id=None).team_id is None


def test_unknown_team_raises_not_found_and_changes_nothing(services: tuple[TodoService, TeamService]) -> None:
    todos, _ = services
    lst = todos.create_list("L")
    for call in (lambda: todos.create_list("L2", team_id=999), lambda: todos.update_list(lst.id, team_id=999)):
        with pytest.raises(NotFoundError, match="Team not found"):
            call()
    assert todos.get_list(lst.id).team_id is None
    assert [l.name for l in todos.list_lists()] == ["L"]


def test_deleting_a_team_keeps_its_lists_and_todos(services: tuple[TodoService, TeamService]) -> None:
    todos, teams = services
    platform = teams.create_team("Platform")
    lst = todos.create_list("Sprint", team_id=platform.id)
    todos.create_todo(lst.id, "ship it")
    teams.delete_team(platform.id)
    kept = todos.get_list(lst.id)
    assert (kept.team_id, kept.open_count) == (None, 1)


def test_list_lists_filters_by_team(services: tuple[TodoService, TeamService]) -> None:
    todos, teams = services
    a, b = teams.create_team("A"), teams.create_team("B")
    todos.create_list("a1", team_id=a.id)
    todos.create_list("none")
    todos.create_list("a2", team_id=a.id)
    todos.create_list("b1", team_id=b.id)
    assert [l.name for l in todos.list_lists(a.id)] == ["a1", "a2"]
    assert [l.name for l in todos.list_lists()] == ["a1", "none", "a2", "b1"]
    assert todos.list_lists(999) == []


def test_assigning_lists_to_teams_over_http(client: TestClient) -> None:
    tid = client.post("/api/teams", json={"name": "Platform"}).json()["id"]

    assert client.post("/api/todo-lists", json={"name": "L", "teamId": 999}).json() == {"error": "Team not found"}
    for bad in ("1", 0, -1, 1.5):
        assert client.post("/api/todo-lists", json={"name": "L", "teamId": bad}).status_code == 400, bad

    res = client.post("/api/todo-lists", json={"name": "Sprint", "teamId": tid})
    assert res.status_code == 201 and res.json()["teamId"] == tid
    lid = res.json()["id"]
    client.post("/api/todo-lists", json={"name": "Groceries"})

    assert [l["name"] for l in client.get("/api/todo-lists", params={"teamId": tid}).json()] == ["Sprint"]
    assert len(client.get("/api/todo-lists").json()) == 2

    assert client.patch(f"/api/todo-lists/{lid}", json={"teamId": 999}).json() == {"error": "Team not found"}
    assert client.patch(f"/api/todo-lists/{lid}", json={"teamId": None}).json()["teamId"] is None
    assert client.patch(f"/api/todo-lists/{lid}", json={"teamId": tid}).json()["teamId"] == tid

    client.delete(f"/api/teams/{tid}")
    assert client.get(f"/api/todo-lists/{lid}").json()["teamId"] is None


def test_openapi_list_team_fields() -> None:
    schemas = create_app(":memory:").openapi()["components"]["schemas"]
    # PATCH: `name?: string` (never null) and `teamId?: number | null` (null unassigns).
    patch = schemas["TodoListPatch"]["properties"]
    assert patch["name"]["type"] == "string"
    assert {t.get("type") for t in patch["teamId"]["anyOf"]} == {"integer", "null"}
