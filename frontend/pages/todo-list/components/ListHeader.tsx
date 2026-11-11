import { TODO_LIST_NAME_MAX, type Team } from "@/api/client";
import { EditableText } from "@/components/EditableText";
import { TeamSelect } from "@/components/TeamSelect";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";

/** The list's name as an editable heading, its team, and a delete button. */
export function ListHeader({
  name,
  teamId,
  teams,
  todoCount,
  onRename,
  onMove,
  onDelete,
}: {
  name: string;
  teamId: number | null;
  teams: Team[] | null;
  todoCount: number;
  onRename: (name: string) => void;
  onMove: (teamId: number | null) => void;
  onDelete: () => void;
}) {
  const confirmDelete = () => {
    const todos = todoCount === 1 ? "1 todo" : `${todoCount} todos`;
    if (window.confirm(`Delete "${name}"${todoCount ? ` and its ${todos}` : ""}? This can't be undone.`)) onDelete();
  };

  return (
    <div className="flex items-center gap-2">
      <h1 className="min-w-0 flex-1">
        <EditableText value={name} onSave={onRename} maxLength={TODO_LIST_NAME_MAX} label="List name" className="text-3xl font-bold" />
      </h1>
      <TeamSelect teams={teams ?? []} value={teamId} onChange={onMove} disabled={!teams} size="sm" />
      <Button variant="ghost" size="icon-sm" onClick={confirmDelete} aria-label={`Delete list "${name}"`} title="Delete list">
        <Trash2 />
      </Button>
    </div>
  );
}
