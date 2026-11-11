Read my PLANNING.md file to get an idea of things I care about

# Frontend structure

- `frontend/routes/` only defines routes (TanStack file-based routing). A route file stays thin: it calls `createFileRoute` and renders a page from `frontend/pages/`. No page UI or logic lives in a route file. (`__root.tsx` is the app layout and is the exception.)
- `frontend/pages/<page>/` holds one page:
  - `<Page>Page.tsx` is the page component (e.g. `pages/todo-list/TodoListPage.tsx`).
  - `components/` holds components used only by that page.
  - Page-only helpers (e.g. `api.ts`) sit next to the page component.
- `frontend/components/` holds components shared by more than one page or by the layout. `components/ui/` is shadcn primitives.
- Non-component code shared by more than one page goes at the top level too: API calls in `frontend/api/` (e.g. `api/todos.ts`), other helpers in `frontend/lib/`.
- When a page component starts being used by a second page, move it to `frontend/components/` rather than importing across page folders.
- A route that isn't built yet can render the shared `Placeholder` directly; give it a page folder once it gets real UI.
