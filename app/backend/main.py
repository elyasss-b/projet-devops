from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge
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

# --- Metriques Prometheus custom (metier) ---
TASKS_CREATED = Counter("todo_tasks_created_total", "Nombre total de taches creees")
TASKS_DELETED = Counter("todo_tasks_deleted_total", "Nombre total de taches supprimees")
TASKS_COMPLETED = Counter("todo_tasks_completed_total", "Nombre total de taches completees")
TASKS_ACTIVE = Gauge("todo_tasks_active", "Nombre de taches actives")
DB_QUERY_DURATION = Histogram("todo_db_query_duration_seconds", "Duree des requetes DB", buckets=[0.01, 0.05, 0.1, 0.5, 1.0])

# --- Instrumentator Prometheus (metriques HTTP auto) ---
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"],
    inprogress_name="todo_http_requests_inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app)


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
    instrumentator.expose(app, include_in_schema=False, should_gzip=False)
    # Init gauge with current active tasks count
    query = tasks.select().where(tasks.c.completed.is_(False))
    rows = await database.fetch_all(query)
    TASKS_ACTIVE.set(len(rows))


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


# --- Routes ---
@app.get("/api/health")
async def health():
    try:
        await database.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {"status": "ok", "database": db_status, "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/tasks")
async def list_tasks():
    with DB_QUERY_DURATION.time():
        query = tasks.select().order_by(tasks.c.created_at.desc())
        rows = await database.fetch_all(query)
    return [dict(row._mapping) for row in rows]


@app.post("/api/tasks", status_code=201)
async def create_task(task: TaskCreate):
    with DB_QUERY_DURATION.time():
        query = tasks.insert().values(
            title=task.title,
            description=task.description,
            completed=False,
            created_at=datetime.utcnow(),
        )
        last_id = await database.execute(query)
    TASKS_CREATED.inc()
    TASKS_ACTIVE.inc()
    return {"id": last_id, "title": task.title, "description": task.description, "completed": False}


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: int):
    with DB_QUERY_DURATION.time():
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
    with DB_QUERY_DURATION.time():
        query = tasks.update().where(tasks.c.id == task_id).values(**values)
        await database.execute(query)
    if task.completed is True:
        TASKS_COMPLETED.inc()
        TASKS_ACTIVE.dec()
    elif task.completed is False:
        TASKS_ACTIVE.inc()
    return await get_task(task_id)


@app.delete("/api/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int):
    # Check if task was active before deleting
    existing = await get_task(task_id)
    with DB_QUERY_DURATION.time():
        query = tasks.delete().where(tasks.c.id == task_id)
        await database.execute(query)
    TASKS_DELETED.inc()
    if not existing.get("completed", False):
        TASKS_ACTIVE.dec()
    return None
