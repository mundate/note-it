import type { Project, TodoList } from "@/api/client";
import { projectApi } from "@/api/projects";
import { dailyApi } from "@/api/todos";
import { DailyHeader } from "@/components/daily/DailyHeader";
import { TodoListView } from "@/components/todo-list/TodoListView";
import { Button } from "@/components/ui/button";
import { toDay } from "@/lib/day";
import { Link } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";

/**
 * A project's daily list for one day. Without `day` it shows today: opening it creates
 * today's list (if needed) and moves unfinished todos from earlier days onto it. When the
 * project's daily list is turned off, today can't be opened but past days still can.
 */
export function ProjectDailyPage({ projectId, day }: { projectId: number; day?: string }) {
  const [project, setProject] = useState<Project | null>(null);
  const [days, setDays] = useState<TodoList[] | null>(null);
  const [list, setList] = useState<TodoList | null | undefined>(undefined); // null: no list for that day
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    projectApi
      .get(projectId)
      .then(async p => {
        setProject(p);
        // Open today first (if asked for and turned on), so today's new list is in `days`.
        const opened = day === undefined && p.dailyEnabled ? await dailyApi.openProjectToday(projectId) : null;
        const all = await dailyApi.projectDays(projectId);
        setDays(all);
        setList(opened ?? (day ? (all.find(l => l.day === day) ?? null) : null));
      })
      .catch(e => setError(e.message));
  };
  useEffect(load, [projectId, day]);

  const today = toDay(new Date()); // the backend runs locally, so its "today" is ours
  const index = list && days ? days.findIndex(l => l.id === list.id) : -1;
  // `days` is newest first, so the previous (older) day is the next entry.
  const prevDay = index >= 0 ? (days![index + 1]?.day ?? null) : null;
  const nextDay = index > 0 ? (days![index - 1]?.day ?? null) : null;
  const off = project && !project.dailyEnabled;

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
          <h1 className="text-3xl font-bold text-muted-foreground">Daily</h1>
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
          <h1 className="text-3xl font-bold">Daily</h1>
          <div className="rounded-xl border border-dashed px-4 py-3 text-sm text-muted-foreground">
            {off ? (
              <>
                This project's daily list is turned off. Turn it on from the{" "}
                <Link to="/projects/$projectId" params={{ projectId }} className="underline underline-offset-2 hover:text-foreground">
                  project page
                </Link>
                .
              </>
            ) : (
              <>
                No daily list for this day.{" "}
                <Link to="/projects/$projectId/daily" params={{ projectId }} className="underline underline-offset-2 hover:text-foreground">
                  Go to today
                </Link>
              </>
            )}
          </div>
          {days && days.length > 0 && (
            <p className="text-sm text-muted-foreground">
              Past days:{" "}
              {days.slice(0, 7).map((d, i) => (
                <span key={d.id}>
                  {i > 0 && ", "}
                  <Link
                    to="/projects/$projectId/daily/$day"
                    params={{ projectId, day: d.day! }}
                    className="underline underline-offset-2 hover:text-foreground"
                  >
                    {d.day}
                  </Link>
                </span>
              ))}
            </p>
          )}
        </>
      )}

      {list && list.day && (
        <>
          <DailyHeader
            owner={{ projectId }}
            day={list.day}
            isToday={list.day === today}
            prevDay={prevDay}
            nextDay={nextDay}
          />
          {off && <p className="text-sm text-muted-foreground">This project's daily list is turned off; past days stay editable.</p>}
          <TodoListView
            key={list.id}
            listId={list.id}
            emptyText={list.day === today ? "Nothing to do today yet." : "Nothing was finished this day."}
          />
        </>
      )}
    </div>
  );
}
