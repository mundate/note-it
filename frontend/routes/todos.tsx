import { TodosPage } from "@/pages/todos/TodosPage";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/todos")({ component: TodosPage });
