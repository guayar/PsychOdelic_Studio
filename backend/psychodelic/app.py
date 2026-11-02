"""FastAPI: fundament M1. Tylko funkcje, ktore faktycznie dzialaja (bez makiet).

Dostep do SQLite jest serializowany blokada (app.state.db_lock): FastAPI wykonuje synchroniczne
endpointy w roznych watkach, a jedno polaczenie SQLite nie jest bezpieczne miedzywatkowo bez blokady.
"""
import os
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import __version__
from .db import connect, migrate
from .doctor import run_doctor
from .jobs import JobStore
from .projects import DuplicateProject, create_project, get_project, list_projects

DEFAULT_DATA = Path(os.environ.get("PSYCHODELIC_DATA", Path.home() / ".local/share/psychodelic-studio"))
DEFAULT_COMFY = os.environ.get("PSYCHODELIC_COMFY_URL", "http://127.0.0.1:8188")


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class JobIn(BaseModel):
    project_id: str
    kind: str = Field(min_length=1, max_length=64)
    idempotency_key: str = Field(min_length=1, max_length=128)
    payload: dict = Field(default_factory=dict)


def create_app(data_dir=None, comfy_url=None):
    data_dir = Path(data_dir or DEFAULT_DATA)
    data_dir.mkdir(parents=True, exist_ok=True)
    conn = connect(data_dir / "studio.db")
    migrate(conn)
    comfy = comfy_url or DEFAULT_COMFY
    lock = threading.RLock()

    app = FastAPI(title="PsychOdelic Studio", version=__version__)
    app.state.conn = conn
    app.state.db_lock = lock
    app.state.data_dir = data_dir

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": __version__}

    @app.get("/api/doctor")
    def doctor():
        return run_doctor(data_dir, comfy_url=comfy)

    @app.get("/api/projects")
    def projects_list():
        with lock:
            return list_projects(conn)

    @app.post("/api/projects", status_code=201)
    def projects_create(body: ProjectIn):
        with lock:
            try:
                return create_project(conn, data_dir, body.name)
            except DuplicateProject:
                raise HTTPException(status_code=409, detail=f"projekt o nazwie „{body.name}” już istnieje")
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc))

    @app.get("/api/projects/{project_id}")
    def projects_get(project_id: str):
        with lock:
            proj = get_project(conn, project_id)
        if proj is None:
            raise HTTPException(status_code=404, detail="brak projektu")
        return proj

    @app.post("/api/jobs", status_code=201)
    def jobs_create(body: JobIn):
        with lock:
            if get_project(conn, body.project_id) is None:
                raise HTTPException(status_code=404, detail="brak projektu")
            return JobStore(conn).create(body.project_id, body.kind, body.idempotency_key, body.payload)

    @app.get("/api/jobs/{job_id}")
    def jobs_get(job_id: str):
        with lock:
            job = JobStore(conn).get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="brak zadania")
        return job

    from .api.routes import register
    register(app, conn, lock, data_dir)

    # Zbudowany frontend (frontend/dist) serwowany z tego samego originu. Trasy /api maja pierwszenstwo.
    ui_dir = Path(os.environ.get("PSYCHODELIC_UI_DIR", Path(__file__).resolve().parents[2] / "frontend" / "dist"))
    if ui_dir.is_dir() and (ui_dir / "index.html").is_file():
        from fastapi.staticfiles import StaticFiles
        app.mount("/", StaticFiles(directory=str(ui_dir), html=True), name="ui")
    return app
