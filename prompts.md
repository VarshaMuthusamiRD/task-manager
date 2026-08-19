# Prompt Journal

Running log of prompts given to the coding agent for this project, what came back,
and what I'd change in hindsight. Updated as work progresses.

---

## Slice 0 — Spec + repo scaffolding

**Asked:** Build a small REST API for managing tasks (create/list/update/delete,
persistence, SQLite) with a React frontend and Python backend. Write the spec first
(endpoints, data shape, validation, status codes, persistence, out-of-scope) before
any code. Plan in plan mode, sliced, each slice approved before executing. Keep every
function under 30 lines, no unnecessary dependencies, tests before new functionality,
error handling with happy + at least 2 failure paths. Stretch: API-key auth.

**Got back:** Clarifying questions on framework (FastAPI), task field shape, git/PR
setup (new GitHub repo), and frontend scope (full CRUD UI) — then a 6-slice plan
(spec/scaffold → create+list → retrieve/update/delete → API-key auth → frontend UI →
docs/journal wrap-up), each slice as its own branch + PR.

**What I'd change:** Nothing yet — will revisit after later slices to note anything
that had to be re-planned.

---

## Slice 1 — Backend: create + list

**Asked:** "yes move to slice 1" — implement `POST /tasks` and `GET /tasks` per the
approved plan, with FastAPI + SQLite, Pydantic validation, and unit tests before
moving on.

**Got back:** `app/db.py` (connection + schema init), `app/models.py` (Pydantic
`TaskCreate`/`TaskOut`), `app/crud.py`, `app/main.py`, and 5 tests (empty list,
create happy path, missing title 422, invalid status 422, list ordering). Discovered
`gh` CLI isn't installed/authenticated in this environment, so PR creation had to be
manual — pushed the branch and handed over the compare URL instead.

**What I'd change:** Switched `@app.on_event("startup")` to the modern `lifespan`
context manager immediately after first running the tests and seeing the deprecation
warning — worth just starting with `lifespan` from the beginning next time.

---

## Slice 2 — Backend: retrieve, update, delete

**Asked:** "go ahead with slice 2" — implement `GET/PUT/DELETE /tasks/{id}`, with 404s
for missing ids, 422s for invalid update payloads, and a test proving data survives a
process restart.

**Got back:** `crud.update_task`/`delete_task` (both return `None`/`False` on missing
id so `main.py` can 404), a `TaskUpdate` model reusing `TaskCreate`'s validation,
`Depends(get_db)` to de-duplicate the connection open/close boilerplate across all 5
endpoints, 7 new unit tests, plus `test_persistence.py` which reopens a temp-file
SQLite DB to simulate a restart. Also manually verified with a real `uvicorn` process:
created a task, killed and restarted the server, confirmed the task was still there,
then exercised get/update/delete against the live server.

**What I'd change:** Since PR 1 wasn't merged yet when this slice started, I stacked
this branch on top of `feat/backend-create-list` instead of `main` — worth deciding
up front whether to wait for each merge or stack branches, rather than re-deciding per
slice.

---

## Slice 3 — Stretch: API-key authentication

**Asked:** "move to slice 3" — add a static `X-API-Key` check on all `/tasks` routes,
401 on missing/wrong key, with `.env.example` and tests for missing/wrong/correct key.

**Got back:** `app/auth.py` with a `require_api_key` dependency reading `API_KEY` from
`os.environ`; refactored `main.py` to an `APIRouter(prefix="/tasks",
dependencies=[Depends(require_api_key)])` so the check applies once instead of on
every route individually. Updated the `client` test fixture to set `API_KEY` and send
a default `X-API-Key` header so all 13 prior tests kept passing unchanged, plus 3 new
auth tests. Verified manually against a live `uvicorn` process with real curl calls
(no key → 401, wrong key → 401, correct key → 200).

**What I'd change:** Deliberately skipped `python-dotenv` to avoid an unnecessary
dependency — `.env.example` is a template, not auto-loaded; the README will need to
say so explicitly (export the var or use a loader) so it's not assumed to "just work".

---

## Slice 4 — Frontend: React CRUD UI

**Asked:** "move to slice 4" — build the React (Vite) CRUD UI: list, create form,
inline edit, delete, status toggle, calling the backend with the API key header.

**Got back:** Scaffolded with `npm create vite@latest frontend -- --template react`,
then `src/api.js` (fetch wrapper attaching `X-API-Key`), `src/statuses.js`,
`TaskForm.jsx`, `TaskItem.jsx` (inline edit + status `<select>` + delete),
`TaskList.jsx`, and `App.jsx` tying them together with `useState`/`useEffect`. Also
had to add `CORSMiddleware` to the backend (`main.py`) so the browser could call it
from the Vite dev origin — not something a curl-only backend slice would have
surfaced. Verified both `npm run dev` and `npm run build` succeed and the backend API
they call is already curl-verified end to end.

**What I'd change:** The Chrome browser extension wasn't connected in this
environment, so I couldn't do an actual click-through verification in a browser —
only confirmed the dev server serves without errors and the production build
compiles. That's a real gap versus the plan's "exercise create/edit/delete/status
toggle in browser" verification step; worth doing a manual pass once a browser is
available, or setting up the browser extension before starting this slice next time.
