/** Helpers for daily-list days, which the API sends as local `YYYY-MM-DD` strings. */

export const DAY_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

/** Parses `YYYY-MM-DD` as a local date (`new Date("2026-11-10")` would be UTC midnight, a day early in the Americas). */
export function parseDay(day: string): Date {
  const [y, m, d] = day.split("-").map(Number) as [number, number, number];
  return new Date(y, m - 1, d);
}

export function isValidDay(day: string): boolean {
  if (!DAY_PATTERN.test(day)) return false;
  const date = parseDay(day);
  return toDay(date) === day; // rejects e.g. 2026-02-31
}

export function toDay(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/** "Tuesday, November 10" (the year is added when it isn't this year). */
export function formatDay(day: string): string {
  const date = parseDay(day);
  const sameYear = date.getFullYear() === new Date().getFullYear();
  return date.toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
    ...(sameYear ? {} : { year: "numeric" }),
  });
}
