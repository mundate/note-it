/** Todo list and todo requests. Each call returns the response data or throws the API's error message. */
import { client, unwrap, type Todo, type TodoList, type TodoListPatch, type TodoPatch } from "./client";

const list = (listId: number) => ({ params: { path: { list_id: listId } } });
const todo = (listId: number, todoId: number) => ({ params: { path: { list_id: listId, todo_id: todoId } } });

export const todoListApi = {
  /** Standard lists, optionally one team's and/or one project's (`noProject`: lists not in a project). */
  all: async (filter: { teamId?: number; projectId?: number; noProject?: boolean } = {}): Promise<TodoList[]> =>
    unwrap(await client.GET("/api/todo-lists", { params: { query: filter } })),

  get: async (listId: number): Promise<TodoList> => unwrap(await client.GET("/api/todo-lists/{list_id}", list(listId))),

  /** `projectId` puts the new list in a project (and so in its team); `teamId` just in a team. */
  create: async (name: string, place: { teamId?: number | null; projectId?: number | null } = {}): Promise<TodoList> =>
    unwrap(await client.POST("/api/todo-lists", { body: { name, ...place } })),

  /** Rename and/or move the list. `null` takes it off its team / project; a project also sets the team. */
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

/**
 * Daily lists: one per project per day (opt-in per project). Opening today creates it and
 * moves unfinished todos from earlier days onto it. A team's view combines its projects'.
 */
export const dailyApi = {
  /** The project's daily lists, newest day first. */
  projectDays: async (projectId: number): Promise<TodoList[]> =>
    unwrap(await client.GET("/api/projects/{project_id}/daily", { params: { path: { project_id: projectId } } })),

  openProjectToday: async (projectId: number): Promise<TodoList> =>
    unwrap(await client.POST("/api/projects/{project_id}/daily/today", { params: { path: { project_id: projectId } } })),

  /** Days with a daily list in any of the team's projects, newest first. */
  teamDays: async (teamId: number): Promise<string[]> =>
    unwrap(await client.GET("/api/teams/{team_id}/daily/days", { params: { path: { team_id: teamId } } })),

  /** That day's daily lists across the team's projects. */
  teamDay: async (teamId: number, day: string): Promise<TodoList[]> =>
    unwrap(await client.GET("/api/teams/{team_id}/daily/{day}", { params: { path: { team_id: teamId, day } } })),

  /** Today's daily lists for the team's active projects with daily turned on. */
  openTeamToday: async (teamId: number): Promise<TodoList[]> =>
    unwrap(await client.POST("/api/teams/{team_id}/daily/today", { params: { path: { team_id: teamId } } })),
};
