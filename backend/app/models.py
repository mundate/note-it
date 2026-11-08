"""API models. These are the source of truth for the frontend's generated TypeScript types.

Model class names become TS type names, so keep them stable. Python attributes are
snake_case; JSON (and therefore TS) is camelCase via the alias generator.
"""

from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StringConstraints, model_validator
from pydantic.alias_generators import to_camel
from pydantic.json_schema import SkipJsonSchema

TODO_TEXT_MAX = 500


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


TodoText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TODO_TEXT_MAX)]


class Todo(ApiModel):
    """A todo as returned by the API. No defaults, so every field is required in TS."""

    id: int
    text: str
    done: bool
    created_at: str
    updated_at: str


class TodoCreate(ApiModel):
    text: TodoText


class TodoPatch(ApiModel):
    # `SkipJsonSchema[None]` keeps these as `text?: string` in TS rather than `string | null`.
    text: TodoText | SkipJsonSchema[None] = None
    done: StrictBool | SkipJsonSchema[None] = None

    @model_validator(mode="after")
    def check_fields(self) -> Self:
        for name in ("text", "done"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"`{name}` must not be null")
        if not self.model_fields_set:
            raise ValueError("Nothing to update: send `text` and/or `done`")
        return self


class ReorderRequest(ApiModel):
    """`ids` is one section of the list in its new order."""

    ids: list[Annotated[StrictInt, Field(gt=0)]]

    @model_validator(mode="after")
    def check_unique(self) -> Self:
        if len(set(self.ids)) != len(self.ids):
            raise ValueError("`ids` must not contain duplicates")
        return self


class ErrorResponse(ApiModel):
    error: str
