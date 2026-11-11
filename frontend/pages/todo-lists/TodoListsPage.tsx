import { TODO_LIST_NAME_MAX, type Team, type TodoList } from "@/api/client";
import { teamApi } from "@/api/teams";
import { todoListApi } from "@/api/todos";
import { TeamSelect } from "@/components/TeamSelect";
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
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [teamId, setTeamId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  const load = () => {
    setError(null);
    Promise.all([todoListApi.all(), teamApi.all()]).then(([l, t]) => {
      setLists(l);
      setTeams(t);
    }, e => setError(e.message));
  };
  useEffect(load, []);

  const teamNames = useMemo(() => new Map(teams?.map(t => [t.id, t.name])), [teams]);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    const value = name.trim();
    if (!value) return;
    setCreating(true);
    setError(null);
    try {
      const created = await todoListApi.create(value, teamId);
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
        {teams && teams.length > 0 && <TeamSelect teams={teams} value={teamId} onChange={setTeamId} />}
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
              <TodoListLink list={list} teamName={list.teamId === null ? undefined : teamNames.get(list.teamId)} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
