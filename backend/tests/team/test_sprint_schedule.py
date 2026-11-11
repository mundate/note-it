"""Sprint schedule maths: the first sprint's start plus a length in weeks."""

from datetime import date

from app.team.sprints import Sprint, sprint_name, sprint_on

START = date(2026, 11, 2)  # a Monday


def test_before_the_first_sprint_there_is_none() -> None:
    assert sprint_on(date(2026, 11, 1), START, 2) is None


def test_two_week_sprints() -> None:
    assert sprint_on(START, START, 2) == Sprint(1, date(2026, 11, 2), date(2026, 11, 15))
    assert sprint_on(date(2026, 11, 15), START, 2) == Sprint(1, date(2026, 11, 2), date(2026, 11, 15))  # last day
    assert sprint_on(date(2026, 11, 16), START, 2) == Sprint(2, date(2026, 11, 16), date(2026, 11, 29))
    assert sprint_on(date(2027, 1, 11), START, 2) == Sprint(6, date(2027, 1, 11), date(2027, 1, 24))


def test_other_lengths() -> None:
    assert sprint_on(date(2026, 11, 9), START, 1) == Sprint(2, date(2026, 11, 9), date(2026, 11, 15))
    assert sprint_on(date(2026, 11, 23), START, 3) == Sprint(2, date(2026, 11, 23), date(2026, 12, 13))


def test_names() -> None:
    assert sprint_name(Sprint(14, date(2026, 11, 2), date(2026, 11, 15))) == "Sprint 14 · Nov 2 – Nov 15, 2026"
    assert sprint_name(Sprint(3, date(2026, 12, 28), date(2027, 1, 10))) == "Sprint 3 · Dec 28, 2026 – Jan 10, 2027"
