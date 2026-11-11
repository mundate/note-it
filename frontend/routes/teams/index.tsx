import { TeamsPage } from "@/pages/teams/TeamsPage";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/teams/")({ component: TeamsPage });
