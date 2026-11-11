import { TODO_TEXT_MAX, type Todo, type TodoPatch } from "@/api/client";
import { todoApi as todoApiFor } from "@/api/todos";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { SortableSection } from "./SortableSection";

/**
 * A list's todos: the add form, open and completed sections, edits and drag-to-reorder.
 * Changes show right away and are undone if the request fails. Render it with
 * `key={listId}` so state resets when the list changes.
 */
export function TodoListView({
  listId,
  onTodosChange,
  emptyText = "Nothing to do yet.",
  name,
  showAddForm = true,
}: {
  listId: number;
  /** Called whenever the todos change (e.g. so a header can show a count). */
  onTodosChange?: (todos: Todo[]) => void;
  emptyText?: string;
  /** The list's name, for the add box's accessible label when several lists share a page. */
  name?: string;
  /** False hides the "Add a todo" box (e.g. a read-mostly summary view). */
  showAddForm?: boolean;
}) {
  const todoApi = todoApiFor(listId);
  const [todos, setTodos] = useState<Todo[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [text, setText] = useState("");

  const load = () => {
    setError(null);
    todoApi.list().then(setTodos, e => setError(e.message));
  };
  useEffect(load, [listId]);
  useEffect(() => {
    if (todos) onTodosChange?.(todos);
  }, [todos]);

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
    <>
      {showAddForm && (
        <form onSubmit={add} className="flex gap-2">
          <Input
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder="Add a todo…"
            aria-label={name ? `New todo for ${name}` : "New todo"}
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
        <p className="py-6 text-center text-sm text-muted-foreground">{emptyText}</p>
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
    </>
  );
}
