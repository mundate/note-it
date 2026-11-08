"""REST routes for todos. Thin: validation lives in the models, SQL in the repository."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from .models import ErrorResponse, ReorderRequest, Todo, TodoCreate, TodoPatch
from .todos import TodoRepo

BAD_REQUEST: dict[int | str, dict[str, Any]] = {400: {"model": ErrorResponse, "description": "Invalid request"}}
NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorResponse, "description": "Todo not found"}}


def get_repo(request: Request) -> TodoRepo:
    return request.app.state.todos


Repo = Annotated[TodoRepo, Depends(get_repo)]

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("")
def list_todos(repo: Repo) -> list[Todo]:
    return repo.list_todos()


@router.post("", status_code=status.HTTP_201_CREATED, responses=BAD_REQUEST)
def create_todo(body: TodoCreate, repo: Repo) -> Todo:
    return repo.create_todo(body.text)


# Declared before "/{todo_id}" so "reorder" isn't parsed as an id.
@router.post("/reorder", responses={**BAD_REQUEST, **NOT_FOUND})
def reorder_todos(body: ReorderRequest, repo: Repo) -> list[Todo]:
    missing = repo.reorder_todos(body.ids)
    if missing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown todo ids: {', '.join(map(str, missing))}")
    return repo.list_todos()


@router.patch("/{todo_id}", responses={**BAD_REQUEST, **NOT_FOUND})
def update_todo(todo_id: int, body: TodoPatch, repo: Repo) -> Todo:
    todo = repo.update_todo(todo_id, **body.model_dump(include=body.model_fields_set))
    if todo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Todo not found")
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_todo(todo_id: int, repo: Repo) -> None:
    if not repo.delete_todo(todo_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Todo not found")
