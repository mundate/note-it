import { TODO_LIST_NAME_MAX, type Team, type TodoList } from "@/api/client";
import { teamApi } from "@/api/teams";
import { todoListApi } from "@/api/todos";
import { TodoListLink } from "@/components/TodoListLink";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Link, useNavigate } from "@tanstack/react-router";
import { ArrowLeft, Plus } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { TeamHeader } from "./components/TeamHeader";

/**
 * One team and everything assigned to it: its todo lists for now (notes and diagrams
 * later). The route renders it with `key={teamId}`, so state resets between teams.
 */
export function TeamPage({ teamId }: { teamId: number }) {
  const navigate = useNavigate();
  const [team, setTeam] = useState<Team | null>(null);
  const [lists, setLists] = useState<TodoList[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [listName, setListName] = useState("");
  const [creating, setCreating] = useState(false);

  const load = () => {
    setError(null);
    Promise.all([teamApi.get(teamId), todoListApi.all(teamId)]).then(([t, l]) => {
      setTeam(t);
      setLists(l);
    }, e => setError(e.message));
  };
  useEffect(load, [teamId]);

  const rename = async (name: string) => {
    const before = team;
    setTeam(t => (t ? { ...t, name } : t));
    setError(null);
    try {
      setTeam(await teamApi.rename(teamId, name));
    } catch (e) {
      setTeam(before);
      setError((e as Error).message);
    }
  };

  const deleteTeam = async () => {
    setError(null);
    try {
      await teamApi.remove(teamId);
      navigate({ to: "/teams" });
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
      const created = await todoListApi.create(name, teamId);
      navigate({ to: "/todos/$listId", params: { listId: created.id } });
    } catch (e) {
      setError((e as Error).message);
      setCreating(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <Link
        to="/teams"
        activeOptions={{ exact: true }} // a back link, not "you are here"
        className="flex w-fit items-center gap-1 rounded-sm text-sm text-muted-foreground outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring"
      >
        <ArrowLeft className="size-4" /> All teams
      </Link>

      {team ? (
        <TeamHeader name={team.name} listCount={lists?.length ?? 0} onRename={rename} onDelete={deleteTeam} />
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

      {/* Hidden when the team failed to load (e.g. it doesn't exist). */}
      {team && lists && (
        <section className="flex flex-col gap-2" aria-label="Todo lists">
          <h2 className="text-lg font-semibold">Todo lists</h2>
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
          {lists.length === 0 ? (
            <p className="rounded-xl border border-dashed px-4 py-3 text-sm text-muted-foreground">
              No todo lists in this team yet.
            </p>
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
      )}
    </div>
  );
}
