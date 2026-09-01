const API_BASE_URL = "http://127.0.0.1:8000";

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

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with ${response.status}`);
  }

  return response.status === 204 ? null : response.json();
}

function listTasks() {
  return apiRequest("/tasks");
}

function createTask(task) {
  return apiRequest("/tasks", { method: "POST", body: JSON.stringify(task) });
}

function updateTask(id, task) {
  return apiRequest(`/tasks/${id}`, { method: "PUT", body: JSON.stringify(task) });
}

function deleteTask(id) {
  return apiRequest(`/tasks/${id}`, { method: "DELETE" });
}

function statusOptionsHtml(selected) {
  return Object.entries(STATUS_LABELS)
    .map(([value, label]) => {
      const isSelected = value === selected ? "selected" : "";
      return `<option value="${value}" ${isSelected}>${label}</option>`;
    })
    .join("");
}

function priorityOptionsHtml(selected) {
  return Object.entries(PRIORITY_LABELS)
    .map(([value, label]) => {
      const isSelected = value === selected ? "selected" : "";
      return `<option value="${value}" ${isSelected}>${label}</option>`;
    })
    .join("");
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

const EDIT_ICON =
  '<svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 16.5l1-4L13 4.5l3 3-8 8-4 1z"/></svg>';
const DELETE_ICON =
  '<svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M5 6h10M8 6V4.5A1.5 1.5 0 019.5 3h1A1.5 1.5 0 0112 4.5V6m-6 0v9a1 1 0 001 1h6a1 1 0 001-1V6"/></svg>';

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

function renderEditMode(li, task) {
  li.classList.add("editing");
  li.innerHTML = `
    <input class="edit-title" type="text" value="${escapeHtml(task.title)}" />
    <input class="edit-description" type="text" value="${escapeHtml(task.description)}" />
    <button type="button" class="save-btn">Save</button>
    <button type="button" class="cancel-btn">Cancel</button>
  `;
  li.querySelector(".save-btn").addEventListener("click", () => {
    const title = li.querySelector(".edit-title").value;
    const description = li.querySelector(".edit-description").value;
    handleSaveEdit(li, task, { title, description, status: task.status, priority: task.priority });
  });
  li.querySelector(".cancel-btn").addEventListener("click", () => renderViewMode(li, task));
}

async function handleStatusChange(task, status) {
  try {
    await updateTask(task.id, {
      title: task.title,
      description: task.description,
      status,
      priority: task.priority,
    });
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
    await updateTask(task.id, {
      title: task.title,
      description: task.description,
      status: task.status,
      priority,
    });
    await refresh();
  } catch (err) {
    statusMessageEl.textContent = err.message;
  }
}

async function handleSaveEdit(li, task, updatedFields) {
  try {
    await updateTask(task.id, updatedFields);
    await refresh();
  } catch (err) {
    statusMessageEl.textContent = err.message;
  }
}

async function handleDelete(id) {
  try {
    await deleteTask(id);
    await refresh();
  } catch (err) {
    statusMessageEl.textContent = err.message;
  }
}

function updateProgress(tasks) {
  const total = tasks.length;
  const done = tasks.filter((t) => t.status === "done").length;
  const countEl = document.getElementById("progress-count");
  const ringEl = document.getElementById("progress-ring-fill");
  if (countEl) countEl.textContent = `${done}/${total}`;
  if (ringEl) {
    const circumference = 2 * Math.PI * 15;
    const fraction = total === 0 ? 0 : done / total;
    ringEl.style.strokeDasharray = `${circumference}`;
    ringEl.style.strokeDashoffset = `${circumference * (1 - fraction)}`;
  }
}

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

refresh();
