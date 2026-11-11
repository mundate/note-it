import type { PeriodKind } from "@/api/todos";
import { formatDay } from "@/lib/day";
import { formatRange } from "@/lib/sprints";
import { cn } from "@/lib/utils";
import { Link } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { ReactNode } from "react";

/** The style of the header's small square buttons, for `actions` that should match them. */
export const navButton =
  "flex size-8 items-center justify-center rounded-md border outline-none transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring";
const disabledButton = "pointer-events-none opacity-40";

/** Whose period lists these are: one project's, or a team's combined view. */
export type PeriodOwner = { projectId: number } | { teamId: number };

const WORDS = {
  daily: { unit: "day", current: "Today", jump: "Jump to today" },
  sprint: { unit: "sprint", current: "Current", jump: "Jump to current sprint" },
} as const;

/** Link to one period's page, or (`start: null`) to the current one. */
function PeriodLink({
  kind,
  owner,
  start,
  ...props
}: { kind: PeriodKind; owner: PeriodOwner; start: string | null } & Omit<React.ComponentProps<"a">, "href">) {
  if ("projectId" in owner) {
    const params = { projectId: owner.projectId };
    if (kind === "daily") {
      return start ? <Link to="/projects/$projectId/daily/$day" params={{ ...params, day: start }} {...props} /> : <Link to="/projects/$projectId/daily" params={params} {...props} />;
    }
    return start ? <Link to="/projects/$projectId/sprint/$start" params={{ ...params, start }} {...props} /> : <Link to="/projects/$projectId/sprint" params={params} {...props} />;
  }
  const params = { teamId: owner.teamId };
  if (kind === "daily") {
    return start ? <Link to="/teams/$teamId/daily/$day" params={{ ...params, day: start }} {...props} /> : <Link to="/teams/$teamId/daily" params={params} {...props} />;
  }
  return start ? <Link to="/teams/$teamId/sprint/$start" params={{ ...params, start }} {...props} /> : <Link to="/teams/$teamId/sprint" params={params} {...props} />;
}

/**
 * Title, the period being shown (a day, or a sprint's dates), and links to the previous /
 * next existing period. `prev`/`next`/`start` are periods' first days.
 */
export function PeriodHeader({
  kind,
  owner,
  title,
  start,
  end,
  isCurrent,
  prev,
  next,
  actions,
}: {
  kind: PeriodKind;
  owner: PeriodOwner;
  /** e.g. "Daily" or "Sprint 14". */
  title: string;
  start: string;
  end: string;
  isCurrent: boolean;
  prev: string | null;
  next: string | null;
  /** Extra controls shown before the period buttons (e.g. a view toggle). */
  actions?: ReactNode;
}) {
  const words = WORDS[kind];
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="min-w-0 flex-1">
        <h1 className="text-3xl font-bold">{title}</h1>
        <p className="mt-1 flex items-center gap-2 text-muted-foreground">
          <span>{kind === "daily" ? formatDay(start) : formatRange(start, end)}</span>
          {isCurrent && (
            <span className="rounded-full bg-primary px-2 py-0.5 text-xs font-medium text-primary-foreground">{words.current}</span>
          )}
        </p>
      </div>
      {actions && <div className="flex items-center gap-1">{actions}</div>}
      <nav aria-label={kind === "daily" ? "Days" : "Sprints"} className="flex items-center gap-1">
        {prev ? (
          <PeriodLink kind={kind} owner={owner} start={prev} className={navButton} aria-label={`Previous ${words.unit}`} title={`Previous ${words.unit}`}>
            <ChevronLeft className="size-4" />
          </PeriodLink>
        ) : (
          <span className={cn(navButton, disabledButton)} aria-hidden>
            <ChevronLeft className="size-4" />
          </span>
        )}
        {next ? (
          <PeriodLink kind={kind} owner={owner} start={next} className={navButton} aria-label={`Next ${words.unit}`} title={`Next ${words.unit}`}>
            <ChevronRight className="size-4" />
          </PeriodLink>
        ) : (
          <span className={cn(navButton, disabledButton)} aria-hidden>
            <ChevronRight className="size-4" />
          </span>
        )}
        {!isCurrent && (
          <PeriodLink
            kind={kind}
            owner={owner}
            start={null}
            className="ml-1 rounded-md border px-3 py-1.5 text-sm outline-none transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring"
          >
            {words.jump}
          </PeriodLink>
        )}
      </nav>
    </div>
  );
}

export { PeriodLink };
