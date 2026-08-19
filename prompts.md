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

---

## Slice 5 — Docs + prompt journal wrap-up

**Asked:** "move to Slice 5" — finalize `README.md` with setup instructions and
example requests/responses, write `IMPLEMENTATION.md` explaining what was built, why,
and how, and keep this journal current.

**Got back:** A full `README.md` replacing the Slice 0 stub (backend/frontend setup,
every endpoint with a `curl` example and its actual response, auth usage) and
`IMPLEMENTATION.md` (design rationale for FastAPI/raw-sqlite3/static-API-key/no-ORM
choices, plus a request-flow diagram from browser click through to SQLite). Verified
every example in the README against a live server run rather than hand-writing
plausible-looking JSON, and re-ran the full backend test suite (16/16 passing) as a
final check before wrapping up.

**What I'd change:** Looking back across all five slices, the biggest process gap was
not having `gh` CLI or a connected browser extension available from the start — both
had to be discovered mid-project and worked around (manual PR links; build-only
verification for the frontend instead of a real click-through). Confirming tooling
availability before slicing the plan would avoid re-explaining the same workaround
each time.

---

## Post-slice-4 bug: "Failed to fetch" + CSS not loading

**Asked:** User reported "failed to fetched, couldnt add task, also css not loading"
while running the app themselves.

**Got back:** Root cause was `frontend/.env` still holding leftover values from my
Slice 4 manual testing (`127.0.0.1:8125` / `secret123`), plus a stray Vite dev-server
process from that same testing that survived a `pkill` call and kept serving those
stale values on port 5173. Fixed `.env`, force-killed the zombie process by PID, added
`server: { host: true }` to `vite.config.js` (Vite was binding IPv6-loopback-only,
which is likely how the stale process went unnoticed), and added a README
troubleshooting section.

**What I'd change:** Don't background dev servers with `command &` for "quick"
manual verification without a guaranteed-reliable way to kill them afterward — on
this machine `pkill -f` silently fails to stop node/python processes started that
way. Should have killed by PID via PowerShell from the start.

---

## Post-slice-4 bug #2: "Invalid or missing API key" persists

**Asked:** User still hit "invalid or missing api" after the fetch fix, questioned
why API-key auth exists at all, and asked me to make it work, verify via the Chrome
extension, and write tests for it.

**Got back:** Clarified via AskUserQuestion: keep auth (it's the approved Slice 3
stretch goal), add more *backend* tests rather than new frontend test tooling, and —
since the Chrome extension still wasn't connecting on my end — have the user check
their own browser with guidance from me instead. Found a real bug while investigating:
`require_api_key` returned the same 401 whether the client sent a wrong key OR the
server had no `API_KEY` configured at all — indistinguishable from the response,
and the second case (a very plausible mistake: setting `API_KEY` in one terminal,
running `uvicorn` in another) would 401 *every* request no matter what key was sent.
Split it into `500` (server misconfigured) vs `401` (wrong client key), added 4 tests
for the new edge cases (empty header, case sensitivity, unconfigured server key),
verified all three response codes against a live server, and documented the
distinction in `SPEC.md` and the README.

**What I'd change:** This should have been caught during Slice 3 itself — a
"fail closed" auth check that can't distinguish "not configured" from "wrong
credentials" is a design smell worth testing for the first time a stretch-goal auth
feature is built, not after a user hits it in the wild.

---

## Post-slice-4 bug #3: removing API-key auth entirely

**Asked:** "its not working, lets do it without api key now first, do the required
changes, make sure its working, use ecc if u want" — after the 500-vs-401 fix still
didn't resolve it for the user, they asked to drop auth entirely rather than keep
debugging environment mismatches.

**Got back:** Removed `require_api_key`, deleted `app/auth.py` and
`backend/tests/test_auth.py`, stripped the `X-API-Key` header and `VITE_API_KEY` from
the frontend, and updated `SPEC.md`/`README.md`/`IMPLEMENTATION.md` to say
`/tasks` is unauthenticated (with an honest note on *why* it was removed, not just
that it was). Ran `ecc:python-reviewer` and `ecc:react-reviewer` in parallel against
the diff before committing — both came back clean of leftover references; the React
review also surfaced a few pre-existing, unrelated minor bugs in `TaskItem.jsx`
(stale local state on prop refresh) worth a separate pass later. Verified end-to-end
with curl (create/list/update/delete, zero auth headers) both against a fresh
isolated backend and against what looked like the user's own live `--reload` process,
which had already auto-picked up the fix.

**What I'd change:** In hindsight, the auth stretch goal cost three rounds of
debugging (fetch/CSS bug, 500-vs-401 fix, full removal) for a feature that was
explicitly optional. If local dev-environment auth is this fragile to verify without
being able to see the user's actual terminals/browser, it's worth asking upfront
whether the stretch goal is worth the iteration cost before building it, not after.

---

## Post-slice-4 bug #4: "no such table: tasks" (500) — self-inflicted

**Asked:** User pasted a traceback showing `sqlite3.OperationalError: no such table:
tasks` on every `GET`/`POST /tasks` request.

**Got back:** This one was on me, not the user. Throughout the earlier debugging
turns I repeatedly ran `rm -f backend/data/tasks.db` as "cleanup" after my own
verification runs — using the *same default path* the user's own live server was
also using. Deleting that file out from under a running process doesn't restart it or
re-trigger its startup schema creation; the next request just opens a fresh, empty
SQLite file with no `tasks` table. Fixed by making the `get_db` FastAPI dependency
run `CREATE TABLE IF NOT EXISTS` on every request (not just once at startup), so the
app self-heals if the underlying file is ever deleted or replaced while running.
Reproduced the exact failure locally (create a task, delete the file mid-session,
confirm the next request used to 500 and now returns `200`/`[]` instead), added a
regression test, verified live.

**What I'd change:** Never run destructive filesystem cleanup (`rm -f <path>`)
against a path a long-running process I don't control might also be using, even for
"my own test scratch files" — should have used a distinct scratch path (a temp dir,
or a port/DB-path suffix unique to my verification runs) for every manual check
throughout this whole session, not reused the app's real default path. The
self-healing fix is a good outcome, but the bug should never have been introduced.

---

## Post-slice-4 bug #5: real root cause — CORS origin mismatch

**Asked:** "there is no css loadingg, it looks like simple html" (still, after the
db-file fix) — then "do deep reasearch on where and whats the issue" when a hard
refresh and DevTools check didn't resolve it.

**Got back:** Since the Claude browser extension was still not connecting, used
`msedge --headless --disable-gpu --screenshot=... http://<url>` directly (Edge is
already installed; no new dependency) to actually *see* the live page for the first
time this session, instead of only curl-based inference. First screenshot (against
`http://127.0.0.1:5173/`) showed the page **was** styled — bordered inputs, a real
button, a large heading — with a visible "Failed to fetch" error, disproving the "CSS
not loading" theory outright: it was always a fetch failure, and the "plain" look was
just an intentionally minimal design plus a leftover oversized template `<h1>` style,
made worse by the error blanking the task list. Took a second screenshot against
`http://localhost:5173/` (the exact URL the README tells users to visit) — no error,
full styled task list rendered. That difference nailed it: the backend's CORS
`allow_origins` only had the exact string `http://localhost:5173`; a browser (unlike
curl) treats `127.0.0.1` and `localhost` as different origins and silently blocks the
fetch response when they don't match, even though the server itself returns `200`.
Fixed by switching to an `allow_origin_regex` matching `localhost`/`127.0.0.1` on any
port by default. Added 3 CORS regression tests (localhost allowed, 127.0.0.1 allowed,
unrelated origin rejected) — 17/17 passing. Verified against the user's own live
`--reload` process with a third screenshot proving `127.0.0.1` now works too.

**What I'd change:** This should have been the very first hypothesis back when "failed
to fetch" was first reported, not the fourth. All my earlier curl-based verification
was structurally blind to this bug class — curl never enforces CORS, so "verified
working via curl" gave false confidence for a symptom whose actual mechanism is
browser-only. The moment visual/browser verification became unavailable, I should
have reached for a headless-screenshot fallback immediately instead of relying solely
on curl for four separate debugging rounds.
