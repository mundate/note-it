import { Placeholder } from "@/components/Placeholder";
import { isValidDay } from "@/lib/day";
import { TeamDailyPage } from "@/pages/team-daily/TeamDailyPage";
import { createFileRoute } from "@tanstack/react-router";

/** The team's combined daily view for one day, e.g. /teams/1/daily/2026-11-10. */
export const Route = createFileRoute("/teams/$teamId/daily/$day")({
  params: {
    parse: ({ teamId, day }) => ({ teamId: Number(teamId), day }),
    stringify: ({ teamId, day }) => ({ teamId: String(teamId), day }),
  },
  component: DayRoute,
});

function DayRoute() {
  const { teamId, day } = Route.useParams();
  if (!Number.isInteger(teamId) || teamId < 1 || !isValidDay(day)) {
    return <Placeholder title="Page not found" message="There's nothing at this address." />;
  }
  // `key` gives each day fresh page state when stepping between days.
  return <TeamDailyPage key={`${teamId}/${day}`} teamId={teamId} day={day} />;
}
