import { Placeholder } from "@/components/Placeholder";
import { isValidDay } from "@/lib/day";
import { ProjectPeriodPage } from "@/pages/project-period/ProjectPeriodPage";
import { createFileRoute } from "@tanstack/react-router";

/** One sprint's list for the project, e.g. /projects/1/sprint/2026-11-02. */
export const Route = createFileRoute("/projects/$projectId/sprint/$start")({
  params: {
    parse: ({ projectId, start }) => ({ projectId: Number(projectId), start }),
    stringify: ({ projectId, start }) => ({ projectId: String(projectId), start }),
  },
  component: SprintRoute,
});

function SprintRoute() {
  const { projectId, start } = Route.useParams();
  if (!Number.isInteger(projectId) || projectId < 1 || !isValidDay(start)) return <Placeholder title="Page not found" message="There's nothing at this address." />;
  // `key` gives each sprint fresh page state when stepping between sprints.
  return <ProjectPeriodPage kind="sprint" key={`${projectId}/${start}`} projectId={projectId} start={start} />;
}
