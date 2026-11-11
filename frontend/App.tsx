import { Sidebar, type NavItem } from "@/components/Sidebar";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { House, ListTodo, Network, NotebookPen, Settings } from "lucide-react";
import { useState } from "react";
import { TodoList } from "./todos/TodoList";
import "./index.css";

const NAV_ITEMS: NavItem[] = [
  { id: "home", label: "Home", icon: House },
  { id: "notes", label: "Notes", icon: NotebookPen },
  { id: "todos", label: "Todo Lists", icon: ListTodo },
  { id: "diagrams", label: "Diagrams", icon: Network },
  { id: "settings", label: "Settings", icon: Settings },
];

export function App() {
  const [activeId, setActiveId] = useState("home");
  const active = NAV_ITEMS.find(item => item.id === activeId) ?? NAV_ITEMS[0]!;

  return (
    <div className="flex min-h-screen">
      <Sidebar items={NAV_ITEMS} activeId={activeId} onSelect={setActiveId} />
      <main className="relative z-10 min-w-0 flex-1 p-8">
        {active.id === "home" ? <Home onNavigate={setActiveId} /> : active.id === "todos" ? <TodoList /> : <Placeholder title={active.label} />}
      </main>
    </div>
  );
}

// Sections the home page links to (everything in the sidebar except Home and Settings).
const SECTION_DESCRIPTIONS: Record<string, string> = {
  notes: "Write and organize notes.",
  todos: "Track daily, sprint and timeless todos.",
  diagrams: "Sketch ideas and flows.",
};

function Home({ onNavigate }: { onNavigate: (id: string) => void }) {
  const sections = NAV_ITEMS.filter(item => item.id in SECTION_DESCRIPTIONS);
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-bold">Welcome to Note it!</h1>
      <p className="mt-2 text-muted-foreground">Pick a section to get started.</p>
      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        {sections.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => onNavigate(id)}
            className="rounded-xl text-left outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Card className="h-full transition-colors hover:bg-accent">
              <CardHeader className="gap-2">
                <Icon className="size-5 text-muted-foreground" />
                <CardTitle>{label}</CardTitle>
                <CardDescription>{SECTION_DESCRIPTIONS[id]}</CardDescription>
              </CardHeader>
            </Card>
          </button>
        ))}
      </div>
    </div>
  );
}

function Placeholder({ title }: { title: string }) {
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-bold">{title}</h1>
      <p className="mt-2 text-muted-foreground">Coming soon.</p>
    </div>
  );
}

export default App;
