"""Team repository: the only place that knows about the `teams` table."""

import sqlite3
from datetime import date

from ..core.db import lock_for
from .models import Team

NOW = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"


class Unset:
    """Marks an argument that wasn't passed, where None is a meaningful value."""


UNSET = Unset()


def _to_team(row: sqlite3.Row) -> Team:
    return Team(
        id=row["id"],
        name=row["name"],
        sprint_start=row["sprint_start"],
        sprint_weeks=row["sprint_weeks"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class TeamRepo:
    def __init__(self, db: sqlite3.Connection) -> None:
        self.db = db
        self._lock = lock_for(db)

    def list_teams(self) -> list[Team]:
        with self._lock:
            rows = self.db.execute("SELECT * FROM teams ORDER BY position, id").fetchall()
        return [_to_team(r) for r in rows]

    def get_team(self, team_id: int) -> Team | None:
        with self._lock:
            row = self.db.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone()
        return _to_team(row) if row else None

    def create_team(self, name: str) -> Team:
        with self._lock:
            row = self.db.execute(
                """INSERT INTO teams (name, position)
                   VALUES (?, (SELECT COALESCE(MAX(position), -1) + 1 FROM teams))
                   RETURNING *""",
                (name,),
            ).fetchone()
        return _to_team(row)

    def update_team(
        self,
        team_id: int,
        *,
        name: str | None = None,
        sprint_start: date | None | Unset = UNSET,
        sprint_weeks: int | None | Unset = UNSET,
    ) -> Team | None:
        """Changes the given fields; returns the team, or None if it doesn't exist."""
        sets, args = [f"updated_at = {NOW}"], []
        if name is not None:
            sets.append("name = ?")
            args.append(name)
        if not isinstance(sprint_start, Unset):
            sets.append("sprint_start = ?")
            args.append(sprint_start.isoformat() if sprint_start else None)
        if not isinstance(sprint_weeks, Unset):
            sets.append("sprint_weeks = ?")
            args.append(sprint_weeks)
        with self._lock:
            row = self.db.execute(
                f"UPDATE teams SET {', '.join(sets)} WHERE id = ? RETURNING *", (*args, team_id)
            ).fetchone()
        return _to_team(row) if row else None

    def delete_team(self, team_id: int) -> bool:
        """Deletes the team; whatever was assigned to it is kept, unassigned. Returns False
        if it didn't exist."""
        with self._lock:
            return self.db.execute("DELETE FROM teams WHERE id = ?", (team_id,)).rowcount > 0
