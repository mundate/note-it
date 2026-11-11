"""TodoService rules, tested without HTTP."""

import pytest

from app.core.db import open_db
from app.core.exceptions import NotFoundError
from app.todo import TodoRepo, TodoService


@pytest.fixture
def service() -> TodoService:
    return TodoService(TodoRepo(open_db(":memory:")))


def test_create_list_update_delete(service: TodoService) -> None:
    a = service.create_todo("a")
    assert [t.text for t in service.list_todos()] == ["a"]

    updated = service.update_todo(a.id, done=True)
    assert (updated.text, updated.done) == ("a", True)  # unspecified fields unchanged

    service.delete_todo(a.id)
    assert service.list_todos() == []


def test_missing_todo_raises_not_found(service: TodoService) -> None:
    with pytest.raises(NotFoundError, match="Todo not found"):
        service.update_todo(999, done=True)
    with pytest.raises(NotFoundError, match="Todo not found"):
        service.delete_todo(999)


def test_reorder_returns_full_list(service: TodoService) -> None:
    a, b = service.create_todo("a"), service.create_todo("b")
    assert [t.text for t in service.reorder_todos([b.id, a.id])] == ["b", "a"]


def test_reorder_with_unknown_ids_raises_and_changes_nothing(service: TodoService) -> None:
    a, b = service.create_todo("a"), service.create_todo("b")
    with pytest.raises(NotFoundError, match="Unknown todo ids: 999"):
        service.reorder_todos([b.id, 999])
    assert [t.text for t in service.list_todos()] == ["a", "b"]
