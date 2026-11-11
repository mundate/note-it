"""Daily todo lists: opt-in per project, one list per day, unfinished todos move to today.
A team's daily view combines its active projects' daily lists."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import AppError, NotFoundError

MON, TUE, WED, FRI = date(2026, 11, 9), date(2026, 11, 10), date(2026, 11, 11), date(2026, 11, 13)


@pytest.fixture
def team(svc) -> int:  # noqa: ANN001
    return svc.teams.create_team("Platform").id


@pytest.fixture
def project(svc, team: int) -> int:  # noqa: ANN001
    p = svc.projects.create_project(team, "Billing")
    svc.projects.update_project(p.id, daily_enabled=True)
    return p.id


def texts(svc, list_id: int) -> list[str]:  # noqa: ANN001
    return [t.text for t in svc.todos.list_todos(list_id)]


def test_opening_today_creates_one_list_per_day(svc, project: int, team: int) -> None:  # noqa: ANN001
    mon = svc.todos.open_project_today(project)
    assert (mon.kind, mon.day, mon.project_id, mon.team_id, mon.name) == (
        "daily", "2026-11-09", project, team, "Daily · Mon, Nov 9, 2026",
    )
    assert svc.todos.open_project_today(project).id == mon.id


def test_unfinished_todos_move_to_today_and_finished_stay(svc, project: int) -> None:  # noqa: ANN001
    mon = svc.todos.open_project_today(project)
    a = svc.todos.create_todo(mon.id, "a")
    svc.todos.create_todo(mon.id, "b")
    svc.todos.create_todo(mon.id, "c")
    svc.todos.update_todo(mon.id, a.id, done=True)

    svc.clock.day = TUE
    tue = svc.todos.open_project_today(project)
    assert texts(svc, tue.id) == ["b", "c"] and texts(svc, mon.id) == ["a"]
    assert (tue.open_count, tue.done_count) == (2, 0)


def test_carried_todos_go_after_todays_and_keep_order(svc, project: int) -> None:  # noqa: ANN001
    mon = svc.todos.open_project_today(project)
    b, c = svc.todos.create_todo(mon.id, "b"), svc.todos.create_todo(mon.id, "c")
    svc.todos.reorder_todos(mon.id, [c.id, b.id])
    svc.clock.day = TUE
    tue = svc.todos.open_project_today(project)
    svc.todos.create_todo(tue.id, "new")
    svc.todos.create_todo(mon.id, "late")  # left unfinished on Monday after Tuesday exists
    svc.todos.open_project_today(project)
    assert texts(svc, tue.id) == ["c", "b", "new", "late"]
    assert svc.todos.list_todos(mon.id) == []


def test_gaps_and_several_earlier_days_collect_oldest_first(svc, project: int) -> None:  # noqa: ANN001
    svc.todos.create_todo(svc.todos.open_project_today(project).id, "from mon")
    svc.clock.day = WED
    svc.todos.create_todo(svc.todos.open_project_today(project).id, "from wed")
    mon = next(l for l in svc.todos.list_project_daily(project) if l.day == "2026-11-09")
    svc.todos.create_todo(mon.id, "mon again")
    svc.clock.day = FRI  # Thursday never opened
    fri = svc.todos.open_project_today(project)
    assert texts(svc, fri.id) == ["mon again", "from mon", "from wed"]
    assert [l.day for l in svc.todos.list_project_daily(project)] == ["2026-11-13", "2026-11-11", "2026-11-09"]


def test_daily_is_opt_in_and_can_be_turned_off(svc, team: int, project: int) -> None:  # noqa: ANN001
    off = svc.projects.create_project(team, "Off").id
    with pytest.raises(AppError, match="turned off"):
        svc.todos.open_project_today(off)

    mon = svc.todos.open_project_today(project)
    svc.todos.create_todo(mon.id, "carry me")
    svc.projects.update_project(project, daily_enabled=False)
    with pytest.raises(AppError, match="turned off"):
        svc.todos.open_project_today(project)
    assert [l.id for l in svc.todos.list_project_daily(project)] == [mon.id]  # history kept

    svc.clock.day = WED
    svc.projects.update_project(project, daily_enabled=True)
    assert texts(svc, svc.todos.open_project_today(project).id) == ["carry me"]


def test_projects_have_separate_daily_lists(svc, team: int, project: int) -> None:  # noqa: ANN001
    other = svc.projects.create_project(team, "Other")
    svc.projects.update_project(other.id, daily_enabled=True)
    svc.todos.create_todo(svc.todos.open_project_today(project).id, "mine")
    svc.todos.create_todo(svc.todos.open_project_today(other.id).id, "theirs")
    svc.clock.day = TUE
    assert texts(svc, svc.todos.open_project_today(project).id) == ["mine"]
    assert texts(svc, svc.todos.open_project_today(other.id).id) == ["theirs"]


def test_team_view_combines_active_enabled_projects(svc, team: int, project: int) -> None:  # noqa: ANN001
    second = svc.projects.create_project(team, "Second").id
    svc.projects.update_project(second, daily_enabled=True)
    svc.projects.create_project(team, "No daily")
    done = svc.projects.create_project(team, "Done").id
    svc.projects.update_project(done, daily_enabled=True, status="done")

    today = svc.todos.open_team_today(team)
    assert [l.project_id for l in today] == [project, second]
    svc.todos.create_todo(today[0].id, "carry")

    svc.clock.day = TUE
    tue = svc.todos.open_team_today(team)
    assert texts(svc, tue[0].id) == ["carry"]
    assert svc.todos.team_daily_days(team) == ["2026-11-10", "2026-11-09"]
    assert [l.project_id for l in svc.todos.team_daily(team, MON)] == [project, second]
    assert svc.todos.team_daily(team, WED) == []


def test_daily_lists_are_left_out_and_locked(svc, team: int, project: int) -> None:  # noqa: ANN001
    daily = svc.todos.open_project_today(project)
    normal = svc.todos.create_list("Backlog", project_id=project)
    assert [l.id for l in svc.todos.list_lists()] == [normal.id]
    assert [l.id for l in svc.todos.list_lists(project_id=project)] == [normal.id]
    for call in (
        lambda: svc.todos.update_list(daily.id, name="x"),
        lambda: svc.todos.update_list(daily.id, project_id=None),
        lambda: svc.todos.update_list(daily.id, team_id=None),
    ):
        with pytest.raises(AppError, match="can't be renamed or moved"):
            call()
    with pytest.raises(AppError, match="can't be deleted"):
        svc.todos.delete_list(daily.id)
    t = svc.todos.create_todo(daily.id, "a")
    svc.todos.update_todo(daily.id, t.id, done=True)
    svc.todos.delete_todo(daily.id, t.id)


def test_teamless_project_daily_keeps_working(svc, team: int, project: int) -> None:  # noqa: ANN001
    svc.todos.create_todo(svc.todos.open_project_today(project).id, "keep going")
    svc.teams.delete_team(team)
    svc.clock.day = TUE
    tue = svc.todos.open_project_today(project)
    assert (tue.team_id, texts(svc, tue.id)) == (None, ["keep going"])


def test_deleting_the_project_deletes_its_daily_lists(svc, project: int) -> None:  # noqa: ANN001
    daily = svc.todos.open_project_today(project)
    svc.projects.delete_project(project)
    with pytest.raises(NotFoundError):
        svc.todos.get_list(daily.id)


def test_unknown_ids(svc) -> None:  # noqa: ANN001
    for call, message in (
        (lambda: svc.todos.open_project_today(999), "Project not found"),
        (lambda: svc.todos.list_project_daily(999), "Project not found"),
        (lambda: svc.todos.open_team_today(999), "Team not found"),
        (lambda: svc.todos.team_daily_days(999), "Team not found"),
        (lambda: svc.todos.team_daily(999, MON), "Team not found"),
    ):
        with pytest.raises(NotFoundError, match=message):
            call()


# ---------- routes ----------


def test_daily_routes(client: TestClient) -> None:
    from tests.conftest import Clock

    clock = Clock(MON)
    client.app.state.todo_service.today = clock  # type: ignore[attr-defined]
    tid = client.post("/api/teams", json={"name": "Platform"}).json()["id"]
    pid = client.post(f"/api/teams/{tid}/projects", json={"name": "Billing"}).json()["id"]

    assert client.post(f"/api/projects/{pid}/daily/today").json() == {"error": "This project's daily list is turned off"}
    client.patch(f"/api/projects/{pid}", json={"dailyEnabled": True})
    mon = client.post(f"/api/projects/{pid}/daily/today").json()
    assert (mon["kind"], mon["day"], mon["projectId"]) == ("daily", "2026-11-09", pid)
    client.post(f"/api/todo-lists/{mon['id']}/todos", json={"text": "carry me"})

    clock.day = TUE
    [tue] = client.post(f"/api/teams/{tid}/daily/today").json()
    assert (tue["day"], tue["openCount"]) == ("2026-11-10", 1)
    assert client.get(f"/api/teams/{tid}/daily/days").json() == ["2026-11-10", "2026-11-09"]
    assert [l["id"] for l in client.get(f"/api/teams/{tid}/daily/2026-11-09").json()] == [mon["id"]]
    assert client.get(f"/api/teams/{tid}/daily/not-a-day").status_code == 404
    assert [l["day"] for l in client.get(f"/api/projects/{pid}/daily").json()] == ["2026-11-10", "2026-11-09"]
    assert client.get("/api/todo-lists").json() == []

    assert client.patch(f"/api/todo-lists/{tue['id']}", json={"name": "x"}).status_code == 400
    assert client.delete(f"/api/todo-lists/{tue['id']}").json() == {"error": "Daily lists can't be deleted"}
    assert client.post("/api/projects/999/daily/today").status_code == 404
    assert client.post("/api/teams/999/daily/today").status_code == 404
