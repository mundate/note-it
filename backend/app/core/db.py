"""SQLite connection and schema migrations."""

import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = os.environ.get("DB_PATH", str(REPO_ROOT / "data" / "note-it.sqlite"))

# Schema migrations, applied in order. The index + 1 is the schema version stored in
# `PRAGMA user_version`. Only ever append; never edit a migration that has shipped.
# A migration is one SQL statement, or a tuple of statements run in one transaction.
MIGRATIONS: list[str | tuple[str, ...]] = [
    # 1: generic todo list
    """
    CREATE TABLE todos (
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      text       TEXT    NOT NULL,
      done       INTEGER NOT NULL DEFAULT 0,
      position   INTEGER NOT NULL,
      created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
      updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    )
    """,
    # 2: multiple todo lists. Every todo belongs to one list; existing todos move into a
    # "Todos" list. SQLite can't add a NOT NULL foreign key column, so `todos` is rebuilt.
    (
        """
        CREATE TABLE todo_lists (
          id         INTEGER PRIMARY KEY AUTOINCREMENT,
          name       TEXT    NOT NULL,
          position   INTEGER NOT NULL,
          created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
          updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        )
        """,
        "INSERT INTO todo_lists (name, position) SELECT 'Todos', 0 WHERE EXISTS (SELECT 1 FROM todos)",
        """
        CREATE TABLE todos_new (
          id         INTEGER PRIMARY KEY AUTOINCREMENT,
          list_id    INTEGER NOT NULL REFERENCES todo_lists (id) ON DELETE CASCADE,
          text       TEXT    NOT NULL,
          done       INTEGER NOT NULL DEFAULT 0,
          position   INTEGER NOT NULL,
          created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
          updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        )
        """,
        """
        INSERT INTO todos_new (id, list_id, text, done, position, created_at, updated_at)
        SELECT id, (SELECT id FROM todo_lists), text, done, position, created_at, updated_at FROM todos
        """,
        "DROP TABLE todos",
        "ALTER TABLE todos_new RENAME TO todos",
        "CREATE INDEX todos_list_position ON todos (list_id, position)",
    ),
]


def open_db(path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    # isolation_level=None: autocommit; multi-statement work uses `transaction()`.
    db = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode = WAL")
    db.execute("PRAGMA foreign_keys = ON")
    migrate(db)
    return db


@contextmanager
def transaction(db: sqlite3.Connection) -> Generator[None]:
    db.execute("BEGIN")
    try:
        yield
    except BaseException:
        db.execute("ROLLBACK")
        raise
    db.execute("COMMIT")


def migrate(db: sqlite3.Connection) -> None:
    (current,) = db.execute("PRAGMA user_version").fetchone()
    if current > len(MIGRATIONS):
        raise RuntimeError(f"Database schema v{current} is newer than this app (v{len(MIGRATIONS)})")

    for version in range(current + 1, len(MIGRATIONS) + 1):
        migration = MIGRATIONS[version - 1]
        with transaction(db):
            for statement in (migration,) if isinstance(migration, str) else migration:
                db.execute(statement)
            db.execute(f"PRAGMA user_version = {version}")
