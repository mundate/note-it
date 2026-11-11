import { TODO_LIST_NAME_MAX, type TodoList } from "@/api/client";
import { todoListApi } from "@/api/todos";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useNavigate } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { TodoListLink } from "./components/TodoListLink";

/** All todo lists, plus a form to create one (which then opens it). */
export function TodoListsPage() {
  const navigate = useNavigate();
  const [lists, setLists] = useState<TodoList[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);

  const load = () => {
    setError(null);
    todoListApi.all().then(setLists, e => setError(e.message));
  };
  useEffect(load, []);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    const value = name.trim();
    if (!value) return;
    setCreating(true);
    setError(null);
    try {
      const created = await todoListApi.create(value);
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
        <Button type="submit" disabled={!name.trim() || creating}>
          <Plus /> Create
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
              <TodoListLink list={list} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
