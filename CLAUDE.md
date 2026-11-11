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

# Backend structure

- `backend/app/core/` is shared infrastructure (db, base models, errors). Each feature is its own package under `backend/app/` (`todo/`, `team/`, ...) with `models.py`, `repository.py` (SQL), `service.py` (rules, raises `core.exceptions` errors) and `routes.py`.
- A feature used by several others (like `team`, which todo lists, notes and diagrams can all be assigned to) is its own package. Other features may depend on it, never the reverse. Teams are optional: no feature may require one.
- Repositories get their lock from `core.db.lock_for(db)` so all repositories on a connection share one lock.
- Projects (`app/project/`) belong to at most one team and outlive it: deleting a team keeps its projects and lists (team cleared). A list's project must be in the list's team (picking a project sets the team; changing team drops the project). Deleting a project deletes its lists. Dependency order: `todo` → `project` → `team`, never the reverse.
- Daily lists (`kind = 'daily'`; sprint and recurring later) belong to a project, are opt-in per project (`dailyEnabled`), and are created and updated only by the server (`POST /api/projects/{id}/daily/today`, or the team's combined `POST /api/teams/{id}/daily/today`), never through `POST /api/todo-lists`. They can't be renamed, moved or deleted, and normal list queries leave them out.
