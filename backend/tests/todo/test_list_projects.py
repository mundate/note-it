"""Putting todo lists in projects: the project decides the team; deleting it deletes them."""

from fastapi.testclient import TestClient
import pytest

from app.core.exceptions import AppError, NotFoundError


@pytest.fixture
def setup(svc):  # noqa: ANN001, ANN201
    a, b = svc.teams.create_team("A").id, svc.teams.create_team("B").id
    return svc, a, b, svc.projects.create_project(a, "PA").id, svc.projects.create_project(b, "PB").id


def test_a_project_puts_the_list_in_its_team(setup) -> None:  # noqa: ANN001
    svc, a, b, pa, pb = setup
    lst = svc.todos.create_list("L", project_id=pa)
    assert (lst.team_id, lst.project_id) == (a, pa)
    assert svc.todos.create_list("L2", team_id=a, project_id=pa).project_id == pa
    with pytest.raises(AppError, match="different team"):
        svc.todos.create_list("L3", team_id=b, project_id=pa)
    with pytest.raises(NotFoundError, match="Project not found"):
        svc.todos.create_list("L4", project_id=999)

    # Moving to another project moves teams too; a mismatched explicit team is rejected.
    assert (svc.todos.update_list(lst.id, project_id=pb).team_id) == b
    with pytest.raises(AppError, match="different team"):
        svc.todos.update_list(lst.id, project_id=pa, team_id=b)
    with pytest.raises(AppError, match="different team"):
        svc.todos.update_list(lst.id, project_id=pa, team_id=None)


def test_changing_team_leaves_the_project_and_null_takes_it_out(setup) -> None:  # noqa: ANN001
    svc, a, b, pa, _ = setup
    lst = svc.todos.create_list("L", project_id=pa)
    assert svc.todos.update_list(lst.id, name="L!").project_id == pa  # rename keeps it
    assert svc.todos.update_list(lst.id, team_id=a).project_id == pa  # same team keeps it
    moved = svc.todos.update_list(lst.id, team_id=b)
    assert (moved.team_id, moved.project_id) == (b, None)

    lst2 = svc.todos.create_list("L2", project_id=pa)
    out = svc.todos.update_list(lst2.id, project_id=None)
    assert (out.team_id, out.project_id) == (a, None)  # stays in the team
    gone = svc.todos.update_list(svc.todos.create_list("L3", project_id=pa).id, team_id=None)
    assert (gone.team_id, gone.project_id) == (None, None)


def test_filters(setup) -> None:  # noqa: ANN001
    svc, a, _, pa, _ = setup
    svc.todos.create_list("in project", project_id=pa)
    svc.todos.create_list("team only", team_id=a)
    svc.todos.create_list("nowhere")
    names = lambda ls: [l.name for l in ls]  # noqa: E731
    assert names(svc.todos.list_lists(a)) == ["in project", "team only"]
    assert names(svc.todos.list_lists(a, None)) == ["team only"]
    assert names(svc.todos.list_lists(project_id=pa)) == ["in project"]
    assert names(svc.todos.list_lists(project_id=None)) == ["team only", "nowhere"]


def test_deleting_a_project_deletes_its_lists_but_deleting_the_team_does_not(setup) -> None:  # noqa: ANN001
    svc, a, _, pa, _ = setup
    doomed = svc.todos.create_list("doomed", project_id=pa)
    svc.todos.create_todo(doomed.id, "x")
    other = svc.projects.create_project(a, "Other")
    kept = svc.todos.create_list("kept", project_id=other.id)

    svc.projects.delete_project(pa)
    with pytest.raises(NotFoundError):
        svc.todos.get_list(doomed.id)

    svc.teams.delete_team(a)
    survivor = svc.todos.get_list(kept.id)
    assert (survivor.team_id, survivor.project_id) == (None, other.id)


def test_list_project_routes(client: TestClient) -> None:
    tid = client.post("/api/teams", json={"name": "A"}).json()["id"]
    pid = client.post(f"/api/teams/{tid}/projects", json={"name": "P"}).json()["id"]
    res = client.post("/api/todo-lists", json={"name": "L", "projectId": pid})
    assert res.status_code == 201 and (res.json()["teamId"], res.json()["projectId"]) == (tid, pid)
    lid = res.json()["id"]
    client.post("/api/todo-lists", json={"name": "Loose", "teamId": tid})

    assert client.post("/api/todo-lists", json={"name": "L", "projectId": 999}).json() == {"error": "Project not found"}
    assert [l["name"] for l in client.get("/api/todo-lists", params={"projectId": pid}).json()] == ["L"]
    assert [l["name"] for l in client.get("/api/todo-lists", params={"teamId": tid, "noProject": "true"}).json()] == ["Loose"]
    assert client.patch(f"/api/todo-lists/{lid}", json={"projectId": None}).json()["projectId"] is None

    client.patch(f"/api/todo-lists/{lid}", json={"projectId": pid})
    client.delete(f"/api/projects/{pid}")
    assert client.get(f"/api/todo-lists/{lid}").status_code == 404
