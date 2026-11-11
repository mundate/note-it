import { Placeholder } from "@/components/Placeholder";
import { isValidDay } from "@/lib/day";
import { TeamPeriodPage } from "@/pages/team-period/TeamPeriodPage";
import { createFileRoute } from "@tanstack/react-router";

/** The team's combined sprint view for one sprint, e.g. /teams/1/sprint/2026-11-02. */
export const Route = createFileRoute("/teams/$teamId/sprint/$start")({
  params: {
    parse: ({ teamId, start }) => ({ teamId: Number(teamId), start }),
    stringify: ({ teamId, start }) => ({ teamId: String(teamId), start }),
  },
  component: SprintRoute,
});

function SprintRoute() {
  const { teamId, start } = Route.useParams();
  if (!Number.isInteger(teamId) || teamId < 1 || !isValidDay(start)) {
    return <Placeholder title="Page not found" message="There's nothing at this address." />;
  }
  // `key` gives each sprint fresh page state when stepping between sprints.
  return <TeamPeriodPage kind="sprint" key={`${teamId}/${start}`} teamId={teamId} start={start} />;
}
