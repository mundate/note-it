from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.db import open_db
from app.main import create_app
from app.todo import TodoRepo


@pytest.fixture
def repo() -> TodoRepo:
    return TodoRepo(open_db(":memory:"))


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(":memory:")) as c:  # `with` runs the lifespan (opens the DB)
        yield c


def texts(todos) -> list[str]:
    return [t.text for t in todos]


# ---------- repository ----------


def test_creates_todos_in_order(repo: TodoRepo) -> None:
    repo.create_todo("first")
    repo.create_todo("second")
    assert [(t.text, t.done) for t in repo.list_todos()] == [("first", False), ("second", False)]


def test_updates_text_and_done_and_lists_done_last(repo: TodoRepo) -> None:
    a = repo.create_todo("a")
    repo.create_todo("b")
    updated = repo.update_todo(a.id, done=True, text="a!")
    assert updated is not None and (updated.text, updated.done) == ("a!", True)
    assert texts(repo.list_todos()) == ["b", "a!"]

    # Partial update leaves other fields alone.
    again = repo.update_todo(a.id, done=False)
    assert again is not None and (again.text, again.done) == ("a!", False)


def test_update_and_delete_missing(repo: TodoRepo) -> None:
    assert repo.update_todo(999, done=True) is None
    assert repo.delete_todo(999) is False


def test_reorder(repo: TodoRepo) -> None:
    a, _, c, d = (repo.create_todo(t) for t in "abcd")
    assert repo.reorder_todos([c.id, a.id]) == []
    assert texts(repo.list_todos()) == ["c", "a", "b", "d"]

    # Unknown ids change nothing.
    assert repo.reorder_todos([d.id, 999]) == [999]
    assert texts(repo.list_todos()) == ["c", "a", "b", "d"]

    # Done items still list after open ones; new todos go to the end.
    repo.update_todo(c.id, done=True)
    repo.create_todo("e")
    assert texts(repo.list_todos()) == ["a", "b", "d", "e", "c"]


def test_deletes(repo: TodoRepo) -> None:
    a = repo.create_todo("a")
    assert repo.delete_todo(a.id) is True
    assert repo.list_todos() == []


# ---------- routes ----------


def test_crud_and_validation(client: TestClient) -> None:
    for bad in ({"text": "  "}, {"text": "x" * 501}, ["nope"], {"text": 5}):
        res = client.post("/api/todos", json=bad)
        assert res.status_code == 400, bad
        assert "error" in res.json()

    res = client.post("/api/todos", json={"text": "  hi  "})
    assert res.status_code == 201
    todo = res.json()
    assert todo["text"] == "hi"
    assert set(todo) == {"id", "text", "done", "createdAt", "updatedAt"}

    tid = todo["id"]
    assert client.patch(f"/api/todos/{tid}", json={"done": "yes"}).status_code == 400
    assert client.patch(f"/api/todos/{tid}", json={"done": None}).status_code == 400
    assert client.patch(f"/api/todos/{tid}", json={}).json() == {"error": "Nothing to update: send `text` and/or `done`"}
    assert client.patch("/api/todos/999", json={"done": True}).status_code == 404
    assert client.patch(f"/api/todos/{tid}", json={"done": True}).json()["done"] is True

    assert client.get("/api/todos").json()[0]["id"] == tid
    assert client.delete("/api/todos/abc").status_code == 404
    res = client.delete(f"/api/todos/{tid}")
    assert res.status_code == 204 and res.content == b""
    assert client.delete(f"/api/todos/{tid}").json() == {"error": "Todo not found"}


def test_reorder_route(client: TestClient) -> None:
    a = client.post("/api/todos", json={"text": "a"}).json()
    b = client.post("/api/todos", json={"text": "b"}).json()
    assert client.post("/api/todos/reorder", json={"ids": "nope"}).status_code == 400
    assert client.post("/api/todos/reorder", json={"ids": [a["id"], a["id"]]}).status_code == 400
    assert client.post("/api/todos/reorder", json={"ids": ["1"]}).status_code == 400
    assert client.post("/api/todos/reorder", json={"ids": [999]}).status_code == 404
    res = client.post("/api/todos/reorder", json={"ids": [b["id"], a["id"]]})
    assert res.status_code == 200
    assert [t["text"] for t in res.json()] == ["b", "a"]


def test_openapi_todo_schemas() -> None:
    """The shapes the frontend's generated TS types depend on."""
    schemas = create_app(":memory:").openapi()["components"]["schemas"]
    assert {"Todo", "TodoCreate", "TodoPatch", "ReorderRequest"} <= set(schemas)
    assert set(schemas["Todo"]["required"]) == {"id", "text", "done", "createdAt", "updatedAt"}
    patch = schemas["TodoPatch"]["properties"]
    assert patch["text"]["type"] == "string" and patch["done"]["type"] == "boolean"  # no `| null`
