"""TodoService rules, tested without HTTP."""

import pytest

from app.core.db import open_db
from app.core.exceptions import NotFoundError
from app.todo import TodoRepo, TodoService


@pytest.fixture
def service() -> TodoService:
    return TodoService(TodoRepo(open_db(":memory:")))


def test_list_lifecycle(service: TodoService) -> None:
    lst = service.create_list("Work")
    assert [l.name for l in service.list_lists()] == ["Work"]
    assert service.rename_list(lst.id, "Job").name == "Job"
    service.delete_list(lst.id)
    assert service.list_lists() == []


def test_missing_list_raises_not_found(service: TodoService) -> None:
    for call in (
        lambda: service.get_list(999),
        lambda: service.rename_list(999, "x"),
        lambda: service.delete_list(999),
        lambda: service.list_todos(999),
        lambda: service.create_todo(999, "a"),
        lambda: service.update_todo(999, 1, done=True),
        lambda: service.delete_todo(999, 1),
        lambda: service.reorder_todos(999, [1]),
    ):
        with pytest.raises(NotFoundError, match="Todo list not found"):
            call()


def test_create_list_update_delete_todos(service: TodoService) -> None:
    lst = service.create_list("L")
    a = service.create_todo(lst.id, "a")
    assert [t.text for t in service.list_todos(lst.id)] == ["a"]

    updated = service.update_todo(lst.id, a.id, done=True)
    assert (updated.text, updated.done) == ("a", True)  # unspecified fields unchanged

    service.delete_todo(lst.id, a.id)
    assert service.list_todos(lst.id) == []


def test_missing_todo_raises_not_found(service: TodoService) -> None:
    lst, other = service.create_list("L"), service.create_list("Other")
    elsewhere = service.create_todo(other.id, "x")
    for todo_id in (999, elsewhere.id):
        with pytest.raises(NotFoundError, match="Todo not found"):
            service.update_todo(lst.id, todo_id, done=True)
        with pytest.raises(NotFoundError, match="Todo not found"):
            service.delete_todo(lst.id, todo_id)


def test_reorder_returns_full_list(service: TodoService) -> None:
    lst = service.create_list("L")
    a, b = service.create_todo(lst.id, "a"), service.create_todo(lst.id, "b")
    assert [t.text for t in service.reorder_todos(lst.id, [b.id, a.id])] == ["b", "a"]


def test_reorder_with_unknown_ids_raises_and_changes_nothing(service: TodoService) -> None:
    lst = service.create_list("L")
    a, b = service.create_todo(lst.id, "a"), service.create_todo(lst.id, "b")
    with pytest.raises(NotFoundError, match="Unknown todo ids: 999"):
        service.reorder_todos(lst.id, [b.id, 999])
    assert [t.text for t in service.list_todos(lst.id)] == ["a", "b"]
