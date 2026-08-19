# Task Manager REST API — Spec

## Overview
A REST API for managing tasks: create, list, retrieve, update, delete. Persistence
via SQLite so data survives a process restart. Backend: Python (FastAPI). Frontend:
React (Vite) CRUD UI consuming this API.

## Data shape

### Task
| Field       | Type   | Notes                                              |
|-------------|--------|-----------------------------------------------------|
| id          | int    | Auto-assigned, primary key                         |
| title       | string | Required, non-empty, max 200 chars                 |
| description | string | Optional, max 2000 chars, defaults to `""`         |
| status      | enum   | One of `todo`, `in_progress`, `done`. Default `todo` |
| created_at  | string | ISO-8601 UTC timestamp, set on creation             |
| updated_at  | string | ISO-8601 UTC timestamp, set on creation and every update |

## Endpoints

All endpoints are under `/tasks`. Request/response bodies are JSON.

### `POST /tasks`
Create a task.

Request body:
```json
{ "title": "Buy milk", "description": "2% preferred", "status": "todo" }
```
`description` and `status` are optional (defaults apply).

Responses:
- `201 Created` — returns the created task, including `id`, `created_at`, `updated_at`.
- `422 Unprocessable Entity` — `title` missing/empty, `title`/`description` too long, or `status` not one of the allowed values.

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
Update a task. Full-replace of the mutable fields (`title`, `description`, `status`); `id` and `created_at` are immutable, `updated_at` is refreshed server-side.

Request body: same shape as create; `title` is still required.

Responses:
- `200 OK` — the updated task.
- `404 Not Found` — no task with that id.
- `422 Unprocessable Entity` — same validation rules as create.

### `DELETE /tasks/{id}`
Delete a task.

Responses:
- `204 No Content` — deleted.
- `404 Not Found` — no task with that id.

## Authentication (stretch goal)
All `/tasks` routes require a header `X-API-Key: <key>` matching a server-configured
key (env var `API_KEY`, loaded via `.env`, no default in code). Missing or wrong key
returns `401 Unauthorized`. If the server itself has no `API_KEY` configured, every
request returns `500 Internal Server Error` instead — this is a server misconfiguration,
distinct from a client sending a bad key, and is reported separately so the two
situations aren't indistinguishable from the response alone. This is a single shared
static key — not per-user auth.

## Persistence
SQLite file at `backend/data/tasks.db` (git-ignored). Schema created automatically on
first startup if the file/table doesn't exist. No migrations framework — schema
changes for this project are additive and handled by startup-time `CREATE TABLE IF
NOT EXISTS`.

## Out of scope
- Multi-user accounts, per-user task ownership/assignment
- Pagination, filtering, or sorting options beyond default created_at order
- File attachments on tasks
- Full session/OAuth-based auth (only the static API-key check above)
- Rate limiting
- Deployment configuration / CI pipelines
- Soft-delete / undo / audit history
