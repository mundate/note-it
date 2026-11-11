from app.core.db import MIGRATIONS, migrate, open_db


def test_migrations_set_version_and_are_safe_to_rerun() -> None:
    db = open_db(":memory:")
    version = lambda: db.execute("PRAGMA user_version").fetchone()[0]  # noqa: E731
    assert version() == len(MIGRATIONS)
    migrate(db)
    assert version() == len(MIGRATIONS)
