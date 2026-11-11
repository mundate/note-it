import { Placeholder } from "@/components/Placeholder";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/notes")({ component: () => <Placeholder title="Notes" /> });
