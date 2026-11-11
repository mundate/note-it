import { Placeholder } from "@/components/Placeholder";
import { TeamDailyPage } from "@/pages/team-daily/TeamDailyPage";
import { createFileRoute } from "@tanstack/react-router";

/** The team's combined daily view for today (each project's list opened, tasks carried over). */
export const Route = createFileRoute("/teams/$teamId/daily/")({
  params: {
    parse: ({ teamId }) => ({ teamId: Number(teamId) }),
    stringify: ({ teamId }) => ({ teamId: String(teamId) }),
  },
  component: TodayRoute,
});

function TodayRoute() {
  const { teamId } = Route.useParams();
  if (!Number.isInteger(teamId) || teamId < 1) return <Placeholder title="Page not found" message="There's nothing at this address." />;
  return <TeamDailyPage key={teamId} teamId={teamId} />;
}
