"""Project API models. Class names become the frontend's TS type names, so keep them stable."""

from datetime import date
from typing import Annotated, Literal, Self

from pydantic import Field, StrictBool, StrictInt, StringConstraints, model_validator
from pydantic.json_schema import SkipJsonSchema

from ..core.models import ApiModel
from ..team.models import TeamId

PROJECT_NAME_MAX = 100
PROJECT_DESCRIPTION_MAX = 2000

ProjectName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=PROJECT_NAME_MAX)]
ProjectDescription = Annotated[str, StringConstraints(strip_whitespace=True, max_length=PROJECT_DESCRIPTION_MAX)]
ProjectStatus = Literal["active", "inactive"]  # inactive: not being worked on right now
# A project id sent in another feature's request body (e.g. a todo list's `projectId`).
ProjectId = Annotated[StrictInt, Field(gt=0)]


class Project(ApiModel):
    id: int
    team_id: int | None  # None: its team was deleted (or it was taken off it)
    name: str
    description: str
    deadline: str | None  # YYYY-MM-DD
    status: ProjectStatus
    daily_enabled: bool  # has a daily todo list (opt-in)
    created_at: str
    updated_at: str


class ProjectCreate(ApiModel):
    name: ProjectName
    description: ProjectDescription = ""
    deadline: date | None = None


class ProjectPatch(ApiModel):
    """Send any of the fields. `deadline: null` clears the deadline; `teamId: null` takes
    the project (and its lists) off its team."""

    name: ProjectName | SkipJsonSchema[None] = None
    description: ProjectDescription | SkipJsonSchema[None] = None
    deadline: date | None = None
    status: ProjectStatus | SkipJsonSchema[None] = None
    daily_enabled: StrictBool | SkipJsonSchema[None] = None
    team_id: TeamId | None = None

    @model_validator(mode="after")
    def check_fields(self) -> Self:
        for name in ("name", "description", "status", "daily_enabled"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"`{type(self).model_fields[name].alias or name}` must not be null")
        if not self.model_fields_set:
            raise ValueError("Nothing to update")
        return self
