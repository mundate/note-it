import { client, type ErrorResponse, type Todo, type TodoPatch } from "../api/client";

/** Returns `data`, or throws the API's `{ error }` message. */
function unwrap<T>(result: { data?: T; error?: ErrorResponse | unknown; response: Response }): T {
  if (result.error !== undefined || !result.response.ok) {
    const message = (result.error as ErrorResponse | undefined)?.error;
    throw new Error(message ?? `Request failed (${result.response.status})`);
  }
  return result.data as T;
}

export const todoApi = {
  list: async (): Promise<Todo[]> => unwrap(await client.GET("/api/todos")),

  create: async (text: string): Promise<Todo> => unwrap(await client.POST("/api/todos", { body: { text } })),

  update: async (id: number, patch: TodoPatch): Promise<Todo> =>
    unwrap(await client.PATCH("/api/todos/{todo_id}", { params: { path: { todo_id: id } }, body: patch })),

  remove: async (id: number): Promise<void> => {
    unwrap(await client.DELETE("/api/todos/{todo_id}", { params: { path: { todo_id: id } } }));
  },

  /** Saves a new order for `ids` (one section of the list); returns the full list. */
  reorder: async (ids: number[]): Promise<Todo[]> =>
    unwrap(await client.POST("/api/todos/reorder", { body: { ids } })),
};
