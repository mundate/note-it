import type { Project, Team, TodoList, TodoListPatch } from "@/api/client";
import { projectApi } from "@/api/projects";
import { teamApi } from "@/api/teams";
import { todoListApi } from "@/api/todos";
import { TodoListView } from "@/components/todo-list/TodoListView";
import { Button } from "@/components/ui/button";
import { Link, useNavigate } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { ListHeader } from "./components/ListHeader";

/** One (standard) todo list. The route renders it with `key={listId}`, so state resets between lists. */
export function TodoListPage({ listId }: { listId: number }) {
  const navigate = useNavigate();
  const [list, setList] = useState<TodoList | null>(null);
  const [teams, setTeams] = useState<Team[] | null>(null);
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [todoCount, setTodoCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    todoListApi.get(listId).then(l => {
      // Daily and sprint lists have their own pages (no rename, team change or delete there).
      if (l.kind === "daily" && l.projectId !== null && l.day) {
        navigate({ to: "/projects/$projectId/daily/$day", params: { projectId: l.projectId, day: l.day }, replace: true });
        return;
      }
      if (l.kind === "sprint" && l.projectId !== null && l.day) {
        navigate({ to: "/projects/$projectId/sprint/$start", params: { projectId: l.projectId, start: l.day }, replace: true });
        return;
      }
      setList(l);
    }, e => setError(e.message));
  };
  useEffect(load, [listId]);
  // Only needed for the team picker, so a failure here doesn't block the list.
  useEffect(() => {
    teamApi.all().then(setTeams, e => setError(e.message));
  }, []);

  // The project picker offers the list's team's projects.
  const listTeamId = list?.teamId ?? null;
  useEffect(() => {
    setProjects(null);
    if (listTeamId === null) return setProjects([]);
    projectApi.forTeam(listTeamId).then(setProjects, e => setError(e.message));
  }, [listTeamId]);

  /** Rename and/or move the list, showing the change right away. */
  const updateList = async (patch: TodoListPatch) => {
    const before = list;
    setList(l => {
      if (!l) return l;
      const next = { ...l, ...patch };
      // Mirror the server: a project sets the team; changing team drops the project.
      if (patch.projectId) next.teamId = projects?.find(p => p.id === patch.projectId)?.teamId ?? l.teamId;
      if (patch.teamId !== undefined && patch.projectId === undefined && patch.teamId !== l.teamId) next.projectId = null;
      return next;
    });
    setError(null);
    try {
      setList(await todoListApi.update(listId, patch));
    } catch (e) {
      setList(before);
      setError((e as Error).message);
    }
  };

  const deleteList = async () => {
    setError(null);
    try {
      await todoListApi.remove(listId);
      navigate({ to: "/todos" });
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <Link
        to="/todos"
        activeOptions={{ exact: true }} // a back link, not "you are here"
        className="flex w-fit items-center gap-1 rounded-sm text-sm text-muted-foreground outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
      >
        <ArrowLeft className="size-4" /> All lists
      </Link>

      {list ? (
        <ListHeader
          name={list.name}
          teamId={list.teamId}
          teams={teams}
          projectId={list.projectId}
          projects={projects}
          todoCount={todoCount}
          onRename={name => updateList({ name })}
          onMove={teamId => updateList({ teamId })}
          onMoveToProject={projectId => updateList({ projectId })}
          onDelete={deleteList}
        />
      ) : (
        <h1 className="text-3xl font-bold text-muted-foreground">{error ? "Todo list" : "Loading…"}</h1>
      )}

      {error && (
        <div role="alert" className="flex items-center justify-between gap-2 rounded-md border border-destructive/50 px-3 py-2 text-sm text-destructive">
          <span>{error}</span>
          {!list && (
            <Button variant="outline" size="sm" onClick={load}>
              Retry
            </Button>
          )}
        </div>
      )}

      {/* Only once the list loaded: a missing list has nothing to add to. */}
      {list && <TodoListView key={listId} listId={listId} onTodosChange={t => setTodoCount(t.length)} />}
    </div>
  );
}
