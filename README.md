# Note it!
Note it! is a notes taking app that is meant to have the flexability needed for any software engineering job. The hope is it can be used for a wide variety of projects, topics, lists, or even designing. Some examples include creating todo lists, creating diagrams of existing architecture, allowing you to embed notes within diagrams in a compact way, and more!

## Stack

- **Frontend:** React + Tailwind in `src/frontend/`, bundled by [Bun](https://bun.com).
- **Backend:** [FastAPI](https://fastapi.tiangolo.com) in `backend/`, storing data in SQLite (`data/note-it.sqlite`).
- **API types:** generated from the backend. `src/frontend/api/openapi.json` and `schema.d.ts` are produced by `bun run gen:api`; don't edit them by hand.

Requires [Bun](https://bun.com) and [uv](https://docs.astral.sh/uv/).

## Commands

```bash
bun install        # JS deps (also installs the type generator in tools/openapi-gen)
cd backend && uv sync && cd ..   # Python deps

bun dev            # backend (:8000) + frontend with hot reload (:3000); regenerates API types on backend changes
bun run gen:api    # regenerate frontend API types from the FastAPI models
bun run check:api  # fail if the committed API types are out of date
bun run test       # backend tests (pytest) + frontend type-check
bun start          # production: build the frontend, then FastAPI serves everything on :8000
```

API docs are at http://localhost:8000/docs while the backend is running.
