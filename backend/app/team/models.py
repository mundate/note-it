"""Team API models. Class names become the frontend's TS type names, so keep them stable."""

from datetime import date
from typing import Annotated, Self

from pydantic import Field, StrictInt, StringConstraints, model_validator
from pydantic.json_schema import SkipJsonSchema

from ..core.models import ApiModel

TEAM_NAME_MAX = 100

TeamName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TEAM_NAME_MAX)]
# A team id sent in another feature's request body (e.g. a todo list's `teamId`).
TeamId = Annotated[StrictInt, Field(gt=0)]
SPRINT_WEEKS_MAX = 8
SprintWeeks = Annotated[StrictInt, Field(ge=1, le=SPRINT_WEEKS_MAX)]


class Team(ApiModel):
    id: int
    name: str
    # Sprint schedule: the first sprint's start (YYYY-MM-DD) and each sprint's length in
    # weeks. Both None: no sprints.
    sprint_start: str | None
    sprint_weeks: int | None
    created_at: str
    updated_at: str


class TeamCreate(ApiModel):
    name: TeamName


class TeamPatch(ApiModel):
    """Send `name` and/or the sprint schedule. `null` start and weeks clear the schedule;
    after the change they must be both set or both empty."""

    name: TeamName | SkipJsonSchema[None] = None
    sprint_start: date | None = None
    sprint_weeks: SprintWeeks | None = None

    @model_validator(mode="after")
    def check_fields(self) -> Self:
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("`name` must not be null")
        if not self.model_fields_set:
            raise ValueError("Nothing to update")
        return self
