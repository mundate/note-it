import type { Project } from "@/api/client";
import { DeadlineBadge } from "@/components/DeadlineBadge";
import { cn } from "@/lib/utils";
import { Link } from "@tanstack/react-router";
import { ChevronRight, FolderKanban } from "lucide-react";

/** A project as a card linking to it, with its deadline/status and list count. */
export function ProjectLink({ project, listCount }: { project: Project; listCount: number }) {
  return (
    <Link
      to="/projects/$projectId"
      params={{ projectId: project.id }}
      className={cn(
        "flex items-center gap-3 rounded-xl border bg-card px-4 py-3 shadow-sm outline-none transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring",
        project.status === "done" && "opacity-70",
      )}
    >
      <FolderKanban className="size-5 shrink-0 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium">{project.name}</div>
        <div className="text-sm text-muted-foreground">
          {listCount === 1 ? "1 todo list" : `${listCount} todo lists`}
          {project.dailyEnabled && " · daily list"}
        </div>
      </div>
      <DeadlineBadge project={project} className="shrink-0" />
      <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
    </Link>
  );
}
