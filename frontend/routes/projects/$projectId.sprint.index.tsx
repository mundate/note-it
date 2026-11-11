import { Placeholder } from "@/components/Placeholder";
import { ProjectPeriodPage } from "@/pages/project-period/ProjectPeriodPage";
import { createFileRoute } from "@tanstack/react-router";

/** The current sprint's sprint list for the project (created, with tasks carried over, on open). */
export const Route = createFileRoute("/projects/$projectId/sprint/")({
  params: {
    parse: ({ projectId }) => ({ projectId: Number(projectId) }),
    stringify: ({ projectId }) => ({ projectId: String(projectId) }),
  },
  component: CurrentRoute,
});

function CurrentRoute() {
  const { projectId } = Route.useParams();
  if (!Number.isInteger(projectId) || projectId < 1) return <Placeholder title="Page not found" message="There's nothing at this address." />;
  return <ProjectPeriodPage kind="sprint" key={projectId} projectId={projectId} />;
}
