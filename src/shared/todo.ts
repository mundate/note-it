/** A todo as returned by the API. Shared by backend and frontend. */
export type Todo = {
  id: number;
  text: string;
  done: boolean;
  createdAt: string;
  updatedAt: string;
};

export type TodoPatch = Partial<Pick<Todo, "text" | "done">>;

export const TODO_TEXT_MAX = 500;
