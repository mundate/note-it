import { TODO_LIST_NAME_MAX } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";
import { useState } from "react";

/** The list's name as an editable heading, plus a delete button. */
export function ListHeader({
  name,
  todoCount,
  onRename,
  onDelete,
}: {
  name: string;
  todoCount: number;
  onRename: (name: string) => void;
  onDelete: () => void;
}) {
  const [draft, setDraft] = useState<string | null>(null); // non-null while editing

  const commit = () => {
    const next = draft?.trim();
    setDraft(null);
    if (next && next !== name) onRename(next);
  };

  const confirmDelete = () => {
    const todos = todoCount === 1 ? "1 todo" : `${todoCount} todos`;
    if (window.confirm(`Delete "${name}"${todoCount ? ` and its ${todos}` : ""}? This can't be undone.`)) onDelete();
  };

  return (
    <div className="flex items-center gap-2">
      <h1 className="min-w-0 flex-1">
        <input
          value={draft ?? name}
          maxLength={TODO_LIST_NAME_MAX}
          aria-label="List name"
          onFocus={() => setDraft(name)}
          onChange={e => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={e => {
            if (e.key === "Enter") e.currentTarget.blur();
            if (e.key === "Escape") {
              setDraft(name);
              const el = e.currentTarget;
              requestAnimationFrame(() => {
                setDraft(null);
                el.blur();
              });
            }
          }}
          className="w-full rounded-sm bg-transparent px-1 -mx-1 text-3xl font-bold outline-none hover:bg-accent/50 focus-visible:ring-2 focus-visible:ring-ring"
        />
      </h1>
      <Button variant="ghost" size="icon-sm" onClick={confirmDelete} aria-label={`Delete list "${name}"`} title="Delete list">
        <Trash2 />
      </Button>
    </div>
  );
}
