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

Set an API key (required — there is no default):

```bash
export API_KEY=changeme          # macOS/Linux
$env:API_KEY = "changeme"        # PowerShell
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
cp .env.example .env   # then edit .env to match your API_KEY and backend URL
npm run dev
```

The UI is now at `http://localhost:5173`, talking to the backend URL configured in
`.env` (`VITE_API_BASE_URL`, default `http://127.0.0.1:8000`) using `VITE_API_KEY` as
the `X-API-Key` header on every request.

## API reference

All requests below assume `API_KEY=changeme` and the server running at
`http://127.0.0.1:8000`. Every request must include `X-API-Key: changeme`; omitting it
or sending the wrong value returns `401 Unauthorized`.

### Create a task — `POST /tasks`

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H "X-API-Key: changeme" \
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
curl http://127.0.0.1:8000/tasks -H "X-API-Key: changeme"
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
curl http://127.0.0.1:8000/tasks/1 -H "X-API-Key: changeme"
```
Status: `200 OK` with the task, or `404 Not Found` if the id doesn't exist.

### Update a task — `PUT /tasks/{id}`

```bash
curl -X PUT http://127.0.0.1:8000/tasks/1 \
  -H "X-API-Key: changeme" \
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
curl -X DELETE http://127.0.0.1:8000/tasks/1 -H "X-API-Key: changeme"
```
Status: `204 No Content`, or `404 Not Found` if the id doesn't exist.

## Out of scope

See `SPEC.md` for the full list (multi-user accounts, pagination/filtering, file
attachments, full OAuth/session auth, rate limiting, deployment/CI config).
