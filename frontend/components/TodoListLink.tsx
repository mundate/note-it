import type { TodoList } from "@/api/client";
import { Link } from "@tanstack/react-router";
import { ChevronRight, Users } from "lucide-react";

/** A todo list as a card linking to it, with its counts and an optional label (e.g. "Team · Project"). */
export function TodoListLink({ list, label }: { list: TodoList; label?: string }) {
  const summary =
    list.openCount + list.doneCount === 0 ? "Empty" : `${list.openCount} open · ${list.doneCount} done`;
  return (
    <Link
      to="/todos/$listId"
      params={{ listId: list.id }}
      className="flex items-center gap-3 rounded-xl border bg-card px-4 py-3 shadow-sm outline-none transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring"
    >
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium">{list.name}</div>
        <div className="text-sm text-muted-foreground">{summary}</div>
      </div>
      {label && (
        <span className="flex max-w-56 shrink-0 items-center gap-1 rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground">
          <Users className="size-3 shrink-0" />
          <span className="truncate">{label}</span>
        </span>
      )}
      <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
    </Link>
  );
}
