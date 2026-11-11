"""Team API models. Class names become the frontend's TS type names, so keep them stable."""

from typing import Annotated

from pydantic import Field, StrictInt, StringConstraints

from ..core.models import ApiModel

TEAM_NAME_MAX = 100

TeamName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TEAM_NAME_MAX)]
# A team id sent in another feature's request body (e.g. a todo list's `teamId`).
TeamId = Annotated[StrictInt, Field(gt=0)]


class Team(ApiModel):
    id: int
    name: str
    created_at: str
    updated_at: str


class TeamCreate(ApiModel):
    name: TeamName


class TeamPatch(ApiModel):
    name: TeamName
