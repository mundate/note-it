"""Todo repository: the only place that knows about the `todo_lists` and `todos` tables."""

import sqlite3
from datetime import date

from ..core.db import lock_for, transaction
from .models import PeriodKind, Todo, TodoList

NOW = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"

# A list row plus its todo counts.
LIST_SELECT = """
    SELECT l.*,
           (SELECT COUNT(*) FROM todos t WHERE t.list_id = l.id AND t.done = 0) AS open_count,
           (SELECT COUNT(*) FROM todos t WHERE t.list_id = l.id AND t.done = 1) AS done_count
    FROM todo_lists l
"""


class Unset:
    """Marks an argument that wasn't passed, where None is a meaningful value."""


UNSET = Unset()


def _to_list(row: sqlite3.Row) -> TodoList:
    return TodoList(
        id=row["id"],
        name=row["name"],
        team_id=row["team_id"],
        project_id=row["project_id"],
        kind=row["kind"],
        day=row["day"],
        end_day=row["end_day"],
        open_count=row["open_count"],
        done_count=row["done_count"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _to_todo(row: sqlite3.Row) -> Todo:
    return Todo(
        id=row["id"],
        text=row["text"],
        done=row["done"] == 1,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class TodoRepo:
    def __init__(self, db: sqlite3.Connection) -> None:
        self.db = db
        self._lock = lock_for(db)  # shared with other repositories on this connection

    # ---------- lists ----------

    def list_lists(self, team_id: int | None = None, project_id: int | None | Unset = UNSET) -> list[TodoList]:
        """Standard lists (daily lists are left out), optionally filtered by team and/or
        project; `project_id=None` means lists that aren't in a project."""
        where, args = ["l.kind = 'standard'"], []
        if team_id is not None:
            where.append("l.team_id = ?")
            args.append(team_id)
        if project_id is None:
            where.append("l.project_id IS NULL")
        elif not isinstance(project_id, Unset):
            where.append("l.project_id = ?")
            args.append(project_id)
        with self._lock:
            rows = self.db.execute(
                f"{LIST_SELECT} WHERE {' AND '.join(where)} ORDER BY l.position, l.id", args
            ).fetchall()
        return [_to_list(r) for r in rows]

    def get_list(self, list_id: int) -> TodoList | None:
        with self._lock:
            row = self.db.execute(f"{LIST_SELECT} WHERE l.id = ?", (list_id,)).fetchone()
        return _to_list(row) if row else None

    def create_list(self, name: str, team_id: int | None = None, project_id: int | None = None) -> TodoList:
        with self._lock:
            (list_id,) = self.db.execute(
                """INSERT INTO todo_lists (name, team_id, project_id, position)
                   VALUES (?, ?, ?, (SELECT COALESCE(MAX(position), -1) + 1 FROM todo_lists))
                   RETURNING id""",
                (name, team_id, project_id),
            ).fetchone()
        list_ = self.get_list(list_id)
        assert list_ is not None
        return list_

    def update_list(
        self,
        list_id: int,
        *,
        name: str | None = None,
        team_id: int | None | Unset = UNSET,
        project_id: int | None | Unset = UNSET,
    ) -> TodoList | None:
        """Changes the given fields (None takes the list off its team / project). Returns the
        updated list, or None if it doesn't exist."""
        sets, args = [f"updated_at = {NOW}"], []
        if name is not None:
            sets.append("name = ?")
            args.append(name)
        for column, value in (("team_id", team_id), ("project_id", project_id)):
            if not isinstance(value, Unset):
                sets.append(f"{column} = ?")
                args.append(value)
        with self._lock:
            changed = self.db.execute(
                f"UPDATE todo_lists SET {', '.join(sets)} WHERE id = ?", (*args, list_id)
            ).rowcount
        return self.get_list(list_id) if changed else None

    # ---------- period lists: daily (one per day) and sprint (one per sprint) ----------
    # A period list belongs to a project; `day` is its first day and `end_day` its last.

    def list_periods(self, kind: PeriodKind, project_id: int) -> list[TodoList]:
        """A project's daily or sprint lists, newest first."""
        with self._lock:
            rows = self.db.execute(
                f"{LIST_SELECT} WHERE l.kind = ? AND l.project_id = ? ORDER BY l.day DESC", (kind, project_id)
            ).fetchall()
        return [_to_list(r) for r in rows]

    def open_period(
        self, kind: PeriodKind, project_id: int, team_id: int | None, start: date, end: date, name: str
    ) -> TodoList:
        """Gets (or creates) the project's `kind` list for the period starting `start`, then
        moves unfinished todos from the project's other lists of that kind onto it (oldest
        first, after its own todos). Daily takes them from earlier days; sprint from every
        other sprint, so a moved schedule still carries everything into the current sprint.
        Runs on every open, so other periods only ever keep finished todos."""
        iso = start.isoformat()
        with self._lock, transaction(self.db):
            row = self.db.execute(
                "SELECT id, name, end_day FROM todo_lists WHERE kind = ? AND project_id = ? AND day = ?",
                (kind, project_id, iso),
            ).fetchone()
            if row:
                list_id = row["id"]
                if (row["name"], row["end_day"]) != (name, end.isoformat()):
                    # The schedule changed (e.g. shifted by whole sprints): same start, new
                    # number / length. Keep the open period's name and end in step with it.
                    self.db.execute(
                        "UPDATE todo_lists SET name = ?, end_day = ? WHERE id = ?", (name, end.isoformat(), list_id)
                    )
            else:
                (list_id,) = self.db.execute(
                    """INSERT INTO todo_lists (name, team_id, project_id, kind, day, end_day, position)
                       VALUES (?, ?, ?, ?, ?, ?, (SELECT COALESCE(MAX(position), -1) + 1 FROM todo_lists))
                       RETURNING id""",
                    (name, team_id, project_id, kind, iso, end.isoformat()),
                ).fetchone()

            source = "l.day < ?" if kind == "daily" else "l.id <> ?"
            carried = self.db.execute(
                f"""SELECT t.id FROM todos t JOIN todo_lists l ON l.id = t.list_id
                    WHERE l.kind = ? AND l.project_id = ? AND {source} AND t.done = 0
                    ORDER BY l.day, t.position, t.id""",
                (kind, project_id, iso if kind == "daily" else list_id),
            ).fetchall()
            if carried:
                (first,) = self.db.execute(
                    "SELECT COALESCE(MAX(position), -1) + 1 FROM todos WHERE list_id = ?", (list_id,)
                ).fetchone()
                self.db.executemany(
                    "UPDATE todos SET list_id = ?, position = ? WHERE id = ?",
                    [(list_id, first + i, r["id"]) for i, r in enumerate(carried)],
                )
            row = self.db.execute(f"{LIST_SELECT} WHERE l.id = ?", (list_id,)).fetchone()
        return _to_list(row)

    def team_period_starts(self, kind: PeriodKind, team_id: int) -> list[str]:
        """First days of the periods with a `kind` list in any of the team's projects, newest first."""
        with self._lock:
            rows = self.db.execute(
                "SELECT DISTINCT day FROM todo_lists WHERE kind = ? AND team_id = ? ORDER BY day DESC",
                (kind, team_id),
            ).fetchall()
        return [r["day"] for r in rows]

    def team_period_lists(self, kind: PeriodKind, team_id: int, start: date) -> list[TodoList]:
        """The `kind` lists starting on `start` across the team's projects, in project order."""
        with self._lock:
            rows = self.db.execute(
                f"""{LIST_SELECT} JOIN projects p ON p.id = l.project_id
                    WHERE l.kind = ? AND l.team_id = ? AND l.day = ?
                    ORDER BY p.status = 'inactive', p.position, p.id""",
                (kind, team_id, start.isoformat()),
            ).fetchall()
        return [_to_list(r) for r in rows]

    def delete_list(self, list_id: int) -> bool:
        """Deletes the list and its todos. Returns False if the list didn't exist."""
        with self._lock:
            return self.db.execute("DELETE FROM todo_lists WHERE id = ?", (list_id,)).rowcount > 0

    # ---------- todos (always scoped to a list) ----------

    def list_todos(self, list_id: int) -> list[Todo]:
        with self._lock:
            rows = self.db.execute(
                "SELECT * FROM todos WHERE list_id = ? ORDER BY done, position, id", (list_id,)
            ).fetchall()
        return [_to_todo(r) for r in rows]

    def create_todo(self, list_id: int, text: str) -> Todo:
        with self._lock:
            row = self.db.execute(
                """INSERT INTO todos (list_id, text, position)
                   VALUES (?, ?, (SELECT COALESCE(MAX(position), -1) + 1 FROM todos WHERE list_id = ?))
                   RETURNING *""",
                (list_id, text, list_id),
            ).fetchone()
        return _to_todo(row)

    def update_todo(
        self, list_id: int, todo_id: int, *, text: str | None = None, done: bool | None = None
    ) -> Todo | None:
        """Returns the updated todo, or None if it doesn't exist in that list."""
        with self._lock:
            row = self.db.execute(
                f"""UPDATE todos
                    SET text       = COALESCE(?, text),
                        done       = COALESCE(?, done),
                        updated_at = {NOW}
                    WHERE id = ? AND list_id = ?
                    RETURNING *""",
                (text, None if done is None else int(done), todo_id, list_id),
            ).fetchone()
        return _to_todo(row) if row else None

    def delete_todo(self, list_id: int, todo_id: int) -> bool:
        """Returns False if the todo didn't exist in that list."""
        with self._lock:
            return (
                self.db.execute("DELETE FROM todos WHERE id = ? AND list_id = ?", (todo_id, list_id)).rowcount > 0
            )

    def reorder_todos(self, list_id: int, ids: list[int]) -> list[int]:
        """`ids` move to the front of the list in the given order; the list's other todos keep
        their relative order after them. Returns the ids that aren't in the list, changing
        nothing if there are any."""
        with self._lock:
            existing = [
                r["id"]
                for r in self.db.execute("SELECT id FROM todos WHERE list_id = ? ORDER BY position, id", (list_id,))
            ]
            known = set(existing)
            missing = [i for i in ids if i not in known]
            if missing:
                return missing

            moved = set(ids)
            order = ids + [i for i in existing if i not in moved]
            with transaction(self.db):
                self.db.executemany(
                    "UPDATE todos SET position = ? WHERE id = ?",
                    [(position, todo_id) for position, todo_id in enumerate(order)],
                )
            return []
