"""SQLite connection and schema migrations."""

import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = os.environ.get("DB_PATH", str(REPO_ROOT / "data" / "note-it.sqlite"))

# Schema migrations, applied in order. The index + 1 is the schema version stored in
# `PRAGMA user_version`. Only ever append; never edit a migration that has shipped.
MIGRATIONS: list[str] = [
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
        with transaction(db):
            db.execute(MIGRATIONS[version - 1])
            db.execute(f"PRAGMA user_version = {version}")
