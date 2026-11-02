"""Endpointy API. Kazde wywolanie do bazy idzie pod blokada (lock). Zadne endpointy nie uruchamiaja renderu."""
import hashlib
import json
import uuid
from pathlib import Path

from fastapi import HTTPException
from pydantic import BaseModel, Field

from ..adapters import h3 as h3a
from ..adapters import ltx as ltxa
from ..db import utc_now
from ..director.planner import plan_shots
from ..director.tools import ToolRegistry, Tool, READ
from ..jobs import JobStore
from ..media.timeline import Clip, TimelineError, export_csv, export_json, validate
from ..orchestrator.gpu import decide_render, read_vram
from ..director.llm import NullRuntime, OllamaRuntime
from ..projects import DuplicateProject, get_project, list_projects
from ..security import UnsafePath, resolve_within, safe_name
from ..fsio import atomic_write_text


class BeatIn(BaseModel):
    start_s: float = Field(ge=0)
    end_s: float = Field(gt=0)
    text: str = ""


class PlanIn(BaseModel):
    beats: list[BeatIn]


class H3In(BaseModel):
    prefix: str
    seed: int = Field(ge=0, le=2**31 - 1)
    prompt_files: list[str] = Field(min_length=1)
    refs: list[str] = Field(default_factory=list, max_length=9)
    cont: str | None = None
    fullres: bool = True
    durs: list[float] = Field(default_factory=list)
    runmode: str = "full_batch"
    validated: int = Field(default=0, ge=0)
    ctrl: str | None = None
    ctrl_frames: int | None = None
    ctrl_strength: float | None = None
    refine: bool = False
    ref_videos: list[str] = Field(default_factory=list, max_length=3)
    ref_audios: list[str] = Field(default_factory=list, max_length=3)


class LtxIn(BaseModel):
    tail: str
    tail_frames: int = 24
    audio: str
    audio_frames: int
    prompt_file: str
    seed: int = 1
    prefix: str = "shots/ltx_lip_01"
    audio_shift: int = 0


class VariantIn(BaseModel):
    job_id: str | None = None
    kind: str = Field(pattern="^(raw|cumulative|new_only|preview|audio_slice|other)$")
    rel_path: str
    frames: int | None = Field(default=None, ge=1)
    fps: float | None = Field(default=24.0, gt=0)
    label: str = ""


class ReviewIn(BaseModel):
    decision: str = Field(pattern="^(accepted|rejected)$")
    note: str = ""


class ClipIn(BaseModel):
    clip_id: str = Field(min_length=1, max_length=64)
    source_path: str
    source_in: int = Field(ge=0)
    source_out: int = Field(gt=0)
    timeline_start: int = Field(ge=0)


class PromptIn(BaseModel):
    content: str = Field(max_length=20000)


class TimelineIn(BaseModel):
    clips: list[ClipIn]


def _hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:32]


def register(app, conn, lock, data_dir, llm_url="http://127.0.0.1:11434", comfy_url="http://127.0.0.1:8188"):
    jobs = JobStore(conn)

    def _project_or_404(pid):
        p = get_project(conn, pid)
        if p is None:
            raise HTTPException(404, "brak projektu")
        return p

    def _prepared(job):
        """PLAN_READY -> PREPARED tylko raz; powtorne wywolanie z tym samym kluczem zwraca stan biezacy."""
        if job["state"] == "PLAN_READY":
            return jobs.transition(job["id"], "PREPARED")
        return job

    def _root(pid):
        return get_project(conn, pid)["root_path"]

    @app.get("/api/director/tools")
    def director_tools():
        reg = ToolRegistry()
        reg.register(Tool("plan.shots", READ, {"beats": "list"}, lambda a: plan_shots(a["beats"]),
                          "Plan ujec z beatow (regulowy)."))
        return reg.describe()

    @app.post("/api/director/plan")
    def director_plan(body: PlanIn):
        try:
            return plan_shots([b.model_dump() for b in body.beats])
        except ValueError as exc:
            raise HTTPException(422, str(exc))

    @app.post("/api/projects/{pid}/h3/prepare", status_code=201)
    def h3_prepare(pid: str, body: H3In):
        with lock:
            root = _root(pid)
            spec = h3a.ExtenderSpec(project_root=root, **body.model_dump())
            try:
                cmd = h3a.build_command(spec)
            except h3a.H3ValidationError as exc:
                raise HTTPException(422, str(exc))
            key = "h3:" + _hash({"pid": pid, **body.model_dump()})
            job = jobs.create(pid, "h3_extend", key, {"command": cmd, "input": body.model_dump()})
            job = _prepared(job)
            return {"job": job, "command": cmd}

    @app.post("/api/projects/{pid}/ltx/prepare", status_code=201)
    def ltx_prepare(pid: str, body: LtxIn):
        with lock:
            root = _root(pid)
            spec = ltxa.LtxSpec(project_root=root, **body.model_dump())
            try:
                cmd = ltxa.build_command(spec)
            except h3a.H3ValidationError as exc:
                raise HTTPException(422, str(exc))
            key = "ltx:" + _hash({"pid": pid, **body.model_dump()})
            job = jobs.create(pid, "ltx_lip", key, {"command": cmd, "input": body.model_dump()})
            job = _prepared(job)
            return {"job": job, "command": cmd}

    @app.get("/api/projects/{pid}/prompts")
    def prompts_list(pid: str):
        root = Path(_root(pid))
        d = root / "prompts"
        names = sorted(p.name for p in d.glob("*.txt")) if d.is_dir() else []
        return [{"name": n, "rel_path": f"prompts/{n}"} for n in names]

    @app.get("/api/projects/{pid}/prompts/{name}")
    def prompt_get(pid: str, name: str):
        try:
            path = resolve_within(_root(pid), f"prompts/{safe_name(name)}.txt")
        except UnsafePath as exc:
            raise HTTPException(422, str(exc))
        if not path.is_file():
            raise HTTPException(404, "brak promptu")
        return {"name": name, "rel_path": f"prompts/{name}.txt", "content": path.read_text(encoding="utf-8")}

    @app.put("/api/projects/{pid}/prompts/{name}")
    def prompt_put(pid: str, name: str, body: PromptIn):
        try:
            path = resolve_within(_root(pid), f"prompts/{safe_name(name)}.txt")
        except UnsafePath as exc:
            raise HTTPException(422, str(exc))
        atomic_write_text(path, body.content)
        return {"name": name, "rel_path": f"prompts/{name}.txt", "bytes": len(body.content.encode("utf-8"))}

    @app.get("/api/projects/{pid}/jobs")
    def project_jobs(pid: str):
        with lock:
            _project_or_404(pid)
            rows = conn.execute("SELECT id, kind, state, error, created_at, updated_at FROM jobs"
                                " WHERE project_id = ? ORDER BY created_at DESC", (pid,)).fetchall()
            return [dict(r) for r in rows]

    @app.get("/api/jobs/{job_id}/events")
    def job_events(job_id: str):
        with lock:
            rows = conn.execute("SELECT event, detail_json, created_at FROM audit_events WHERE job_id = ?"
                                " ORDER BY id", (job_id,)).fetchall()
            return [{"event": r["event"], "detail": json.loads(r["detail_json"]), "at": r["created_at"]} for r in rows]

    @app.post("/api/projects/{pid}/variants", status_code=201)
    def variant_create(pid: str, body: VariantIn):
        with lock:
            root = _root(pid)
            try:
                resolve_within(root, body.rel_path)
            except UnsafePath as exc:
                raise HTTPException(422, f"sciezka poza projektem: {exc}")
            vid = str(uuid.uuid4())
            now = utc_now()
            conn.execute("INSERT INTO render_variants (id, project_id, review_status, is_active, created_at)"
                         " VALUES (?, ?, 'pending', 0, ?)", (vid, pid, now))
            conn.execute("INSERT INTO artifacts (id, variant_id, kind, abs_path, frames, fps, created_at)"
                         " VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (str(uuid.uuid4()), vid, body.kind, body.rel_path, body.frames, body.fps, now))
            conn.execute("INSERT INTO audit_events (project_id, job_id, event, detail_json, created_at)"
                         " VALUES (?, ?, 'variant_registered', ?, ?)",
                         (pid, body.job_id, json.dumps({"variant": vid, "path": body.rel_path}), now))
            return {"id": vid, "review_status": "pending"}

    @app.get("/api/projects/{pid}/variants")
    def variants_list(pid: str):
        with lock:
            _project_or_404(pid)
            rows = conn.execute(
                "SELECT v.id, v.review_status, v.created_at, a.kind, a.abs_path, a.frames, a.fps"
                " FROM render_variants v LEFT JOIN artifacts a ON a.variant_id = v.id"
                " WHERE v.project_id = ? ORDER BY v.created_at", (pid,)).fetchall()
            return [dict(r) for r in rows]

    @app.post("/api/variants/{vid}/review")
    def variant_review(vid: str, body: ReviewIn):
        with lock:
            row = conn.execute("SELECT project_id FROM render_variants WHERE id = ?", (vid,)).fetchone()
            if row is None:
                raise HTTPException(404, "brak wariantu")
            now = utc_now()
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute("UPDATE render_variants SET review_status = ? WHERE id = ?", (body.decision, vid))
                conn.execute("INSERT INTO reviews (id, variant_id, decision, note, created_at) VALUES (?, ?, ?, ?, ?)",
                             (str(uuid.uuid4()), vid, body.decision, body.note, now))
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
            # Przeglad NIGDY nie kasuje plikow: zadna sciezka do usuwania nie istnieje w API.
            return {"id": vid, "review_status": body.decision}

    @app.get("/api/projects/{pid}/timeline")
    def timeline_get(pid: str):
        with lock:
            _project_or_404(pid)
            rows = conn.execute("SELECT clip_id, source_path, source_in_frame, source_out_frame, timeline_start_frame"
                                " FROM timeline_items WHERE project_id = ? ORDER BY timeline_start_frame", (pid,)).fetchall()
            return {"clips": [{"clip_id": r["clip_id"], "source_path": r["source_path"],
                               "source_in": r["source_in_frame"], "source_out": r["source_out_frame"],
                               "timeline_start": r["timeline_start_frame"]} for r in rows]}

    @app.put("/api/projects/{pid}/timeline")
    def timeline_put(pid: str, body: TimelineIn):
        with lock:
            _project_or_404(pid)
            clips = [Clip(c.clip_id, c.source_path, c.source_in, c.source_out, c.timeline_start) for c in body.clips]
            errs = validate(clips)
            if errs:
                raise HTTPException(422, "; ".join(errs))
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute("DELETE FROM timeline_items WHERE project_id = ?", (pid,))
                for c in body.clips:
                    conn.execute("INSERT INTO timeline_items (id, project_id, clip_id, source_path, timeline_start_frame,"
                                 " source_in_frame, source_out_frame) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                 (str(uuid.uuid4()), pid, c.clip_id, c.source_path, c.timeline_start,
                                  c.source_in, c.source_out))
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
            return {"saved": len(body.clips)}

    @app.get("/api/projects/{pid}/timeline/export")
    def timeline_export(pid: str, format: str = "json"):
        with lock:
            _project_or_404(pid)
            rows = conn.execute("SELECT clip_id, source_path, source_in_frame, source_out_frame, timeline_start_frame"
                                " FROM timeline_items WHERE project_id = ?", (pid,)).fetchall()
        clips = [Clip(r["clip_id"], r["source_path"], r["source_in_frame"], r["source_out_frame"],
                      r["timeline_start_frame"]) for r in rows]
        try:
            if format == "csv":
                return {"format": "csv", "content": export_csv(clips)}
            if format == "json":
                return {"format": "json", "content": json.loads(export_json(clips))}
        except TimelineError as exc:
            raise HTTPException(422, str(exc))
        raise HTTPException(422, "format: json | csv")

    @app.get("/api/system/status")
    def system_status():
        llm = OllamaRuntime(llm_url).status() if llm_url else NullRuntime().status()
        vram = read_vram()
        return {"llm": llm, "vram": vram, "render": decide_render(vram),
                "render_enabled": False,
                "note": "Render na GPU jest wylaczony w tej wersji (brak zgody uzytkownika)."}

    @app.get("/api/projects-summary")
    def projects_summary():
        with lock:
            out = []
            for p in list_projects(conn):
                n_jobs = conn.execute("SELECT COUNT(*) FROM jobs WHERE project_id = ?", (p["id"],)).fetchone()[0]
                n_var = conn.execute("SELECT COUNT(*) FROM render_variants WHERE project_id = ?", (p["id"],)).fetchone()[0]
                out.append(dict(p, jobs=n_jobs, variants=n_var))
            return out

    @app.get("/api/comfy/check/{profile}")
    def comfy_check(profile: str):
        """Porownuje wymagania profilu z object_info serwera ComfyUI. Tylko GET; tylko 127.0.0.1."""
        from ..workflows.profiles import PROFILES, check_profile, summary
        if profile not in PROFILES:
            raise HTTPException(404, "nieznany profil")
        if not comfy_url.startswith(("http://127.0.0.1", "http://localhost")):
            raise HTTPException(422, "ComfyUI tylko lokalnie")
        import urllib.error
        import urllib.request
        try:
            with urllib.request.urlopen(f"{comfy_url}/object_info", timeout=5) as resp:
                info = json.load(resp)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            return {"profile": profile, "title": PROFILES[profile]["title"], "reachable": False,
                    "detail": f"ComfyUI nie odpowiada ({type(exc).__name__}). To nie dowod braku modeli.",
                    "items": [], "summary": None}
        items = check_profile(profile, info)
        return {"profile": profile, "title": PROFILES[profile]["title"], "reachable": True,
                "items": items, "summary": summary(items)}

    @app.api_route("/api/{rest:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], include_in_schema=False)
    def api_not_found(rest: str):
        """Nieznana trasa API zawsze 404 (nie wpada w zamontowany UI)."""
        raise HTTPException(404, f"brak trasy API: /api/{rest}")
