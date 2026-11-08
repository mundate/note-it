/**
 * Frontend dev server: Bun bundles the React app with hot reload, and forwards /api/*
 * to the FastAPI backend so the browser sees one origin (no CORS).
 * Production doesn't use this: FastAPI serves the built `dist/` itself.
 */
import { serve } from "bun";
import index from "./frontend/index.html";

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

async function proxy(req: Request): Promise<Response> {
  const url = new URL(req.url);
  const headers = new Headers(req.headers);
  headers.delete("host");
  try {
    return await fetch(`${API_URL}${url.pathname}${url.search}`, {
      method: req.method,
      headers,
      body: req.method === "GET" || req.method === "HEAD" ? undefined : await req.arrayBuffer(),
      redirect: "manual",
    });
  } catch {
    return Response.json({ error: `API server isn't reachable at ${API_URL}` }, { status: 502 });
  }
}

const server = serve({
  port: Number(process.env.PORT ?? 3000),
  routes: {
    "/*": index,
    "/api/*": proxy,
  },
  development: {
    hmr: true,
    console: true,
  },
});

console.log(`🚀 Frontend running at ${server.url} (API → ${API_URL})`);
