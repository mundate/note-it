"""REST routes for todos. Thin: request validation lives in the models, rules in the
service, SQL in the repository. Routes only translate HTTP ↔ service calls."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from ..core.exceptions import BAD_REQUEST, not_found
from .models import (
    ReorderRequest,
    Todo,
    TodoCreate,
    TodoList,
    TodoListCreate,
    TodoListPatch,
    TodoPatch,
)
from .repository import UNSET
from .service import TodoService

# Documents the 404s that TodoService raises as NotFoundError.
TEAM_NOT_FOUND = not_found("Team not found")
PROJECT_NOT_FOUND = not_found("Project not found")
TEAM_OR_PROJECT_NOT_FOUND = not_found("Team or project not found")
LIST_NOT_FOUND = not_found("Todo list not found")
LIST_OR_TEAM_NOT_FOUND = not_found("Todo list, team or project not found")
NOT_FOUND = not_found("Todo list or todo not found")


def get_service(request: Request) -> TodoService:
    return request.app.state.todo_service


Service = Annotated[TodoService, Depends(get_service)]

router = APIRouter(prefix="/api/todo-lists", tags=["todos"])
# Daily lists live under their project's / team's URL, but this feature owns them (todo
# depends on project and team, never the reverse).
project_daily_router = APIRouter(prefix="/api/projects/{project_id}/daily", tags=["todos"])
team_daily_router = APIRouter(prefix="/api/teams/{team_id}/daily", tags=["todos"])


# ---------- lists ----------


@router.get("")
def list_todo_lists(
    service: Service,
    team_id: Annotated[int | None, Query(alias="teamId", description="Only this team's lists")] = None,
    project_id: Annotated[int | None, Query(alias="projectId", description="Only this project's lists")] = None,
    no_project: Annotated[bool, Query(alias="noProject", description="Only lists not in a project")] = False,
) -> list[TodoList]:
    """Standard lists (daily lists are left out)."""
    return service.list_lists(team_id, None if no_project else project_id if project_id is not None else UNSET)


@router.post("", status_code=status.HTTP_201_CREATED, responses={**BAD_REQUEST, **TEAM_OR_PROJECT_NOT_FOUND})
def create_todo_list(body: TodoListCreate, service: Service) -> TodoList:
    return service.create_list(body.name, body.team_id, body.project_id)


@router.get("/{list_id}", responses=LIST_NOT_FOUND)
def get_todo_list(list_id: int, service: Service) -> TodoList:
    return service.get_list(list_id)


@router.patch("/{list_id}", responses={**BAD_REQUEST, **LIST_OR_TEAM_NOT_FOUND})
def update_todo_list(list_id: int, body: TodoListPatch, service: Service) -> TodoList:
    return service.update_list(list_id, **body.model_dump(include=body.model_fields_set))


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT, responses={**BAD_REQUEST, **LIST_NOT_FOUND})
def delete_todo_list(list_id: int, service: Service) -> None:
    service.delete_list(list_id)


# ---------- todos in a list ----------


@router.get("/{list_id}/todos", responses=LIST_NOT_FOUND)
def list_todos(list_id: int, service: Service) -> list[Todo]:
    return service.list_todos(list_id)


@router.post("/{list_id}/todos", status_code=status.HTTP_201_CREATED, responses={**BAD_REQUEST, **LIST_NOT_FOUND})
def create_todo(list_id: int, body: TodoCreate, service: Service) -> Todo:
    return service.create_todo(list_id, body.text)


# Declared before "/{todo_id}" so "reorder" isn't parsed as an id.
@router.post("/{list_id}/todos/reorder", responses={**BAD_REQUEST, **NOT_FOUND})
def reorder_todos(list_id: int, body: ReorderRequest, service: Service) -> list[Todo]:
    return service.reorder_todos(list_id, body.ids)


@router.patch("/{list_id}/todos/{todo_id}", responses={**BAD_REQUEST, **NOT_FOUND})
def update_todo(list_id: int, todo_id: int, body: TodoPatch, service: Service) -> Todo:
    return service.update_todo(list_id, todo_id, **body.model_dump(include=body.model_fields_set))


@router.delete("/{list_id}/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_todo(list_id: int, todo_id: int, service: Service) -> None:
    service.delete_todo(list_id, todo_id)


# ---------- daily lists ----------


@project_daily_router.get("", responses=PROJECT_NOT_FOUND)
def list_project_daily_lists(project_id: int, service: Service) -> list[TodoList]:
    """The project's daily lists, newest day first (kept even after daily is turned off)."""
    return service.list_project_daily(project_id)


@project_daily_router.post("/today", responses={**BAD_REQUEST, **PROJECT_NOT_FOUND})
def open_project_today(project_id: int, service: Service) -> TodoList:
    """Today's daily list for the project, created if needed. Every unfinished todo from
    earlier days is moved onto it. 400 if the project's daily list is turned off."""
    return service.open_project_today(project_id)


@team_daily_router.post("/today", responses=TEAM_NOT_FOUND)
def open_team_today(team_id: int, service: Service) -> list[TodoList]:
    """Today's daily lists for the team's active projects that have daily turned on (each
    created and carried over like the project endpoint)."""
    return service.open_team_today(team_id)


@team_daily_router.get("/days", responses=TEAM_NOT_FOUND)
def list_team_daily_days(team_id: int, service: Service) -> list[str]:
    """Days (YYYY-MM-DD) with a daily list in any of the team's projects, newest first."""
    return service.team_daily_days(team_id)


@team_daily_router.get("/{day}", responses={**BAD_REQUEST, **TEAM_NOT_FOUND})
def get_team_daily(team_id: int, day: date, service: Service) -> list[TodoList]:
    """That day's daily lists across the team's projects."""
    return service.team_daily(team_id, day)
