import { beforeEach, describe, expect, test } from "bun:test";
import type { Database } from "bun:sqlite";
import { migrate, openDb } from "./db";
import { todoRoutes } from "./todoRoutes";
import { createTodoRepo, type TodoRepo } from "./todos";

let db: Database;
let repo: TodoRepo;

beforeEach(() => {
  db = openDb(":memory:");
  repo = createTodoRepo(db);
});

describe("migrations", () => {
  test("set the schema version and are safe to re-run", () => {
    const version = () => (db.query("PRAGMA user_version").get() as { user_version: number }).user_version;
    expect(version()).toBe(1);
    migrate(db);
    expect(version()).toBe(1);
  });
});

describe("todo repo", () => {
  test("creates todos in order", () => {
    repo.createTodo("first");
    repo.createTodo("second");
    expect(repo.listTodos().map(t => [t.text, t.done])).toEqual([
      ["first", false],
      ["second", false],
    ]);
  });

  test("updates text and done, and lists done items last", () => {
    const a = repo.createTodo("a");
    repo.createTodo("b");
    const updated = repo.updateTodo(a.id, { done: true, text: "a!" });
    expect(updated).toMatchObject({ id: a.id, text: "a!", done: true });
    expect(repo.listTodos().map(t => t.text)).toEqual(["b", "a!"]);

    // Partial update leaves other fields alone.
    expect(repo.updateTodo(a.id, { done: false })).toMatchObject({ text: "a!", done: false });
  });

  test("update and delete of a missing todo", () => {
    expect(repo.updateTodo(999, { done: true })).toBeNull();
    expect(repo.deleteTodo(999)).toBe(false);
  });

  test("reorders given ids and keeps the rest in their relative order", () => {
    const [a, , c, d] = ["a", "b", "c", "d"].map(t => repo.createTodo(t));
    expect(repo.reorderTodos([c!.id, a!.id])).toEqual([]);
    expect(repo.listTodos().map(t => t.text)).toEqual(["c", "a", "b", "d"]);

    // Unknown ids change nothing.
    expect(repo.reorderTodos([d!.id, 999])).toEqual([999]);
    expect(repo.listTodos().map(t => t.text)).toEqual(["c", "a", "b", "d"]);

    // Done items still list after open ones regardless of position.
    repo.updateTodo(c!.id, { done: true });
    expect(repo.listTodos().map(t => t.text)).toEqual(["a", "b", "d", "c"]);
    // New todos go to the end.
    repo.createTodo("e");
    expect(repo.listTodos().map(t => t.text)).toEqual(["a", "b", "d", "e", "c"]);
  });

  test("deletes", () => {
    const a = repo.createTodo("a");
    expect(repo.deleteTodo(a.id)).toBe(true);
    expect(repo.listTodos()).toEqual([]);
  });
});

describe("routes", () => {
  const call = (routes: ReturnType<typeof todoRoutes>, method: string, id?: number, body?: unknown) => {
    const url = `http://test/api/todos${id ? `/${id}` : ""}`;
    const req = Object.assign(
      new Request(url, { method, body: body === undefined ? undefined : JSON.stringify(body) }),
      { params: { id: String(id ?? "") } },
    ) as any;
    const handlers = (id ? routes["/api/todos/:id"] : routes["/api/todos"]) as Record<string, (r: any) => any>;
    return Promise.resolve(handlers[method]!(req)) as Promise<Response>;
  };

  test("validates input", async () => {
    const routes = todoRoutes(repo);
    expect((await call(routes, "POST", undefined, { text: "  " })).status).toBe(400);
    expect((await call(routes, "POST", undefined, { text: "x".repeat(501) })).status).toBe(400);
    expect((await call(routes, "POST", undefined, ["nope"])).status).toBe(400);

    const created = await call(routes, "POST", undefined, { text: "  hi  " });
    expect(created.status).toBe(201);
    const todo = await created.json();
    expect(todo.text).toBe("hi");

    expect((await call(routes, "PATCH", todo.id, { done: "yes" })).status).toBe(400);
    expect((await call(routes, "PATCH", todo.id, {})).status).toBe(400);
    expect((await call(routes, "PATCH", 999, { done: true })).status).toBe(404);
    expect((await call(routes, "DELETE", todo.id)).status).toBe(204);
    expect((await call(routes, "DELETE", todo.id)).status).toBe(404);
  });

  test("reorder validates ids", async () => {
    const routes = todoRoutes(repo);
    const reorder = (body: unknown) =>
      (routes["/api/todos/reorder"].POST as (r: Request) => Promise<Response>)(
        new Request("http://test/api/todos/reorder", { method: "POST", body: JSON.stringify(body) }),
      );
    const a = repo.createTodo("a");
    const b = repo.createTodo("b");
    expect((await reorder({ ids: "nope" })).status).toBe(400);
    expect((await reorder({ ids: [a.id, a.id] })).status).toBe(400);
    expect((await reorder({ ids: [999] })).status).toBe(404);
    const ok = await reorder({ ids: [b.id, a.id] });
    expect(ok.status).toBe(200);
    expect((await ok.json()).map((t: { text: string }) => t.text)).toEqual(["b", "a"]);
  });
});
