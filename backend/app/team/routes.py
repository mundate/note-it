"""REST routes for teams. Thin: validation in the models, rules in the service."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from ..core.exceptions import BAD_REQUEST, not_found
from .models import Team, TeamCreate, TeamPatch
from .service import TeamService

# Documents the 404s that TeamService raises as NotFoundError.
TEAM_NOT_FOUND = not_found("Team not found")


def get_service(request: Request) -> TeamService:
    return request.app.state.team_service


Service = Annotated[TeamService, Depends(get_service)]

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("")
def list_teams(service: Service) -> list[Team]:
    return service.list_teams()


@router.post("", status_code=status.HTTP_201_CREATED, responses=BAD_REQUEST)
def create_team(body: TeamCreate, service: Service) -> Team:
    return service.create_team(body.name)


@router.get("/{team_id}", responses=TEAM_NOT_FOUND)
def get_team(team_id: int, service: Service) -> Team:
    return service.get_team(team_id)


@router.patch("/{team_id}", responses={**BAD_REQUEST, **TEAM_NOT_FOUND})
def update_team(team_id: int, body: TeamPatch, service: Service) -> Team:
    """Rename the team and/or set its sprint schedule."""
    return service.update_team(team_id, **body.model_dump(include=body.model_fields_set))


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT, responses=TEAM_NOT_FOUND)
def delete_team(team_id: int, service: Service) -> None:
    """Deletes the team. What was assigned to it is kept, without a team."""
    service.delete_team(team_id)
