import type { Project, Team, TodoList } from "@/api/client";
import { projectApi } from "@/api/projects";
import { teamApi } from "@/api/teams";
import { periodApi, type PeriodKind } from "@/api/todos";
import { PeriodHeader, PeriodLink } from "@/components/period/PeriodHeader";
import { TodoListView } from "@/components/todo-list/TodoListView";
import { Button } from "@/components/ui/button";
import { formatDay, toDay } from "@/lib/day";
import { formatRange, sprintOn, sprintTitle } from "@/lib/sprints";
import { Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";

/**
 * A project's daily or sprint list for one period. Without `start` it shows the current one:
 * opening it creates the list (if needed) and moves unfinished todos onto it. When there's no
 * current period (daily turned off; sprint: inactive, no schedule, not started) it says why,
 * and past periods stay viewable.
 */
export function ProjectPeriodPage({ kind, projectId, start }: { kind: PeriodKind; projectId: number; start?: string }) {
  const api = periodApi[kind];
  const [project, setProject] = useState<Project | null>(null);
  const [team, setTeam] = useState<Team | null>(null); // for the sprint schedule
  const [periods, setPeriods] = useState<TodoList[] | null>(null);
  const [list, setList] = useState<TodoList | null | undefined>(undefined); // null: no list for that period
  const [unavailable, setUnavailable] = useState<string | null>(null); // why there's no current period
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    setUnavailable(null);
    projectApi
      .get(projectId)
      .then(async p => {
        setProject(p);
        if (kind === "sprint" && p.teamId !== null) setTeam(await teamApi.get(p.teamId));
        let opened: TodoList | null = null;
        if (start === undefined) {
          if (kind === "daily" && !p.dailyEnabled) {
            setUnavailable("This project's daily list is turned off.");
          } else {
            // Open the current period first, so its (new) list is in `periods`. The server
            // explains a missing sprint (inactive project, no schedule, not started).
            opened = await api.openProjectCurrent(projectId).catch(e => {
              setUnavailable(e.message);
              return null;
            });
          }
        }
        const all = await api.projectPeriods(projectId);
        setPeriods(all);
        setList(opened ?? (start ? (all.find(l => l.day === start) ?? null) : null));
      })
      .catch(e => setError(e.message));
  };
  useEffect(load, [kind, projectId, start]);

  const today = toDay(new Date()); // the backend runs locally, so its "today" is ours
  const index = list && periods ? periods.findIndex(l => l.id === list.id) : -1;
  // `periods` is newest first, so the previous (older) one is the next entry.
  const prev = index >= 0 ? (periods![index + 1]?.day ?? null) : null;
  const next = index > 0 ? (periods![index - 1]?.day ?? null) : null;
  // Current = the period the server would open today. For sprints that's the team schedule's
  // current sprint (a past list's dates can still contain today after the schedule changes).
  const currentSprint = team?.sprintStart && team.sprintWeeks ? sprintOn(today, team.sprintStart, team.sprintWeeks) : null;
  const isCurrent =
    !!list?.day && (kind === "daily" ? list.day === today : project?.status === "active" && list.day === currentSprint?.start);
  const noun = kind === "daily" ? "daily list" : "sprint list";
  const label = (l: TodoList) => (kind === "daily" ? formatDay(l.day!) : `${sprintTitle(l.name)} · ${formatRange(l.day!, l.endDay!)}`);

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <Link
        to="/projects/$projectId"
        params={{ projectId }}
        className="flex w-fit items-center gap-1 rounded-sm text-sm text-muted-foreground outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
      >
        <ArrowLeft className="size-4" /> {project?.name ?? "Project"}
      </Link>

      {error && (
        <>
          <h1 className="text-3xl font-bold text-muted-foreground">{kind === "daily" ? "Daily" : "Sprint"}</h1>
          <div role="alert" className="flex items-center justify-between gap-2 rounded-md border border-destructive/50 px-3 py-2 text-sm text-destructive">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={load}>
              Retry
            </Button>
          </div>
        </>
      )}

      {!error && list === undefined && <p className="text-sm text-muted-foreground">Loading…</p>}

      {list === null && (
        <>
          <h1 className="text-3xl font-bold">{kind === "daily" ? "Daily" : "Sprint"}</h1>
          <div className="rounded-xl border border-dashed px-4 py-3 text-sm text-muted-foreground">
            {unavailable ? (
              <>
                {unavailable}{" "}
                {project?.teamId && unavailable.includes("sprint schedule") ? (
                  <Link to="/teams/$teamId" params={{ teamId: project.teamId }} className="underline underline-offset-2 hover:text-foreground">
                    Set one on the team page.
                  </Link>
                ) : (
                  <Link to="/projects/$projectId" params={{ projectId }} className="underline underline-offset-2 hover:text-foreground">
                    Back to the project.
                  </Link>
                )}
              </>
            ) : (
              <>
                No {noun} for this {kind === "daily" ? "day" : "sprint"}.{" "}
                <PeriodLink kind={kind} owner={{ projectId }} start={null} className="underline underline-offset-2 hover:text-foreground">
                  Go to the current one
                </PeriodLink>
              </>
            )}
          </div>
          {periods && periods.length > 0 && (
            <div className="text-sm text-muted-foreground">
              <p>Past {kind === "daily" ? "days" : "sprints"}:</p>
              <ul className="mt-1 flex flex-col gap-0.5">
                {periods.slice(0, 7).map(p => (
                  <li key={p.id}>
                    <PeriodLink kind={kind} owner={{ projectId }} start={p.day} className="underline underline-offset-2 hover:text-foreground">
                      {label(p)}
                    </PeriodLink>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {list && list.day && (
        <>
          <PeriodHeader
            kind={kind}
            owner={{ projectId }}
            title={kind === "daily" ? "Daily" : sprintTitle(list.name)}
            start={list.day}
            end={list.endDay ?? list.day}
            isCurrent={isCurrent}
            prev={prev}
            next={next}
          />
          {kind === "daily" && project && !project.dailyEnabled && (
            <p className="text-sm text-muted-foreground">This project's daily list is turned off; past days stay editable.</p>
          )}
          <TodoListView
            key={list.id}
            listId={list.id}
            emptyText={isCurrent ? `Nothing to do ${kind === "daily" ? "today" : "this sprint"} yet.` : `Nothing was finished this ${kind === "daily" ? "day" : "sprint"}.`}
          />
        </>
      )}
    </div>
  );
}
