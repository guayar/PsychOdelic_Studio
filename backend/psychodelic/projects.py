"""Projekty: wpis w SQLite + katalog z manifestem JSON (manifest jest zapisywany atomowo)."""
import json
import uuid
from pathlib import Path

from .db import transaction, utc_now
from .fsio import atomic_write_json

MAX_NAME = 120


class DuplicateProject(ValueError):
    pass


def create_project(conn, data_dir, name):
    name = (name or "").strip()
    if not name or len(name) > MAX_NAME or "\x00" in name:
        raise ValueError("nazwa projektu: 1-120 znakow, bez znakow sterujacych")
    dup = conn.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()
    if dup is not None:
        raise DuplicateProject(name)
    project_id = str(uuid.uuid4())
    root = Path(data_dir) / "projects" / project_id
    root.mkdir(parents=True, exist_ok=False)
    created = utc_now()
    manifest = {"schema": 1, "id": project_id, "name": name, "created_at": created,
                "note": "manifest nie zastepuje bazy; zawiera tylko metadane projektu"}
    atomic_write_json(root / "manifest.json", manifest, overwrite=False)
    with transaction(conn):
        conn.execute("INSERT INTO projects (id, name, root_path, created_at) VALUES (?, ?, ?, ?)",
                     (project_id, name, str(root), created))
        conn.execute("INSERT INTO audit_events (project_id, job_id, event, detail_json, created_at)"
                     " VALUES (?, NULL, 'project_created', ?, ?)",
                     (project_id, json.dumps({"name": name}, ensure_ascii=False), created))
    return get_project(conn, project_id)


def get_project(conn, project_id):
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return dict(row) if row else None


def list_projects(conn):
    return [dict(r) for r in conn.execute("SELECT * FROM projects ORDER BY created_at, id")]

