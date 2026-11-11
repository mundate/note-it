"""A team's sprint schedule: the first sprint's start date plus a length in weeks. Sprints
run back to back from the start (Sprint 1, 2, 3, ...). Pure date maths, no database."""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class Sprint:
    number: int  # 1-based
    start: date
    end: date  # inclusive (the sprint's last day)


def sprint_on(day: date, start: date, weeks: int) -> Sprint | None:
    """The sprint that `day` falls in, or None before the first sprint starts."""
    if day < start:
        return None
    length = 7 * weeks
    n = (day - start).days // length
    first = start + timedelta(days=n * length)
    return Sprint(number=n + 1, start=first, end=first + timedelta(days=length - 1))


def sprint_name(sprint: Sprint) -> str:
    """e.g. "Sprint 14 · Nov 3 – Nov 16, 2026" (the start's year is shown if it differs)."""
    start = f"{sprint.start:%b} {sprint.start.day}"
    if sprint.start.year != sprint.end.year:
        start += f", {sprint.start.year}"
    return f"Sprint {sprint.number} · {start} – {sprint.end:%b} {sprint.end.day}, {sprint.end.year}"
