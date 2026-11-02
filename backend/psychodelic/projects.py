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



def delete_project(conn, project_id):
    """Usuwa projekt z bazy studia (wraz z powiazanymi wierszami). Pliki na dysku NIE sa kasowane.

    Zwraca None, gdy projektu nie ma; w przeciwnym razie slownik z katalogiem, ktory zostal na dysku.
    Kolejnosc kasowania respektuje klucze obce (od lisci do korzenia).
    """
    proj = get_project(conn, project_id)
    if proj is None:
        return None
    pid = project_id
    variants = "SELECT id FROM render_variants WHERE project_id = ?"
    jobs = "SELECT id FROM jobs WHERE project_id = ?"
    with transaction(conn):
        conn.execute(f"DELETE FROM artifacts WHERE variant_id IN ({variants})", (pid,))
        conn.execute(f"DELETE FROM reviews WHERE variant_id IN ({variants})", (pid,))
        conn.execute("DELETE FROM timeline_items WHERE project_id = ?", (pid,))
        conn.execute("DELETE FROM render_variants WHERE project_id = ?", (pid,))
        conn.execute(f"DELETE FROM resource_leases WHERE job_id IN ({jobs})", (pid,))
        conn.execute("DELETE FROM jobs WHERE project_id = ?", (pid,))
        conn.execute("UPDATE generation_nodes SET parent_id = NULL WHERE project_id = ?", (pid,))
        conn.execute("DELETE FROM generation_nodes WHERE project_id = ?", (pid,))
        conn.execute("DELETE FROM reference_assignments WHERE project_id = ?", (pid,))
        conn.execute("DELETE FROM assets WHERE project_id = ?", (pid,))
        conn.execute("DELETE FROM scene_plans WHERE project_id = ?", (pid,))
        conn.execute("DELETE FROM director_sessions WHERE project_id = ?", (pid,))
        conn.execute("DELETE FROM cues WHERE project_id = ?", (pid,))
        conn.execute("DELETE FROM projects WHERE id = ?", (pid,))
        conn.execute("INSERT INTO audit_events (project_id, job_id, event, detail_json, created_at)"
                     " VALUES (?, NULL, 'project_deleted', ?, ?)",
                     (pid, json.dumps({"name": proj["name"], "files_kept": proj["root_path"]}, ensure_ascii=False),
                      utc_now()))
    return {"deleted": pid, "name": proj["name"], "files_kept": proj["root_path"]}
