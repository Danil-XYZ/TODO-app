from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TODO API",
    description="Простое TODO-приложение с Users, Projects и Tasks",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === MODELS ===
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False
    project_id: UUID

class Task(TaskCreate):
    id: UUID = Field(default_factory=uuid4)

class ProjectCreate(BaseModel):
    name: str
    user_id: UUID

class Project(ProjectCreate):
    id: UUID = Field(default_factory=uuid4)

class UserCreate(BaseModel):
    name: str

class User(UserCreate):
    id: UUID = Field(default_factory=uuid4)

# === IN-MEMORY REPOSITORIES ===
class TaskRepository:
    def __init__(self):
        self.tasks: List[Task] = []

    def list(self): return self.tasks

    def get(self, task_id: UUID):
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def create(self, task_data: TaskCreate):
        task = Task(**task_data.dict())
        self.tasks.append(task)
        return task

    def update(self, task_id: UUID, new_task: Task):
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                self.tasks[i] = new_task
                return new_task
        return None

    def delete(self, task_id: UUID):
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                del self.tasks[i]
                return True
        return False

class ProjectRepository:
    def __init__(self): self.projects: List[Project] = []
    def list(self): return self.projects
    def create(self, project_data: ProjectCreate):
        project = Project(**project_data.dict())
        self.projects.append(project)
        return project

class UserRepository:
    def __init__(self): self.users: List[User] = []
    def list(self): return self.users
    def create(self, user_data: UserCreate):
        user = User(**user_data.dict())
        self.users.append(user)
        return user

# === REPOSITORY INSTANCES ===
task_repo = TaskRepository()
project_repo = ProjectRepository()
user_repo = UserRepository()

# === TASK ENDPOINTS ===
@app.get("/tasks", response_model=List[Task], tags=["Tasks"])
def get_tasks(project_id: Optional[UUID] = Query(default=None)):
    tasks = task_repo.list()
    if project_id:
        tasks = [t for t in tasks if t.project_id == project_id]
    return tasks

@app.post("/tasks", response_model=Task, tags=["Tasks"])
def create_task(task: TaskCreate):
    if not any(p.id == task.project_id for p in project_repo.projects):
        raise HTTPException(status_code=400, detail="Project does not exist")
    return task_repo.create(task)

@app.get("/tasks/{task_id}", response_model=Task, tags=["Tasks"])
def get_task(task_id: UUID):
    task = task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=Task, tags=["Tasks"])
def update_task(task_id: UUID, task: Task):
    if not any(p.id == task.project_id for p in project_repo.projects):
        raise HTTPException(status_code=400, detail="Project does not exist")
    updated = task_repo.update(task_id, task)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated

@app.delete("/tasks/{task_id}", tags=["Tasks"])
def delete_task(task_id: UUID):
    if not task_repo.delete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}

# === PROJECT ENDPOINTS ===
@app.get("/projects", response_model=List[Project], tags=["Projects"])
def get_projects(user_id: Optional[UUID] = Query(default=None)):
    projects = project_repo.list()
    if user_id:
        projects = [p for p in projects if p.user_id == user_id]
    return projects

@app.post("/projects", response_model=Project, tags=["Projects"])
def create_project(project: ProjectCreate):
    if not any(u.id == project.user_id for u in user_repo.users):
        raise HTTPException(status_code=400, detail="User does not exist")
    return project_repo.create(project)

# === USER ENDPOINTS ===
@app.get("/users", response_model=List[User], tags=["Users"])
def get_users():
    return user_repo.list()

@app.post("/users", response_model=User, tags=["Users"])
def create_user(user: UserCreate):
    return user_repo.create(user)
