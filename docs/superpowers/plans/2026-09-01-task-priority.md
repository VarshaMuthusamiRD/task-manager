# Task Priority + Filtering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a required `priority` field (`low`/`medium`/`high`) to tasks, surface it in the create/list UI, and let users filter the visible task list by priority — following the exact pattern the existing `status` field already uses end-to-end.

**Architecture:** Additive change to the existing FastAPI + raw-SQLite backend (new enum, new required Pydantic field, new NOT NULL column with a runtime ALTER TABLE migration for pre-existing databases) and the existing static vanilla-JS frontend (new `<select>` mirroring `status-select`, new priority badge, new client-side-only checkbox filter over the already-fetched task list — no new API surface for filtering).

**Tech Stack:** Python 3 / FastAPI / Pydantic / raw `sqlite3` (backend), vanilla HTML/CSS/JS with no build step (frontend), pytest + FastAPI `TestClient` (tests).

**Spec:** No separate spec file exists for this feature — it was approved directly in chat during a `superpowers:brainstorming` (bounded-path) session. The approved requirements are restated in full in the Global Constraints section below; this plan is self-contained.

## Global Constraints

- Priority levels: exactly `low`, `medium`, `high` — no other values.
- **No default at creation.** `priority` is a required field on `TaskCreate` (and therefore `TaskUpdate`, which inherits it) — omitting it must return `422`, exactly like `title`.
- Existing task list sort order (`created_at ASC`) is unchanged. Priority is never a sort key.
- Filtering is **client-side only** — no new query parameters on `GET /tasks`. The frontend fetches the full list as today and hides non-matching `<li>` elements in the DOM.
- Filter UI is **multi-select checkboxes** (Low / Medium / High), all checked by default (= show everything).
- **Backward compatibility:** pre-existing rows in `tasks.db` (created before this feature) have no `priority` value. They must be backfilled to `medium` via a `NOT NULL DEFAULT 'medium'` column added through a runtime migration in `init_db()` — this DB-level default exists solely to satisfy old rows; it must never let a new `POST`/`PUT` request omit `priority` (Pydantic enforces that, independently of the DB default).
- Follow the existing `status` field's pattern at every layer (enum in `models.py`, column in `db.py`, SQL in `crud.py`, `<select>` + label map in `app.js`) rather than inventing a new pattern.

---

## File Structure

| File | Change |
|---|---|
| `backend/app/models.py` | Add `TaskPriority` enum; add required `priority` field to `TaskCreate`/`TaskOut` |
| `backend/app/db.py` | Add `priority` column to `CREATE TABLE`; add runtime `ALTER TABLE` migration for existing DBs |
| `backend/app/crud.py` | Add `priority` to `INSERT`/`UPDATE` column lists in `create_task`/`update_task` |
| `backend/tests/test_models.py` | **New.** Unit tests for `TaskPriority`/`TaskCreate` validation (no DB, no HTTP) |
| `backend/tests/test_priority_migration.py` | **New.** Integration test: pre-existing DB file without `priority` column gets backfilled to `medium` |
| `backend/tests/test_tasks_create_list.py` | Update existing payloads to include `priority`; add missing/invalid-priority `422` tests |
| `backend/tests/test_tasks_retrieve_update_delete.py` | Update `_create` helper and update-payload test to include `priority` |
| `backend/tests/test_persistence.py` | Update direct `TaskCreate(...)` construction to include `priority` |
| `SPEC.md` | Document the new field, validation rule, and backward-compat behavior |
| `frontend/app.js` | Add `PRIORITY_LABELS`, `priorityOptionsHtml()`, wire priority into create form, list rendering, inline priority change, and checkbox filtering |
| `frontend/index.html` | Add priority `<select>` to the create form; add filter checkbox row above the task list |
| `frontend/style.css` | Add `.priority-select`/badge color variants for low/medium/high, filter row styling |

---

## Task 1: Backend data model — `TaskPriority` enum + required field

**Files:**
- Modify: `backend/app/models.py`
- Test: `backend/tests/test_models.py` (new)

**Interfaces:**
- Produces: `TaskPriority` enum with members `low`, `medium`, `high` (values equal names); `TaskCreate.priority: TaskPriority` (required, no default); `TaskUpdate` inherits it; `TaskOut.priority: TaskPriority`.

- [ ] **Step 1: Write the failing unit test**

Create `backend/tests/test_models.py`:

```python
import pytest
from pydantic import ValidationError

from app.models import TaskCreate, TaskOut, TaskPriority


def test_task_priority_has_exactly_three_levels():
    assert {p.value for p in TaskPriority} == {"low", "medium", "high"}


def test_task_create_requires_priority():
    with pytest.raises(ValidationError):
        TaskCreate(title="Task")


def test_task_create_accepts_valid_priority():
    task = TaskCreate(title="Task", priority="high")
    assert task.priority == TaskPriority.high


def test_task_create_rejects_invalid_priority():
    with pytest.raises(ValidationError):
        TaskCreate(title="Task", priority="urgent")


def test_task_out_requires_priority():
    with pytest.raises(ValidationError):
        TaskOut(
            id=1,
            title="Task",
            description="",
            status="todo",
            created_at="2026-09-01T00:00:00+00:00",
            updated_at="2026-09-01T00:00:00+00:00",
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_models.py -v`
Expected: `test_task_priority_has_exactly_three_levels` and the "accepts_valid_priority"/"rejects_invalid_priority" tests FAIL with `ImportError: cannot import name 'TaskPriority'` (module doesn't exist yet); the two "requires_priority" tests FAIL because `pytest.raises(ValidationError)` doesn't trigger (fields aren't required yet).

- [ ] **Step 3: Implement the model changes**

Edit `backend/app/models.py`:

```python
from enum import Enum

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority


class TaskUpdate(TaskCreate):
    pass


class TaskOut(BaseModel):
    id: int
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    created_at: str
    updated_at: str
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_models.py -v`
Expected: PASS (5/5)

- [ ] **Step 5: Commit**

```bash
git add backend/app/models.py backend/tests/test_models.py
git commit -m "feat: add required TaskPriority field to task models"
```

---

## Task 2: DB schema — new column + backward-compatible migration

**Files:**
- Modify: `backend/app/db.py`
- Test: `backend/tests/test_priority_migration.py` (new)

**Interfaces:**
- Consumes: nothing new from Task 1.
- Produces: `init_db(conn)` guarantees the `tasks` table has a `priority TEXT NOT NULL DEFAULT 'medium'` column, whether the table is freshly created or pre-existing without that column.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_priority_migration.py`:

```python
import os
import sqlite3
import tempfile

from app.db import get_connection, init_db


def _create_legacy_schema(path):
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'todo',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "INSERT INTO tasks (title, description, status, created_at, updated_at) "
        "VALUES ('Pre-existing task', '', 'todo', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00')"
    )
    conn.commit()
    conn.close()


def test_init_db_backfills_priority_column_on_legacy_database(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    _create_legacy_schema(path)
    monkeypatch.setenv("TASKS_DB_PATH", path)

    try:
        conn = get_connection()
        init_db(conn)

        row = conn.execute("SELECT priority FROM tasks WHERE title = 'Pre-existing task'").fetchone()
        conn.close()

        assert row["priority"] == "medium"
    finally:
        os.remove(path)


def test_init_db_is_idempotent_on_already_migrated_database(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("TASKS_DB_PATH", path)

    try:
        conn = get_connection()
        init_db(conn)
        init_db(conn)  # must not raise "duplicate column" on second call
        conn.close()
    finally:
        os.remove(path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_priority_migration.py -v`
Expected: `test_init_db_backfills_priority_column_on_legacy_database` FAILS with `sqlite3.OperationalError: no such column: priority`.

- [ ] **Step 3: Implement the migration**

Edit `backend/app/db.py`:

```python
import os
import sqlite3

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tasks.db")


def get_db_path() -> str:
    return os.environ.get("TASKS_DB_PATH", DEFAULT_DB_PATH)


def get_connection() -> sqlite3.Connection:
    path = get_db_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'todo',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    _migrate_add_priority_column(conn)
    conn.commit()


def _migrate_add_priority_column(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)")}
    if "priority" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'")
```

Note: `CREATE TABLE IF NOT EXISTS` alone does not add `priority` to a table that already exists without it — the freshly-created-table case is covered by the `CREATE TABLE` statement (which does not include `priority` inline, so it's added uniformly through the same `_migrate_add_priority_column` path for both fresh and legacy databases). This keeps a single migration code path rather than two.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_priority_migration.py -v`
Expected: PASS (2/2)

- [ ] **Step 5: Run the full existing test suite to check nothing else broke**

Run: `cd backend && python -m pytest -v`
Expected: `test_persistence.py` tests still PASS (they don't touch `priority` directly yet); `test_tasks_create_list.py` and `test_tasks_retrieve_update_delete.py` will start FAILING here because `TaskCreate` now requires `priority` and their payloads don't send it — this is expected and fixed in Task 4. Confirm the failures are all `422` assertion mismatches, not errors from Task 2's own code.

- [ ] **Step 6: Commit**

```bash
git add backend/app/db.py backend/tests/test_priority_migration.py
git commit -m "feat: add priority column with backward-compatible migration"
```

---

## Task 3: CRUD layer — thread `priority` through SQL

**Files:**
- Modify: `backend/app/crud.py`

**Interfaces:**
- Consumes: `TaskCreate.priority`, `TaskUpdate.priority` (Task 1); migrated `priority` column (Task 2).
- Produces: `create_task`/`update_task` persist and return `priority` as part of the row dict (via `_row_to_dict`, unchanged).

- [ ] **Step 1: Implement the SQL changes**

Edit `backend/app/crud.py`:

```python
import sqlite3
from datetime import datetime, timezone

from app.models import TaskCreate, TaskUpdate


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def create_task(conn: sqlite3.Connection, task: TaskCreate) -> dict:
    now = _now_iso()
    cursor = conn.execute(
        """
        INSERT INTO tasks (title, description, status, priority, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (task.title, task.description, task.status.value, task.priority.value, now, now),
    )
    conn.commit()
    return get_task(conn, cursor.lastrowid)


def list_tasks(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM tasks ORDER BY created_at ASC").fetchall()
    return [_row_to_dict(row) for row in rows]


def get_task(conn: sqlite3.Connection, task_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _row_to_dict(row) if row else None


def update_task(conn: sqlite3.Connection, task_id: int, task: TaskUpdate) -> dict | None:
    if get_task(conn, task_id) is None:
        return None
    conn.execute(
        """
        UPDATE tasks SET title = ?, description = ?, status = ?, priority = ?, updated_at = ?
        WHERE id = ?
        """,
        (task.title, task.description, task.status.value, task.priority.value, _now_iso(), task_id),
    )
    conn.commit()
    return get_task(conn, task_id)


def delete_task(conn: sqlite3.Connection, task_id: int) -> bool:
    if get_task(conn, task_id) is None:
        return False
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    return True
```

- [ ] **Step 2: Update `test_persistence.py`'s direct `TaskCreate` construction**

Edit `backend/tests/test_persistence.py` line 26 — change:

```python
        create_task(first_conn, TaskCreate(title="Survive restart"))
```

to:

```python
        create_task(first_conn, TaskCreate(title="Survive restart", priority="medium"))
```

- [ ] **Step 3: Run the persistence tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_persistence.py -v`
Expected: PASS (2/2)

- [ ] **Step 4: Commit**

```bash
git add backend/app/crud.py backend/tests/test_persistence.py
git commit -m "feat: persist priority through create/update CRUD operations"
```

---

## Task 4: API integration tests — update existing suite + add validation coverage

**Files:**
- Modify: `backend/tests/test_tasks_create_list.py`
- Modify: `backend/tests/test_tasks_retrieve_update_delete.py`

**Interfaces:**
- Consumes: `POST /tasks`, `PUT /tasks/{id}` (unchanged routes from `main.py`, now validating `priority` via Task 1's model).

- [ ] **Step 1: Update `test_tasks_create_list.py`**

Replace the full file content:

```python
def test_list_empty_db_returns_empty_array(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_create_task_happy_path(client):
    payload = {"title": "Buy milk", "description": "2% preferred", "status": "todo", "priority": "high"}
    response = client.post("/tasks", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Buy milk"
    assert body["description"] == "2% preferred"
    assert body["status"] == "todo"
    assert body["priority"] == "high"
    assert isinstance(body["id"], int)
    assert body["created_at"] == body["updated_at"]


def test_create_task_missing_title_returns_422(client):
    response = client.post("/tasks", json={"description": "no title here", "priority": "medium"})
    assert response.status_code == 422


def test_create_task_invalid_status_returns_422(client):
    response = client.post("/tasks", json={"title": "Task", "status": "bogus", "priority": "medium"})
    assert response.status_code == 422


def test_create_task_missing_priority_returns_422(client):
    response = client.post("/tasks", json={"title": "Task"})
    assert response.status_code == 422


def test_create_task_invalid_priority_returns_422(client):
    response = client.post("/tasks", json={"title": "Task", "priority": "urgent"})
    assert response.status_code == 422


def test_list_returns_created_tasks(client):
    client.post("/tasks", json={"title": "First", "priority": "low"})
    client.post("/tasks", json={"title": "Second", "priority": "high"})

    response = client.get("/tasks")
    assert response.status_code == 200
    titles = [task["title"] for task in response.json()]
    assert titles == ["First", "Second"]
```

- [ ] **Step 2: Update `test_tasks_retrieve_update_delete.py`**

Replace the full file content:

```python
def _create(client, title="Task", priority="medium"):
    response = client.post("/tasks", json={"title": title, "priority": priority})
    return response.json()


def test_get_task_happy_path(client):
    created = _create(client)
    response = client.get(f"/tasks/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_task_missing_id_returns_404(client):
    response = client.get("/tasks/999")
    assert response.status_code == 404


def test_update_task_happy_path(client):
    created = _create(client, priority="low")
    payload = {"title": "Updated", "description": "new desc", "status": "done", "priority": "high"}
    response = client.put(f"/tasks/{created['id']}", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Updated"
    assert body["status"] == "done"
    assert body["priority"] == "high"
    assert body["created_at"] == created["created_at"]
    assert body["updated_at"] != created["updated_at"]


def test_update_task_missing_id_returns_404(client):
    response = client.put("/tasks/999", json={"title": "X", "priority": "medium"})
    assert response.status_code == 404


def test_update_task_invalid_payload_returns_422(client):
    created = _create(client)
    response = client.put(f"/tasks/{created['id']}", json={"title": "", "priority": "medium"})
    assert response.status_code == 422


def test_update_task_missing_priority_returns_422(client):
    created = _create(client)
    response = client.put(f"/tasks/{created['id']}", json={"title": "Task"})
    assert response.status_code == 422


def test_delete_task_happy_path(client):
    created = _create(client)
    response = client.delete(f"/tasks/{created['id']}")
    assert response.status_code == 204

    follow_up = client.get(f"/tasks/{created['id']}")
    assert follow_up.status_code == 404


def test_delete_task_missing_id_returns_404(client):
    response = client.delete("/tasks/999")
    assert response.status_code == 404
```

- [ ] **Step 3: Run the full backend test suite**

Run: `cd backend && python -m pytest -v`
Expected: PASS, all tests (test_models.py, test_priority_migration.py, test_persistence.py, test_tasks_create_list.py, test_tasks_retrieve_update_delete.py, test_cors.py — CORS tests are untouched by this feature and should already pass).

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_tasks_create_list.py backend/tests/test_tasks_retrieve_update_delete.py
git commit -m "test: extend task CRUD API tests to cover required priority field"
```

---

## Task 5: `SPEC.md` — document the new field

**Files:**
- Modify: `SPEC.md`

- [ ] **Step 1: Update the Task field table**

In `SPEC.md`, in the `### Task` table, add a row after `status`:

```markdown
| priority    | enum   | One of `low`, `medium`, `high`. Required — no default.  |
```

- [ ] **Step 2: Update the `POST /tasks` section**

Change:

```markdown
Request body:
```json
{ "title": "Buy milk", "description": "2% preferred", "status": "todo" }
```
`description` and `status` are optional (defaults apply).
```

to:

```markdown
Request body:
```json
{ "title": "Buy milk", "description": "2% preferred", "status": "todo", "priority": "high" }
```
`description` and `status` are optional (defaults apply). `priority` is **required** — one of `low`, `medium`, `high` — with no default.
```

And add to the `422` bullet: "or `priority` missing/not one of the allowed values."

- [ ] **Step 3: Update the `PUT /tasks/{id}` section**

Add a note: "`priority` is required on update, same as on create — there is no partial-update semantics; the full mutable field set (`title`, `description`, `status`, `priority`) must be sent."

- [ ] **Step 4: Add a backward-compatibility note**

Add a short subsection near the Data shape section:

```markdown
### Backward compatibility

`priority` was added after initial release. Existing databases are migrated
automatically on startup: a `priority` column is added with `DEFAULT 'medium'`,
so pre-existing tasks read back with `priority: "medium"`. New tasks created or
updated through the API must still supply `priority` explicitly — the database
default exists only to backfill old rows, not to make the field optional.
```

- [ ] **Step 5: Commit**

```bash
git add SPEC.md
git commit -m "docs: document required priority field and migration behavior"
```

---

## Task 6: Frontend — priority on the create form

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/app.js`

**Interfaces:**
- Produces: `PRIORITY_LABELS` (object, mirrors `STATUS_LABELS`), `priorityOptionsHtml(selected)` (mirrors `statusOptionsHtml`), the submit handler now includes `priority` in the `createTask` payload.

- [ ] **Step 1: Add the priority `<select>` to the create form**

Edit `frontend/index.html`, in the `.task-form-footer` div (currently lines 50–61), add a priority select before the status select:

```html
        <div class="task-form-footer">
          <label class="sr-only" for="task-priority">Priority</label>
          <select id="task-priority" required>
            <option value="" disabled selected>Priority</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
          <label class="sr-only" for="task-status">Status</label>
          <select id="task-status">
            <option value="todo">To do</option>
            <option value="in_progress">In progress</option>
            <option value="done">Done</option>
          </select>
          <button type="submit">
            <span class="icon" aria-hidden="true">+</span>
            Add task
          </button>
        </div>
```

The disabled placeholder `<option value="" disabled selected>` plus the select's `required` attribute enforces "no default, must pick one" at the HTML level — submitting with the placeholder still selected fails native form validation before `submit` even fires.

- [ ] **Step 2: Add `PRIORITY_LABELS` and `priorityOptionsHtml`**

Edit `frontend/app.js`, after the `STATUS_LABELS` block (currently lines 3–7):

```javascript
const STATUS_LABELS = {
  todo: "To do",
  in_progress: "In progress",
  done: "Done",
};

const PRIORITY_LABELS = {
  low: "Low",
  medium: "Medium",
  high: "High",
};
```

Add after `statusOptionsHtml` (currently lines 44–51):

```javascript
function priorityOptionsHtml(selected) {
  return Object.entries(PRIORITY_LABELS)
    .map(([value, label]) => {
      const isSelected = value === selected ? "selected" : "";
      return `<option value="${value}" ${isSelected}>${label}</option>`;
    })
    .join("");
}
```

- [ ] **Step 3: Include `priority` in the create payload**

Edit the form submit handler in `frontend/app.js` (currently lines 188–204):

```javascript
formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  formErrorEl.classList.add("hidden");

  const title = document.getElementById("task-title").value;
  const description = document.getElementById("task-description").value;
  const status = document.getElementById("task-status").value;
  const priority = document.getElementById("task-priority").value;

  try {
    await createTask({ title, description, status, priority });
    formEl.reset();
    await refresh();
  } catch (err) {
    formErrorEl.textContent = err.message;
    formErrorEl.classList.remove("hidden");
  }
});
```

Note: `formEl.reset()` restores the disabled placeholder `<option>` as selected again, so the "no default" requirement holds for the next task too.

- [ ] **Step 4: Manual verification**

Start the backend (`cd backend && uvicorn app.main:app --reload`) and open `frontend/index.html` directly in a browser (or via `python -m http.server` from `frontend/`).

1. Try submitting the form with no priority selected → the browser should block submission with a native "please select an item" validation message (no network request fires — check the Network tab).
2. Select "High", fill in a title, submit → task is created; confirm via `GET /tasks` (or the Network tab response) that `"priority": "high"` is present.
3. Repeat for "Low" and "Medium".

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html frontend/app.js
git commit -m "feat: add required priority selection to task creation form"
```

---

## Task 7: Frontend — priority badge + inline change in the task list

**Files:**
- Modify: `frontend/app.js`
- Modify: `frontend/style.css`

**Interfaces:**
- Consumes: `PRIORITY_LABELS`, `priorityOptionsHtml` (Task 6); `task.priority` (now present on every task returned by the API, per Task 1–3).
- Produces: `handlePriorityChange(task, priority)` (mirrors `handleStatusChange`); `.priority-select` element per task row, styled by `data-priority`.

- [ ] **Step 1: Add the inline priority select to `renderViewMode`**

The existing UI changes `status` via an inline `<select class="status-select">` in view mode (not through the edit-title/description form) — `priority` follows the identical pattern for consistency, rather than being added to `renderEditMode`'s title/description-only edit form.

Edit `frontend/app.js`'s `renderViewMode` (currently lines 64–97):

```javascript
function renderViewMode(li, task) {
  li.className = `task-item status-${task.status} priority-${task.priority}`;
  li.innerHTML = `
    <span
      class="task-checkbox"
      data-status="${task.status}"
      role="button"
      tabindex="0"
      aria-label="${task.status === "done" ? "Mark as not done" : "Mark as done"}"
    >${task.status === "done" ? "✓" : ""}</span>
    <div class="task-main">
      <strong>${escapeHtml(task.title)}</strong>
      ${task.description ? `<span class="description">${escapeHtml(task.description)}</span>` : ""}
    </div>
    <select class="priority-select" data-priority="${task.priority}" aria-label="Change priority">${priorityOptionsHtml(task.priority)}</select>
    <select class="status-select" data-status="${task.status}" aria-label="Change status">${statusOptionsHtml(task.status)}</select>
    <div class="task-actions">
      <button type="button" class="edit-btn" aria-label="Edit task">${EDIT_ICON}</button>
      <button type="button" class="delete-btn" aria-label="Delete task">${DELETE_ICON}</button>
    </div>
  `;
  li.querySelector(".priority-select").addEventListener("change", (e) =>
    handlePriorityChange(task, e.target.value)
  );
  li.querySelector(".status-select").addEventListener("change", (e) =>
    handleStatusChange(task, e.target.value)
  );
  const checkbox = li.querySelector(".task-checkbox");
  checkbox.addEventListener("click", () => handleToggleDone(task));
  checkbox.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleToggleDone(task);
    }
  });
  li.querySelector(".edit-btn").addEventListener("click", () => renderEditMode(li, task));
  li.querySelector(".delete-btn").addEventListener("click", () => handleDelete(task.id));
}
```

- [ ] **Step 2: Add `handlePriorityChange`**

Edit `frontend/app.js`, after `handleStatusChange`/`handleToggleDone` (currently lines 115–127):

```javascript
async function handleStatusChange(task, status) {
  try {
    await updateTask(task.id, { title: task.title, description: task.description, status, priority: task.priority });
    await refresh();
  } catch (err) {
    statusMessageEl.textContent = err.message;
  }
}

function handleToggleDone(task) {
  const nextStatus = task.status === "done" ? "todo" : "done";
  return handleStatusChange(task, nextStatus);
}

async function handlePriorityChange(task, priority) {
  try {
    await updateTask(task.id, { title: task.title, description: task.description, status: task.status, priority });
    await refresh();
  } catch (err) {
    statusMessageEl.textContent = err.message;
  }
}
```

Note: `handleStatusChange`'s `updateTask` call must now also include `priority: task.priority` — since `PUT /tasks/{id}` requires the full field set (Global Constraints), omitting it here would 422 on every status change once Task 1 lands. This is a required edit to existing code, not new code.

- [ ] **Step 3: Also fix `handleSaveEdit`'s payload**

Edit `frontend/app.js`'s `renderEditMode` (currently lines 99–113) — the save button currently sends `{ title, description, status: task.status }`, missing priority:

```javascript
  li.querySelector(".save-btn").addEventListener("click", () => {
    const title = li.querySelector(".edit-title").value;
    const description = li.querySelector(".edit-description").value;
    handleSaveEdit(li, task, { title, description, status: task.status, priority: task.priority });
  });
```

- [ ] **Step 4: Add priority badge styling**

Edit `frontend/style.css`, after the `.status-select[data-status="done"]` rule (currently lines 432–435), add:

```css
.priority-select {
  appearance: none;
  border: 1px solid var(--color-outline-variant);
  border-radius: var(--radius-pill);
  padding: 4px 26px 4px 12px;
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  cursor: pointer;
  background-color: var(--color-surface-container);
  color: var(--color-on-surface);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%236b8778' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 6px center;
  background-size: 12px;
  flex-shrink: 0;
}

.priority-select[data-priority="low"] {
  background-color: var(--color-surface-container-high);
  color: var(--color-primary-hover);
  border-color: var(--color-primary-fixed);
}

.priority-select[data-priority="medium"] {
  background-color: var(--color-tertiary-bg);
  color: var(--color-tertiary);
  border-color: var(--color-tertiary-border);
}

.priority-select[data-priority="high"] {
  background-color: #fee2e2;
  color: var(--color-error);
  border-color: #fca5a5;
}
```

Also add a left-border accent per priority, mirroring the existing `.task-item.status-*` rules (currently lines 329–340) — add after them:

```css
.task-item.priority-high {
  border-left-width: 6px;
}
```

(Only `high` gets a thicker accent border — `low`/`medium` don't need a visual border override since the badge color already communicates priority, and doubling up both a border-color AND a badge-color per priority on top of the existing status border-color would make the left border ambiguous between two competing signals.)

- [ ] **Step 5: Manual verification**

With the backend running and `frontend/index.html` open:

1. Create three tasks with Low, Medium, High priority respectively.
2. Confirm each shows a distinctly colored priority badge/select in the list, and the High one has a visibly thicker left border.
3. Change a task's priority via its inline select → confirm the badge color updates immediately and `GET /tasks/{id}` reflects the new value.
4. Edit a task's title via the pencil icon (enters edit mode), save → confirm priority is unchanged afterward (i.e., `handleSaveEdit` didn't drop it).
5. Toggle a task's status (checkbox or status select) → confirm priority is unchanged afterward (i.e., `handleStatusChange` didn't drop it).

- [ ] **Step 6: Commit**

```bash
git add frontend/app.js frontend/style.css
git commit -m "feat: show and edit task priority inline in the task list"
```

---

## Task 8: Frontend — client-side priority filtering

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/app.js`
- Modify: `frontend/style.css`

**Interfaces:**
- Consumes: `PRIORITY_LABELS` (Task 6); the full task array already held in memory after `listTasks()` in `refresh()`.
- Produces: module-level `activePriorityFilters` (Set), `applyPriorityFilter(tasks)` (pure function), filter checkbox row wired to re-render on change without re-fetching.

- [ ] **Step 1: Add the filter checkbox row to `index.html`**

Edit `frontend/index.html`, between the form and the task list (currently between line 62 `</form>` and line 64 `<p id="form-error"...`):

```html
      </form>

      <fieldset class="priority-filter">
        <legend class="sr-only">Filter by priority</legend>
        <label class="priority-filter-option">
          <input type="checkbox" class="priority-filter-checkbox" value="low" checked />
          Low
        </label>
        <label class="priority-filter-option">
          <input type="checkbox" class="priority-filter-checkbox" value="medium" checked />
          Medium
        </label>
        <label class="priority-filter-option">
          <input type="checkbox" class="priority-filter-checkbox" value="high" checked />
          High
        </label>
      </fieldset>

      <p id="form-error" class="error hidden"></p>
```

- [ ] **Step 2: Add filter state and logic to `app.js`**

Edit `frontend/app.js`: add near the top, after the `taskListEl`/`formEl`/etc. element lookups (currently lines 9–12):

```javascript
const taskListEl = document.getElementById("task-list");
const formEl = document.getElementById("task-form");
const formErrorEl = document.getElementById("form-error");
const statusMessageEl = document.getElementById("status-message");
const priorityFilterCheckboxes = document.querySelectorAll(".priority-filter-checkbox");

let allTasks = [];

function activePriorityFilters() {
  return new Set(
    Array.from(priorityFilterCheckboxes)
      .filter((checkbox) => checkbox.checked)
      .map((checkbox) => checkbox.value)
  );
}

function applyPriorityFilter(tasks, activeFilters) {
  return tasks.filter((task) => activeFilters.has(task.priority));
}
```

- [ ] **Step 3: Wire filtering into rendering without re-fetching**

Replace `renderTasks` and `refresh` (currently lines 161–186):

```javascript
function renderTasks(tasks) {
  updateProgress(tasks);
  const filtered = applyPriorityFilter(tasks, activePriorityFilters());
  taskListEl.innerHTML = "";
  if (filtered.length === 0) {
    const message =
      tasks.length === 0
        ? "🌱 No tasks yet — add one above."
        : "No tasks match the selected priority filters.";
    taskListEl.innerHTML = `<li class="empty-state">${message}</li>`;
    return;
  }
  for (const task of filtered) {
    const li = document.createElement("li");
    taskListEl.appendChild(li);
    renderViewMode(li, task);
  }
}

async function refresh() {
  statusMessageEl.textContent = "Loading…";
  try {
    allTasks = await listTasks();
    statusMessageEl.textContent = "";
    renderTasks(allTasks);
  } catch (err) {
    statusMessageEl.textContent = "";
    formErrorEl.textContent = err.message;
    formErrorEl.classList.remove("hidden");
  }
}

priorityFilterCheckboxes.forEach((checkbox) =>
  checkbox.addEventListener("change", () => renderTasks(allTasks))
);
```

Note: `updateProgress(tasks)` in `renderTasks` intentionally still receives the **unfiltered** `tasks` array (the "done today" ring should reflect all tasks, not just the currently-filtered-visible ones) — only the `<li>` rendering loop uses `filtered`.

- [ ] **Step 4: Add filter row styling**

Edit `frontend/style.css`, after `.task-form button .icon` (currently lines 294–297), add:

```css
.priority-filter {
  display: flex;
  gap: var(--space-md);
  align-items: center;
  border: none;
  padding: 0;
  margin: 0 0 var(--space-md);
}

.priority-filter-option {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.8rem;
  color: var(--color-on-surface-variant);
  cursor: pointer;
}

.priority-filter-checkbox {
  accent-color: var(--color-primary);
  cursor: pointer;
}
```

- [ ] **Step 5: Manual verification**

With the backend running and `frontend/index.html` open, and at least one task of each priority already created (from Task 6/7's verification):

1. Uncheck "Low" → confirm Low-priority tasks disappear from the list immediately, with **no network request** fired (check the Network tab — this must be a pure client-side re-render).
2. Uncheck "Medium" and "High" too (all boxes unchecked) → confirm the empty state shows "No tasks match the selected priority filters." (distinct from the "no tasks yet" message you'd see with zero tasks total).
3. Re-check all three → all tasks reappear.
4. With "High" unchecked, create a new High-priority task via the form → confirm it does *not* appear in the list until "High" is re-checked (since `refresh()` re-applies the current filter state after every mutation).
5. With "Low" unchecked, change some visible task's priority to "Low" via its inline select → confirm it disappears from the list after the update (since `handlePriorityChange` calls `refresh()`, which re-filters).
6. Reload the page (`F5`) → confirm all checkboxes reset to checked (filter state is page-only, not persisted — this is expected per the approved design).

- [ ] **Step 6: Commit**

```bash
git add frontend/index.html frontend/app.js frontend/style.css
git commit -m "feat: add client-side priority filtering to the task list"
```

---

## Task 9: Full-suite verification pass

**Files:** none (verification only)

- [ ] **Step 1: Run the full backend test suite**

Run: `cd backend && python -m pytest -v`
Expected: all tests PASS, including `test_cors.py` (untouched, confirms this feature introduced no CORS regressions).

- [ ] **Step 2: Fresh-clone smoke test of the migration path**

Simulate a real pre-feature user upgrading:

```bash
cd backend
rm -f data/tasks.db  # only if you have no real data you care about — check first!
python -c "
import sqlite3
conn = sqlite3.connect('data/tasks.db')
conn.execute('''CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'todo',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)''')
conn.execute(\"INSERT INTO tasks (title, description, status, created_at, updated_at) VALUES ('Legacy task', '', 'todo', '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00')\")
conn.commit()
conn.close()
"
uvicorn app.main:app --reload
```

In another terminal: `curl http://127.0.0.1:8000/tasks` — confirm `"Legacy task"` comes back with `"priority": "medium"`.

- [ ] **Step 3: Full manual E2E pass in the browser**

Repeat the consolidated checklist from Tasks 6–8's manual verification steps in one sitting, end-to-end, against the app freshly started from Step 2's migrated database — creating, editing, filtering, and confirming persistence across a page reload. If browser automation tooling is available, use it to drive this instead of a human doing it by hand; otherwise perform it manually and note results.

- [ ] **Step 4: Final commit (if any fixes were needed)**

If verification surfaced any fixes, commit them individually with descriptive messages following the pattern above. If verification passed clean, no commit is needed for this task.
