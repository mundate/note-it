import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { TODO_TEXT_MAX, type Todo } from "@/api/client";
import { GripVertical, Trash2 } from "lucide-react";
import { useState } from "react";
import type { RowHandlers } from "./SortableSection";

export function TodoRow({ todo, onUpdate, onRemove }: { todo: Todo } & Omit<RowHandlers, "onReorder">) {
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
