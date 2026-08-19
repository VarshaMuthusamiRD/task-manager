# Implementation Notes

A plain-language summary of what was built, why, and how it fits together — written
for someone who didn't watch the work happen.

## What was built

A REST API for managing tasks (create, list, retrieve, update, delete), persisted in
SQLite so data survives a server restart, with a plain HTML/CSS/vanilla-JS frontend
that exercises the full CRUD flow. The frontend started as a React (Vite) app and was
later replaced — see "React, then plain HTML/CSS/JS" below. A static API-key check
was also built and later removed. The whole thing was built in slices, each on its
own branch, tested before the next slice began; see `prompts.md` for the full history
including the mid-course pivots.

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

**React, then plain HTML/CSS/JS.** The frontend was originally built with React
(Vite) — a reasonable default for a CRUD UI. In practice it introduced a chain of
environment problems that were hard to diagnose remotely (a stray dev-server process
serving stale config, a CORS origin mismatch that curl-based verification couldn't
detect since curl doesn't enforce CORS) before actually being confirmed broken. After
that debugging cost, and because this app's UI is genuinely simple — one form, one
list, four operations — it was rewritten as three static files (`index.html`,
`style.css`, `app.js`) with no build step, no framework, no dev server required at
all. `app.js` uses the same `fetch`-wrapper pattern the React version used, just
without JSX or component state; DOM updates are done directly (`innerHTML` on the
relevant `<li>`, re-attaching event listeners) since there's no virtual DOM to do it
for you. This removes an entire class of "did the build tool pick up my change"
failure modes for a UI this small.

## How the pieces fit together

```
frontend/ (static HTML/CSS/JS)    backend/ (FastAPI)
+----------------------+           +---------------------------+
| index.html            |  fetch    | main.py                   |
|  (form + task list)   |--/tasks-->|  APIRouter("/tasks")      |
| app.js                |           |  +- create_task_endpoint |
|  +- apiRequest()       |           |  +- list_tasks_endpoint  |
|  +- renderTasks()      |           |  +- get_task_endpoint    |
|  +- renderViewMode()   |           |  +- update_task_endpoint |
|  +- renderEditMode()   |           |  +- delete_task_endpoint |
| style.css              |           +-----------+---------------+
+----------------------+                       | calls
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
status dropdown) triggers an event listener in `app.js`, which calls `apiRequest()` —
a small `fetch` wrapper — straight to the matching route handler in `main.py` (no
auth check in front of it — see above). The handler calls into `crud.py`, which runs
SQL against the connection it's given and returns a plain `dict`; FastAPI serializes
that against the `TaskOut` Pydantic model into JSON. Back in the browser, `app.js`
re-fetches the full list (`refresh()`) and re-renders the affected DOM rather than
patching state in place — simple and correct for a list this small, at the cost of
being less efficient than a diffing UI library for a much larger one.

**Persistence.** Every request opens its own SQLite connection (via the `get_db`
FastAPI dependency) and closes it when the request finishes — there's no long-lived
connection or pool to manage. Because the data lives in a file (`backend/data/tasks.db`),
killing and restarting the `uvicorn` process doesn't lose anything; this is verified
directly in `backend/tests/test_persistence.py`, which reopens the database file in a
fresh connection and confirms a previously created task is still there.

**Frontend<->backend contract.** The Task JSON shape (`id, title, description, status,
created_at, updated_at`) is defined once in `SPEC.md` and mirrored on both sides: as
Pydantic models (`TaskCreate`/`TaskUpdate`/`TaskOut`) in `models.py`, and as the
`STATUS_LABELS` map plus the plain objects `app.js` sends and receives — the status
`<select>` options are generated from that same map so the dropdown can never submit a
value the backend would reject.

**CORS.** Since the frontend has no fixed origin (it can be opened via `file://`,
served from `127.0.0.1`, or `localhost`, depending on how you run it), the backend's
CORS policy matches any `localhost`/`127.0.0.1` origin plus the literal `null` origin
a browser sends for `file://` pages, rather than a single hardcoded URL. This was the
actual root cause of an early "it's broken" report that looked like a CSS/rendering
bug but was really the browser silently discarding a `200` response — see
`prompts.md`.

**Testing strategy.** Each backend slice added its own test file focused on that
slice's endpoints (create/list, retrieve/update/delete) plus dedicated persistence
and CORS tests — 17 tests total, covering the happy path and at least the two
required failure modes (validation errors and missing-id 404s) for every mutating
endpoint. The frontend has no automated tests (plain DOM manipulation, no test
runner set up for it — see `prompts.md` for why that tradeoff was made); it was
verified with real end-to-end checks instead: curl against the API plus
headless-browser screenshots (`msedge --headless --screenshot`) of the actual
rendered page, including the create/edit/delete/status-change flows.

## Known limitations

Everything under "Out of scope" in `SPEC.md` — no multi-user accounts, no
pagination/filtering, no file attachments, no rate limiting, no deployment
configuration. `/tasks` currently has no authentication at all — anyone who can reach
the port can read and modify every task. Fine for local development; would need
revisiting (fixed correctly this time, or a different approach like a reverse-proxy
auth layer) before any non-local deployment.
