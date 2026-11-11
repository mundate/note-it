import type { Project, Team, TodoList } from "@/api/client";
import { projectApi } from "@/api/projects";
import { teamApi } from "@/api/teams";
import { periodApi, type PeriodKind } from "@/api/todos";
import { PeriodHeader, navButton } from "@/components/period/PeriodHeader";
import { TodoListView } from "@/components/todo-list/TodoListView";
import { Button } from "@/components/ui/button";
import { toDay } from "@/lib/day";
import { sprintOn, sprintTitle, type Sprint } from "@/lib/sprints";
import { cn } from "@/lib/utils";
import { Link } from "@tanstack/react-router";
import { ArrowLeft, ListPlus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

/** Whether the add boxes are shown (hidden by default), remembered per kind in this browser. */
function useShowAddBoxes(kind: PeriodKind): [boolean, (show: boolean) => void] {
  const key = kind === "daily" ? "team-daily:show-add-boxes" : "team-sprint:show-add-boxes";
  const [show, setShow] = useState(() => {
    try {
      return localStorage.getItem(key) === "true";
    } catch {
      return false;
    }
  });
  useEffect(() => {
    try {
      localStorage.setItem(key, String(show));
    } catch {}
  }, [key, show]);
  return [show, setShow];
}

/**
 * A team's combined daily or sprint view: one editable section per project with a list for
 * that period. Without `start` it shows the current period, opening each project's list
 * (and carrying over its unfinished todos).
 */
export function TeamPeriodPage({ kind, teamId, start }: { kind: PeriodKind; teamId: number; start?: string }) {
  const api = periodApi[kind];
  const [team, setTeam] = useState<Team | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [starts, setStarts] = useState<string[] | null>(null);
  const [lists, setLists] = useState<TodoList[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useShowAddBoxes(kind);

  const load = () => {
    setError(null);
    Promise.all([teamApi.get(teamId), projectApi.forTeam(teamId)])
      .then(async ([t, p]) => {
        const shown = start === undefined ? await api.openTeamCurrent(teamId) : await api.teamPeriod(teamId, start);
        const all = await api.teamStarts(teamId); // after opening the current period, so it's included
        setTeam(t);
        setProjects(p);
        setLists(shown);
        setStarts(all);
      })
      .catch(e => setError(e.message));
  };
  useEffect(load, [kind, teamId, start]);

  const projectNames = useMemo(() => new Map(projects.map(p => [p.id, p.name])), [projects]);
  const today = toDay(new Date()); // the backend runs locally, so its "today" is ours
  // The current sprint by the team's schedule (null for daily, or without a schedule / before it starts).
  const current: Sprint | null =
    kind === "sprint" && team?.sprintStart && team.sprintWeeks ? sprintOn(today, team.sprintStart, team.sprintWeeks) : null;
  const shownStart = start ?? lists?.[0]?.day ?? (kind === "daily" ? today : (current?.start ?? null));
  const shownEnd = lists?.[0]?.endDay ?? (kind === "daily" ? shownStart : (current?.end ?? shownStart));
  const isCurrent = kind === "daily" ? shownStart === today : !!current && shownStart === current.start;
  const title =
    kind === "daily" ? "Daily" : lists?.[0] ? sprintTitle(lists[0].name) : current ? `Sprint ${current.number}` : "Sprint";

  const index = starts && shownStart ? starts.indexOf(shownStart) : -1;
  // `starts` is newest first, so the previous (older) period is the next entry.
  const prev = starts && shownStart ? (index >= 0 ? (starts[index + 1] ?? null) : (starts.find(d => d < shownStart) ?? null)) : null;
  const next = starts && index > 0 ? (starts[index - 1] ?? null) : null;
  const noSchedule = kind === "sprint" && team && !team.sprintStart;
  const notStarted = kind === "sprint" && team?.sprintStart && !current && start === undefined;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <Link
        to="/teams/$teamId"
        params={{ teamId }}
        className="flex w-fit items-center gap-1 rounded-sm text-sm text-muted-foreground outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
      >
        <ArrowLeft className="size-4" /> {team?.name ?? "Team"}
      </Link>

      {shownStart && shownEnd ? (
        <PeriodHeader
          kind={kind}
          owner={{ teamId }}
          title={title}
          start={shownStart}
          end={shownEnd}
          isCurrent={isCurrent}
          prev={prev}
          next={next}
          actions={
            lists &&
            lists.length > 0 && (
              <button
                type="button"
                aria-pressed={showAdd}
                aria-label="Show add boxes"
                title={showAdd ? "Hide the add boxes" : "Show the add boxes to add tasks"}
                onClick={() => setShowAdd(!showAdd)}
                className={cn(navButton, showAdd && "bg-accent text-accent-foreground")}
              >
                <ListPlus className="size-4" />
              </button>
            )
          }
        />
      ) : (
        <h1 className="text-3xl font-bold">{title}</h1>
      )}

      {error && (
        <div role="alert" className="flex items-center justify-between gap-2 rounded-md border border-destructive/50 px-3 py-2 text-sm text-destructive">
          <span>{error}</span>
          <Button variant="outline" size="sm" onClick={load}>
            Retry
          </Button>
        </div>
      )}

      {!error && !lists && <p className="text-sm text-muted-foreground">Loading…</p>}

      {lists && lists.length === 0 && (
        <p className="rounded-xl border border-dashed px-4 py-3 text-sm text-muted-foreground">
          {noSchedule ? (
            <>
              This team has no sprint schedule.{" "}
              <Link to="/teams/$teamId" params={{ teamId }} className="underline underline-offset-2 hover:text-foreground">
                Set one on the team page.
              </Link>
            </>
          ) : notStarted ? (
            `The first sprint starts ${team!.sprintStart}.`
          ) : start !== undefined ? (
            `No ${kind} lists for this ${kind === "daily" ? "day" : "sprint"}.`
          ) : kind === "daily" ? (
            "No projects have a daily list. Turn it on from a project's page."
          ) : (
            "This team has no active projects."
          )}
        </p>
      )}

      {lists?.map(list => (
        <section key={list.id} aria-label={projectNames.get(list.projectId!) ?? "Project"} className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold">
            {kind === "daily" ? (
              <Link
                to="/projects/$projectId/daily/$day"
                params={{ projectId: list.projectId!, day: list.day! }}
                className="rounded-sm outline-none hover:underline focus-visible:ring-2 focus-visible:ring-ring"
              >
                {projectNames.get(list.projectId!) ?? "Project"}
              </Link>
            ) : (
              <Link
                to="/projects/$projectId/sprint/$start"
                params={{ projectId: list.projectId!, start: list.day! }}
                className="rounded-sm outline-none hover:underline focus-visible:ring-2 focus-visible:ring-ring"
              >
                {projectNames.get(list.projectId!) ?? "Project"}
              </Link>
            )}
          </h2>
          <TodoListView
            key={list.id}
            listId={list.id}
            name={projectNames.get(list.projectId!)}
            showAddForm={showAdd}
            emptyText={isCurrent ? `Nothing to do ${kind === "daily" ? "today" : "this sprint"} yet.` : `Nothing was finished this ${kind === "daily" ? "day" : "sprint"}.`}
          />
        </section>
      ))}
    </div>
  );
}
