"""Project feature: projects within a team that todo lists (and later notes, diagrams) are
assigned to. A project has at most one team and outlives it (deleting the team leaves the
project teamless). Depends on `team`; `todo` depends on this package, never the reverse.
"""

from .repository import ProjectRepo
from .routes import router, team_projects_router
from .service import ProjectService

__all__ = ["ProjectRepo", "ProjectService", "router", "team_projects_router"]
