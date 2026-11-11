"""Todo business logic, between the routes (HTTP) and the repository (SQL).

Rules live here: what counts as "not found", what a reorder must contain, and anything
that combines several repository calls. Raises domain errors from `app.core.exceptions`;
never `HTTPException`, so it can be reused outside HTTP (scripts, other features).
"""

from ..core.exceptions import NotFoundError
from .models import Todo, TodoList
from .repository import TodoRepo

LIST_NOT_FOUND = "Todo list not found"
TODO_NOT_FOUND = "Todo not found"


class TodoService:
    def __init__(self, repo: TodoRepo) -> None:
        self.repo = repo

    # ---------- lists ----------

    def list_lists(self) -> list[TodoList]:
        return self.repo.list_lists()

    def get_list(self, list_id: int) -> TodoList:
        list_ = self.repo.get_list(list_id)
        if list_ is None:
            raise NotFoundError(LIST_NOT_FOUND)
        return list_

    def create_list(self, name: str) -> TodoList:
        return self.repo.create_list(name)

    def rename_list(self, list_id: int, name: str) -> TodoList:
        list_ = self.repo.rename_list(list_id, name)
        if list_ is None:
            raise NotFoundError(LIST_NOT_FOUND)
        return list_

    def delete_list(self, list_id: int) -> None:
        """Deletes the list and all of its todos."""
        if not self.repo.delete_list(list_id):
            raise NotFoundError(LIST_NOT_FOUND)

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
