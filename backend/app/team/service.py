"""Team rules. Raises domain errors from `app.core.exceptions`, never `HTTPException`."""

from ..core.exceptions import NotFoundError
from .models import Team
from .repository import TeamRepo

TEAM_NOT_FOUND = "Team not found"


class TeamService:
    def __init__(self, repo: TeamRepo) -> None:
        self.repo = repo

    def list_teams(self) -> list[Team]:
        return self.repo.list_teams()

    def get_team(self, team_id: int) -> Team:
        """Also how other features check a team exists before assigning something to it."""
        team = self.repo.get_team(team_id)
        if team is None:
            raise NotFoundError(TEAM_NOT_FOUND)
        return team

    def create_team(self, name: str) -> Team:
        return self.repo.create_team(name)

    def rename_team(self, team_id: int, name: str) -> Team:
        team = self.repo.rename_team(team_id, name)
        if team is None:
            raise NotFoundError(TEAM_NOT_FOUND)
        return team

    def delete_team(self, team_id: int) -> None:
        """Deletes the team. Its todo lists (and later notes, diagrams) are kept, unassigned."""
        if not self.repo.delete_team(team_id):
            raise NotFoundError(TEAM_NOT_FOUND)
