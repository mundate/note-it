import { PROJECT_DESCRIPTION_MAX, type Project, type ProjectPatch, type Team } from "@/api/client";
import { NullableSelect } from "@/components/NullableSelect";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useState } from "react";

/** Description (saved on blur), deadline, and team of a project. */
export function ProjectDetails({
  project,
  teams,
  onChange,
}: {
  project: Project;
  teams: Team[] | null;
  onChange: (patch: ProjectPatch) => void;
}) {
  const [description, setDescription] = useState<string | null>(null); // non-null while editing

  const saveDescription = () => {
    const next = description?.trim();
    setDescription(null);
    if (next !== undefined && next !== project.description) onChange({ description: next });
  };

  return (
    <div className="flex flex-col gap-4 rounded-xl border p-4">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="project-description">Description</Label>
        <Textarea
          id="project-description"
          value={description ?? project.description}
          maxLength={PROJECT_DESCRIPTION_MAX}
          placeholder="What is this project about?"
          onFocus={() => setDescription(project.description)}
          onChange={e => setDescription(e.target.value)}
          onBlur={saveDescription}
          rows={3}
        />
      </div>
      <div className="flex flex-wrap items-end gap-6">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="project-deadline">Deadline</Label>
          <div className="flex items-center gap-2">
            <input
              id="project-deadline"
              type="date"
              value={project.deadline ?? ""}
              onChange={e => onChange({ deadline: e.target.value || null })}
              className="h-9 rounded-md border bg-transparent px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring dark:[color-scheme:dark]"
            />
            {project.deadline && (
              <Button variant="ghost" size="sm" onClick={() => onChange({ deadline: null })}>
                Clear
              </Button>
            )}
          </div>
        </div>
        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium">Team</span>
          <NullableSelect
            items={teams ?? []}
            value={project.teamId}
            onChange={teamId => onChange({ teamId })}
            noneLabel="No team"
            label="Team"
            disabled={!teams}
          />
        </div>
      </div>
    </div>
  );
}
