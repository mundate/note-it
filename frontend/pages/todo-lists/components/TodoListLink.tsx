import type { TodoList } from "@/api/client";
import { Link } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";

export function TodoListLink({ list }: { list: TodoList }) {
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
      <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
    </Link>
  );
}
