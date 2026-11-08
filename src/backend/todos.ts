/**
 * Todo repository: the only place that knows about the `todos` table.
 * Routes (REST today, anything else later) call these functions.
 */
import type { Todo, TodoPatch } from "@shared/todo";
import type { Database } from "bun:sqlite";

type TodoRow = {
  id: number;
  text: string;
  done: 0 | 1;
  position: number;
  created_at: string;
  updated_at: string;
};

const toTodo = (row: TodoRow): Todo => ({
  id: row.id,
  text: row.text,
  done: row.done === 1,
  createdAt: row.created_at,
  updatedAt: row.updated_at,
});

export function createTodoRepo(db: Database) {
  const list = db.query<TodoRow, []>("SELECT * FROM todos ORDER BY done, position, id");
  const get = db.query<TodoRow, { id: number }>("SELECT * FROM todos WHERE id = $id");
  const insert = db.query<TodoRow, { text: string }>(
    `INSERT INTO todos (text, position)
     VALUES ($text, (SELECT COALESCE(MAX(position), -1) + 1 FROM todos))
     RETURNING *`,
  );
  const update = db.query<TodoRow, { id: number; text: string | null; done: number | null }>(
    `UPDATE todos
     SET text       = COALESCE($text, text),
         done       = COALESCE($done, done),
         updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
     WHERE id = $id
     RETURNING *`,
  );
  const remove = db.query<never, { id: number }>("DELETE FROM todos WHERE id = $id");
  const idsByPosition = db.query<{ id: number }, []>("SELECT id FROM todos ORDER BY position, id");
  const setPosition = db.query<never, { id: number; position: number }>(
    "UPDATE todos SET position = $position WHERE id = $id",
  );

  /** `ids` move to the front in the given order; all other todos keep their relative order after them. */
  const reorder = db.transaction((ids: number[]) => {
    const moved = new Set(ids);
    const rest = idsByPosition.all().map(r => r.id).filter(id => !moved.has(id));
    [...ids, ...rest].forEach((id, position) => setPosition.run({ id, position }));
  });

  return {
    listTodos(): Todo[] {
      return list.all().map(toTodo);
    },

    getTodo(id: number): Todo | null {
      const row = get.get({ id });
      return row ? toTodo(row) : null;
    },

    createTodo(text: string): Todo {
      return toTodo(insert.get({ text })!);
    },

    /** Returns the updated todo, or null if it doesn't exist. */
    updateTodo(id: number, patch: TodoPatch): Todo | null {
      const row = update.get({
        id,
        text: patch.text ?? null,
        done: patch.done === undefined ? null : patch.done ? 1 : 0,
      });
      return row ? toTodo(row) : null;
    },

    /** Returns false if the todo didn't exist. */
    deleteTodo(id: number): boolean {
      return remove.run({ id }).changes > 0;
    },

    /**
     * Reorders todos: `ids` take the given order (e.g. one section of the list after a
     * drag). Returns the ids that don't exist, without changing anything if there are any.
     */
    reorderTodos(ids: number[]): number[] {
      const missing = ids.filter(id => !get.get({ id }));
      if (missing.length === 0) reorder(ids);
      return missing;
    },
  };
}

export type TodoRepo = ReturnType<typeof createTodoRepo>;
