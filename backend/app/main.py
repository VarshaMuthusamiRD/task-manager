from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.crud import create_task, list_tasks
from app.db import get_connection, init_db
from app.models import TaskCreate, TaskOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_connection()
    try:
        init_db(conn)
    finally:
        conn.close()
    yield


app = FastAPI(title="Task Manager API", lifespan=lifespan)


@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task_endpoint(task: TaskCreate):
    conn = get_connection()
    try:
        return create_task(conn, task)
    finally:
        conn.close()


@app.get("/tasks", response_model=list[TaskOut])
def list_tasks_endpoint():
    conn = get_connection()
    try:
        return list_tasks(conn)
    finally:
        conn.close()
