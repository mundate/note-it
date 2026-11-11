"""FastAPI app. Run with: uv run uvicorn app.main:app --reload (from backend/)."""

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .core.db import DEFAULT_DB_PATH, REPO_ROOT, open_db
from .core.exceptions import ERROR_RESPONSES, drop_validation_responses, register_exception_handlers
from .todo import TodoRepo, TodoService
from .todo import router as todos_router

DIST_DIR = REPO_ROOT / "dist"


def create_app(db_path: str = DEFAULT_DB_PATH) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        # Opened here (not at import) so exporting the OpenAPI schema has no side effects.
        db = open_db(db_path)
        app.state.todo_service = TodoService(TodoRepo(db))
        yield
        db.close()

    app = FastAPI(
        title="Note it! API",
        version="0.1.0",
        lifespan=lifespan,
        # Every route documents ErrorResponse for any status it doesn't list itself.
        responses=ERROR_RESPONSES,
        # Clean operation ids (e.g. "list_todos") in the OpenAPI schema.
        generate_unique_id_function=lambda route: route.name,
    )

    # All errors use one shape: {"error": "..."}, documented as ErrorResponse.
    register_exception_handlers(app)

    app.include_router(todos_router)

    # FastAPI documents a 422 on every route with a body, but our handler above turns
    # those into 400 ErrorResponse. Drop them so the generated TS types are accurate.
    def openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = drop_validation_responses(FastAPI.openapi(app))
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
