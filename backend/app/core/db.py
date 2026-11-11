"""SQLite connection and schema migrations."""

import os
import sqlite3
import threading
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = os.environ.get("DB_PATH", str(REPO_ROOT / "data" / "note-it.sqlite"))

# Default for created_at / updated_at columns: an ISO-8601 UTC timestamp.
TS = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"

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
    # 2: sprint lists and project status "done" -> "inactive".
    # - todo_lists: kind may be 'sprint'; `day`/`end_day` hold each period's first/last day;
    #   one list per project per period. (A CHECK can only change by rebuilding the table.)
    # - projects: status 'active' | 'inactive' (a project may only be set aside for a while).
    # - teams: sprint schedule = first sprint's start + length in weeks (both NULL = none).
    (
        # The trigger is attached to `projects` and writes `todo_lists`; drop it while both
        # tables are rebuilt and recreate it at the end.
        "DROP TRIGGER projects_team_follows_to_lists",
        # --- projects: status 'done' -> 'inactive' (a CHECK can only change by rebuilding) ---
        f"""
        CREATE TABLE projects_new (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          team_id     INTEGER REFERENCES teams (id) ON DELETE SET NULL,
          name        TEXT    NOT NULL,
          description TEXT    NOT NULL DEFAULT '',
          deadline    TEXT,
          status      TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
          daily_enabled INTEGER NOT NULL DEFAULT 0,
          position    INTEGER NOT NULL,
          created_at  TEXT    NOT NULL DEFAULT ({TS}),
          updated_at  TEXT    NOT NULL DEFAULT ({TS})
        )
        """,
        """
        INSERT INTO projects_new (id, team_id, name, description, deadline, status, daily_enabled, position, created_at, updated_at)
        SELECT id, team_id, name, description, deadline,
               CASE status WHEN 'done' THEN 'inactive' ELSE status END,
               daily_enabled, position, created_at, updated_at
        FROM projects
        """,
        "DROP TABLE projects",
        "ALTER TABLE projects_new RENAME TO projects",
        "CREATE INDEX projects_team ON projects (team_id)",
        # --- todo_lists: allow kind 'sprint' and store each period's end ---
        f"""
        CREATE TABLE todo_lists_new (
          id         INTEGER PRIMARY KEY AUTOINCREMENT,
          team_id    INTEGER REFERENCES teams (id) ON DELETE SET NULL,
          project_id INTEGER REFERENCES projects (id) ON DELETE CASCADE,
          kind       TEXT    NOT NULL DEFAULT 'standard' CHECK (kind IN ('standard', 'daily', 'sprint')),
          day        TEXT,
          end_day    TEXT,
          name       TEXT    NOT NULL,
          position   INTEGER NOT NULL,
          created_at TEXT    NOT NULL DEFAULT ({TS}),
          updated_at TEXT    NOT NULL DEFAULT ({TS}),
          CHECK (kind = 'standard' OR (project_id IS NOT NULL AND day IS NOT NULL))
        )
        """,
        """
        INSERT INTO todo_lists_new (id, team_id, project_id, kind, day, end_day, name, position, created_at, updated_at)
        SELECT id, team_id, project_id, kind, day, CASE kind WHEN 'daily' THEN day END, name, position, created_at, updated_at
        FROM todo_lists
        """,
        "DROP TABLE todo_lists",
        "ALTER TABLE todo_lists_new RENAME TO todo_lists",
        "CREATE INDEX todo_lists_team ON todo_lists (team_id)",
        "CREATE INDEX todo_lists_project ON todo_lists (project_id)",
        # One list per project per period (day for daily, sprint start for sprint).
        "CREATE UNIQUE INDEX todo_lists_period ON todo_lists (project_id, kind, day) WHERE kind <> 'standard'",
        """
        CREATE TRIGGER projects_team_follows_to_lists AFTER UPDATE OF team_id ON projects BEGIN
          UPDATE todo_lists SET team_id = NEW.team_id WHERE project_id = NEW.id;
        END
        """,
        # --- teams: sprint schedule (both NULL = no schedule) ---
        "ALTER TABLE teams ADD COLUMN sprint_start TEXT",
        "ALTER TABLE teams ADD COLUMN sprint_weeks INTEGER CHECK (sprint_weeks BETWEEN 1 AND 8)",
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

    if current == len(MIGRATIONS):
        return
    # Foreign keys are off while migrating, so a migration can rebuild a table (create new,
    # copy, drop old, rename) without the drop cascading into other tables. They can't be
    # switched inside a transaction, hence out here; each migration is checked before commit.
    db.execute("PRAGMA foreign_keys = OFF")
    try:
        for version in range(current + 1, len(MIGRATIONS) + 1):
            migration = MIGRATIONS[version - 1]
            with transaction(db):
                for statement in (migration,) if isinstance(migration, str) else migration:
                    db.execute(statement)
                problems = db.execute("PRAGMA foreign_key_check").fetchall()
                if problems:
                    raise RuntimeError(f"Migration {version} broke foreign keys: {[tuple(p) for p in problems]}")
                db.execute(f"PRAGMA user_version = {version}")
    finally:
        db.execute("PRAGMA foreign_keys = ON")
