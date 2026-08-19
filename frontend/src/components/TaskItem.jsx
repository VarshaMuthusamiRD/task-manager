import { useState } from 'react'
import { STATUSES, STATUS_LABELS } from '../statuses'

export default function TaskItem({ task, onUpdate, onDelete }) {
  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState(task.title)
  const [description, setDescription] = useState(task.description)
  const [error, setError] = useState(null)

  async function saveEdit() {
    setError(null)
    try {
      await onUpdate(task.id, { title, description, status: task.status })
      setEditing(false)
    } catch (err) {
      setError(err.message)
    }
  }

  async function changeStatus(event) {
    setError(null)
    try {
      await onUpdate(task.id, { title: task.title, description: task.description, status: event.target.value })
    } catch (err) {
      setError(err.message)
    }
  }

  if (editing) {
    return (
      <li className="task-item editing">
        <input value={title} onChange={(e) => setTitle(e.target.value)} />
        <input value={description} onChange={(e) => setDescription(e.target.value)} />
        <button onClick={saveEdit}>Save</button>
        <button onClick={() => setEditing(false)}>Cancel</button>
        {error && <p className="error">{error}</p>}
      </li>
    )
  }

  return (
    <li className="task-item">
      <div className="task-main">
        <strong>{task.title}</strong>
        {task.description && <span className="description">{task.description}</span>}
      </div>
      <select value={task.status} onChange={changeStatus}>
        {STATUSES.map((s) => (
          <option key={s} value={s}>
            {STATUS_LABELS[s]}
          </option>
        ))}
      </select>
      <button onClick={() => setEditing(true)}>Edit</button>
      <button onClick={() => onDelete(task.id)}>Delete</button>
      {error && <p className="error">{error}</p>}
    </li>
  )
}
