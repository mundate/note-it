import sqlite3

from app.core.db import MIGRATIONS, migrate, open_db


def test_migrations_set_version_and_are_safe_to_rerun() -> None:
    db = open_db(":memory:")
    version = lambda: db.execute("PRAGMA user_version").fetchone()[0]  # noqa: E731
    assert version() == len(MIGRATIONS)
    migrate(db)
    assert version() == len(MIGRATIONS)


def _db_at_version(version: int) -> sqlite3.Connection:
    db = sqlite3.connect(":memory:", isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    for statement in MIGRATIONS[:version]:
        for sql in (statement,) if isinstance(statement, str) else statement:
            db.execute(sql)
    db.execute(f"PRAGMA user_version = {version}")
    return db


def test_migration_2_moves_existing_todos_into_a_list() -> None:
    db = _db_at_version(1)
    db.execute("INSERT INTO todos (text, done, position) VALUES ('a', 0, 1), ('b', 1, 0)")
    migrate(db)

    lists = db.execute("SELECT id, name FROM todo_lists").fetchall()
    assert [tuple(r) for r in lists] == [(1, "Todos")]
    rows = db.execute("SELECT id, list_id, text, done, position FROM todos ORDER BY id").fetchall()
    assert [tuple(r) for r in rows] == [(1, 1, "a", 0, 1), (2, 1, "b", 1, 0)]

    # Ids keep counting up from the old table's, and deleting the list cascades.
    (new_id,) = db.execute("INSERT INTO todos (list_id, text, position) VALUES (1, 'c', 2) RETURNING id").fetchone()
    assert new_id == 3
    db.execute("DELETE FROM todo_lists")
    assert db.execute("SELECT COUNT(*) FROM todos").fetchone()[0] == 0


def test_migration_2_on_an_empty_db_creates_no_list() -> None:
    db = _db_at_version(1)
    migrate(db)
    assert db.execute("SELECT COUNT(*) FROM todo_lists").fetchone()[0] == 0
