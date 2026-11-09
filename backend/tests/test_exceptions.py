"""The error contract ({"error": "..."}), tested without todo routes or a database."""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.exceptions import register_exception_handlers
from app.exceptions.handlers import _validation_message


class Body(BaseModel):
    name: str


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/conflict")
    def conflict() -> None:
        raise HTTPException(409, "boom")

    @app.post("/body")
    def body(_: Body) -> None: ...

    @app.get("/items/{item_id}")
    def item(item_id: int) -> int:
        return item_id

    return TestClient(app)


def test_http_exception_uses_error_shape(client: TestClient) -> None:
    res = client.get("/conflict")
    assert (res.status_code, res.json()) == (409, {"error": "boom"})


def test_invalid_body_is_400_with_field_name(client: TestClient) -> None:
    res = client.post("/body", json={"name": 5})
    assert res.status_code == 400
    assert res.json()["error"].startswith("`name`: ")


def test_bad_path_param_is_404(client: TestClient) -> None:
    assert client.get("/items/abc").status_code == 404
    assert client.get("/items/7").json() == 7


def test_unknown_route_is_404_with_error_shape(client: TestClient) -> None:
    res = client.get("/nope")
    assert (res.status_code, res.json()) == (404, {"error": "Not Found"})


def _error(loc: tuple, msg: str) -> RequestValidationError:
    return RequestValidationError([{"loc": loc, "msg": msg, "type": "value_error"}])


@pytest.mark.parametrize(
    ("loc", "msg", "expected"),
    [
        (("body", "a", "b"), "Field required", "`a.b`: Field required"),
        (("body", "text"), "Value error, too long", "`text`: too long"),
        (("body",), "Value error, `ids` must not contain duplicates", "`ids` must not contain duplicates"),
        (("body", "ids"), "`ids` must not contain duplicates", "`ids` must not contain duplicates"),
    ],
)
def test_validation_message(loc: tuple, msg: str, expected: str) -> None:
    assert _validation_message(_error(loc, msg)) == expected
