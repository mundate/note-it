/**
 * A team's sprint schedule in the browser: mirrors backend/app/team/sprints.py (the first
 * sprint's start plus a length in weeks; sprints run back to back). Days are YYYY-MM-DD.
 */
import { parseDay, toDay } from "./day";

export type Sprint = { number: number; start: string; end: string };

const DAY_MS = 24 * 60 * 60 * 1000;

function addDays(day: string, days: number): string {
  const d = parseDay(day);
  d.setDate(d.getDate() + days);
  return toDay(d);
}

/** The sprint that `day` falls in, or null before the first sprint starts. */
export function sprintOn(day: string, start: string, weeks: number): Sprint | null {
  if (day < start) return null;
  const length = 7 * weeks;
  // Whole days between the two local dates (rounding absorbs daylight-saving hours).
  const elapsed = Math.round((parseDay(day).getTime() - parseDay(start).getTime()) / DAY_MS);
  const n = Math.floor(elapsed / length);
  const first = addDays(start, n * length);
  return { number: n + 1, start: first, end: addDays(first, length - 1) };
}

/** "Nov 2 – Nov 15" (years added when they aren't this year or differ). */
export function formatRange(start: string, end: string): string {
  const s = parseDay(start);
  const e = parseDay(end);
  const thisYear = new Date().getFullYear();
  const showYears = s.getFullYear() !== e.getFullYear() || e.getFullYear() !== thisYear;
  const fmt = (d: Date) =>
    d.toLocaleDateString(undefined, { month: "short", day: "numeric", ...(showYears ? { year: "numeric" } : {}) });
  return `${fmt(s)} – ${fmt(e)}`;
}

/** "Sprint 14" from a sprint list's name ("Sprint 14 · Nov 2 – Nov 15, 2026"). */
export function sprintTitle(name: string): string {
  return name.split(" · ")[0] ?? "Sprint";
}
