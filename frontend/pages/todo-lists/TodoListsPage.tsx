import { TODO_LIST_NAME_MAX, type Project, type Team, type TodoList } from "@/api/client";
import { projectApi } from "@/api/projects";
import { teamApi } from "@/api/teams";
import { todoListApi } from "@/api/todos";
import { NullableSelect } from "@/components/NullableSelect";
import { TodoListLink } from "@/components/TodoListLink";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useNavigate } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { useEffect, useMemo, useState, type FormEvent } from "react";

/** All todo lists, each labelled with its team, plus a form to create one (which then opens it). */
export function TodoListsPage() {
  const navigate = useNavigate();
  const [lists, setLists] = useState<TodoList[] | null>(null);
  const [teams, setTeams] = useState<Team[] | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [teamId, setTeamId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  const load = () => {
    setError(null);
    Promise.all([todoListApi.all(), teamApi.all(), projectApi.teamless()])
      .then(async ([l, t, teamless]) => {
        // Project names for the labels: only the teams that have lists need fetching.
        const teamIds = [...new Set(l.map(x => x.teamId).filter((id): id is number => id !== null))];
        const perTeam = await Promise.all(teamIds.map(id => projectApi.forTeam(id)));
        setLists(l);
        setTeams(t);
        setProjects([...perTeam.flat(), ...teamless]);
      })
      .catch(e => setError(e.message));
  };
  useEffect(load, []);

  const teamNames = useMemo(() => new Map(teams?.map(t => [t.id, t.name])), [teams]);
  const projectNames = useMemo(() => new Map(projects.map(p => [p.id, p.name])), [projects]);
  /** "Team · Project", "Team", "Project" or nothing. */
  const label = (list: TodoList) =>
    [list.teamId !== null && teamNames.get(list.teamId), list.projectId !== null && projectNames.get(list.projectId)]
      .filter(Boolean)
      .join(" · ") || undefined;

  const create = async (e: FormEvent) => {
    e.preventDefault();
    const value = name.trim();
    if (!value) return;
    setCreating(true);
    setError(null);
    try {
      const created = await todoListApi.create(value, { teamId });
      navigate({ to: "/todos/$listId", params: { listId: created.id } });
    } catch (e) {
      setError((e as Error).message);
      setCreating(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <h1 className="text-3xl font-bold">Todo Lists</h1>

      <form onSubmit={create} className="flex gap-2">
        <Input
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="New list name…"
          aria-label="New list name"
          maxLength={TODO_LIST_NAME_MAX}
        />
        {teams && teams.length > 0 && (
          <NullableSelect items={teams} value={teamId} onChange={setTeamId} noneLabel="No team" label="Team" />
        )}
        <Button type="submit" disabled={!name.trim() || creating || !lists}>
          <Plus /> Create list
        </Button>
      </form>

      {error && (
        <div role="alert" className="flex items-center justify-between gap-2 rounded-md border border-destructive/50 px-3 py-2 text-sm text-destructive">
          <span>{error}</span>
          {!lists && (
            <Button variant="outline" size="sm" onClick={load}>
              Retry
            </Button>
          )}
        </div>
      )}

      {!lists ? (
        !error && <p className="text-sm text-muted-foreground">Loading…</p>
      ) : lists.length === 0 ? (
        <p className="py-6 text-center text-sm text-muted-foreground">No lists yet. Create one above.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {lists.map(list => (
            <li key={list.id}>
              <TodoListLink list={list} label={label(list)} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
