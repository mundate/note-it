from app.core.db import MIGRATIONS, migrate, open_db


def test_migrations_set_version_and_are_safe_to_rerun() -> None:
    db = open_db(":memory:")
    version = lambda: db.execute("PRAGMA user_version").fetchone()[0]  # noqa: E731
    assert version() == len(MIGRATIONS)
    migrate(db)
    assert version() == len(MIGRATIONS)



def test_schema_relationships() -> None:
    """Deleting a team unassigns its lists; deleting a list deletes its todos."""
    db = open_db(":memory:")
    (team,) = db.execute("INSERT INTO teams (name, position) VALUES ('T', 0) RETURNING id").fetchone()
    (lst,) = db.execute(
        "INSERT INTO todo_lists (name, team_id, position) VALUES ('L', ?, 0) RETURNING id", (team,)
    ).fetchone()
    db.execute("INSERT INTO todos (list_id, text, position) VALUES (?, 'a', 0)", (lst,))

    db.execute("DELETE FROM teams")
    assert db.execute("SELECT team_id FROM todo_lists").fetchone()[0] is None
    db.execute("DELETE FROM todo_lists")
    assert db.execute("SELECT COUNT(*) FROM todos").fetchone()[0] == 0


def test_repositories_on_one_connection_share_a_lock() -> None:
    from app.core.db import lock_for
    from app.team import TeamRepo
    from app.todo import TodoRepo

    db = open_db(":memory:")
    assert TeamRepo(db)._lock is TodoRepo(db)._lock is lock_for(db)
    assert lock_for(open_db(":memory:")) is not lock_for(db)
