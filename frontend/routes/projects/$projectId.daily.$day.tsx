import { Placeholder } from "@/components/Placeholder";
import { isValidDay } from "@/lib/day";
import { ProjectDailyPage } from "@/pages/project-daily/ProjectDailyPage";
import { createFileRoute } from "@tanstack/react-router";

/** One day's daily list for the project, e.g. /projects/1/daily/2026-11-10. */
export const Route = createFileRoute("/projects/$projectId/daily/$day")({
  params: {
    parse: ({ projectId, day }) => ({ projectId: Number(projectId), day }),
    stringify: ({ projectId, day }) => ({ projectId: String(projectId), day }),
  },
  component: DayRoute,
});

function DayRoute() {
  const { projectId, day } = Route.useParams();
  if (!Number.isInteger(projectId) || projectId < 1 || !isValidDay(day)) return <Placeholder title="Page not found" message="There's nothing at this address." />;
  // `key` gives each day fresh page state when stepping between days.
  return <ProjectDailyPage key={`${projectId}/${day}`} projectId={projectId} day={day} />;
}
