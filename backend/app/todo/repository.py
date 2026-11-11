"""Todo repository: the only place that knows about the `todo_lists` and `todos` tables."""

import sqlite3

from ..core.db import lock_for, transaction
from .models import Todo, TodoList

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

    def list_lists(self, team_id: int | None = None) -> list[TodoList]:
        """All lists, or only one team's when `team_id` is given."""
        where, args = ("WHERE l.team_id = ?", (team_id,)) if team_id is not None else ("", ())
        with self._lock:
            rows = self.db.execute(f"{LIST_SELECT} {where} ORDER BY l.position, l.id", args).fetchall()
        return [_to_list(r) for r in rows]

    def get_list(self, list_id: int) -> TodoList | None:
        with self._lock:
            row = self.db.execute(f"{LIST_SELECT} WHERE l.id = ?", (list_id,)).fetchone()
        return _to_list(row) if row else None

    def create_list(self, name: str, team_id: int | None = None) -> TodoList:
        with self._lock:
            (list_id,) = self.db.execute(
                """INSERT INTO todo_lists (name, team_id, position)
                   VALUES (?, ?, (SELECT COALESCE(MAX(position), -1) + 1 FROM todo_lists))
                   RETURNING id""",
                (name, team_id),
            ).fetchone()
        list_ = self.get_list(list_id)
        assert list_ is not None
        return list_

    def update_list(
        self, list_id: int, *, name: str | None = None, team_id: int | None | Unset = UNSET
    ) -> TodoList | None:
        """Changes the given fields (`team_id=None` takes the list off its team). Returns the
        updated list, or None if it doesn't exist."""
        sets, args = [f"updated_at = {NOW}"], []
        if name is not None:
            sets.append("name = ?")
            args.append(name)
        if not isinstance(team_id, Unset):
            sets.append("team_id = ?")
            args.append(team_id)
        with self._lock:
            changed = self.db.execute(
                f"UPDATE todo_lists SET {', '.join(sets)} WHERE id = ?", (*args, list_id)
            ).rowcount
        return self.get_list(list_id) if changed else None

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
