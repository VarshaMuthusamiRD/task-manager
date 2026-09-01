# Task Manager REST API — Spec

## Overview
A REST API for managing tasks: create, list, retrieve, update, delete. Persistence
via SQLite so data survives a process restart. Backend: Python (FastAPI). Frontend:
a static HTML/CSS/vanilla JS CRUD UI consuming this API — no build step, no
framework (originally React/Vite; replaced — see `prompts.md`).

## Data shape

### Task
| Field       | Type   | Notes                                              |
|-------------|--------|-----------------------------------------------------|
| id          | int    | Auto-assigned, primary key                         |
| title       | string | Required, non-empty, max 200 chars                 |
| description | string | Optional, max 2000 chars, defaults to `""`         |
| status      | enum   | One of `todo`, `in_progress`, `done`. Default `todo` |
| priority    | enum   | One of `low`, `medium`, `high`. Required — no default. |
| created_at  | string | ISO-8601 UTC timestamp, set on creation             |
| updated_at  | string | ISO-8601 UTC timestamp, set on creation and every update |

### Backward compatibility

`priority` was added after initial release. Existing databases are migrated
automatically on startup: a `priority` column is added with `DEFAULT 'medium'`,
so pre-existing tasks read back with `priority: "medium"`. New tasks created or
updated through the API must still supply `priority` explicitly — the database
default exists only to backfill old rows, not to make the field optional.

## Endpoints

All endpoints are under `/tasks`. Request/response bodies are JSON.

### `POST /tasks`
Create a task.

Request body:
```json
{ "title": "Buy milk", "description": "2% preferred", "status": "todo", "priority": "high" }
```
`description` and `status` are optional (defaults apply). `priority` is **required** —
one of `low`, `medium`, `high` — with no default.

Responses:
- `201 Created` — returns the created task, including `id`, `created_at`, `updated_at`.
- `422 Unprocessable Entity` — `title` missing/empty, `title`/`description` too long, `status` not one of the allowed values, or `priority` missing/not one of the allowed values.

### `GET /tasks`
List all tasks, ordered by `created_at` ascending.

Responses:
- `200 OK` — JSON array of tasks (empty array if none exist).

### `GET /tasks/{id}`
Retrieve a single task.

Responses:
- `200 OK` — the task.
- `404 Not Found` — no task with that id.

### `PUT /tasks/{id}`
Update a task. Full-replace of the mutable fields (`title`, `description`, `status`, `priority`); `id` and `created_at` are immutable, `updated_at` is refreshed server-side.

Request body: same shape as create; `title` and `priority` are still required with no
default. `description` and `status` fall back to their create-time defaults (`""` and
`todo`) if omitted, same as on create — there is no partial-update semantics; omitted
optional fields are reset, not left unchanged.

Responses:
- `200 OK` — the updated task.
- `404 Not Found` — no task with that id.
- `422 Unprocessable Entity` — same validation rules as create.

### `DELETE /tasks/{id}`
Delete a task.

Responses:
- `204 No Content` — deleted.
- `404 Not Found` — no task with that id.

## Authentication
None currently. The `/tasks` routes are open. API-key authentication (the original
stretch goal) was implemented, then removed after persistent local environment-
variable mismatches made it unworkable to verify end-to-end during development — see
`prompts.md` for the history. It can be re-added later if needed.

## Persistence
SQLite file at `backend/data/tasks.db` (git-ignored). Schema created automatically on
first startup if the file/table doesn't exist. No migrations framework — schema
changes for this project are additive, handled by startup-time `CREATE TABLE IF NOT
EXISTS` plus targeted `ALTER TABLE ADD COLUMN` statements for fields (like `priority`)
added after initial release, run idempotently on every request via `init_db()`.

## Out of scope
- Multi-user accounts, per-user task ownership/assignment
- Pagination or sorting options beyond default created_at order
- Server-side filtering (query parameters on `GET /tasks`). The frontend's
  priority filter is client-side only, over the already-fetched task list.
- File attachments on tasks
- Full session/OAuth-based auth (only the static API-key check above)
- Rate limiting
- Deployment configuration / CI pipelines
- Soft-delete / undo / audit history
