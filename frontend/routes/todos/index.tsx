import { TodoListsPage } from "@/pages/todo-lists/TodoListsPage";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/todos/")({ component: TodoListsPage });
