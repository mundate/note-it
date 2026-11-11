"""Todo business logic, between the routes (HTTP) and the repository (SQL).

Rules live here: what counts as "not found", which team a list's project puts it in, the
daily-list rules, and anything that combines several repository calls. Raises domain
errors from `app.core.exceptions`; never `HTTPException`.
"""

from collections.abc import Callable
from datetime import date

from ..core.exceptions import AppError, NotFoundError
from ..project import ProjectService
from ..team import TeamService
from ..team.sprints import Sprint, sprint_name
from .models import Todo, TodoList
from .repository import UNSET, TodoRepo, Unset

LIST_NOT_FOUND = "Todo list not found"
NO_SCHEDULE = "This project's team has no sprint schedule"
DAILY_OFF = "This project's daily list is turned off"
WRONG_TEAM = "The project belongs to a different team"
TODO_NOT_FOUND = "Todo not found"


class TodoService:
    def __init__(
        self,
        repo: TodoRepo,
        teams: TeamService,
        projects: ProjectService,
        today: Callable[[], date] = date.today,
    ) -> None:
        self.repo = repo
        self.teams = teams  # to check a team exists before assigning a list to it
        self.projects = projects  # same, for projects
        # "Today" for daily lists: the server's local date. Tests swap in a fixed clock.
        self.today = today

    # ---------- lists ----------

    def list_lists(self, team_id: int | None = None, project_id: int | None | Unset = UNSET) -> list[TodoList]:
        """Standard lists, optionally one team's and/or one project's (`project_id=None`:
        lists not in a project). Unknown ids just give an empty list."""
        return self.repo.list_lists(team_id, project_id)

    def get_list(self, list_id: int) -> TodoList:
        list_ = self.repo.get_list(list_id)
        if list_ is None:
            raise NotFoundError(LIST_NOT_FOUND)
        return list_

    def _placement(
        self, team_id: int | None | Unset, project_id: int | None | Unset, current: TodoList | None = None
    ) -> tuple[int | None | Unset, int | None | Unset]:
        """Resolves which team and project a list ends up in. A project decides the team; a
        team change alone drops a project from another team."""
        if isinstance(project_id, int):
            project = self.projects.get_project(project_id)
            if isinstance(team_id, int) and team_id != project.team_id:
                raise AppError(WRONG_TEAM)
            if team_id is None and project.team_id is not None:  # explicitly "no team"
                raise AppError(WRONG_TEAM)
            return project.team_id, project_id
        if isinstance(team_id, int):
            self.teams.get_team(team_id)
        if not isinstance(team_id, Unset) and isinstance(project_id, Unset) and current and current.project_id:
            if team_id != current.team_id:
                project_id = None  # moving teams leaves the project behind
        return team_id, project_id

    def create_list(self, name: str, team_id: int | None = None, project_id: int | None = None) -> TodoList:
        # On create, a missing team just means "not given": the project (if any) decides it.
        team, project = self._placement(UNSET if team_id is None else team_id, project_id)
        return self.repo.create_list(
            name, None if isinstance(team, Unset) else team, None if isinstance(project, Unset) else project
        )

    def update_list(
        self,
        list_id: int,
        *,
        name: str | None = None,
        team_id: int | None | Unset = UNSET,
        project_id: int | None | Unset = UNSET,
    ) -> TodoList:
        """Renames a list and/or moves it to a team / project (None takes it off)."""
        current = self.get_list(list_id)  # a missing list wins over a missing team or project
        if current.kind != "standard":
            raise AppError(f"{current.kind.capitalize()} lists can't be renamed or moved")
        team_id, project_id = self._placement(team_id, project_id, current)
        list_ = self.repo.update_list(list_id, name=name, team_id=team_id, project_id=project_id)
        if list_ is None:
            raise NotFoundError(LIST_NOT_FOUND)
        return list_

    def delete_list(self, list_id: int) -> None:
        """Deletes the list and all of its todos."""
        kind = self.get_list(list_id).kind
        if kind != "standard":
            raise AppError(f"{kind.capitalize()} lists can't be deleted")
        if not self.repo.delete_list(list_id):
            raise NotFoundError(LIST_NOT_FOUND)

    # ---------- daily lists ----------
    # A project's daily list (opt-in) is one list per day. Opening today's creates it if
    # needed and moves every unfinished todo from earlier days onto it. A team's daily view
    # combines its active projects' daily lists.

    def _open_daily(self, project_id: int, team_id: int | None) -> TodoList:
        today = self.today()
        name = f"Daily · {today:%a, %b} {today.day}, {today.year}"
        return self.repo.open_period("daily", project_id, team_id, today, today, name)

    def open_project_today(self, project_id: int) -> TodoList:
        project = self.projects.get_project(project_id)
        if not project.daily_enabled:
            raise AppError(DAILY_OFF)
        return self._open_daily(project.id, project.team_id)

    def list_project_daily(self, project_id: int) -> list[TodoList]:
        """The project's daily lists, newest day first (kept even after it's turned off)."""
        self.projects.get_project(project_id)
        return self.repo.list_periods("daily", project_id)

    def open_team_today(self, team_id: int) -> list[TodoList]:
        """Today's daily list for each of the team's active projects with daily turned on."""
        return [
            self._open_daily(p.id, team_id)
            for p in self.projects.list_for_team(team_id)
            if p.status == "active" and p.daily_enabled
        ]

    def team_daily_days(self, team_id: int) -> list[str]:
        self.teams.get_team(team_id)
        return self.repo.team_period_starts("daily", team_id)

    def team_daily(self, team_id: int, day: date) -> list[TodoList]:
        self.teams.get_team(team_id)
        return self.repo.team_period_lists("daily", team_id, day)

    # ---------- sprint lists ----------
    # Every active project in a team with a sprint schedule has one list per sprint (no
    # opt-in). Opening the current sprint creates it if needed and moves every unfinished
    # todo from the project's other sprints onto it.

    def _current_sprint(self, team_id: int) -> Sprint:
        team = self.teams.get_team(team_id)
        if team.sprint_start is None:
            raise AppError(NO_SCHEDULE)
        sprint = self.teams.sprint_on(team, self.today())
        if sprint is None:
            raise AppError(f"The first sprint hasn't started yet (it starts {team.sprint_start})")
        return sprint

    def _open_sprint(self, project_id: int, team_id: int, sprint: Sprint) -> TodoList:
        return self.repo.open_period("sprint", project_id, team_id, sprint.start, sprint.end, sprint_name(sprint))

    def open_project_sprint(self, project_id: int) -> TodoList:
        """The project's list for the current sprint of its team."""
        project = self.projects.get_project(project_id)
        if project.team_id is None:
            raise AppError(NO_SCHEDULE)
        if project.status != "active":
            raise AppError("This project is inactive, so it has no current sprint")
        return self._open_sprint(project.id, project.team_id, self._current_sprint(project.team_id))

    def list_project_sprints(self, project_id: int) -> list[TodoList]:
        """The project's sprint lists, newest first (kept while it's inactive or teamless)."""
        self.projects.get_project(project_id)
        return self.repo.list_periods("sprint", project_id)

    def open_team_sprint(self, team_id: int) -> list[TodoList]:
        """The current sprint's list for each of the team's active projects; empty if the team
        has no schedule or its first sprint hasn't started."""
        team = self.teams.get_team(team_id)
        sprint = self.teams.sprint_on(team, self.today())
        if sprint is None:
            return []
        return [self._open_sprint(p.id, team_id, sprint) for p in self.projects.list_for_team(team_id) if p.status == "active"]

    def team_sprint_starts(self, team_id: int) -> list[str]:
        self.teams.get_team(team_id)
        return self.repo.team_period_starts("sprint", team_id)

    def team_sprint(self, team_id: int, start: date) -> list[TodoList]:
        self.teams.get_team(team_id)
        return self.repo.team_period_lists("sprint", team_id, start)

    # ---------- todos ----------
    # Every todo operation names its list. A todo id that exists in a different list is
    # "not found", so a list's URL only ever reaches its own todos.

    def list_todos(self, list_id: int) -> list[Todo]:
        self.get_list(list_id)
        return self.repo.list_todos(list_id)

    def create_todo(self, list_id: int, text: str) -> Todo:
        self.get_list(list_id)
        return self.repo.create_todo(list_id, text)

    def update_todo(self, list_id: int, todo_id: int, *, text: str | None = None, done: bool | None = None) -> Todo:
        todo = self.repo.update_todo(list_id, todo_id, text=text, done=done)
        if todo is None:
            self.get_list(list_id)  # a missing list reports as such
            raise NotFoundError(TODO_NOT_FOUND)
        return todo

    def delete_todo(self, list_id: int, todo_id: int) -> None:
        if not self.repo.delete_todo(list_id, todo_id):
            self.get_list(list_id)
            raise NotFoundError(TODO_NOT_FOUND)

    def reorder_todos(self, list_id: int, ids: list[int]) -> list[Todo]:
        """Saves `ids` (one section of the list) in that order and returns the full list."""
        self.get_list(list_id)
        missing = self.repo.reorder_todos(list_id, ids)
        if missing:
            raise NotFoundError(f"Unknown todo ids: {', '.join(map(str, missing))}")
        return self.repo.list_todos(list_id)
