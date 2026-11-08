"""FastAPI app. Run with: uv run uvicorn app.main:app --reload (from backend/)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .db import DEFAULT_DB_PATH, REPO_ROOT, open_db
from .routes import router as todos_router
from .todos import TodoRepo

DIST_DIR = REPO_ROOT / "dist"


def _validation_message(exc: RequestValidationError) -> str:
    err = exc.errors()[0]
    field = ".".join(str(p) for p in err["loc"][1:] if p != "body")
    msg = str(err["msg"]).removeprefix("Value error, ")
    return f"`{field}`: {msg}" if field and not msg.startswith("`") else msg


def create_app(db_path: str = DEFAULT_DB_PATH) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Opened here (not at import) so exporting the OpenAPI schema has no side effects.
        db = open_db(db_path)
        app.state.todos = TodoRepo(db)
        yield
        db.close()

    app = FastAPI(
        title="Note it! API",
        version="0.1.0",
        lifespan=lifespan,
        # Clean operation ids (e.g. "list_todos") in the OpenAPI schema.
        generate_unique_id_function=lambda route: route.name,
    )

    # All errors use one shape: {"error": "..."}, documented as ErrorResponse.
    @app.exception_handler(RequestValidationError)
    async def on_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # A malformed path id (e.g. /api/todos/abc) is just a todo that doesn't exist.
        if any(e["loc"][0] == "path" for e in exc.errors()):
            return JSONResponse({"error": "Todo not found"}, status_code=404)
        return JSONResponse({"error": _validation_message(exc)}, status_code=400)

    @app.exception_handler(StarletteHTTPException)
    async def on_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse({"error": exc.detail}, status_code=exc.status_code, headers=exc.headers)

    app.include_router(todos_router)

    # FastAPI documents a 422 on every route with a body, but our handler above turns
    # those into 400 ErrorResponse. Drop them so the generated TS types are accurate.
    def openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = FastAPI.openapi(app)
        for path in schema.get("paths", {}).values():
            for operation in path.values():
                operation.get("responses", {}).pop("422", None)
        for name in ("HTTPValidationError", "ValidationError"):
            schema.get("components", {}).get("schemas", {}).pop(name, None)
        app.openapi_schema = schema
        return schema

    app.openapi = openapi  # type: ignore[method-assign]

    # Production: serve the built frontend (bun run build) with an SPA fallback.
    if (DIST_DIR / "index.html").exists():

        @app.get("/{path:path}", include_in_schema=False)
        async def frontend(path: str) -> FileResponse:
            if path.startswith("api/"):
                raise StarletteHTTPException(404, "Not Found")
            file = (DIST_DIR / path).resolve()
            if path and file.is_file() and file.is_relative_to(DIST_DIR):
                return FileResponse(file)
            return FileResponse(DIST_DIR / "index.html")

    return app


app = create_app()
