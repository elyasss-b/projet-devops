from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import databases
import sqlalchemy
import os

# --- Config ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://todo_user:todo_pass@db:5432/todo_db")

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

tasks = sqlalchemy.Table(
    "tasks",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("title", sqlalchemy.String(255), nullable=False),
    sqlalchemy.Column("description", sqlalchemy.Text, default=""),
    sqlalchemy.Column("completed", sqlalchemy.Boolean, default=False),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, default=datetime.utcnow),
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)

# --- App ---
app = FastAPI(title="Todo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


# --- Events ---
@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


# --- Routes ---
@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/tasks")
async def list_tasks():
    query = tasks.select().order_by(tasks.c.created_at.desc())
    rows = await database.fetch_all(query)
    return [dict(row._mapping) for row in rows]


@app.post("/api/tasks", status_code=201)
async def create_task(task: TaskCreate):
    query = tasks.insert().values(
        title=task.title,
        description=task.description,
        completed=False,
        created_at=datetime.utcnow(),
    )
    last_id = await database.execute(query)
    return {"id": last_id, "title": task.title, "description": task.description, "completed": False}


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: int):
    query = tasks.select().where(tasks.c.id == task_id)
    row = await database.fetch_one(query)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return dict(row._mapping)


@app.put("/api/tasks/{task_id}")
async def update_task(task_id: int, task: TaskUpdate):
    values = {k: v for k, v in task.dict().items() if v is not None}
    if not values:
        raise HTTPException(status_code=400, detail="No fields to update")
    query = tasks.update().where(tasks.c.id == task_id).values(**values)
    await database.execute(query)
    return await get_task(task_id)


@app.delete("/api/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int):
    query = tasks.delete().where(tasks.c.id == task_id)
    await database.execute(query)
    return None
