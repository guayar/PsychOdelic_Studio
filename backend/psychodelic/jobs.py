"""Maszyna stanow zadan (sekcja 9 promptu). Jedyne miejsce, w ktorym wolno zmieniac stan zadania.

Przejscia sa jawnie zdefiniowane. Nielegalne przejscie rzuca IllegalTransition.
Kazda zmiana stanu zapisuje wpis w audit_events (w tej samej transakcji).
"""
import json
import uuid

from .db import transaction, utc_now

STATES = {
    "PLAN_READY", "PREPARED", "DIRECTOR_UNLOADING", "GPU_FREE_VERIFIED", "RENDER_QUEUED", "RENDERING",
    "OUTPUT_VALIDATING", "POSTPROCESSING", "AWAITING_USER_REVIEW", "ACCEPTED", "REJECTED",
    "DIRECTOR_RELOAD_PENDING", "DIRECTOR_READY", "FAILED", "CANCELLED", "RECOVERING", "GPU_BUSY",
    "CAPABILITY_UNAVAILABLE",
}
TERMINAL = {"FAILED", "CANCELLED", "CAPABILITY_UNAVAILABLE"}
TRANSITIONS = {
    "PLAN_READY": {"PREPARED", "CAPABILITY_UNAVAILABLE", "CANCELLED"},
    # PREPARED -> GPU_FREE_VERIFIED: gdy Director nie jest zaladowany (nic do wyladowania)
    "PREPARED": {"DIRECTOR_UNLOADING", "GPU_FREE_VERIFIED", "CAPABILITY_UNAVAILABLE", "CANCELLED"},
    "DIRECTOR_UNLOADING": {"GPU_FREE_VERIFIED", "GPU_BUSY", "FAILED", "CANCELLED"},
    "GPU_FREE_VERIFIED": {"RENDER_QUEUED", "GPU_BUSY", "CANCELLED"},
    "GPU_BUSY": {"RENDER_QUEUED", "FAILED", "CANCELLED"},
    "RENDER_QUEUED": {"RENDERING", "CANCELLED", "FAILED"},
    "RENDERING": {"OUTPUT_VALIDATING", "FAILED", "CANCELLED", "RECOVERING"},
    "RECOVERING": {"RENDERING", "OUTPUT_VALIDATING", "FAILED"},
    "OUTPUT_VALIDATING": {"POSTPROCESSING", "FAILED"},
    "POSTPROCESSING": {"AWAITING_USER_REVIEW", "FAILED"},
    "AWAITING_USER_REVIEW": {"ACCEPTED", "REJECTED"},
    "ACCEPTED": {"DIRECTOR_RELOAD_PENDING", "DIRECTOR_READY"},
    "REJECTED": {"DIRECTOR_RELOAD_PENDING", "DIRECTOR_READY"},
    "DIRECTOR_RELOAD_PENDING": {"DIRECTOR_READY", "FAILED"},
    "DIRECTOR_READY": set(),
    "FAILED": set(),
    "CANCELLED": set(),
    "CAPABILITY_UNAVAILABLE": set(),
}


class IllegalTransition(RuntimeError):
    pass


def check_transition(src, dst):
    if src not in STATES or dst not in STATES:
        raise IllegalTransition(f"nieznany stan: {src} -> {dst}")
    if dst not in TRANSITIONS.get(src, set()):
        raise IllegalTransition(f"niedozwolone przejscie {src} -> {dst}")


class JobStore:
    def __init__(self, conn):
        self.conn = conn

    def create(self, project_id, kind, idempotency_key, payload=None):
        """Idempotentne: ten sam idempotency_key zwraca istniejace zadanie."""
        existing = self.conn.execute("SELECT * FROM jobs WHERE idempotency_key = ?", (idempotency_key,)).fetchone()
        if existing:
            return dict(existing)
        job_id = str(uuid.uuid4())
        now = utc_now()
        with transaction(self.conn):
            self.conn.execute(
                "INSERT INTO jobs (id, project_id, kind, state, idempotency_key, payload_json, created_at, updated_at)"
                " VALUES (?, ?, ?, 'PLAN_READY', ?, ?, ?, ?)",
                (job_id, project_id, kind, idempotency_key, json.dumps(payload or {}, ensure_ascii=False), now, now),
            )
            self._audit(job_id, project_id, "job_created", {"kind": kind})
        return self.get(job_id)

    def get(self, job_id):
        row = self.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return dict(row) if row else None

    def transition(self, job_id, dst, error=None):
        with transaction(self.conn):
            row = self.conn.execute("SELECT state, project_id FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if row is None:
                raise KeyError(job_id)
            check_transition(row["state"], dst)
            self.conn.execute(
                "UPDATE jobs SET state = ?, error = COALESCE(?, error), updated_at = ? WHERE id = ?",
                (dst, error, utc_now(), job_id),
            )
            self._audit(job_id, row["project_id"], "state_changed", {"from": row["state"], "to": dst, "error": error})
        return self.get(job_id)

    def _audit(self, job_id, project_id, event, detail):
        self.conn.execute(
            "INSERT INTO audit_events (project_id, job_id, event, detail_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (project_id, job_id, event, json.dumps(detail, ensure_ascii=False), utc_now()),
        )
