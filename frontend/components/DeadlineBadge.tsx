import type { Project } from "@/api/client";
import { formatDay, parseDay, toDay } from "@/lib/day";
import { cn } from "@/lib/utils";
import { CalendarClock, Pause } from "lucide-react";

/** "Inactive", "Overdue · Tue, Dec 15" or "Due Tue, Dec 15" for a project; nothing without a deadline. */
export function DeadlineBadge({ project, className }: { project: Pick<Project, "deadline" | "status">; className?: string }) {
  const base = "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium";
  if (project.status === "inactive") {
    return (
      <span className={cn(base, "bg-secondary text-secondary-foreground", className)} title="Not being worked on right now">
        <Pause className="size-3" /> Inactive
      </span>
    );
  }
  if (!project.deadline) return null;
  const short = parseDay(project.deadline).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
  const overdue = project.deadline < toDay(new Date());
  return (
    <span
      className={cn(base, overdue ? "bg-destructive/15 text-destructive" : "bg-secondary text-secondary-foreground", className)}
      title={formatDay(project.deadline)}
    >
      <CalendarClock className="size-3" /> {overdue ? `Overdue · ${short}` : `Due ${short}`}
    </span>
  );
}
