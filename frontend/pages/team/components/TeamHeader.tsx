import { TEAM_NAME_MAX } from "@/api/client";
import { EditableText } from "@/components/EditableText";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";

/** The team's name as an editable heading, plus a delete button. */
export function TeamHeader({
  name,
  listCount,
  onRename,
  onDelete,
}: {
  name: string;
  listCount: number;
  onRename: (name: string) => void;
  onDelete: () => void;
}) {
  const confirmDelete = () => {
    const kept = listCount
      ? ` Its ${listCount === 1 ? "todo list" : `${listCount} todo lists`} will be kept, without a team.`
      : "";
    if (window.confirm(`Delete the team "${name}"?${kept}`)) onDelete();
  };

  return (
    <div className="flex items-center gap-2">
      <h1 className="min-w-0 flex-1">
        <EditableText value={name} onSave={onRename} maxLength={TEAM_NAME_MAX} label="Team name" className="text-3xl font-bold" />
      </h1>
      <Button variant="ghost" size="icon-sm" onClick={confirmDelete} aria-label={`Delete team "${name}"`} title="Delete team">
        <Trash2 />
      </Button>
    </div>
  );
}
