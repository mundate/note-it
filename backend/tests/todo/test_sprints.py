"""Sprint todo lists: every active project in a team with a sprint schedule has one list
per sprint; unfinished todos move into the current sprint."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import AppError, NotFoundError

START = date(2026, 11, 2)  # Monday; 2-week sprints: S1 Nov 2-15, S2 Nov 16-29, S3 Nov 30-Dec 13


@pytest.fixture
def team(svc) -> int:  # noqa: ANN001
    t = svc.teams.create_team("Platform")
    svc.teams.update_team(t.id, sprint_start=START, sprint_weeks=2)
    svc.clock.day = date(2026, 11, 10)  # in sprint 1
    return t.id


@pytest.fixture
def project(svc, team: int) -> int:  # noqa: ANN001
    return svc.projects.create_project(team, "Billing").id


def texts(svc, list_id: int) -> list[str]:  # noqa: ANN001
    return [t.text for t in svc.todos.list_todos(list_id)]


def test_every_active_project_has_the_current_sprint(svc, team: int, project: int) -> None:  # noqa: ANN001
    s1 = svc.todos.open_project_sprint(project)
    assert (s1.kind, s1.day, s1.end_day, s1.team_id, s1.name) == (
        "sprint", "2026-11-02", "2026-11-15", team, "Sprint 1 · Nov 2 – Nov 15, 2026",
    )
    assert svc.todos.open_project_sprint(project).id == s1.id
    svc.clock.day = date(2026, 11, 15)  # last day: still sprint 1
    assert svc.todos.open_project_sprint(project).id == s1.id


def test_unfinished_todos_move_into_the_next_sprint(svc, team: int, project: int) -> None:  # noqa: ANN001
    s1 = svc.todos.open_project_sprint(project)
    a = svc.todos.create_todo(s1.id, "a")
    svc.todos.create_todo(s1.id, "b")
    svc.todos.create_todo(s1.id, "c")
    svc.todos.update_todo(s1.id, a.id, done=True)

    svc.clock.day = date(2026, 11, 16)
    s2 = svc.todos.open_project_sprint(project)
    assert (s2.day, s2.name) == ("2026-11-16", "Sprint 2 · Nov 16 – Nov 29, 2026")
    assert texts(svc, s2.id) == ["b", "c"] and texts(svc, s1.id) == ["a"]

    svc.clock.day = date(2026, 12, 20)  # sprint 4: sprint 3 never opened
    s4 = svc.todos.open_project_sprint(project)
    assert s4.name.startswith("Sprint 4 ") and texts(svc, s4.id) == ["b", "c"]
    assert [l.day for l in svc.todos.list_project_sprints(project)] == ["2026-12-14", "2026-11-16", "2026-11-02"]


def test_changing_the_schedule_mid_sprint_carries_everything(svc, team: int, project: int) -> None:  # noqa: ANN001
    s1 = svc.todos.open_project_sprint(project)
    svc.todos.create_todo(s1.id, "carry me")
    # Move the schedule back a week: sprints now run Oct 26-Nov 8, Nov 9-22, so today
    # (Nov 10) is in a sprint that started Nov 9, a different period from the open one.
    svc.teams.update_team(team, sprint_start=date(2026, 10, 26))
    moved = svc.todos.open_project_sprint(project)
    assert (moved.day, moved.name) == ("2026-11-09", "Sprint 2 · Nov 9 – Nov 22, 2026")
    assert texts(svc, moved.id) == ["carry me"]
    assert svc.todos.list_todos(s1.id) == []


def test_shifting_the_schedule_by_whole_sprints_renames_the_open_sprint(svc, team: int, project: int) -> None:  # noqa: ANN001
    s1 = svc.todos.open_project_sprint(project)
    svc.teams.update_team(team, sprint_start=date(2026, 10, 19))  # two weeks earlier: same boundaries
    renumbered = svc.todos.open_project_sprint(project)
    assert renumbered.id == s1.id
    assert renumbered.name == "Sprint 2 · Nov 2 – Nov 15, 2026"
    svc.teams.update_team(team, sprint_weeks=3, sprint_start=date(2026, 11, 2))  # same start, longer
    longer = svc.todos.open_project_sprint(project)
    assert (longer.id, longer.end_day, longer.name) == (s1.id, "2026-11-22", "Sprint 1 · Nov 2 – Nov 22, 2026")


def test_when_there_is_no_current_sprint(svc, team: int, project: int) -> None:  # noqa: ANN001
    svc.todos.create_todo(svc.todos.open_project_sprint(project).id, "x")

    svc.projects.update_project(project, status="inactive")
    with pytest.raises(AppError, match="inactive"):
        svc.todos.open_project_sprint(project)
    assert len(svc.todos.list_project_sprints(project)) == 1  # history kept
    assert svc.todos.open_team_sprint(team) == []
    svc.projects.update_project(project, status="active")
    svc.clock.day = date(2026, 11, 20)
    assert texts(svc, svc.todos.open_project_sprint(project).id) == ["x"]  # resumes, carrying over

    svc.teams.update_team(team, sprint_start=None, sprint_weeks=None)
    with pytest.raises(AppError, match="no sprint schedule"):
        svc.todos.open_project_sprint(project)
    assert svc.todos.open_team_sprint(team) == []

    svc.teams.update_team(team, sprint_start=date(2027, 1, 4), sprint_weeks=2)
    with pytest.raises(AppError, match="hasn't started"):
        svc.todos.open_project_sprint(project)

    teamless = svc.projects.create_project(team, "Teamless")
    svc.projects.update_project(teamless.id, team_id=None)
    with pytest.raises(AppError, match="no sprint schedule"):
        svc.todos.open_project_sprint(teamless.id)


def test_team_view_has_every_active_project(svc, team: int, project: int) -> None:  # noqa: ANN001
    second = svc.projects.create_project(team, "Second").id
    paused = svc.projects.create_project(team, "Paused").id
    svc.projects.update_project(paused, status="inactive")
    lists = svc.todos.open_team_sprint(team)
    assert [l.project_id for l in lists] == [project, second]
    assert svc.todos.team_sprint_starts(team) == ["2026-11-02"]
    assert [l.project_id for l in svc.todos.team_sprint(team, START)] == [project, second]
    assert svc.todos.team_sprint(team, date(2026, 11, 16)) == []


def test_sprint_lists_are_left_out_and_locked(svc, team: int, project: int) -> None:  # noqa: ANN001
    sprint = svc.todos.open_project_sprint(project)
    normal = svc.todos.create_list("Backlog", project_id=project)
    assert [l.id for l in svc.todos.list_lists(project_id=project)] == [normal.id]
    with pytest.raises(AppError, match="Sprint lists can't be renamed or moved"):
        svc.todos.update_list(sprint.id, name="x")
    with pytest.raises(AppError, match="Sprint lists can't be deleted"):
        svc.todos.delete_list(sprint.id)
    t = svc.todos.create_todo(sprint.id, "a")
    svc.todos.update_todo(sprint.id, t.id, done=True)
    # Daily and sprint lists of the same project don't mix.
    svc.projects.update_project(project, daily_enabled=True)
    daily = svc.todos.open_project_today(project)
    assert daily.kind == "daily" and texts(svc, daily.id) == []

    svc.projects.delete_project(project)
    with pytest.raises(NotFoundError):
        svc.todos.get_list(sprint.id)


def test_unknown_ids(svc) -> None:  # noqa: ANN001
    for call, message in (
        (lambda: svc.todos.open_project_sprint(999), "Project not found"),
        (lambda: svc.todos.list_project_sprints(999), "Project not found"),
        (lambda: svc.todos.open_team_sprint(999), "Team not found"),
        (lambda: svc.todos.team_sprint_starts(999), "Team not found"),
        (lambda: svc.todos.team_sprint(999, START), "Team not found"),
    ):
        with pytest.raises(NotFoundError, match=message):
            call()


def test_sprint_routes(client: TestClient) -> None:
    from tests.conftest import Clock

    clock = Clock(date(2026, 11, 10))
    client.app.state.todo_service.today = clock  # type: ignore[attr-defined]
    tid = client.post("/api/teams", json={"name": "Platform"}).json()["id"]
    pid = client.post(f"/api/teams/{tid}/projects", json={"name": "Billing"}).json()["id"]

    assert client.post(f"/api/projects/{pid}/sprints/current").json() == {"error": "This project's team has no sprint schedule"}
    assert client.post(f"/api/teams/{tid}/sprints/current").json() == []
    client.patch(f"/api/teams/{tid}", json={"sprintStart": "2026-11-02", "sprintWeeks": 2})
    s1 = client.post(f"/api/projects/{pid}/sprints/current").json()
    assert (s1["kind"], s1["day"], s1["endDay"]) == ("sprint", "2026-11-02", "2026-11-15")
    client.post(f"/api/todo-lists/{s1['id']}/todos", json={"text": "carry me"})

    clock.day = date(2026, 11, 16)
    [s2] = client.post(f"/api/teams/{tid}/sprints/current").json()
    assert (s2["day"], s2["openCount"]) == ("2026-11-16", 1)
    assert client.get(f"/api/teams/{tid}/sprints/starts").json() == ["2026-11-16", "2026-11-02"]
    assert [l["id"] for l in client.get(f"/api/teams/{tid}/sprints/2026-11-02").json()] == [s1["id"]]
    assert [l["day"] for l in client.get(f"/api/projects/{pid}/sprints").json()] == ["2026-11-16", "2026-11-02"]
    assert client.get("/api/todo-lists").json() == []
    assert client.delete(f"/api/todo-lists/{s2['id']}").json() == {"error": "Sprint lists can't be deleted"}
