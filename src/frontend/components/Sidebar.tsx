import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { PanelLeftClose, PanelLeftOpen, type LucideIcon } from "lucide-react";
import { useEffect, useState } from "react";

export type NavItem = {
  id: string;
  label: string;
  icon: LucideIcon;
};

const STORAGE_KEY = "sidebar:collapsed";

function readCollapsed(): boolean {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored !== null) return stored === "true";
  } catch {}
  return window.matchMedia("(max-width: 767px)").matches;
}

export function Sidebar({
  items,
  activeId,
  onSelect,
}: {
  items: NavItem[];
  activeId: string;
  onSelect: (id: string) => void;
}) {
  const [collapsed, setCollapsed] = useState(readCollapsed);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, String(collapsed));
    } catch {}
  }, [collapsed]);

  // Ctrl/Cmd + B toggles the sidebar
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === "b" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setCollapsed(c => !c);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const ToggleIcon = collapsed ? PanelLeftOpen : PanelLeftClose;

  return (
    <aside
      data-collapsed={collapsed}
      className={cn(
        "sticky top-0 flex h-screen shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-[width] duration-200 ease-in-out",
        collapsed ? "w-16" : "w-60",
      )}
    >
      <div className={cn("flex h-14 items-center gap-2 px-3", collapsed ? "justify-center" : "justify-between")}>
        {!collapsed && <span className="truncate pl-2 text-lg font-semibold">Note it!</span>}
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => setCollapsed(c => !c)}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-expanded={!collapsed}
          title={`${collapsed ? "Expand" : "Collapse"} sidebar (Ctrl/⌘ B)`}
        >
          <ToggleIcon />
        </Button>
      </div>

      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto overflow-x-hidden px-3 py-2">
        {items.map(({ id, label, icon: Icon }) => {
          const active = id === activeId;
          return (
            <button
              key={id}
              type="button"
              onClick={() => onSelect(id)}
              aria-current={active ? "page" : undefined}
              title={collapsed ? label : undefined}
              className={cn(
                "flex h-9 items-center gap-3 rounded-md px-2.5 text-sm font-medium outline-none transition-colors",
                "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 focus-visible:ring-sidebar-ring",
                active && "bg-sidebar-primary text-sidebar-primary-foreground hover:bg-sidebar-primary hover:text-sidebar-primary-foreground",
                collapsed && "justify-center px-0",
              )}
            >
              <Icon className="size-4 shrink-0" />
              {!collapsed && <span className="truncate">{label}</span>}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
