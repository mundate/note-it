import { TEAM_NAME_MAX, type Project, type Team, type TodoList } from "@/api/client";
import { projectApi } from "@/api/projects";
import { teamApi } from "@/api/teams";
import { todoListApi } from "@/api/todos";
import { ProjectLink } from "@/components/ProjectLink";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useNavigate } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { TeamLink } from "./components/TeamLink";

/** All teams, plus a form to create one (which then opens it). */
export function TeamsPage() {
  const navigate = useNavigate();
  const [teams, setTeams] = useState<Team[] | null>(null);
  const [lists, setLists] = useState<TodoList[] | null>(null);
  const [teamless, setTeamless] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);

  const load = () => {
    setError(null);
    Promise.all([teamApi.all(), todoListApi.all(), projectApi.teamless()]).then(([t, l, p]) => {
      setTeams(t);
      setLists(l);
      setTeamless(p);
    }, e => setError(e.message));
  };
  useEffect(load, []);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    const value = name.trim();
    if (!value) return;
    setCreating(true);
    setError(null);
    try {
      const created = await teamApi.create(value);
      navigate({ to: "/teams/$teamId", params: { teamId: created.id } });
    } catch (e) {
      setError((e as Error).message);
      setCreating(false);
    }
  };

  const listCount = (teamId: number) => lists?.filter(l => l.teamId === teamId).length ?? 0;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <div>
        <h1 className="text-3xl font-bold">Teams</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Teams hold projects and todo lists. They're optional: lists work fine without one.
        </p>
      </div>

      <form onSubmit={create} className="flex gap-2">
        <Input
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="New team name…"
          aria-label="New team name"
          maxLength={TEAM_NAME_MAX}
        />
        <Button type="submit" disabled={!name.trim() || creating}>
          <Plus /> Create team
        </Button>
      </form>

      {error && (
        <div role="alert" className="flex items-center justify-between gap-2 rounded-md border border-destructive/50 px-3 py-2 text-sm text-destructive">
          <span>{error}</span>
          {!teams && (
            <Button variant="outline" size="sm" onClick={load}>
              Retry
            </Button>
          )}
        </div>
      )}

      {!teams ? (
        !error && <p className="text-sm text-muted-foreground">Loading…</p>
      ) : teams.length === 0 ? (
        <p className="py-6 text-center text-sm text-muted-foreground">No teams yet. Create one above.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {teams.map(team => (
            <li key={team.id}>
              <TeamLink team={team} listCount={listCount(team.id)} />
            </li>
          ))}
        </ul>
      )}

      {teamless.length > 0 && (
        <section className="mt-4 flex flex-col gap-2" aria-label="Projects without a team">
          <div>
            <h2 className="text-lg font-semibold">Projects without a team</h2>
            <p className="text-sm text-muted-foreground">Their team was deleted. Give one a team from its page.</p>
          </div>
          <ul className="flex flex-col gap-2">
            {teamless.map(p => (
              <li key={p.id}>
                <ProjectLink project={p} listCount={lists?.filter(l => l.projectId === p.id).length ?? 0} />
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
