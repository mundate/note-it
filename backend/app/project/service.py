"""Project rules. Raises domain errors from `app.core.exceptions`, never `HTTPException`."""

from datetime import date

from ..core.exceptions import NotFoundError
from ..team import TeamService
from .models import Project
from .repository import UNSET, ProjectRepo, Unset

PROJECT_NOT_FOUND = "Project not found"


class ProjectService:
    def __init__(self, repo: ProjectRepo, teams: TeamService) -> None:
        self.repo = repo
        self.teams = teams

    def list_for_team(self, team_id: int) -> list[Project]:
        self.teams.get_team(team_id)
        return self.repo.list_projects(team_id)

    def list_teamless(self) -> list[Project]:
        return self.repo.list_projects(None)

    def get_project(self, project_id: int) -> Project:
        """Also how other features check a project exists before assigning something to it."""
        project = self.repo.get_project(project_id)
        if project is None:
            raise NotFoundError(PROJECT_NOT_FOUND)
        return project

    def create_project(self, team_id: int, name: str, description: str = "", deadline: date | None = None) -> Project:
        self.teams.get_team(team_id)
        return self.repo.create_project(team_id, name, description, deadline)

    def update_project(self, project_id: int, *, team_id: int | None | Unset = UNSET, **fields: object) -> Project:
        self.get_project(project_id)  # a missing project wins over a missing team
        if isinstance(team_id, int):
            self.teams.get_team(team_id)
        project = self.repo.update_project(project_id, team_id=team_id, **fields)  # type: ignore[arg-type]
        if project is None:
            raise NotFoundError(PROJECT_NOT_FOUND)
        return project

    def delete_project(self, project_id: int) -> None:
        """Deletes the project and all of its todo lists (daily lists included)."""
        if not self.repo.delete_project(project_id):
            raise NotFoundError(PROJECT_NOT_FOUND)
