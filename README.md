# Task Manager

A small REST API for managing tasks (Python/FastAPI + SQLite), with a React (Vite)
CRUD frontend. See `SPEC.md` for the full API spec and `IMPLEMENTATION.md` for what
was built, why, and how the pieces fit together.

## Requirements

- Python 3.11+
- Node.js 18+ / npm

## Backend setup

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate   # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
```

Run the server:

```bash
uvicorn app.main:app --reload
```

The API is now at `http://127.0.0.1:8000`. The SQLite database is created
automatically at `backend/data/tasks.db` on first startup and persists across
restarts.

Run the tests:

```bash
pytest
```

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env   # then edit .env if your backend runs on a different URL
npm run dev
```

The UI is now at `http://localhost:5173`, talking to the backend URL configured in
`.env` (`VITE_API_BASE_URL`, default `http://127.0.0.1:8000`). No authentication is
required — see "Authentication" in `SPEC.md` for why.

### Troubleshooting

- **"Failed to fetch" when creating/loading tasks:** two common causes:
  1. `VITE_API_BASE_URL` in `frontend/.env` doesn't match the port the backend is
     actually running on, or the backend isn't running. Vite only reads `.env` at
     server startup — after editing it, stop `npm run dev` (Ctrl+C) and start it
     again; it will not pick up the change live.
  2. **CORS.** The browser blocks the response if the page's origin isn't one the
     backend allows — this can silently fail even though the backend responds `200`
     (curl won't show this, since curl doesn't enforce CORS; only real browsers do).
     By default the backend allows any `http://localhost:<port>` or
     `http://127.0.0.1:<port>` origin, which covers the normal case. If you set
     `FRONTEND_ORIGIN` explicitly, it must exactly match what's in the browser's
     address bar (`localhost` and `127.0.0.1` are different origins to a browser even
     though they're the same machine).
- **Styles look wrong or a stray dev server:** if port 5173 is unexpectedly reported
  as "in use" when starting `npm run dev`, an old dev server process is likely still
  running with stale config baked in. Find and stop it (e.g. Task Manager on Windows,
  or `lsof -i :5173` / `kill` on macOS/Linux) before starting a fresh one.

## API reference

All requests below assume the server is running at `http://127.0.0.1:8000`. No
authentication is required.

### Create a task — `POST /tasks`

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "description": "2% preferred", "status": "todo"}'
```

```json
{
  "id": 1,
  "title": "Buy milk",
  "description": "2% preferred",
  "status": "todo",
  "created_at": "2026-08-19T16:52:39.548421+00:00",
  "updated_at": "2026-08-19T16:52:39.548421+00:00"
}
```
Status: `201 Created`. Missing/empty `title` or an invalid `status` returns `422`.

### List tasks — `GET /tasks`

```bash
curl http://127.0.0.1:8000/tasks
```

```json
[
  {
    "id": 1,
    "title": "Buy milk",
    "description": "2% preferred",
    "status": "todo",
    "created_at": "2026-08-19T16:52:39.548421+00:00",
    "updated_at": "2026-08-19T16:52:39.548421+00:00"
  }
]
```
Status: `200 OK` (empty array `[]` if there are no tasks).

### Retrieve a task — `GET /tasks/{id}`

```bash
curl http://127.0.0.1:8000/tasks/1
```
Status: `200 OK` with the task, or `404 Not Found` if the id doesn't exist.

### Update a task — `PUT /tasks/{id}`

```bash
curl -X PUT http://127.0.0.1:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk", "description": "done", "status": "done"}'
```

```json
{
  "id": 1,
  "title": "Buy milk",
  "description": "done",
  "status": "done",
  "created_at": "2026-08-19T16:52:39.548421+00:00",
  "updated_at": "2026-08-19T16:53:12.040542+00:00"
}
```
Status: `200 OK`, `404 Not Found` for a missing id, `422` for an invalid payload.

### Delete a task — `DELETE /tasks/{id}`

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/1
```
Status: `204 No Content`, or `404 Not Found` if the id doesn't exist.

## Out of scope

See `SPEC.md` for the full list (multi-user accounts, pagination/filtering, file
attachments, full OAuth/session auth, rate limiting, deployment/CI config).
