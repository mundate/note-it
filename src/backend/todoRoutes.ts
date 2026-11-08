/** REST routes for todos. Thin: parse + validate, then call the repository. */
import { TODO_TEXT_MAX, type TodoPatch } from "@shared/todo";
import type { BunRequest } from "bun";
import type { TodoRepo } from "./todos";

const badRequest = (error: string) => Response.json({ error }, { status: 400 });
const notFound = () => Response.json({ error: "Todo not found" }, { status: 404 });

async function readJson(req: Request): Promise<Record<string, unknown> | null> {
  try {
    const body = await req.json();
    return body && typeof body === "object" && !Array.isArray(body) ? (body as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

/** Returns the cleaned text, or an error message. */
function validText(value: unknown): { text: string } | { error: string } {
  if (typeof value !== "string") return { error: "`text` must be a string" };
  const text = value.trim();
  if (!text) return { error: "`text` must not be empty" };
  if (text.length > TODO_TEXT_MAX) return { error: `\`text\` must be at most ${TODO_TEXT_MAX} characters` };
  return { text };
}

function parseId(raw: string): number | null {
  const id = Number(raw);
  return Number.isSafeInteger(id) && id > 0 ? id : null;
}

export function todoRoutes(repo: TodoRepo) {
  return {
    "/api/todos": {
      GET() {
        return Response.json(repo.listTodos());
      },
      async POST(req: Request) {
        const body = await readJson(req);
        if (!body) return badRequest("Body must be a JSON object");
        const result = validText(body.text);
        if ("error" in result) return badRequest(result.error);
        return Response.json(repo.createTodo(result.text), { status: 201 });
      },
    },

    // Exact routes take precedence over "/api/todos/:id" in Bun, so this doesn't clash.
    "/api/todos/reorder": {
      async POST(req: Request) {
        const body = await readJson(req);
        const ids = body?.ids;
        if (!Array.isArray(ids) || !ids.every(id => Number.isSafeInteger(id) && id > 0)) {
          return badRequest("`ids` must be an array of todo ids");
        }
        if (new Set(ids).size !== ids.length) return badRequest("`ids` must not contain duplicates");

        const missing = repo.reorderTodos(ids as number[]);
        if (missing.length) return Response.json({ error: `Unknown todo ids: ${missing.join(", ")}` }, { status: 404 });
        return Response.json(repo.listTodos());
      },
    },

    "/api/todos/:id": {
      async PATCH(req: BunRequest<"/api/todos/:id">) {
        const id = parseId(req.params.id);
        if (id === null) return notFound();

        const body = await readJson(req);
        if (!body) return badRequest("Body must be a JSON object");

        const patch: TodoPatch = {};
        if ("text" in body) {
          const result = validText(body.text);
          if ("error" in result) return badRequest(result.error);
          patch.text = result.text;
        }
        if ("done" in body) {
          if (typeof body.done !== "boolean") return badRequest("`done` must be a boolean");
          patch.done = body.done;
        }
        if (Object.keys(patch).length === 0) return badRequest("Nothing to update: send `text` and/or `done`");

        const todo = repo.updateTodo(id, patch);
        return todo ? Response.json(todo) : notFound();
      },
      DELETE(req: BunRequest<"/api/todos/:id">) {
        const id = parseId(req.params.id);
        if (id === null || !repo.deleteTodo(id)) return notFound();
        return new Response(null, { status: 204 });
      },
    },
  };
}
