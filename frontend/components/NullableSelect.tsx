import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const NONE = "none"; // Radix Select needs a non-empty value for the "none" choice

/** Picks one of `items` by id, or none (e.g. a team or "No team"). */
export function NullableSelect({
  items,
  value,
  onChange,
  noneLabel,
  label,
  disabled,
  size,
}: {
  items: { id: number; name: string }[];
  value: number | null;
  onChange: (id: number | null) => void;
  /** Shown for "none", e.g. "No team". */
  noneLabel: string;
  /** Accessible name, e.g. "Team". */
  label: string;
  disabled?: boolean;
  size?: "sm" | "default";
}) {
  return (
    <Select
      value={value === null ? NONE : String(value)}
      onValueChange={v => onChange(v === NONE ? null : Number(v))}
      disabled={disabled}
    >
      <SelectTrigger size={size} aria-label={label} className="max-w-48">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={NONE}>{noneLabel}</SelectItem>
        {items.map(item => (
          <SelectItem key={item.id} value={String(item.id)}>
            {item.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
