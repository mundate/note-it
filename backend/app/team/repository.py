"""Team repository: the only place that knows about the `teams` table."""

import sqlite3

from ..core.db import lock_for
from .models import Team

NOW = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"


def _to_team(row: sqlite3.Row) -> Team:
    return Team(id=row["id"], name=row["name"], created_at=row["created_at"], updated_at=row["updated_at"])


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

    def rename_team(self, team_id: int, name: str) -> Team | None:
        """Returns the renamed team, or None if it doesn't exist."""
        with self._lock:
            row = self.db.execute(
                f"UPDATE teams SET name = ?, updated_at = {NOW} WHERE id = ? RETURNING *", (name, team_id)
            ).fetchone()
        return _to_team(row) if row else None

    def delete_team(self, team_id: int) -> bool:
        """Deletes the team; whatever was assigned to it is kept, unassigned. Returns False
        if it didn't exist."""
        with self._lock:
            return self.db.execute("DELETE FROM teams WHERE id = ?", (team_id,)).rowcount > 0
