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
