import { Placeholder } from "@/components/Placeholder";
import { Sidebar } from "@/components/Sidebar";
import { NAV_ITEMS } from "@/nav";
import { createRootRoute, Outlet } from "@tanstack/react-router";

export const Route = createRootRoute({
  component: RootLayout,
  notFoundComponent: () => <Placeholder title="Page not found" message="There's nothing at this address." />,
});

function RootLayout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar items={NAV_ITEMS} />
      <main className="relative z-10 min-w-0 flex-1 p-8">
        <Outlet />
      </main>
    </div>
  );
}
