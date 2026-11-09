import { Button } from "@/components/ui/button";
import { THEMES, useTheme, type Theme } from "@/lib/theme";
import { cn } from "@/lib/utils";
import { Monitor, Moon, Sun, type LucideIcon } from "lucide-react";

const OPTIONS: Record<Theme, { label: string; icon: LucideIcon }> = {
  light: { label: "Light", icon: Sun },
  dark: { label: "Dark", icon: Moon },
  system: { label: "System", icon: Monitor },
};

/** Segmented Light/Dark/System control; `compact` shows one button that cycles instead. */
export function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const { theme, setTheme } = useTheme();

  if (compact) {
    const next = THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length]!;
    const Icon = OPTIONS[theme].icon;
    return (
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={() => setTheme(next)}
        aria-label={`Theme: ${OPTIONS[theme].label}. Switch to ${OPTIONS[next].label}`}
        title={`Theme: ${OPTIONS[theme].label}`}
      >
        <Icon />
      </Button>
    );
  }

  return (
    <div role="radiogroup" aria-label="Theme" className="flex rounded-md bg-sidebar-accent p-0.5">
      {THEMES.map(value => {
        const { label, icon: Icon } = OPTIONS[value];
        const selected = value === theme;
        return (
          <button
            key={value}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => setTheme(value)}
            title={label}
            className={cn(
              "flex h-7 flex-1 items-center justify-center gap-1.5 rounded-[5px] text-xs font-medium outline-none transition-colors",
              "text-muted-foreground hover:text-sidebar-foreground focus-visible:ring-2 focus-visible:ring-sidebar-ring",
              selected && "bg-sidebar text-sidebar-foreground shadow-xs",
            )}
          >
            <Icon className="size-3.5" />
            {label}
          </button>
        );
      })}
    </div>
  );
}
