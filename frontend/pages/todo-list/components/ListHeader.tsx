import { TODO_LIST_NAME_MAX, type Project, type Team } from "@/api/client";
import { EditableText } from "@/components/EditableText";
import { NullableSelect } from "@/components/NullableSelect";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";

/** The list's name as an editable heading, its team and project, and a delete button. */
export function ListHeader({
  name,
  teamId,
  teams,
  projectId,
  projects,
  todoCount,
  onRename,
  onMove,
  onMoveToProject,
  onDelete,
}: {
  name: string;
  teamId: number | null;
  teams: Team[] | null;
  projectId: number | null;
  /** The list's team's projects (null while loading). */
  projects: Project[] | null;
  todoCount: number;
  onRename: (name: string) => void;
  onMove: (teamId: number | null) => void;
  onMoveToProject: (projectId: number | null) => void;
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
      <NullableSelect items={teams ?? []} value={teamId} onChange={onMove} noneLabel="No team" label="Team" disabled={!teams} size="sm" />
      <NullableSelect
        items={projects ?? []}
        value={projectId}
        onChange={onMoveToProject}
        noneLabel="No project"
        label="Project"
        disabled={teamId === null || !projects}
        size="sm"
      />
      <Button variant="ghost" size="icon-sm" onClick={confirmDelete} aria-label={`Delete list "${name}"`} title="Delete list">
        <Trash2 />
      </Button>
    </div>
  );
}
