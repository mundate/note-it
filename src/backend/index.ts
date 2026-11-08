import { serve } from "bun";
import index from "../frontend/index.html";
import { openDb } from "./db";
import { todoRoutes } from "./todoRoutes";
import { createTodoRepo } from "./todos";

const db = openDb();
const todos = createTodoRepo(db);

const server = serve({
  routes: {
    // Serve index.html for all unmatched routes.
    "/*": index,

    ...todoRoutes(todos),

    "/api/hello": {
      async GET(req) {
        return Response.json({
          message: "Hello, world!",
          method: "GET",
        });
      },
      async PUT(req) {
        return Response.json({
          message: "Hello, world!",
          method: "PUT",
        });
      },
    },

    "/api/hello/:name": async req => {
      const name = req.params.name;
      return Response.json({
        message: `Hello, ${name}!`,
      });
    },
  },

  development: process.env.NODE_ENV !== "production" && {
    // Enable browser hot reloading in development
    hmr: true,

    // Echo console logs from the browser to the server
    console: true,
  },
});

console.log(`🚀 Server running at ${server.url}`);
