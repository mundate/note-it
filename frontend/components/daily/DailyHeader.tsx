import { formatDay } from "@/lib/day";
import { cn } from "@/lib/utils";
import { Link } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { ReactNode } from "react";

/** The style of the header's small square buttons, for `actions` that should match them. */
export const navButton =
  "flex size-8 items-center justify-center rounded-md border outline-none transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring";
const disabledButton = "pointer-events-none opacity-40";

/** Whose daily list this is: one project's, or a team's combined view. */
export type DailyOwner = { projectId: number } | { teamId: number };

function DayLink({ owner, day, ...props }: { owner: DailyOwner; day: string | null } & Omit<React.ComponentProps<"a">, "href">) {
  // `day: null` is today (the page that opens today's list).
  if ("projectId" in owner) {
    return day ? (
      <Link to="/projects/$projectId/daily/$day" params={{ projectId: owner.projectId, day }} {...props} />
    ) : (
      <Link to="/projects/$projectId/daily" params={{ projectId: owner.projectId }} {...props} />
    );
  }
  return day ? (
    <Link to="/teams/$teamId/daily/$day" params={{ teamId: owner.teamId, day }} {...props} />
  ) : (
    <Link to="/teams/$teamId/daily" params={{ teamId: owner.teamId }} {...props} />
  );
}

/** "Daily" title, the day being shown, and links to the previous / next existing day. */
export function DailyHeader({
  owner,
  title = "Daily",
  day,
  isToday,
  prevDay,
  nextDay,
  actions,
}: {
  owner: DailyOwner;
  title?: string;
  day: string;
  isToday: boolean;
  prevDay: string | null;
  nextDay: string | null;
  /** Extra controls shown before the day buttons (e.g. a view toggle). */
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="min-w-0 flex-1">
        <h1 className="text-3xl font-bold">{title}</h1>
        <p className="mt-1 flex items-center gap-2 text-muted-foreground">
          <span>{formatDay(day)}</span>
          {isToday && (
            <span className="rounded-full bg-primary px-2 py-0.5 text-xs font-medium text-primary-foreground">Today</span>
          )}
        </p>
      </div>
      {actions && <div className="flex items-center gap-1">{actions}</div>}
      <nav aria-label="Days" className="flex items-center gap-1">
        {prevDay ? (
          <DayLink owner={owner} day={prevDay} className={navButton} aria-label="Previous day" title="Previous day">
            <ChevronLeft className="size-4" />
          </DayLink>
        ) : (
          <span className={cn(navButton, disabledButton)} aria-hidden>
            <ChevronLeft className="size-4" />
          </span>
        )}
        {nextDay ? (
          <DayLink owner={owner} day={nextDay} className={navButton} aria-label="Next day" title="Next day">
            <ChevronRight className="size-4" />
          </DayLink>
        ) : (
          <span className={cn(navButton, disabledButton)} aria-hidden>
            <ChevronRight className="size-4" />
          </span>
        )}
        {!isToday && (
          <DayLink
            owner={owner}
            day={null}
            className="ml-1 rounded-md border px-3 py-1.5 text-sm outline-none transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring"
          >
            Jump to today
          </DayLink>
        )}
      </nav>
    </div>
  );
}
