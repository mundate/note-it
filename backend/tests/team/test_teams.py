"""Teams on their own (assigning todo lists is in tests/todo/test_list_teams.py)."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.db import open_db
from app.core.exceptions import NotFoundError
from app.main import create_app
from app.team import TeamRepo, TeamService


@pytest.fixture
def service() -> TeamService:
    return TeamService(TeamRepo(open_db(":memory:")))


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(":memory:")) as c:
        yield c


def test_team_lifecycle(service: TeamService) -> None:
    platform = service.create_team("Platform")
    service.create_team("Personal")
    assert [t.name for t in service.list_teams()] == ["Platform", "Personal"]
    assert service.update_team(platform.id, name="Infra").name == "Infra"
    assert service.get_team(platform.id).name == "Infra"
    service.delete_team(platform.id)
    assert [t.name for t in service.list_teams()] == ["Personal"]


def test_missing_team_raises_not_found(service: TeamService) -> None:
    for call in (lambda: service.get_team(999), lambda: service.update_team(999, name="x"), lambda: service.delete_team(999)):
        with pytest.raises(NotFoundError, match="Team not found"):
            call()


def test_team_routes(client: TestClient) -> None:
    for bad in ({"name": "  "}, {"name": "x" * 101}, {}, {"name": 5}):
        res = client.post("/api/teams", json=bad)
        assert res.status_code == 400, bad
        assert "error" in res.json()

    res = client.post("/api/teams", json={"name": "  Platform  "})
    assert res.status_code == 201
    team = res.json()
    assert team["name"] == "Platform"
    assert set(team) == {"id", "name", "sprintStart", "sprintWeeks", "createdAt", "updatedAt"}

    tid = team["id"]
    assert [t["id"] for t in client.get("/api/teams").json()] == [tid]
    assert client.get(f"/api/teams/{tid}").json()["name"] == "Platform"
    assert client.get("/api/teams/999").json() == {"error": "Team not found"}
    assert client.get("/api/teams/abc").status_code == 404
    assert client.patch(f"/api/teams/{tid}", json={"name": ""}).status_code == 400
    assert client.patch("/api/teams/999", json={"name": "x"}).status_code == 404
    assert client.patch(f"/api/teams/{tid}", json={"name": "Infra"}).json()["name"] == "Infra"

    res = client.delete(f"/api/teams/{tid}")
    assert res.status_code == 204 and res.content == b""
    assert client.delete(f"/api/teams/{tid}").status_code == 404


def test_openapi_team_schemas() -> None:
    schemas = create_app(":memory:").openapi()["components"]["schemas"]
    assert {"Team", "TeamCreate", "TeamPatch"} <= set(schemas)
    assert set(schemas["Team"]["required"]) == {"id", "name", "sprintStart", "sprintWeeks", "createdAt", "updatedAt"}


def test_sprint_schedule(service: TeamService) -> None:
    from datetime import date

    from app.core.exceptions import AppError

    team = service.create_team("Platform")
    assert (team.sprint_start, team.sprint_weeks) == (None, None)
    set_ = service.update_team(team.id, sprint_start=date(2026, 11, 2), sprint_weeks=2)
    assert (set_.sprint_start, set_.sprint_weeks, set_.name) == ("2026-11-02", 2, "Platform")
    assert service.update_team(team.id, sprint_weeks=3).sprint_start == "2026-11-02"  # change one at a time
    assert service.update_team(team.id, name="Infra").sprint_weeks == 3  # a rename leaves it alone
    with pytest.raises(AppError, match="both"):
        service.update_team(team.id, sprint_weeks=None)
    cleared = service.update_team(team.id, sprint_start=None, sprint_weeks=None)
    assert (cleared.sprint_start, cleared.sprint_weeks) == (None, None)
    with pytest.raises(AppError, match="both"):
        service.update_team(team.id, sprint_start=date(2026, 11, 2))
    assert service.sprint_on(cleared, date(2026, 11, 10)) is None


def test_sprint_schedule_routes(client: TestClient) -> None:
    tid = client.post("/api/teams", json={"name": "Platform"}).json()["id"]
    patch = lambda body: client.patch(f"/api/teams/{tid}", json=body)  # noqa: E731
    assert patch({}).json() == {"error": "Nothing to update"}
    for bad in ({"name": None}, {"sprintWeeks": 0}, {"sprintWeeks": 9}, {"sprintWeeks": "2"}, {"sprintStart": "soon"},
                {"sprintStart": "2026-11-02"}):
        assert patch(bad).status_code == 400, bad
    res = patch({"sprintStart": "2026-11-02", "sprintWeeks": 2}).json()
    assert (res["sprintStart"], res["sprintWeeks"]) == ("2026-11-02", 2)
    assert patch({"sprintStart": None, "sprintWeeks": None}).json()["sprintWeeks"] is None
