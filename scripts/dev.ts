/**
 * `bun dev`: runs the FastAPI backend and the Bun frontend dev server together,
 * regenerates the frontend's API types whenever backend code changes, and regenerates
 * the route tree (frontend/routeTree.gen.ts) whenever files in frontend/routes/ change.
 */
import { spawn, type Subprocess } from "bun";
import { watch } from "node:fs";

const API_PORT = process.env.API_PORT ?? "8000";
const root = new URL("..", import.meta.url).pathname;

const children: Subprocess[] = [
  spawn(["uv", "run", "uvicorn", "app.main:app", "--reload", "--port", API_PORT], {
    cwd: `${root}backend`,
    stdout: "inherit",
    stderr: "inherit",
  }),
  spawn(["bun", "--hot", "frontend/dev.ts"], {
    cwd: root,
    env: { ...process.env, API_URL: `http://127.0.0.1:${API_PORT}` },
    stdout: "inherit",
    stderr: "inherit",
  }),
  spawn(["bunx", "tsr", "watch"], { cwd: root, stdout: "ignore", stderr: "inherit" }),
];

// Regenerate types on backend changes (debounced; one run at a time).
let timer: Timer | undefined;
let running = false;
let again = false;
const regenerate = async () => {
  if (running) return void (again = true);
  running = true;
  const gen = spawn(["bun", "run", "gen:api"], { cwd: root, stdout: "ignore", stderr: "inherit" });
  const code = await gen.exited;
  console.log(code === 0 ? "🔁 API types regenerated" : "⚠️  API type generation failed");
  running = false;
  if (again) {
    again = false;
    void regenerate();
  }
};
watch(`${root}backend/app`, { recursive: true }, (_, file) => {
  if (!file?.endsWith(".py")) return;
  clearTimeout(timer);
  timer = setTimeout(regenerate, 300);
});

const shutdown = () => {
  for (const child of children) child.kill();
  process.exit(0);
};
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

// If either process dies, stop the other.
await Promise.race(children.map(c => c.exited));
shutdown();
