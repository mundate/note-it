import { Placeholder } from "@/components/Placeholder";
import { TeamPeriodPage } from "@/pages/team-period/TeamPeriodPage";
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
  return <TeamPeriodPage kind="daily" key={teamId} teamId={teamId} />;
}
