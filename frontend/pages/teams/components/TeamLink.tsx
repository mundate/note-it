import type { Team } from "@/api/client";
import { Link } from "@tanstack/react-router";
import { ChevronRight, Users } from "lucide-react";

export function TeamLink({ team, listCount }: { team: Team; listCount: number }) {
  return (
    <Link
      to="/teams/$teamId"
      params={{ teamId: team.id }}
      className="flex items-center gap-3 rounded-xl border bg-card px-4 py-3 shadow-sm outline-none transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring"
    >
      <Users className="size-5 shrink-0 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium">{team.name}</div>
        <div className="text-sm text-muted-foreground">{listCount === 1 ? "1 todo list" : `${listCount} todo lists`}</div>
      </div>
      <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
    </Link>
  );
}
