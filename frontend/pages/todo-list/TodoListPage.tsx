import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TODO_TEXT_MAX, type Team, type Todo, type TodoList, type TodoListPatch, type TodoPatch } from "@/api/client";
import { teamApi } from "@/api/teams";
import { todoApi as todoApiFor, todoListApi } from "@/api/todos";
import { Link, useNavigate } from "@tanstack/react-router";
import { ArrowLeft, Plus } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { ListHeader } from "./components/ListHeader";
import { SortableSection } from "./components/SortableSection";

/** One todo list. The route renders it with `key={listId}`, so state resets between lists. */
export function TodoListPage({ listId }: { listId: number }) {
  const navigate = useNavigate();
  const todoApi = todoApiFor(listId);
  const [list, setList] = useState<TodoList | null>(null);
  const [teams, setTeams] = useState<Team[] | null>(null);
  const [todos, setTodos] = useState<Todo[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [text, setText] = useState("");

  const load = () => {
    setError(null);
    Promise.all([todoListApi.get(listId), todoApi.list()]).then(([l, t]) => {
      setList(l);
      setTodos(t);
    }, e => setError(e.message));
  };
  useEffect(load, [listId]);
  // Only needed for the team picker, so a failure here doesn't block the list.
  useEffect(() => {
    teamApi.all().then(setTeams, e => setError(e.message));
  }, []);

  /** Rename and/or move the list, showing the change right away. */
  const updateList = async (patch: TodoListPatch) => {
    const before = list;
    setList(l => (l ? { ...l, ...patch } : l));
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

  /** Apply a change locally right away; undo it if the request fails. */
  const optimistic = async (apply: (todos: Todo[]) => Todo[], request: () => Promise<void>) => {
    const before = todos;
    setTodos(t => (t ? apply(t) : t));
    setError(null);
    try {
      await request();
    } catch (e) {
      setTodos(before);
      setError((e as Error).message);
    }
  };

  const add = (e: FormEvent) => {
    e.preventDefault();
    const value = text.trim();
    if (!value) return;
    setText("");
    const tempId = -Date.now(); // placeholder until the server assigns a real id
    const now = new Date().toISOString();
    optimistic(
      t => [...t, { id: tempId, text: value, done: false, createdAt: now, updatedAt: now }],
      async () => {
        const created = await todoApi.create(value);
        setTodos(t => t?.map(todo => (todo.id === tempId ? created : todo)) ?? t);
      },
    );
  };

  const update = (id: number, patch: TodoPatch) =>
    optimistic(
      t => t.map(todo => (todo.id === id ? { ...todo, ...patch } : todo)),
      async () => {
        const saved = await todoApi.update(id, patch);
        setTodos(t => t?.map(todo => (todo.id === id ? saved : todo)) ?? t);
      },
    );

  const remove = (id: number) =>
    optimistic(
      t => t.filter(todo => todo.id !== id),
      () => todoApi.remove(id),
    );

  /** `ids` is one section (open or completed) in its new order. */
  const reorder = (ids: number[]) =>
    optimistic(
      t => {
        const rank = new Map(ids.map((id, i) => [id, i]));
        const sorted = t.filter(todo => rank.has(todo.id)).sort((a, b) => rank.get(a.id)! - rank.get(b.id)!);
        let next = 0;
        return t.map(todo => (rank.has(todo.id) ? sorted[next++]! : todo));
      },
      async () => {
        // Unsaved (temporary) todos aren't on the server yet; they keep their place at the end.
        await todoApi.reorder(ids.filter(id => id > 0));
      },
    );

  const rowProps = { onUpdate: update, onRemove: remove, onReorder: reorder };

  const open = todos?.filter(t => !t.done) ?? [];
  const done = todos?.filter(t => t.done) ?? [];

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
          todoCount={todos?.length ?? 0}
          onRename={name => updateList({ name })}
          onMove={teamId => updateList({ teamId })}
          onDelete={deleteList}
        />
      ) : (
        <h1 className="text-3xl font-bold text-muted-foreground">{error ? "Todo list" : "Loading…"}</h1>
      )}

      {/* Hidden when the list failed to load (e.g. it doesn't exist): there's nothing to add to. */}
      {(list || !error) && (
        <form onSubmit={add} className="flex gap-2">
          <Input
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder="Add a todo…"
            aria-label="New todo"
            maxLength={TODO_TEXT_MAX}
          />
          <Button type="submit" disabled={!text.trim() || !todos}>
            <Plus /> Add
          </Button>
        </form>
      )}

      {error && (
        <div role="alert" className="flex items-center justify-between gap-2 rounded-md border border-destructive/50 px-3 py-2 text-sm text-destructive">
          <span>{error}</span>
          {!todos && (
            <Button variant="outline" size="sm" onClick={load}>
              Retry
            </Button>
          )}
        </div>
      )}

      {!todos ? (
        !error && <p className="text-sm text-muted-foreground">Loading…</p>
      ) : todos.length === 0 ? (
        <p className="py-6 text-center text-sm text-muted-foreground">Nothing to do yet.</p>
      ) : (
        <>
          <SortableSection todos={open} {...rowProps} />
          {done.length > 0 && (
            <div className="flex flex-col gap-1">
              <h2 className="px-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Completed ({done.length})
              </h2>
              <SortableSection todos={done} {...rowProps} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
