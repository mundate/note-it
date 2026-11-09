import { Sidebar, type NavItem } from "@/components/Sidebar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { House, ListTodo, Network, NotebookPen, Settings } from "lucide-react";
import { useState } from "react";
import { APITester } from "./APITester";
import { TodoList } from "./todos/TodoList";
import "./index.css";

import logo from "./logo.svg";
import reactLogo from "./react.svg";

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
        {active.id === "home" ? <Home /> : active.id === "todos" ? <TodoList /> : <Placeholder title={active.label} />}
      </main>
    </div>
  );
}

function Home() {
  return (
    <div className="mx-auto max-w-3xl text-center">
      <div className="flex justify-center items-center gap-8 mb-8">
        <img
          src={logo}
          alt="Bun Logo"
          className="h-36 p-6 transition-all duration-300 hover:drop-shadow-[0_0_2em_#646cffaa] scale-120"
        />
        <img
          src={reactLogo}
          alt="React Logo"
          className="h-36 p-6 transition-all duration-300 hover:drop-shadow-[0_0_2em_#61dafbaa] [animation:spin_20s_linear_infinite]"
        />
      </div>
      <Card>
        <CardHeader className="gap-4">
          <CardTitle className="text-3xl font-bold">Bun + React</CardTitle>
          <CardDescription>
            Edit <code className="rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono">frontend/App.tsx</code> and
            save to test HMR
          </CardDescription>
        </CardHeader>
        <CardContent>
          <APITester />
        </CardContent>
      </Card>
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
