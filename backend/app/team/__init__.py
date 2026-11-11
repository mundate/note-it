"""Team feature: teams that todo lists (and later notes and diagrams) can be assigned to.

Teams are optional: nothing requires one. Other features depend on this package (to check
a team exists); it never depends on them. Deleting a team leaves its assigned items in
place, unassigned (the database's ON DELETE SET NULL).
"""

from .repository import TeamRepo
from .routes import router
from .service import TeamService

__all__ = ["TeamRepo", "TeamService", "router"]
