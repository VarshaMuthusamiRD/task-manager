# Implementation Notes

A plain-language summary of what was built, why, and how it fits together — written
for someone who didn't watch the work happen.

## What was built

A REST API for managing tasks (create, list, retrieve, update, delete), persisted in
SQLite so data survives a server restart, with a React frontend that exercises the
full CRUD flow. A static API-key check protects every `/tasks` route. The whole thing
was built in six slices, each on its own branch, tested before the next slice began.

## Why these choices

**FastAPI over Flask.** FastAPI gives request validation "for free" via Pydantic
models — a missing title or a bad status value is rejected with a `422` before any
handler code runs, instead of hand-writing `if`-checks. It also generates interactive
API docs (`/docs`) from the same models, which is useful for a project meant to be
picked up by someone else later.

**Raw `sqlite3` over an ORM.** The data model is one table with five columns and no
relationships. An ORM (SQLAlchemy, etc.) would add a dependency and an abstraction
layer for no real benefit here — plain SQL in `crud.py` is shorter and easier to
audit. `db.py` creates the table with `CREATE TABLE IF NOT EXISTS` on startup, which
is enough for a project with no schema migrations planned.

**API-key authentication, then removed.** The brief's stretch goal was a static
`X-API-Key` header check, and it was built and tested that way in Slice 3. In
practice it kept breaking during local setup — the frontend's and backend's copies of
the key or port drifted out of sync across terminals/`.env` edits in a way that was
hard to diagnose remotely, including one case where the backend having *no* key
configured at all produced the same error as a genuinely wrong key. After that was
fixed and the problem persisted, it was removed outright rather than keep debugging
config drift for a project with no real users to protect yet. `/tasks` is currently
open with no authentication — see "Known limitations" below.

**No `python-dotenv`.** `.env.example` files exist as documentation of what
environment variables are needed, but the app reads `os.environ` directly rather than
auto-loading `.env`. Adding a dependency just to read a text file felt unnecessary for
a project this size; the README says explicitly how to set the variables instead.

**React + Vite, plain `fetch`.** No state management library, no UI framework — the
task list is small (a handful of tasks, five fields each), so `useState`/`useEffect`
in `App.jsx` is enough to hold and refresh it. `fetch` needs no extra dependency at
all.

## How the pieces fit together

```
frontend/ (React + Vite)          backend/ (FastAPI)
+----------------------+           +---------------------------+
| App.jsx               |  fetch    | main.py                   |
|  +- TaskForm.jsx       |--/tasks-->|  APIRouter("/tasks")      |
|  +- TaskList.jsx       |           |  +- create_task_endpoint |
|  |   +- TaskItem.jsx   |           |  +- list_tasks_endpoint  |
|  +- api.js (fetch      |           |  +- get_task_endpoint    |
|      wrapper)          |           |  +- update_task_endpoint |
+----------------------+           |  +- delete_task_endpoint |
                                    +-----------+---------------+
                                                | calls
                                    +-----------v---------------+
                                    | crud.py                   |
                                    |  create/list/get/update/  |
                                    |  delete_task               |
                                    +-----------+---------------+
                                                | SQL
                                    +-----------v---------------+
                                    | db.py -> tasks.db (SQLite)|
                                    | survives process restart  |
                                    +----------------------------+
```

**Request flow.** A browser action (submit the create form, click delete, change the
status dropdown) calls a function in `api.js`, which sends a `fetch` request straight
to the matching route handler in `main.py` (no auth check in front of it — see above).
The handler calls into `crud.py`, which runs SQL against the connection it's given and
returns a plain `dict`; FastAPI serializes that against the `TaskOut` Pydantic model
into JSON.

**Persistence.** Every request opens its own SQLite connection (via the `get_db`
FastAPI dependency) and closes it when the request finishes — there's no long-lived
connection or pool to manage. Because the data lives in a file (`backend/data/tasks.db`),
killing and restarting the `uvicorn` process doesn't lose anything; this is verified
directly in `backend/tests/test_persistence.py`, which reopens the database file in a
fresh connection and confirms a previously created task is still there.

**Frontend<->backend contract.** The Task JSON shape (`id, title, description, status,
created_at, updated_at`) is defined once in `SPEC.md` and mirrored on both sides: as
Pydantic models (`TaskCreate`/`TaskUpdate`/`TaskOut`) in `models.py`, and as the plain
objects `api.js` sends and receives. `statuses.js` on the frontend mirrors the
`TaskStatus` enum on the backend so the status dropdown can never submit a value the
backend would reject.

**Testing strategy.** Each backend slice added its own test file focused on that
slice's endpoints (create/list, retrieve/update/delete) plus one dedicated
persistence test — 13 tests total, covering the happy path and at least the two
required failure modes (validation errors and missing-id 404s) for every mutating
endpoint. The frontend was verified by running `npm run build` (catches compile/import
errors) and `npm run dev` against a live backend; a full click-through in an actual
browser window was not possible in the environment this was built in — see
`prompts.md` for that caveat and how to close it.

## Known limitations

Everything under "Out of scope" in `SPEC.md` — no multi-user accounts, no
pagination/filtering, no file attachments, no rate limiting, no deployment
configuration. `/tasks` currently has no authentication at all — anyone who can reach
the port can read and modify every task. Fine for local development; would need
revisiting (fixed correctly this time, or a different approach like a reverse-proxy
auth layer) before any non-local deployment.
