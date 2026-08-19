from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException

from app.crud import create_task, delete_task, get_task, list_tasks, update_task
from app.db import get_connection, init_db
from app.models import TaskCreate, TaskOut, TaskUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_connection()
    try:
        init_db(conn)
    finally:
        conn.close()
    yield


app = FastAPI(title="Task Manager API", lifespan=lifespan)


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task_endpoint(task: TaskCreate, conn=Depends(get_db)):
    return create_task(conn, task)


@app.get("/tasks", response_model=list[TaskOut])
def list_tasks_endpoint(conn=Depends(get_db)):
    return list_tasks(conn)


@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task_endpoint(task_id: int, conn=Depends(get_db)):
    task = get_task(conn, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/tasks/{task_id}", response_model=TaskOut)
def update_task_endpoint(task_id: int, task: TaskUpdate, conn=Depends(get_db)):
    updated = update_task(conn, task_id, task)
    if updated is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task_endpoint(task_id: int, conn=Depends(get_db)):
    if not delete_task(conn, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
