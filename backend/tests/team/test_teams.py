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
    assert service.rename_team(platform.id, "Infra").name == "Infra"
    assert service.get_team(platform.id).name == "Infra"
    service.delete_team(platform.id)
    assert [t.name for t in service.list_teams()] == ["Personal"]


def test_missing_team_raises_not_found(service: TeamService) -> None:
    for call in (lambda: service.get_team(999), lambda: service.rename_team(999, "x"), lambda: service.delete_team(999)):
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
    assert set(team) == {"id", "name", "createdAt", "updatedAt"}

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
    assert set(schemas["Team"]["required"]) == {"id", "name", "createdAt", "updatedAt"}
