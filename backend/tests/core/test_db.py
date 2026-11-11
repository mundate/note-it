import pytest

from app.core.db import MIGRATIONS, migrate, open_db


def test_migrations_set_version_and_are_safe_to_rerun() -> None:
    db = open_db(":memory:")
    version = lambda: db.execute("PRAGMA user_version").fetchone()[0]  # noqa: E731
    assert version() == len(MIGRATIONS)
    migrate(db)
    assert version() == len(MIGRATIONS)



def test_schema_relationships() -> None:
    """Deleting a team keeps its projects and lists; a project's team follows to its lists;
    deleting a project deletes its lists, and deleting a list deletes its todos."""
    db = open_db(":memory:")
    (t1,) = db.execute("INSERT INTO teams (name, position) VALUES ('T1', 0) RETURNING id").fetchone()
    (t2,) = db.execute("INSERT INTO teams (name, position) VALUES ('T2', 1) RETURNING id").fetchone()
    (proj,) = db.execute("INSERT INTO projects (team_id, name, position) VALUES (?, 'P', 0) RETURNING id", (t1,)).fetchone()
    (in_proj,) = db.execute(
        "INSERT INTO todo_lists (name, team_id, project_id, position) VALUES ('A', ?, ?, 0) RETURNING id", (t1, proj)
    ).fetchone()
    (loose,) = db.execute("INSERT INTO todo_lists (name, team_id, position) VALUES ('B', ?, 1) RETURNING id", (t1,)).fetchone()
    db.execute("INSERT INTO todos (list_id, text, position) VALUES (?, 'a', 0)", (in_proj,))

    db.execute("UPDATE projects SET team_id = ? WHERE id = ?", (t2, proj))
    assert db.execute("SELECT team_id FROM todo_lists WHERE id = ?", (in_proj,)).fetchone()[0] == t2

    db.execute("DELETE FROM teams")
    assert db.execute("SELECT team_id FROM projects").fetchone()[0] is None
    assert [tuple(r) for r in db.execute("SELECT id, team_id FROM todo_lists ORDER BY id")] == [(in_proj, None), (loose, None)]

    db.execute("DELETE FROM projects")
    assert [r[0] for r in db.execute("SELECT id FROM todo_lists")] == [loose]
    assert db.execute("SELECT COUNT(*) FROM todos").fetchone()[0] == 0


def test_daily_list_rules_are_enforced_by_the_schema() -> None:
    import sqlite3

    db = open_db(":memory:")
    db.execute("INSERT INTO projects (name, position) VALUES ('P', 0)")
    db.execute("INSERT INTO todo_lists (name, project_id, kind, day, position) VALUES ('D', 1, 'daily', '2026-11-10', 0)")
    for bad in (
        "INSERT INTO todo_lists (name, project_id, kind, day, position) VALUES ('D2', 1, 'daily', '2026-11-10', 1)",  # same day
        "INSERT INTO todo_lists (name, kind, day, position) VALUES ('D3', 'daily', '2026-11-11', 2)",  # no project
        "INSERT INTO todo_lists (name, project_id, kind, position) VALUES ('D4', 1, 'daily', 3)",  # no day
        "INSERT INTO todo_lists (name, kind, position) VALUES ('X', 'weekly', 4)",
        "INSERT INTO projects (name, status, position) VALUES ('Q', 'done', 1)",
    ):
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(bad)


def test_repositories_on_one_connection_share_a_lock() -> None:
    from app.core.db import lock_for
    from app.project import ProjectRepo
    from app.team import TeamRepo
    from app.todo import TodoRepo

    db = open_db(":memory:")
    assert TeamRepo(db)._lock is ProjectRepo(db)._lock is TodoRepo(db)._lock is lock_for(db)
    assert lock_for(open_db(":memory:")) is not lock_for(db)


def test_migration_2_keeps_every_row_and_renames_done_projects() -> None:
    import sqlite3

    db = sqlite3.connect(":memory:", isolation_level=None)
    db.execute("PRAGMA foreign_keys = ON")
    for sql in MIGRATIONS[0]:
        db.execute(sql)
    db.execute("PRAGMA user_version = 1")
    db.execute("INSERT INTO teams (name, position) VALUES ('T', 0)")
    db.execute("INSERT INTO projects (team_id, name, status, daily_enabled, position) VALUES (1, 'Live', 'active', 1, 0)")
    db.execute("INSERT INTO projects (team_id, name, status, position) VALUES (1, 'Old', 'done', 1)")
    db.execute("INSERT INTO todo_lists (team_id, project_id, name, position) VALUES (1, 1, 'Std', 0)")
    db.execute("INSERT INTO todo_lists (team_id, project_id, kind, day, name, position) VALUES (1, 1, 'daily', '2026-11-10', 'D', 1)")
    db.execute("INSERT INTO todos (list_id, text, done, position) VALUES (1, 'a', 0, 0), (2, 'b', 1, 0)")
    todos_before = db.execute("SELECT * FROM todos ORDER BY id").fetchall()

    migrate(db)
    assert db.execute("PRAGMA user_version").fetchone()[0] == len(MIGRATIONS)
    assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert db.execute("SELECT * FROM todos ORDER BY id").fetchall() == todos_before
    assert db.execute("SELECT id, status FROM projects ORDER BY id").fetchall() == [(1, "active"), (2, "inactive")]
    assert db.execute("SELECT id, kind, day, end_day FROM todo_lists ORDER BY id").fetchall() == [
        (1, "standard", None, None),
        (2, "daily", "2026-11-10", "2026-11-10"),
    ]
    assert db.execute("SELECT sprint_start, sprint_weeks FROM teams").fetchone() == (None, None)

    # The rebuilt tables keep their rules: trigger, cascade, unique periods, kinds and statuses.
    db.execute("INSERT INTO teams (name, position) VALUES ('T2', 1)")
    db.execute("UPDATE projects SET team_id = 2 WHERE id = 1")
    assert {r[0] for r in db.execute("SELECT team_id FROM todo_lists")} == {2}
    db.execute("INSERT INTO todo_lists (project_id, kind, day, end_day, name, position) VALUES (1, 'sprint', '2026-11-02', '2026-11-15', 'S', 2)")
    for bad in (
        "INSERT INTO todo_lists (project_id, kind, day, name, position) VALUES (1, 'sprint', '2026-11-02', 'S2', 3)",
        "INSERT INTO todo_lists (name, kind, position) VALUES ('X', 'weekly', 4)",
        "INSERT INTO projects (name, status, position) VALUES ('P', 'done', 2)",
        "UPDATE teams SET sprint_weeks = 9",
    ):
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(bad)
    db.execute("DELETE FROM projects WHERE id = 1")
    assert db.execute("SELECT COUNT(*) FROM todo_lists").fetchone()[0] == 0
    assert db.execute("SELECT COUNT(*) FROM todos").fetchone()[0] == 0
