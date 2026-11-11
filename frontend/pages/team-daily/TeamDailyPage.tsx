import type { Project, Team, TodoList } from "@/api/client";
import { projectApi } from "@/api/projects";
import { teamApi } from "@/api/teams";
import { dailyApi } from "@/api/todos";
import { DailyHeader, navButton } from "@/components/daily/DailyHeader";
import { TodoListView } from "@/components/todo-list/TodoListView";
import { Button } from "@/components/ui/button";
import { toDay } from "@/lib/day";
import { Link } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import { ArrowLeft, ListPlus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

/**
 * A team's combined daily view: one editable section per project that has a daily list
 * that day. Without `day` it shows today, opening today's list for each active project with
 * daily turned on (and carrying over its unfinished todos).
 */
const SHOW_ADD_KEY = "team-daily:show-add-boxes";

/** Whether the add boxes are shown (hidden by default), remembered in this browser. */
function useShowAddBoxes(): [boolean, (show: boolean) => void] {
  const [show, setShow] = useState(() => {
    try {
      return localStorage.getItem(SHOW_ADD_KEY) === "true";
    } catch {
      return false;
    }
  });
  useEffect(() => {
    try {
      localStorage.setItem(SHOW_ADD_KEY, String(show));
    } catch {}
  }, [show]);
  return [show, setShow];
}

export function TeamDailyPage({ teamId, day }: { teamId: number; day?: string }) {
  const [team, setTeam] = useState<Team | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [days, setDays] = useState<string[] | null>(null);
  const [lists, setLists] = useState<TodoList[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useShowAddBoxes();

  const load = () => {
    setError(null);
    Promise.all([teamApi.get(teamId), projectApi.forTeam(teamId)])
      .then(async ([t, p]) => {
        const shown = day === undefined ? await dailyApi.openTeamToday(teamId) : await dailyApi.teamDay(teamId, day);
        const all = await dailyApi.teamDays(teamId); // after opening today, so it's included
        setTeam(t);
        setProjects(p);
        setLists(shown);
        setDays(all);
      })
      .catch(e => setError(e.message));
  };
  useEffect(load, [teamId, day]);

  const projectNames = useMemo(() => new Map(projects.map(p => [p.id, p.name])), [projects]);
  const today = toDay(new Date()); // the backend runs locally, so its "today" is ours
  const shownDay = day ?? today;
  const index = days ? days.indexOf(shownDay) : -1;
  // `days` is newest first, so the previous (older) day is the next entry.
  const prevDay = days ? (index >= 0 ? (days[index + 1] ?? null) : (days.find(d => d < shownDay) ?? null)) : null;
  const nextDay = days ? (index > 0 ? (days[index - 1] ?? null) : null) : null;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <Link
        to="/teams/$teamId"
        params={{ teamId }}
        className="flex w-fit items-center gap-1 rounded-sm text-sm text-muted-foreground outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
      >
        <ArrowLeft className="size-4" /> {team?.name ?? "Team"}
      </Link>

      <DailyHeader
        owner={{ teamId }}
        day={shownDay}
        isToday={shownDay === today}
        prevDay={prevDay}
        nextDay={nextDay}
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
          {day === undefined
            ? "No projects have a daily list. Turn it on from a project's page."
            : "No daily lists for this day."}
        </p>
      )}

      {lists?.map(list => (
        <section key={list.id} aria-label={projectNames.get(list.projectId!) ?? "Project"} className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold">
            <Link
              to="/projects/$projectId/daily/$day"
              params={{ projectId: list.projectId!, day: list.day! }}
              className="rounded-sm outline-none hover:underline focus-visible:ring-2 focus-visible:ring-ring"
            >
              {projectNames.get(list.projectId!) ?? "Project"}
            </Link>
          </h2>
          <TodoListView
            key={list.id}
            listId={list.id}
            name={projectNames.get(list.projectId!)}
            showAddForm={showAdd}
            emptyText={shownDay === today ? "Nothing to do today yet." : "Nothing was finished this day."}
          />
        </section>
      ))}
    </div>
  );
}
