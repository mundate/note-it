"""SQLite connection and schema migrations."""

import os
import sqlite3
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = os.environ.get("DB_PATH", str(REPO_ROOT / "data" / "note-it.sqlite"))

# Schema migrations, applied in order. The index + 1 is the schema version stored in
# `PRAGMA user_version`. Only ever append; never edit a migration that has shipped.
# A migration is one SQL statement, or a tuple of statements run in one transaction.
MIGRATIONS: list[str | tuple[str, ...]] = [
    # 1: initial schema.
    # - Teams are optional and shared across features: deleting a team keeps its projects
    #   and lists (SET NULL).
    # - A project belongs to at most one team; its lists carry the project's team (kept in
    #   sync by the trigger). Deleting a project deletes its lists (CASCADE).
    # - A daily list (kind = 'daily') is one list per project per day.
    (
        """
        CREATE TABLE teams (
          id         INTEGER PRIMARY KEY AUTOINCREMENT,
          name       TEXT    NOT NULL,
          position   INTEGER NOT NULL,
          created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
          updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        )
        """,
        """
        CREATE TABLE projects (
          id            INTEGER PRIMARY KEY AUTOINCREMENT,
          team_id       INTEGER REFERENCES teams (id) ON DELETE SET NULL,
          name          TEXT    NOT NULL,
          description   TEXT    NOT NULL DEFAULT '',
          deadline      TEXT,
          status        TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'done')),
          daily_enabled INTEGER NOT NULL DEFAULT 0,
          position      INTEGER NOT NULL,
          created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
          updated_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        )
        """,
        """
        CREATE TABLE todo_lists (
          id         INTEGER PRIMARY KEY AUTOINCREMENT,
          team_id    INTEGER REFERENCES teams (id) ON DELETE SET NULL,
          project_id INTEGER REFERENCES projects (id) ON DELETE CASCADE,
          kind       TEXT    NOT NULL DEFAULT 'standard' CHECK (kind IN ('standard', 'daily')),
          day        TEXT,
          name       TEXT    NOT NULL,
          position   INTEGER NOT NULL,
          created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
          updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
          CHECK (kind = 'standard' OR (project_id IS NOT NULL AND day IS NOT NULL))
        )
        """,
        """
        CREATE TABLE todos (
          id         INTEGER PRIMARY KEY AUTOINCREMENT,
          list_id    INTEGER NOT NULL REFERENCES todo_lists (id) ON DELETE CASCADE,
          text       TEXT    NOT NULL,
          done       INTEGER NOT NULL DEFAULT 0,
          position   INTEGER NOT NULL,
          created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
          updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
        )
        """,
        "CREATE INDEX projects_team ON projects (team_id)",
        "CREATE INDEX todo_lists_team ON todo_lists (team_id)",
        "CREATE INDEX todo_lists_project ON todo_lists (project_id)",
        "CREATE UNIQUE INDEX todo_lists_daily_day ON todo_lists (project_id, day) WHERE kind = 'daily'",
        "CREATE INDEX todos_list_position ON todos (list_id, position)",
        """
        CREATE TRIGGER projects_team_follows_to_lists AFTER UPDATE OF team_id ON projects BEGIN
          UPDATE todo_lists SET team_id = NEW.team_id WHERE project_id = NEW.id;
        END
        """,
    ),
]


class Connection(sqlite3.Connection):
    """A connection that carries the lock its repositories share (see `lock_for`)."""

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        super().__init__(*args, **kwargs)
        self.lock = threading.Lock()


def lock_for(db: sqlite3.Connection) -> threading.Lock:
    """The lock shared by every repository on `db`. FastAPI runs sync endpoints in a thread
    pool, so each repository operation (and transaction) holds this lock; one lock per
    connection keeps one repository's statements out of another's transaction."""
    if not isinstance(db, Connection):
        raise TypeError("Repositories need a connection from open_db()")
    return db.lock


def open_db(path: str = DEFAULT_DB_PATH) -> Connection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    # isolation_level=None: autocommit; multi-statement work uses `transaction()`.
    db = sqlite3.connect(path, check_same_thread=False, isolation_level=None, factory=Connection)
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
