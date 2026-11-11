/**
 * Entry point for the React app (included in `frontend/index.html`).
 *
 * Pages are file-based: each file in `routes/` is a route, and `routes/__root.tsx` is the
 * layout around them. `routeTree.gen.ts` is generated from that folder by `bun run gen:routes`
 * (also run by `dev` and `build`); don't edit it by hand.
 */

import { createRouter, RouterProvider } from "@tanstack/react-router";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { routeTree } from "./routeTree.gen";

const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

const elem = document.getElementById("root")!;
const app = (
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);

// https://bun.com/docs/bundler/hot-reloading#import-meta-hot-data
(import.meta.hot.data.root ??= createRoot(elem)).render(app);
