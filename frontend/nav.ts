import { House, ListTodo, Network, NotebookPen, Settings, type LucideIcon } from "lucide-react";
import type { FileRouteTypes } from "./routeTree.gen";

export type NavItem = {
  to: FileRouteTypes["to"];
  label: string;
  icon: LucideIcon;
  /** Shown on the home page's section cards. Items without one aren't listed there. */
  description?: string;
};

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Home", icon: House },
  { to: "/notes", label: "Notes", icon: NotebookPen, description: "Write and organize notes." },
  { to: "/todos", label: "Todo Lists", icon: ListTodo, description: "Track daily, sprint and timeless todos." },
  { to: "/diagrams", label: "Diagrams", icon: Network, description: "Sketch ideas and flows." },
  { to: "/settings", label: "Settings", icon: Settings },
];
