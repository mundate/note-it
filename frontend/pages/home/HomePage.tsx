import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { NAV_ITEMS } from "@/nav";
import { Link } from "@tanstack/react-router";

export function HomePage() {
  const sections = NAV_ITEMS.filter(item => item.description);
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-bold">Welcome to Note it!</h1>
      <p className="mt-2 text-muted-foreground">Pick a section to get started.</p>
      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        {sections.map(({ to, label, icon: Icon, description }) => (
          <Link key={to} to={to} className="rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <Card className="h-full transition-colors hover:bg-accent">
              <CardHeader className="gap-2">
                <Icon className="size-5 text-muted-foreground" />
                <CardTitle>{label}</CardTitle>
                <CardDescription>{description}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
