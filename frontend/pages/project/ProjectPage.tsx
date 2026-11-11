import { TODO_LIST_NAME_MAX, type Project, type ProjectPatch, type Team, type TodoList } from "@/api/client";
import { projectApi } from "@/api/projects";
import { teamApi } from "@/api/teams";
import { todoListApi } from "@/api/todos";
import { TodoListLink } from "@/components/TodoListLink";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Link, useNavigate } from "@tanstack/react-router";
import { ArrowLeft, CalendarCheck, ChevronRight, Plus } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { ProjectDetails } from "./components/ProjectDetails";
import { ProjectHeader } from "./components/ProjectHeader";

/** One project: its details, its (opt-in) daily list, and its todo lists. */
export function ProjectPage({ projectId }: { projectId: number }) {
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [teams, setTeams] = useState<Team[] | null>(null);
  const [lists, setLists] = useState<TodoList[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [listName, setListName] = useState("");
  const [creating, setCreating] = useState(false);

  const load = () => {
    setError(null);
    Promise.all([projectApi.get(projectId), todoListApi.all({ projectId }), teamApi.all()]).then(([p, l, t]) => {
      setProject(p);
      setLists(l);
      setTeams(t);
    }, e => setError(e.message));
  };
  useEffect(load, [projectId]);

  /** Change the project, showing the change right away; undo it if the request fails. */
  const update = async (patch: ProjectPatch) => {
    const before = project;
    setProject(p => (p ? ({ ...p, ...patch } as Project) : p));
    setError(null);
    try {
      setProject(await projectApi.update(projectId, patch));
    } catch (e) {
      setProject(before);
      setError((e as Error).message);
    }
  };

  const deleteProject = async () => {
    setError(null);
    try {
      await projectApi.remove(projectId);
      navigate(project?.teamId ? { to: "/teams/$teamId", params: { teamId: project.teamId } } : { to: "/teams" });
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const createList = async (e: FormEvent) => {
    e.preventDefault();
    const name = listName.trim();
    if (!name) return;
    setCreating(true);
    setError(null);
    try {
      const created = await todoListApi.create(name, { projectId });
      navigate({ to: "/todos/$listId", params: { listId: created.id } });
    } catch (e) {
      setError((e as Error).message);
      setCreating(false);
    }
  };

  const team = teams?.find(t => t.id === project?.teamId);
  const backLink =
    "flex w-fit items-center gap-1 rounded-sm text-sm text-muted-foreground outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring";

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      {project?.teamId ? (
        <Link to="/teams/$teamId" params={{ teamId: project.teamId }} className={backLink}>
          <ArrowLeft className="size-4" /> {team?.name ?? "Team"}
        </Link>
      ) : (
        <Link to="/teams" activeOptions={{ exact: true }} className={backLink}>
          <ArrowLeft className="size-4" /> All teams
        </Link>
      )}

      {project ? (
        <ProjectHeader
          project={project}
          listCount={lists?.length ?? 0}
          onRename={name => update({ name })}
          onToggleDone={() => update({ status: project.status === "done" ? "active" : "done" })}
          onDelete={deleteProject}
        />
      ) : (
        <h1 className="text-3xl font-bold text-muted-foreground">{error ? "Project" : "Loading…"}</h1>
      )}

      {error && (
        <div role="alert" className="flex items-center justify-between gap-2 rounded-md border border-destructive/50 px-3 py-2 text-sm text-destructive">
          <span>{error}</span>
          {!project && (
            <Button variant="outline" size="sm" onClick={load}>
              Retry
            </Button>
          )}
        </div>
      )}

      {/* Hidden when the project failed to load (e.g. it doesn't exist). */}
      {project && lists && (
        <>
          <ProjectDetails project={project} teams={teams} onChange={update} />

          <section aria-label="Daily list" className="flex flex-col gap-2">
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-lg font-semibold">Daily list</h2>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  role="switch"
                  checked={project.dailyEnabled}
                  onChange={() => update({ dailyEnabled: !project.dailyEnabled })}
                  aria-label="Daily list on"
                  className="size-4 accent-primary"
                />
                {project.dailyEnabled ? "On" : "Off"}
              </label>
            </div>
            {project.dailyEnabled ? (
              <Link
                to="/projects/$projectId/daily"
                params={{ projectId }}
                className="flex items-center gap-3 rounded-xl border bg-card px-4 py-3 shadow-sm outline-none transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring"
              >
                <CalendarCheck className="size-5 shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <div className="font-medium">Today's list</div>
                  <div className="text-sm text-muted-foreground">Unfinished tasks carry over to the next day.</div>
                </div>
                <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
              </Link>
            ) : (
              <p className="text-sm text-muted-foreground">
                Turn it on to get a fresh list of what needs doing each day; unfinished tasks carry over.{" "}
                <Link to="/projects/$projectId/daily" params={{ projectId }} className="underline underline-offset-2 hover:text-foreground">
                  Past days
                </Link>
              </p>
            )}
          </section>

          <section className="flex flex-col gap-2" aria-label="Todo lists">
            <h2 className="text-lg font-semibold">Todo lists</h2>
            <form onSubmit={createList} className="flex gap-2">
              <Input
                value={listName}
                onChange={e => setListName(e.target.value)}
                placeholder="New list for this project…"
                aria-label="New list name"
                maxLength={TODO_LIST_NAME_MAX}
              />
              <Button type="submit" disabled={!listName.trim() || creating}>
                <Plus /> Create list
              </Button>
            </form>
            {lists.length === 0 ? (
              <p className="rounded-xl border border-dashed px-4 py-3 text-sm text-muted-foreground">No todo lists in this project yet.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {lists.map(list => (
                  <li key={list.id}>
                    <TodoListLink list={list} />
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
