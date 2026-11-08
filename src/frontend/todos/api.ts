import type { Todo, TodoPatch } from "@shared/todo";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: init?.body ? { "Content-Type": "application/json" } : undefined,
  });
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { error?: string } | null;
    throw new Error(body?.error ?? `Request failed (${res.status})`);
  }
  return (res.status === 204 ? undefined : await res.json()) as T;
}

export const todoApi = {
  list: () => request<Todo[]>("/api/todos"),
  create: (text: string) => request<Todo>("/api/todos", { method: "POST", body: JSON.stringify({ text }) }),
  update: (id: number, patch: TodoPatch) =>
    request<Todo>(`/api/todos/${id}`, { method: "PATCH", body: JSON.stringify(patch) }),
  remove: (id: number) => request<void>(`/api/todos/${id}`, { method: "DELETE" }),
  /** Saves a new order for `ids` (one section of the list); returns the full list. */
  reorder: (ids: number[]) =>
    request<Todo[]>("/api/todos/reorder", { method: "POST", body: JSON.stringify({ ids }) }),
};
