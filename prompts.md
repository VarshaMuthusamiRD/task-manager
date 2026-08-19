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
