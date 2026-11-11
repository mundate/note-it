/** Todo list and todo requests. Each call returns the response data or throws the API's error message. */
import { client, unwrap, type Todo, type TodoList, type TodoPatch } from "./client";

const list = (listId: number) => ({ params: { path: { list_id: listId } } });
const todo = (listId: number, todoId: number) => ({ params: { path: { list_id: listId, todo_id: todoId } } });

export const todoListApi = {
  all: async (): Promise<TodoList[]> => unwrap(await client.GET("/api/todo-lists")),

  get: async (listId: number): Promise<TodoList> => unwrap(await client.GET("/api/todo-lists/{list_id}", list(listId))),

  create: async (name: string): Promise<TodoList> =>
    unwrap(await client.POST("/api/todo-lists", { body: { name } })),

  rename: async (listId: number, name: string): Promise<TodoList> =>
    unwrap(await client.PATCH("/api/todo-lists/{list_id}", { ...list(listId), body: { name } })),

  /** Deletes the list and all of its todos. */
  remove: async (listId: number): Promise<void> => {
    unwrap(await client.DELETE("/api/todo-lists/{list_id}", list(listId)));
  },
};

/** Requests for the todos in one list. */
export function todoApi(listId: number) {
  return {
    list: async (): Promise<Todo[]> => unwrap(await client.GET("/api/todo-lists/{list_id}/todos", list(listId))),

    create: async (text: string): Promise<Todo> =>
      unwrap(await client.POST("/api/todo-lists/{list_id}/todos", { ...list(listId), body: { text } })),

    update: async (id: number, patch: TodoPatch): Promise<Todo> =>
      unwrap(await client.PATCH("/api/todo-lists/{list_id}/todos/{todo_id}", { ...todo(listId, id), body: patch })),

    remove: async (id: number): Promise<void> => {
      unwrap(await client.DELETE("/api/todo-lists/{list_id}/todos/{todo_id}", todo(listId, id)));
    },

    /** Saves a new order for `ids` (one section of the list); returns the full list. */
    reorder: async (ids: number[]): Promise<Todo[]> =>
      unwrap(await client.POST("/api/todo-lists/{list_id}/todos/reorder", { ...list(listId), body: { ids } })),
  };
}
