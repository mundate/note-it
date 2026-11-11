import { Placeholder } from "@/components/Placeholder";
import { ProjectDailyPage } from "@/pages/project-daily/ProjectDailyPage";
import { createFileRoute } from "@tanstack/react-router";

/** Today's daily list for the project (created, with tasks carried over, on open). */
export const Route = createFileRoute("/projects/$projectId/daily/")({
  params: {
    parse: ({ projectId }) => ({ projectId: Number(projectId) }),
    stringify: ({ projectId }) => ({ projectId: String(projectId) }),
  },
  component: TodayRoute,
});

function TodayRoute() {
  const { projectId } = Route.useParams();
  if (!Number.isInteger(projectId) || projectId < 1) return <Placeholder title="Page not found" message="There's nothing at this address." />;
  return <ProjectDailyPage key={projectId} projectId={projectId} />;
}
