"""Domain errors raised by the service layer.

These know nothing about HTTP: services raise them, and `handlers.app_error_handler` maps
each class to a status code. Add a subclass (and an entry in STATUS_CODES) for new cases.
"""


class AppError(Exception):
    """Base for expected, user-facing errors. `message` is shown to the client."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    """The requested resource doesn't exist."""


class ConflictError(AppError):
    """The request conflicts with the current state (e.g. a duplicate)."""
