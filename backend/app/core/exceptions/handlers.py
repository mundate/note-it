"""Exception handlers. Every error response has one shape: {"error": "..."} (ErrorResponse)."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .errors import AppError, ConflictError, NotFoundError

# Domain error → HTTP status. Checked in order, so list subclasses before their bases.
STATUS_CODES: list[tuple[type[AppError], int]] = [
    (NotFoundError, 404),
    (ConflictError, 409),
    (AppError, 400),
]


def _validation_message(exc: RequestValidationError) -> str:
    err = exc.errors()[0]
    field = ".".join(str(p) for p in err["loc"][1:] if p != "body")
    msg = str(err["msg"]).removeprefix("Value error, ")
    return f"`{field}`: {msg}" if field and not msg.startswith("`") else msg

async def catch_all_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions. Returns a 500 with a generic message."""
    return JSONResponse({"error": "Internal server error"}, status_code=500)

async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """FastAPI's 422 becomes 400, except a malformed path id (e.g. /api/todos/abc),
    which is just a resource that doesn't exist."""
    if any(e["loc"][0] == "path" for e in exc.errors()):
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"error": _validation_message(exc)}, status_code=400)


async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code, headers=exc.headers)


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    status_code = next(code for cls, code in STATUS_CODES if isinstance(exc, cls))
    return JSONResponse({"error": exc.message}, status_code=status_code)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, catch_all_exception_handler)  # type: ignore[arg-type]