"""Todo repository: the only place that knows about the `todos` table."""

import sqlite3
import threading

from .db import transaction
from .models import Todo

NOW = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"


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
        # FastAPI runs sync endpoints in a thread pool; one lock keeps each operation
        # (and each transaction) on the shared connection atomic.
        self._lock = threading.Lock()

    def list_todos(self) -> list[Todo]:
        with self._lock:
            rows = self.db.execute("SELECT * FROM todos ORDER BY done, position, id").fetchall()
        return [_to_todo(r) for r in rows]

    def create_todo(self, text: str) -> Todo:
        with self._lock:
            row = self.db.execute(
                """INSERT INTO todos (text, position)
                   VALUES (?, (SELECT COALESCE(MAX(position), -1) + 1 FROM todos))
                   RETURNING *""",
                (text,),
            ).fetchone()
        return _to_todo(row)

    def update_todo(self, todo_id: int, *, text: str | None = None, done: bool | None = None) -> Todo | None:
        """Returns the updated todo, or None if it doesn't exist."""
        with self._lock:
            row = self.db.execute(
                f"""UPDATE todos
                    SET text       = COALESCE(?, text),
                        done       = COALESCE(?, done),
                        updated_at = {NOW}
                    WHERE id = ?
                    RETURNING *""",
                (text, None if done is None else int(done), todo_id),
            ).fetchone()
        return _to_todo(row) if row else None

    def delete_todo(self, todo_id: int) -> bool:
        """Returns False if the todo didn't exist."""
        with self._lock:
            return self.db.execute("DELETE FROM todos WHERE id = ?", (todo_id,)).rowcount > 0

    def reorder_todos(self, ids: list[int]) -> list[int]:
        """`ids` move to the front in the given order; all other todos keep their relative
        order after them. Returns the ids that don't exist, changing nothing if there are any."""
        with self._lock:
            existing = [r["id"] for r in self.db.execute("SELECT id FROM todos ORDER BY position, id")]
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
