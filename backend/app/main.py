import os
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_methods=["*"],
    allow_headers=["*"],
)
router = APIRouter(prefix="/tasks")


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


@router.post("", response_model=TaskOut, status_code=201)
def create_task_endpoint(task: TaskCreate, conn=Depends(get_db)):
    return create_task(conn, task)


@router.get("", response_model=list[TaskOut])
def list_tasks_endpoint(conn=Depends(get_db)):
    return list_tasks(conn)


@router.get("/{task_id}", response_model=TaskOut)
def get_task_endpoint(task_id: int, conn=Depends(get_db)):
    task = get_task(conn, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskOut)
def update_task_endpoint(task_id: int, task: TaskUpdate, conn=Depends(get_db)):
    updated = update_task(conn, task_id, task)
    if updated is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@router.delete("/{task_id}", status_code=204)
def delete_task_endpoint(task_id: int, conn=Depends(get_db)):
    if not delete_task(conn, task_id):
        raise HTTPException(status_code=404, detail="Task not found")


app.include_router(router)
