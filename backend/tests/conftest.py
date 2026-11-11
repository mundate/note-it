"""Shared fixtures: every service wired on one in-memory database, with a settable clock."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.db import open_db
from app.main import create_app
from app.project import ProjectRepo, ProjectService
from app.team import TeamRepo, TeamService
from app.todo import TodoRepo, TodoService


class Clock:
    """A settable "today" for daily lists."""

    def __init__(self, today: date = date(2026, 11, 9)) -> None:
        self.day = today

    def __call__(self) -> date:
        return self.day


@dataclass
class Services:
    teams: TeamService
    projects: ProjectService
    todos: TodoService
    clock: Clock


@pytest.fixture
def svc() -> Services:
    db = open_db(":memory:")
    clock = Clock()
    teams = TeamService(TeamRepo(db))
    projects = ProjectService(ProjectRepo(db), teams)
    return Services(teams, projects, TodoService(TodoRepo(db), teams, projects, today=clock), clock)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(":memory:")) as c:  # `with` runs the lifespan (opens the DB)
        yield c
