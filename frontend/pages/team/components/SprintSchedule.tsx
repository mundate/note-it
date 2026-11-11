import type { Team, TeamPatch } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { formatDay, toDay } from "@/lib/day";
import { formatRange, sprintOn } from "@/lib/sprints";
import { useState } from "react";

const WEEKS = [1, 2, 3, 4, 5, 6, 7, 8];

/**
 * The team's sprint schedule: the first sprint's start date and each sprint's length.
 * Sprints run back to back from the start; every active project gets a list per sprint.
 */
export function SprintSchedule({ team, onChange }: { team: Team; onChange: (patch: TeamPatch) => void }) {
  // While only one of the two is chosen, keep it here (the server needs both or neither).
  const [draftStart, setDraftStart] = useState<string | null>(null);
  const [draftWeeks, setDraftWeeks] = useState<number | null>(null);
  const start = draftStart ?? team.sprintStart;
  const weeks = draftWeeks ?? team.sprintWeeks;

  const choose = (nextStart: string | null, nextWeeks: number | null) => {
    if (nextStart && nextWeeks) {
      setDraftStart(null);
      setDraftWeeks(null);
      onChange({ sprintStart: nextStart, sprintWeeks: nextWeeks });
    } else {
      setDraftStart(nextStart);
      setDraftWeeks(nextWeeks);
    }
  };

  const today = toDay(new Date());
  const current = team.sprintStart && team.sprintWeeks ? sprintOn(today, team.sprintStart, team.sprintWeeks) : null;

  return (
    <section aria-label="Sprint schedule" className="flex flex-col gap-3 rounded-xl border p-4">
      <div>
        <h2 className="text-lg font-semibold">Sprint schedule</h2>
        <p className="text-sm text-muted-foreground">
          {current
            ? `Sprint ${current.number} · ${formatRange(current.start, current.end)} (current)`
            : team.sprintStart
              ? `The first sprint starts ${formatDay(team.sprintStart)}.`
              : "Set when the first sprint starts and how long sprints are. Every active project gets a sprint list."}
        </p>
      </div>
      <div className="flex flex-wrap items-end gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="sprint-start">First sprint starts</Label>
          <input
            id="sprint-start"
            type="date"
            value={start ?? ""}
            onChange={e => choose(e.target.value || null, weeks)}
            className="h-9 rounded-md border bg-transparent px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring dark:[color-scheme:dark]"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium">Length</span>
          <Select value={weeks ? String(weeks) : ""} onValueChange={v => choose(start, Number(v))}>
            <SelectTrigger aria-label="Sprint length" className="w-32">
              <SelectValue placeholder="Weeks" />
            </SelectTrigger>
            <SelectContent>
              {WEEKS.map(w => (
                <SelectItem key={w} value={String(w)}>
                  {w === 1 ? "1 week" : `${w} weeks`}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {(team.sprintStart || draftStart || draftWeeks) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setDraftStart(null);
              setDraftWeeks(null);
              if (team.sprintStart) onChange({ sprintStart: null, sprintWeeks: null });
            }}
          >
            Clear schedule
          </Button>
        )}
      </div>
    </section>
  );
}
