"""REST routes for todos. Thin: request validation lives in the models, rules in the
service, SQL in the repository. Routes only translate HTTP ↔ service calls."""

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
from .service import TodoService

# Documents the 404s that TodoService raises as NotFoundError.
TEAM_NOT_FOUND = not_found("Team not found")
LIST_NOT_FOUND = not_found("Todo list not found")
LIST_OR_TEAM_NOT_FOUND = not_found("Todo list or team not found")
NOT_FOUND = not_found("Todo list or todo not found")


def get_service(request: Request) -> TodoService:
    return request.app.state.todo_service


Service = Annotated[TodoService, Depends(get_service)]

router = APIRouter(prefix="/api/todo-lists", tags=["todos"])


# ---------- lists ----------


@router.get("")
def list_todo_lists(
    service: Service,
    team_id: Annotated[int | None, Query(alias="teamId", description="Only this team's lists")] = None,
) -> list[TodoList]:
    return service.list_lists(team_id)


@router.post("", status_code=status.HTTP_201_CREATED, responses={**BAD_REQUEST, **TEAM_NOT_FOUND})
def create_todo_list(body: TodoListCreate, service: Service) -> TodoList:
    return service.create_list(body.name, body.team_id)


@router.get("/{list_id}", responses=LIST_NOT_FOUND)
def get_todo_list(list_id: int, service: Service) -> TodoList:
    return service.get_list(list_id)


@router.patch("/{list_id}", responses={**BAD_REQUEST, **LIST_OR_TEAM_NOT_FOUND})
def update_todo_list(list_id: int, body: TodoListPatch, service: Service) -> TodoList:
    return service.update_list(list_id, **body.model_dump(include=body.model_fields_set))


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT, responses=LIST_NOT_FOUND)
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
