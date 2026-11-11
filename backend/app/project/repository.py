"""Project repository: the only place that knows about the `projects` table."""

import sqlite3
from datetime import date

from ..core.db import lock_for
from .models import Project

NOW = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"


class Unset:
    """Marks an argument that wasn't passed, where None is a meaningful value."""


UNSET = Unset()


def _to_project(row: sqlite3.Row) -> Project:
    return Project(
        id=row["id"],
        team_id=row["team_id"],
        name=row["name"],
        description=row["description"],
        deadline=row["deadline"],
        status=row["status"],
        daily_enabled=row["daily_enabled"] == 1,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class ProjectRepo:
    def __init__(self, db: sqlite3.Connection) -> None:
        self.db = db
        self._lock = lock_for(db)

    def list_projects(self, team_id: int | None) -> list[Project]:
        """A team's projects, or (`team_id=None`) projects without a team. Active first."""
        where = "team_id = ?" if team_id is not None else "team_id IS NULL"
        args = (team_id,) if team_id is not None else ()
        with self._lock:
            rows = self.db.execute(
                f"SELECT * FROM projects WHERE {where} ORDER BY status = 'done', position, id", args
            ).fetchall()
        return [_to_project(r) for r in rows]

    def get_project(self, project_id: int) -> Project | None:
        with self._lock:
            row = self.db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return _to_project(row) if row else None

    def create_project(self, team_id: int, name: str, description: str = "", deadline: date | None = None) -> Project:
        with self._lock:
            row = self.db.execute(
                """INSERT INTO projects (team_id, name, description, deadline, position)
                   VALUES (?, ?, ?, ?, (SELECT COALESCE(MAX(position), -1) + 1 FROM projects))
                   RETURNING *""",
                (team_id, name, description, deadline.isoformat() if deadline else None),
            ).fetchone()
        return _to_project(row)

    def update_project(
        self,
        project_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        deadline: date | None | Unset = UNSET,
        status: str | None = None,
        daily_enabled: bool | None = None,
        team_id: int | None | Unset = UNSET,
    ) -> Project | None:
        """Changes the given fields; returns the project, or None if it doesn't exist.
        Changing `team_id` also moves its lists (a trigger keeps them in sync)."""
        sets, args = [f"updated_at = {NOW}"], []
        for column, value in (("name", name), ("description", description), ("status", status)):
            if value is not None:
                sets.append(f"{column} = ?")
                args.append(value)
        if daily_enabled is not None:
            sets.append("daily_enabled = ?")
            args.append(int(daily_enabled))
        if not isinstance(deadline, Unset):
            sets.append("deadline = ?")
            args.append(deadline.isoformat() if deadline else None)
        if not isinstance(team_id, Unset):
            sets.append("team_id = ?")
            args.append(team_id)
        with self._lock:
            row = self.db.execute(
                f"UPDATE projects SET {', '.join(sets)} WHERE id = ? RETURNING *", (*args, project_id)
            ).fetchone()
        return _to_project(row) if row else None

    def delete_project(self, project_id: int) -> bool:
        """Deletes the project and (by cascade) its todo lists. False if it didn't exist."""
        with self._lock:
            return self.db.execute("DELETE FROM projects WHERE id = ?", (project_id,)).rowcount > 0
