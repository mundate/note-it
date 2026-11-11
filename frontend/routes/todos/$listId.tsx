import { Placeholder } from "@/components/Placeholder";
import { TodoListPage } from "@/pages/todo-list/TodoListPage";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/todos/$listId")({
  params: {
    parse: ({ listId }) => ({ listId: Number(listId) }),
    stringify: ({ listId }) => ({ listId: String(listId) }),
  },
  component: TodoListRoute,
});

function TodoListRoute() {
  const { listId } = Route.useParams();
  if (!Number.isInteger(listId) || listId < 1) return <Placeholder title="Page not found" message="There's nothing at this address." />;
  // `key` gives each list fresh page state when navigating between lists.
  return <TodoListPage key={listId} listId={listId} />;
}
