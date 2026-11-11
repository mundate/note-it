import { PROJECT_NAME_MAX, type Project } from "@/api/client";
import { DeadlineBadge } from "@/components/DeadlineBadge";
import { EditableText } from "@/components/EditableText";
import { Button } from "@/components/ui/button";
import { CheckCircle2, RotateCcw, Trash2 } from "lucide-react";

/** The project's name as an editable heading, its status, and done / delete buttons. */
export function ProjectHeader({
  project,
  listCount,
  onRename,
  onToggleDone,
  onDelete,
}: {
  project: Project;
  listCount: number;
  onRename: (name: string) => void;
  onToggleDone: () => void;
  onDelete: () => void;
}) {
  const confirmDelete = () => {
    const lists = listCount === 1 ? "its todo list" : `its ${listCount} todo lists`;
    const daily = project.dailyEnabled ? " and daily lists" : "";
    if (window.confirm(`Delete "${project.name}", ${lists}${daily} and all their todos? This can't be undone.`)) onDelete();
  };
  const done = project.status === "done";

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <h1 className="min-w-0 flex-1">
          <EditableText value={project.name} onSave={onRename} maxLength={PROJECT_NAME_MAX} label="Project name" className="text-3xl font-bold" />
        </h1>
        <Button variant="outline" size="sm" onClick={onToggleDone}>
          {done ? <RotateCcw /> : <CheckCircle2 />} {done ? "Reopen" : "Mark done"}
        </Button>
        <Button variant="ghost" size="icon-sm" onClick={confirmDelete} aria-label={`Delete project "${project.name}"`} title="Delete project">
          <Trash2 />
        </Button>
      </div>
      <DeadlineBadge project={project} className="w-fit" />
    </div>
  );
}
