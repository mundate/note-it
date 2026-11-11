"""Todo business logic, between the routes (HTTP) and the repository (SQL).

Rules live here: what counts as "not found", what a reorder must contain, and anything
that combines several repository calls. Raises domain errors from `app.core.exceptions`;
never `HTTPException`, so it can be reused outside HTTP (scripts, other features).
"""

from ..core.exceptions import NotFoundError
from .models import Todo
from .repository import TodoRepo


class TodoService:
    def __init__(self, repo: TodoRepo) -> None:
        self.repo = repo

    def list_todos(self) -> list[Todo]:
        return self.repo.list_todos()

    def create_todo(self, text: str) -> Todo:
        return self.repo.create_todo(text)

    def update_todo(self, todo_id: int, *, text: str | None = None, done: bool | None = None) -> Todo:
        todo = self.repo.update_todo(todo_id, text=text, done=done)
        if todo is None:
            raise NotFoundError("Todo not found")
        return todo

    def delete_todo(self, todo_id: int) -> None:
        if not self.repo.delete_todo(todo_id):
            raise NotFoundError("Todo not found")

    def reorder_todos(self, ids: list[int]) -> list[Todo]:
        """Saves `ids` (one section of the list) in that order and returns the full list."""
        missing = self.repo.reorder_todos(ids)
        if missing:
            raise NotFoundError(f"Unknown todo ids: {', '.join(map(str, missing))}")
        return self.repo.list_todos()
