"""Todo API models. Class names become the frontend's TS type names, so keep them stable."""

from typing import Annotated, Self

from pydantic import Field, StrictBool, StrictInt, StringConstraints, model_validator
from pydantic.json_schema import SkipJsonSchema

from ..core.models import ApiModel
from ..team.models import TeamId

TODO_TEXT_MAX = 500
TODO_LIST_NAME_MAX = 100

TodoText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TODO_TEXT_MAX)]
TodoListName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TODO_LIST_NAME_MAX)]


class TodoList(ApiModel):
    """A todo list as returned by the API, with counts of its todos."""

    id: int
    name: str
    team_id: int | None  # None: not assigned to a team
    open_count: int
    done_count: int
    created_at: str
    updated_at: str


class TodoListCreate(ApiModel):
    name: TodoListName
    team_id: TeamId | None = None


class TodoListPatch(ApiModel):
    """Send `name` and/or `teamId`. `teamId: null` takes the list off its team."""

    name: TodoListName | SkipJsonSchema[None] = None
    team_id: TeamId | None = None

    @model_validator(mode="after")
    def check_fields(self) -> Self:
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("`name` must not be null")
        if not self.model_fields_set:
            raise ValueError("Nothing to update: send `name` and/or `teamId`")
        return self


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
