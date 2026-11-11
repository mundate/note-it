import { Placeholder } from "@/components/Placeholder";
import { ProjectPage } from "@/pages/project/ProjectPage";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/projects/$projectId/")({
  params: {
    parse: ({ projectId }) => ({ projectId: Number(projectId) }),
    stringify: ({ projectId }) => ({ projectId: String(projectId) }),
  },
  component: ProjectRoute,
});

function ProjectRoute() {
  const { projectId } = Route.useParams();
  if (!Number.isInteger(projectId) || projectId < 1) return <Placeholder title="Page not found" message="There's nothing at this address." />;
  // `key` gives each project fresh page state when navigating between projects.
  return <ProjectPage key={projectId} projectId={projectId} />;
}
