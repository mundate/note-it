import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type Announcements,
  type DragEndEvent,
} from "@dnd-kit/core";
import { restrictToParentElement, restrictToVerticalAxis } from "@dnd-kit/modifiers";
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { TODO_TEXT_MAX, type Todo, type TodoPatch } from "../api/client";
import { GripVertical, Plus, Trash2 } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { todoApi } from "./api";

export function TodoList() {
  const [todos, setTodos] = useState<Todo[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [text, setText] = useState("");

  const load = () => {
    setError(null);
    todoApi.list().then(setTodos, e => setError(e.message));
  };
  useEffect(load, []);

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
      <h1 className="text-3xl font-bold">Todos</h1>

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

type RowHandlers = {
  onUpdate: (id: number, patch: TodoPatch) => void;
  onRemove: (id: number) => void;
  onReorder: (ids: number[]) => void;
};

/** A drag-sortable list. Items can only be dragged within their own section. */
function SortableSection({ todos, onReorder, ...handlers }: { todos: Todo[] } & RowHandlers) {
  const sensors = useSensors(
    // A small distance threshold keeps plain clicks on the handle from starting a drag.
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const textOf = (id: unknown) => `"${todos.find(t => t.id === id)?.text ?? "item"}"`;
  const position = (id: unknown) => `${todos.findIndex(t => t.id === id) + 1} of ${todos.length}`;
  const announcements: Announcements = {
    onDragStart: ({ active }) => `Picked up ${textOf(active.id)}, position ${position(active.id)}.`,
    onDragOver: ({ active, over }) => (over ? `${textOf(active.id)} is over position ${position(over.id)}.` : undefined),
    onDragEnd: ({ active, over }) =>
      over ? `Dropped ${textOf(active.id)} at position ${position(over.id)}.` : `Dropped ${textOf(active.id)}.`,
    onDragCancel: ({ active }) => `Cancelled moving ${textOf(active.id)}.`,
  };

  const onDragEnd = ({ active, over }: DragEndEvent) => {
    if (!over || active.id === over.id) return;
    const from = todos.findIndex(t => t.id === active.id);
    const to = todos.findIndex(t => t.id === over.id);
    if (from < 0 || to < 0) return;
    onReorder(arrayMove(todos, from, to).map(t => t.id));
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      modifiers={[restrictToVerticalAxis, restrictToParentElement]}
      onDragEnd={onDragEnd}
      accessibility={{
        announcements,
        screenReaderInstructions: {
          draggable: "To reorder, press space or enter, use the arrow keys to move, then press space or enter again to drop. Press escape to cancel.",
        },
      }}
    >
      <SortableContext items={todos.map(t => t.id)} strategy={verticalListSortingStrategy}>
        <ul className="flex flex-col">
          {todos.map(todo => (
            <TodoRow key={todo.id} todo={todo} {...handlers} />
          ))}
        </ul>
      </SortableContext>
    </DndContext>
  );
}

function TodoRow({ todo, onUpdate, onRemove }: { todo: Todo } & Omit<RowHandlers, "onReorder">) {
  const [draft, setDraft] = useState<string | null>(null); // non-null while editing
  const pending = todo.id < 0; // created locally, not saved yet
  const { attributes, listeners, setNodeRef, setActivatorNodeRef, transform, transition, isDragging } = useSortable({
    id: todo.id,
    disabled: pending,
  });

  const commit = () => {
    const next = draft?.trim();
    setDraft(null);
    if (next && next !== todo.text) onUpdate(todo.id, { text: next });
  };

  return (
    <li
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform), transition }}
      className={cn(
        "group relative flex items-center gap-2 rounded-md py-1 pr-2 pl-0.5 hover:bg-accent/50 focus-within:bg-accent/50",
        isDragging && "z-10 bg-background shadow-md ring-1 ring-border",
      )}
    >
      <button
        type="button"
        ref={setActivatorNodeRef}
        {...attributes}
        {...listeners}
        disabled={pending}
        aria-label={`Reorder "${todo.text}"`}
        className={cn(
          "flex h-7 w-5 shrink-0 cursor-grab touch-none items-center justify-center rounded-sm text-muted-foreground outline-none",
          "focus-visible:ring-2 focus-visible:ring-ring active:cursor-grabbing disabled:cursor-default disabled:opacity-30",
          "md:opacity-0 md:group-hover:opacity-100 md:group-focus-within:opacity-100",
          isDragging && "md:opacity-100",
        )}
      >
        <GripVertical className="size-4" />
      </button>
      <input
        type="checkbox"
        checked={todo.done}
        disabled={pending}
        onChange={() => onUpdate(todo.id, { done: !todo.done })}
        aria-label={`Mark "${todo.text}" ${todo.done ? "not done" : "done"}`}
        className="size-4 shrink-0 accent-primary"
      />
      <input
        value={draft ?? todo.text}
        readOnly={pending}
        maxLength={TODO_TEXT_MAX}
        aria-label="Todo text"
        onFocus={() => !pending && setDraft(todo.text)}
        onChange={e => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={e => {
          if (e.key === "Enter") e.currentTarget.blur();
          if (e.key === "Escape") {
            setDraft(todo.text);
            const el = e.currentTarget;
            requestAnimationFrame(() => {
              setDraft(null);
              el.blur();
            });
          }
        }}
        className={cn(
          "min-w-0 flex-1 rounded-sm bg-transparent px-1 py-0.5 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring",
          todo.done && "text-muted-foreground line-through",
          pending && "opacity-60",
        )}
      />
      <Button
        variant="ghost"
        size="icon-sm"
        className="size-7 md:opacity-0 md:group-hover:opacity-100 md:group-focus-within:opacity-100"
        disabled={pending}
        onClick={() => onRemove(todo.id)}
        aria-label={`Delete "${todo.text}"`}
      >
        <Trash2 />
      </Button>
    </li>
  );
}
