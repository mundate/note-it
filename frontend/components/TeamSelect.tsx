import type { Team } from "@/api/client";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const NONE = "none"; // Radix Select needs a non-empty value for "no team"

/** Picks a team, or "No team". */
export function TeamSelect({
  teams,
  value,
  onChange,
  disabled,
  size,
}: {
  teams: Team[];
  value: number | null;
  onChange: (teamId: number | null) => void;
  disabled?: boolean;
  size?: "sm" | "default";
}) {
  return (
    <Select
      value={value === null ? NONE : String(value)}
      onValueChange={v => onChange(v === NONE ? null : Number(v))}
      disabled={disabled}
    >
      <SelectTrigger size={size} aria-label="Team" className="max-w-48">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={NONE}>No team</SelectItem>
        {teams.map(t => (
          <SelectItem key={t.id} value={String(t.id)}>
            {t.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
