"""REST routes for projects. Thin: validation in the models, rules in the service."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from ..core.exceptions import BAD_REQUEST, not_found
from .models import Project, ProjectCreate, ProjectPatch
from .service import ProjectService

PROJECT_NOT_FOUND = not_found("Project not found")
TEAM_NOT_FOUND = not_found("Team not found")
PROJECT_OR_TEAM_NOT_FOUND = not_found("Project or team not found")


def get_service(request: Request) -> ProjectService:
    return request.app.state.project_service


Service = Annotated[ProjectService, Depends(get_service)]

router = APIRouter(prefix="/api/projects", tags=["projects"])
team_projects_router = APIRouter(prefix="/api/teams/{team_id}/projects", tags=["projects"])


@team_projects_router.get("", responses=TEAM_NOT_FOUND)
def list_team_projects(team_id: int, service: Service) -> list[Project]:
    """The team's projects, active first."""
    return service.list_for_team(team_id)


@team_projects_router.post("", status_code=status.HTTP_201_CREATED, responses={**BAD_REQUEST, **TEAM_NOT_FOUND})
def create_project(team_id: int, body: ProjectCreate, service: Service) -> Project:
    return service.create_project(team_id, body.name, body.description, body.deadline)


# Declared before "/{project_id}" so "teamless" isn't parsed as an id.
@router.get("/teamless")
def list_teamless_projects(service: Service) -> list[Project]:
    """Projects without a team (e.g. after their team was deleted)."""
    return service.list_teamless()


@router.get("/{project_id}", responses=PROJECT_NOT_FOUND)
def get_project(project_id: int, service: Service) -> Project:
    return service.get_project(project_id)


@router.patch("/{project_id}", responses={**BAD_REQUEST, **PROJECT_OR_TEAM_NOT_FOUND})
def update_project(project_id: int, body: ProjectPatch, service: Service) -> Project:
    return service.update_project(project_id, **body.model_dump(include=body.model_fields_set))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, responses=PROJECT_NOT_FOUND)
def delete_project(project_id: int, service: Service) -> None:
    """Deletes the project and all of its todo lists (daily lists included)."""
    service.delete_project(project_id)
