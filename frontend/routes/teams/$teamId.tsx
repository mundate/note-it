import { Placeholder } from "@/components/Placeholder";
import { TeamPage } from "@/pages/team/TeamPage";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/teams/$teamId")({
  params: {
    parse: ({ teamId }) => ({ teamId: Number(teamId) }),
    stringify: ({ teamId }) => ({ teamId: String(teamId) }),
  },
  component: TeamRoute,
});

function TeamRoute() {
  const { teamId } = Route.useParams();
  if (!Number.isInteger(teamId) || teamId < 1) return <Placeholder title="Page not found" message="There's nothing at this address." />;
  // `key` gives each team fresh page state when navigating between teams.
  return <TeamPage key={teamId} teamId={teamId} />;
}
