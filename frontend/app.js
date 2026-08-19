const API_BASE_URL = "http://127.0.0.1:8000";

const STATUS_LABELS = {
  todo: "To do",
  in_progress: "In progress",
  done: "Done",
};

const taskListEl = document.getElementById("task-list");
const formEl = document.getElementById("task-form");
const formErrorEl = document.getElementById("form-error");
const statusMessageEl = document.getElementById("status-message");

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

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function renderViewMode(li, task) {
  li.classList.remove("editing");
  li.innerHTML = `
    <div class="task-main">
      <strong>${escapeHtml(task.title)}</strong>
      ${task.description ? `<span class="description">${escapeHtml(task.description)}</span>` : ""}
    </div>
    <select class="status-select">${statusOptionsHtml(task.status)}</select>
    <button type="button" class="edit-btn">Edit</button>
    <button type="button" class="delete-btn">Delete</button>
  `;
  li.querySelector(".status-select").addEventListener("change", (e) =>
    handleStatusChange(task, e.target.value)
  );
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
    handleSaveEdit(li, task, { title, description, status: task.status });
  });
  li.querySelector(".cancel-btn").addEventListener("click", () => renderViewMode(li, task));
}

async function handleStatusChange(task, status) {
  try {
    await updateTask(task.id, { title: task.title, description: task.description, status });
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

function renderTasks(tasks) {
  taskListEl.innerHTML = "";
  if (tasks.length === 0) {
    taskListEl.innerHTML = `<li class="status">No tasks yet — add one above.</li>`;
    return;
  }
  for (const task of tasks) {
    const li = document.createElement("li");
    li.className = "task-item";
    taskListEl.appendChild(li);
    renderViewMode(li, task);
  }
}

async function refresh() {
  statusMessageEl.textContent = "Loading…";
  try {
    const tasks = await listTasks();
    statusMessageEl.textContent = "";
    renderTasks(tasks);
  } catch (err) {
    statusMessageEl.textContent = "";
    formErrorEl.textContent = err.message;
    formErrorEl.classList.remove("hidden");
  }
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  formErrorEl.classList.add("hidden");

  const title = document.getElementById("task-title").value;
  const description = document.getElementById("task-description").value;
  const status = document.getElementById("task-status").value;

  try {
    await createTask({ title, description, status });
    formEl.reset();
    await refresh();
  } catch (err) {
    formErrorEl.textContent = err.message;
    formErrorEl.classList.remove("hidden");
  }
});

refresh();
