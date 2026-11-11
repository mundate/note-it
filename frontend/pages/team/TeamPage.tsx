import { PROJECT_NAME_MAX, TODO_LIST_NAME_MAX, type Project, type Team, type TodoList } from "@/api/client";
import { projectApi } from "@/api/projects";
import { teamApi } from "@/api/teams";
import { todoListApi } from "@/api/todos";
import { ProjectLink } from "@/components/ProjectLink";
import { TodoListLink } from "@/components/TodoListLink";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Link, useNavigate } from "@tanstack/react-router";
import { ArrowLeft, CalendarCheck, ChevronRight, FolderPlus, Plus } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { TeamHeader } from "./components/TeamHeader";

/**
 * One team: its combined daily view, its projects, and its todo lists that aren't in a
 * project (notes and diagrams later). The route renders it with `key={teamId}`.
 */
export function TeamPage({ teamId }: { teamId: number }) {
  const navigate = useNavigate();
  const [team, setTeam] = useState<Team | null>(null);
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [allLists, setAllLists] = useState<TodoList[] | null>(null); // every list in the team
  const [error, setError] = useState<string | null>(null);
  const [projectName, setProjectName] = useState("");
  const [listName, setListName] = useState("");
  const [creating, setCreating] = useState(false);

  const load = () => {
    setError(null);
    Promise.all([teamApi.get(teamId), projectApi.forTeam(teamId), todoListApi.all({ teamId })]).then(([t, p, l]) => {
      setTeam(t);
      setProjects(p);
      setAllLists(l);
    }, e => setError(e.message));
  };
  useEffect(load, [teamId]);

  const fail = (e: unknown) => {
    setError((e as Error).message);
    setCreating(false);
  };

  const rename = async (name: string) => {
    const before = team;
    setTeam(t => (t ? { ...t, name } : t));
    setError(null);
    try {
      setTeam(await teamApi.rename(teamId, name));
    } catch (e) {
      setTeam(before);
      fail(e);
    }
  };

  const deleteTeam = async () => {
    setError(null);
    try {
      await teamApi.remove(teamId);
      navigate({ to: "/teams" });
    } catch (e) {
      fail(e);
    }
  };

  const createProject = async (e: FormEvent) => {
    e.preventDefault();
    const name = projectName.trim();
    if (!name) return;
    setCreating(true);
    setError(null);
    try {
      const created = await projectApi.create(teamId, name);
      navigate({ to: "/projects/$projectId", params: { projectId: created.id } });
    } catch (e) {
      fail(e);
    }
  };

  const createList = async (e: FormEvent) => {
    e.preventDefault();
    const name = listName.trim();
    if (!name) return;
    setCreating(true);
    setError(null);
    try {
      const created = await todoListApi.create(name, { teamId });
      navigate({ to: "/todos/$listId", params: { listId: created.id } });
    } catch (e) {
      fail(e);
    }
  };

  const listCount = (projectId: number) => allLists?.filter(l => l.projectId === projectId).length ?? 0;
  const looseLists = allLists?.filter(l => l.projectId === null) ?? [];
  const active = projects?.filter(p => p.status === "active") ?? [];
  const done = projects?.filter(p => p.status === "done") ?? [];
  const hasDaily = active.some(p => p.dailyEnabled);
  const card =
    "flex items-center gap-3 rounded-xl border bg-card px-4 py-3 shadow-sm outline-none transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring";

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div className="flex flex-col gap-4">
        <Link
          to="/teams"
          activeOptions={{ exact: true }} // a back link, not "you are here"
          className="flex w-fit items-center gap-1 rounded-sm text-sm text-muted-foreground outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
        >
          <ArrowLeft className="size-4" /> All teams
        </Link>

        {team ? (
          <TeamHeader
            name={team.name}
            listCount={allLists?.length ?? 0}
            projectCount={projects?.length ?? 0}
            onRename={rename}
            onDelete={deleteTeam}
          />
        ) : (
          <h1 className="text-3xl font-bold text-muted-foreground">{error ? "Team" : "Loading…"}</h1>
        )}

        {error && (
          <div role="alert" className="flex items-center justify-between gap-2 rounded-md border border-destructive/50 px-3 py-2 text-sm text-destructive">
            <span>{error}</span>
            {!team && (
              <Button variant="outline" size="sm" onClick={load}>
                Retry
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Hidden when the team failed to load (e.g. it doesn't exist). */}
      {team && projects && allLists && (
        <>
          {hasDaily && (
            <Link to="/teams/$teamId/daily" params={{ teamId }} className={card}>
              <CalendarCheck className="size-5 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <div className="font-medium">Daily</div>
                <div className="text-sm text-muted-foreground">Today's lists for every project with a daily list, in one place.</div>
              </div>
              <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
            </Link>
          )}

          <section className="flex flex-col gap-2" aria-label="Projects">
            <h2 className="text-lg font-semibold">Projects</h2>
            <form onSubmit={createProject} className="flex gap-2">
              <Input
                value={projectName}
                onChange={e => setProjectName(e.target.value)}
                placeholder="New project name…"
                aria-label="New project name"
                maxLength={PROJECT_NAME_MAX}
              />
              <Button type="submit" disabled={!projectName.trim() || creating}>
                <FolderPlus /> Create project
              </Button>
            </form>
            {projects.length === 0 && (
              <p className="rounded-xl border border-dashed px-4 py-3 text-sm text-muted-foreground">No projects yet.</p>
            )}
            {active.length > 0 && (
              <ul className="flex flex-col gap-2">
                {active.map(p => (
                  <li key={p.id}>
                    <ProjectLink project={p} listCount={listCount(p.id)} />
                  </li>
                ))}
              </ul>
            )}
            {done.length > 0 && (
              <div className="mt-2 flex flex-col gap-2" aria-label="Done projects">
                <h3 className="px-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">Done ({done.length})</h3>
                <ul className="flex flex-col gap-2">
                  {done.map(p => (
                    <li key={p.id}>
                      <ProjectLink project={p} listCount={listCount(p.id)} />
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>

          <section className="flex flex-col gap-2" aria-label="Todo lists">
            <div>
              <h2 className="text-lg font-semibold">Todo lists</h2>
              <p className="text-sm text-muted-foreground">Lists in this team that aren't part of a project.</p>
            </div>
            <form onSubmit={createList} className="flex gap-2">
              <Input
                value={listName}
                onChange={e => setListName(e.target.value)}
                placeholder="New list for this team…"
                aria-label="New list name"
                maxLength={TODO_LIST_NAME_MAX}
              />
              <Button type="submit" disabled={!listName.trim() || creating}>
                <Plus /> Create list
              </Button>
            </form>
            {looseLists.length === 0 ? (
              <p className="rounded-xl border border-dashed px-4 py-3 text-sm text-muted-foreground">
                No todo lists outside a project.
              </p>
            ) : (
              <ul className="flex flex-col gap-2">
                {looseLists.map(list => (
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
