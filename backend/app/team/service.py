"""Team rules. Raises domain errors from `app.core.exceptions`, never `HTTPException`."""

from datetime import date

from ..core.exceptions import AppError, NotFoundError
from .models import Team
from .repository import UNSET, TeamRepo, Unset
from .sprints import Sprint, sprint_on

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

    def update_team(
        self,
        team_id: int,
        *,
        name: str | None = None,
        sprint_start: date | None | Unset = UNSET,
        sprint_weeks: int | None | Unset = UNSET,
    ) -> Team:
        """Renames the team and/or sets its sprint schedule (start and weeks must end up both
        set or both empty)."""
        current = self.get_team(team_id)
        start = current.sprint_start if isinstance(sprint_start, Unset) else sprint_start
        weeks = current.sprint_weeks if isinstance(sprint_weeks, Unset) else sprint_weeks
        if (start is None) != (weeks is None):
            raise AppError("Set both the sprint start date and length, or neither")
        team = self.repo.update_team(team_id, name=name, sprint_start=sprint_start, sprint_weeks=sprint_weeks)
        if team is None:
            raise NotFoundError(TEAM_NOT_FOUND)
        return team

    def sprint_on(self, team: Team, day: date) -> Sprint | None:
        """The team's sprint that `day` falls in; None without a schedule or before it starts."""
        if team.sprint_start is None or team.sprint_weeks is None:
            return None
        return sprint_on(day, date.fromisoformat(team.sprint_start), team.sprint_weeks)

    def delete_team(self, team_id: int) -> None:
        """Deletes the team. Its todo lists (and later notes, diagrams) are kept, unassigned."""
        if not self.repo.delete_team(team_id):
            raise NotFoundError(TEAM_NOT_FOUND)
