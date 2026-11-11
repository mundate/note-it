/** Todo list and todo requests. Each call returns the response data or throws the API's error message. */
import { client, unwrap, type Todo, type TodoList, type TodoListPatch, type TodoPatch } from "./client";

const list = (listId: number) => ({ params: { path: { list_id: listId } } });
const todo = (listId: number, todoId: number) => ({ params: { path: { list_id: listId, todo_id: todoId } } });

export const todoListApi = {
  /** All lists, or only one team's. */
  all: async (teamId?: number): Promise<TodoList[]> =>
    unwrap(await client.GET("/api/todo-lists", { params: { query: teamId === undefined ? {} : { teamId } } })),

  get: async (listId: number): Promise<TodoList> => unwrap(await client.GET("/api/todo-lists/{list_id}", list(listId))),

  /** `teamId` assigns the new list to a team. */
  create: async (name: string, teamId: number | null = null): Promise<TodoList> =>
    unwrap(await client.POST("/api/todo-lists", { body: { name, teamId } })),

  /** Rename the list and/or move it to a team. `teamId: null` takes it off its team. */
  update: async (listId: number, patch: TodoListPatch): Promise<TodoList> =>
    unwrap(await client.PATCH("/api/todo-lists/{list_id}", { ...list(listId), body: patch })),

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
