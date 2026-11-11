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


# ---------- repository: lists ----------


def test_list_crud_and_counts(repo: TodoRepo) -> None:
    work = repo.create_list("Work")
    home = repo.create_list("Home")
    assert [(l.name, l.open_count, l.done_count) for l in repo.list_lists()] == [("Work", 0, 0), ("Home", 0, 0)]

    a = repo.create_todo(work.id, "a")
    repo.create_todo(work.id, "b")
    repo.update_todo(work.id, a.id, done=True)
    got = repo.get_list(work.id)
    assert got is not None and (got.open_count, got.done_count) == (1, 1)

    renamed = repo.update_list(home.id, name="House")
    assert renamed is not None and renamed.name == "House"
    assert repo.update_list(999, name="x") is None
    assert repo.get_list(999) is None


def test_deleting_a_list_deletes_its_todos(repo: TodoRepo) -> None:
    work, home = repo.create_list("Work"), repo.create_list("Home")
    repo.create_todo(work.id, "a")
    repo.create_todo(home.id, "b")
    assert repo.delete_list(work.id) is True
    assert repo.delete_list(work.id) is False
    assert repo.list_todos(work.id) == []
    assert repo.db.execute("SELECT COUNT(*) FROM todos").fetchone()[0] == 1
    assert texts(repo.list_todos(home.id)) == ["b"]


# ---------- repository: todos ----------


def test_creates_todos_in_order_per_list(repo: TodoRepo) -> None:
    work, home = repo.create_list("Work"), repo.create_list("Home")
    repo.create_todo(work.id, "first")
    repo.create_todo(home.id, "elsewhere")
    repo.create_todo(work.id, "second")
    assert [(t.text, t.done) for t in repo.list_todos(work.id)] == [("first", False), ("second", False)]
    assert texts(repo.list_todos(home.id)) == ["elsewhere"]


def test_updates_text_and_done_and_lists_done_last(repo: TodoRepo) -> None:
    lst = repo.create_list("L")
    a = repo.create_todo(lst.id, "a")
    repo.create_todo(lst.id, "b")
    updated = repo.update_todo(lst.id, a.id, done=True, text="a!")
    assert updated is not None and (updated.text, updated.done) == ("a!", True)
    assert texts(repo.list_todos(lst.id)) == ["b", "a!"]

    # Partial update leaves other fields alone.
    again = repo.update_todo(lst.id, a.id, done=False)
    assert again is not None and (again.text, again.done) == ("a!", False)


def test_todos_are_only_reachable_through_their_own_list(repo: TodoRepo) -> None:
    work, home = repo.create_list("Work"), repo.create_list("Home")
    a = repo.create_todo(work.id, "a")
    assert repo.update_todo(home.id, a.id, done=True) is None
    assert repo.delete_todo(home.id, a.id) is False
    assert repo.reorder_todos(home.id, [a.id]) == [a.id]
    assert repo.list_todos(work.id)[0].done is False


def test_update_and_delete_missing(repo: TodoRepo) -> None:
    lst = repo.create_list("L")
    assert repo.update_todo(lst.id, 999, done=True) is None
    assert repo.delete_todo(lst.id, 999) is False


def test_reorder(repo: TodoRepo) -> None:
    lst, other = repo.create_list("L"), repo.create_list("Other")
    a, _, c, d = (repo.create_todo(lst.id, t) for t in "abcd")
    x = repo.create_todo(other.id, "x")
    assert repo.reorder_todos(lst.id, [c.id, a.id]) == []
    assert texts(repo.list_todos(lst.id)) == ["c", "a", "b", "d"]
    assert texts(repo.list_todos(other.id)) == ["x"]

    # Unknown ids (including another list's) change nothing.
    assert repo.reorder_todos(lst.id, [d.id, 999, x.id]) == [999, x.id]
    assert texts(repo.list_todos(lst.id)) == ["c", "a", "b", "d"]

    # Done items still list after open ones; new todos go to the end.
    repo.update_todo(lst.id, c.id, done=True)
    repo.create_todo(lst.id, "e")
    assert texts(repo.list_todos(lst.id)) == ["a", "b", "d", "e", "c"]


# ---------- routes ----------


def new_list(client: TestClient, name: str = "List") -> int:
    res = client.post("/api/todo-lists", json={"name": name})
    assert res.status_code == 201
    return res.json()["id"]


def test_list_routes(client: TestClient) -> None:
    for bad in ({"name": "  "}, {"name": "x" * 101}, {}, {"name": 5}):
        res = client.post("/api/todo-lists", json=bad)
        assert res.status_code == 400, bad
        assert "error" in res.json()

    res = client.post("/api/todo-lists", json={"name": "  Work  "})
    assert res.status_code == 201
    lst = res.json()
    assert lst["name"] == "Work"
    assert set(lst) == {"id", "name", "teamId", "openCount", "doneCount", "createdAt", "updatedAt"}
    assert lst["teamId"] is None

    lid = lst["id"]
    assert [l["id"] for l in client.get("/api/todo-lists").json()] == [lid]
    assert client.get(f"/api/todo-lists/{lid}").json()["name"] == "Work"
    assert client.get("/api/todo-lists/999").json() == {"error": "Todo list not found"}
    assert client.get("/api/todo-lists/abc").status_code == 404

    assert client.patch(f"/api/todo-lists/{lid}", json={"name": ""}).status_code == 400
    assert client.patch(f"/api/todo-lists/{lid}", json={"name": None}).status_code == 400
    assert client.patch(f"/api/todo-lists/{lid}", json={}).json() == {
        "error": "Nothing to update: send `name` and/or `teamId`"
    }
    assert client.patch("/api/todo-lists/999", json={"name": "x"}).status_code == 404
    assert client.patch(f"/api/todo-lists/{lid}", json={"name": "Job"}).json()["name"] == "Job"

    client.post(f"/api/todo-lists/{lid}/todos", json={"text": "a"})
    assert client.get(f"/api/todo-lists/{lid}").json()["openCount"] == 1

    res = client.delete(f"/api/todo-lists/{lid}")
    assert res.status_code == 204 and res.content == b""
    assert client.delete(f"/api/todo-lists/{lid}").status_code == 404
    assert client.get(f"/api/todo-lists/{lid}/todos").json() == {"error": "Todo list not found"}


def test_todo_crud_and_validation(client: TestClient) -> None:
    lid = new_list(client)
    base = f"/api/todo-lists/{lid}/todos"
    for bad in ({"text": "  "}, {"text": "x" * 501}, ["nope"], {"text": 5}):
        res = client.post(base, json=bad)
        assert res.status_code == 400, bad
        assert "error" in res.json()
    assert client.post("/api/todo-lists/999/todos", json={"text": "a"}).json() == {"error": "Todo list not found"}

    res = client.post(base, json={"text": "  hi  "})
    assert res.status_code == 201
    todo = res.json()
    assert todo["text"] == "hi"
    assert set(todo) == {"id", "text", "done", "createdAt", "updatedAt"}

    tid = todo["id"]
    assert client.patch(f"{base}/{tid}", json={"done": "yes"}).status_code == 400
    assert client.patch(f"{base}/{tid}", json={"done": None}).status_code == 400
    assert client.patch(f"{base}/{tid}", json={}).json() == {"error": "Nothing to update: send `text` and/or `done`"}
    assert client.patch(f"{base}/999", json={"done": True}).json() == {"error": "Todo not found"}
    assert client.patch(f"/api/todo-lists/999/todos/{tid}", json={"done": True}).json() == {
        "error": "Todo list not found"
    }
    assert client.patch(f"{base}/{tid}", json={"done": True}).json()["done"] is True

    assert client.get(base).json()[0]["id"] == tid
    assert client.delete(f"{base}/abc").status_code == 404
    res = client.delete(f"{base}/{tid}")
    assert res.status_code == 204 and res.content == b""
    assert client.delete(f"{base}/{tid}").json() == {"error": "Todo not found"}


def test_todo_in_another_list_is_not_found(client: TestClient) -> None:
    work, home = new_list(client, "Work"), new_list(client, "Home")
    tid = client.post(f"/api/todo-lists/{work}/todos", json={"text": "a"}).json()["id"]
    assert client.patch(f"/api/todo-lists/{home}/todos/{tid}", json={"done": True}).status_code == 404
    assert client.delete(f"/api/todo-lists/{home}/todos/{tid}").status_code == 404
    assert client.get(f"/api/todo-lists/{home}/todos").json() == []


def test_reorder_route(client: TestClient) -> None:
    lid = new_list(client)
    base = f"/api/todo-lists/{lid}/todos"
    a = client.post(base, json={"text": "a"}).json()
    b = client.post(base, json={"text": "b"}).json()
    assert client.post(f"{base}/reorder", json={"ids": "nope"}).status_code == 400
    assert client.post(f"{base}/reorder", json={"ids": [a["id"], a["id"]]}).status_code == 400
    assert client.post(f"{base}/reorder", json={"ids": ["1"]}).status_code == 400
    assert client.post(f"{base}/reorder", json={"ids": [999]}).status_code == 404
    assert client.post("/api/todo-lists/999/todos/reorder", json={"ids": [a["id"]]}).status_code == 404
    res = client.post(f"{base}/reorder", json={"ids": [b["id"], a["id"]]})
    assert res.status_code == 200
    assert [t["text"] for t in res.json()] == ["b", "a"]


def test_openapi_todo_schemas() -> None:
    """The shapes the frontend's generated TS types depend on."""
    schemas = create_app(":memory:").openapi()["components"]["schemas"]
    assert {"Todo", "TodoCreate", "TodoPatch", "ReorderRequest", "TodoList", "TodoListCreate", "TodoListPatch"} <= set(
        schemas
    )
    assert set(schemas["Todo"]["required"]) == {"id", "text", "done", "createdAt", "updatedAt"}
    assert set(schemas["TodoList"]["required"]) == {
        "id", "name", "teamId", "openCount", "doneCount", "createdAt", "updatedAt"
    }
    patch = schemas["TodoPatch"]["properties"]
    assert patch["text"]["type"] == "string" and patch["done"]["type"] == "boolean"  # no `| null`
