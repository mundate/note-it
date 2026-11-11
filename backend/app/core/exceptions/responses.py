"""The error response contract as seen by OpenAPI (and so the generated TS types).

`ErrorResponse` is the body every handler in `handlers.py` returns. `ERROR_RESPONSES` is
set on the app so every route documents it; the other `responses=` helpers add specific
codes to routes (a route's entry replaces the app's for the same code), and `drop_validation_responses` removes
FastAPI's default 422 docs, since `validation_error_handler` turns those into 400s.
"""

from typing import Any

from ..models import ApiModel

Responses = dict[int | str, dict[str, Any]]


class ErrorResponse(ApiModel):
    """The body of every error response."""

    error: str


# App-wide: any status a route doesn't list returns ErrorResponse (OpenAPI "default").
ERROR_RESPONSES: Responses = {"default": {"model": ErrorResponse, "description": "Error"}}

BAD_REQUEST: Responses = {400: {"model": ErrorResponse, "description": "Invalid request"}}


def not_found(description: str = "Not found") -> Responses:
    return {404: {"model": ErrorResponse, "description": description}}


def drop_validation_responses(schema: dict[str, Any]) -> dict[str, Any]:
    """Remove FastAPI's 422 responses and their schemas from an OpenAPI schema, in place."""
    for path in schema.get("paths", {}).values():
        for operation in path.values():
            operation.get("responses", {}).pop("422", None)
    for name in ("HTTPValidationError", "ValidationError"):
        schema.get("components", {}).get("schemas", {}).pop(name, None)
    return schema
