"""REST routes for todos. Thin: request validation lives in the models, rules in the
service, SQL in the repository. Routes only translate HTTP ↔ service calls."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from ..core.exceptions import BAD_REQUEST, not_found
from .models import ReorderRequest, Todo, TodoCreate, TodoPatch
from .service import TodoService

# Documents the 404s that TodoService raises as NotFoundError.
NOT_FOUND = not_found("Todo not found")


def get_service(request: Request) -> TodoService:
    return request.app.state.todo_service


Service = Annotated[TodoService, Depends(get_service)]

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("")
def list_todos(service: Service) -> list[Todo]:
    return service.list_todos()


@router.post("", status_code=status.HTTP_201_CREATED, responses=BAD_REQUEST)
def create_todo(body: TodoCreate, service: Service) -> Todo:
    return service.create_todo(body.text)


# Declared before "/{todo_id}" so "reorder" isn't parsed as an id.
@router.post("/reorder", responses={**BAD_REQUEST, **NOT_FOUND})
def reorder_todos(body: ReorderRequest, service: Service) -> list[Todo]:
    return service.reorder_todos(body.ids)


@router.patch("/{todo_id}", responses={**BAD_REQUEST, **NOT_FOUND})
def update_todo(todo_id: int, body: TodoPatch, service: Service) -> Todo:
    return service.update_todo(todo_id, **body.model_dump(include=body.model_fields_set))


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_todo(todo_id: int, service: Service) -> None:
    service.delete_todo(todo_id)
