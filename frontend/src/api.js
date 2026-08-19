const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed with ${response.status}`)
  }

  return response.status === 204 ? null : response.json()
}

export function listTasks() {
  return request('/tasks')
}

export function createTask(task) {
  return request('/tasks', { method: 'POST', body: JSON.stringify(task) })
}

export function updateTask(id, task) {
  return request(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(task) })
}

export function deleteTask(id) {
  return request(`/tasks/${id}`, { method: 'DELETE' })
}
