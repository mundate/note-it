import { cn } from "@/lib/utils";
import { useState } from "react";

/**
 * Text that edits in place: click or tab in to edit, Enter or blur saves, Escape cancels.
 * Empty or unchanged text isn't saved.
 */
export function EditableText({
  value,
  onSave,
  maxLength,
  label,
  className,
}: {
  value: string;
  onSave: (value: string) => void;
  maxLength?: number;
  /** Accessible name, e.g. "List name". */
  label: string;
  className?: string;
}) {
  const [draft, setDraft] = useState<string | null>(null); // non-null while editing

  const commit = () => {
    const next = draft?.trim();
    setDraft(null);
    if (next && next !== value) onSave(next);
  };

  return (
    <input
      value={draft ?? value}
      maxLength={maxLength}
      aria-label={label}
      onFocus={() => setDraft(value)}
      onChange={e => setDraft(e.target.value)}
      onBlur={commit}
      onKeyDown={e => {
        if (e.key === "Enter") e.currentTarget.blur();
        if (e.key === "Escape") {
          setDraft(value);
          const el = e.currentTarget;
          requestAnimationFrame(() => {
            setDraft(null);
            el.blur();
          });
        }
      }}
      className={cn(
        "-mx-1 w-full min-w-0 rounded-sm bg-transparent px-1 outline-none hover:bg-accent/50 focus-visible:ring-2 focus-visible:ring-ring",
        className,
      )}
    />
  );
}
