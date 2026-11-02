import pytest

from psychodelic.db import connect, migrate
from psychodelic.jobs import IllegalTransition, JobStore
from psychodelic.projects import create_project


@pytest.fixture()
def store(tmp_path):
    conn = connect(tmp_path / "s.db")
    migrate(conn)
    proj = create_project(conn, tmp_path / "data", "Test")
    return JobStore(conn), proj["id"]


def test_create_is_idempotent(store):
    js, pid = store
    a = js.create(pid, "h3_extend", "key-1", {"shot": 1})
    b = js.create(pid, "h3_extend", "key-1", {"shot": 1})
    assert a["id"] == b["id"]
    assert a["state"] == "PLAN_READY"


def test_full_legal_path_to_director_ready(store):
    js, pid = store
    job = js.create(pid, "render", "key-2")
    path = ["PREPARED", "DIRECTOR_UNLOADING", "GPU_FREE_VERIFIED", "RENDER_QUEUED", "RENDERING",
            "OUTPUT_VALIDATING", "POSTPROCESSING", "AWAITING_USER_REVIEW", "ACCEPTED", "DIRECTOR_RELOAD_PENDING",
            "DIRECTOR_READY"]
    for st in path:
        job = js.transition(job["id"], st)
    assert job["state"] == "DIRECTOR_READY"


def test_illegal_transition_rejected_and_state_unchanged(store):
    js, pid = store
    job = js.create(pid, "render", "key-3")
    with pytest.raises(IllegalTransition):
        js.transition(job["id"], "RENDERING")  # z PLAN_READY nie wolno od razu renderowac
    assert js.get(job["id"])["state"] == "PLAN_READY"


def test_terminal_states_do_not_move(store):
    js, pid = store
    job = js.create(pid, "render", "key-4")
    js.transition(job["id"], "CAPABILITY_UNAVAILABLE", error="brak modelu")
    with pytest.raises(IllegalTransition):
        js.transition(job["id"], "PREPARED")
    assert js.get(job["id"])["error"] == "brak modelu"


def test_every_transition_is_audited(store):
    js, pid = store
    job = js.create(pid, "render", "key-5")
    js.transition(job["id"], "PREPARED")
    events = js.conn.execute("SELECT event FROM audit_events WHERE job_id = ? ORDER BY id", (job["id"],)).fetchall()
    assert [e[0] for e in events] == ["job_created", "state_changed"]


def test_review_rejection_path_is_allowed(store):
    js, pid = store
    job = js.create(pid, "render", "key-6")
    for st in ["PREPARED", "GPU_FREE_VERIFIED", "RENDER_QUEUED", "RENDERING", "OUTPUT_VALIDATING",
               "POSTPROCESSING", "AWAITING_USER_REVIEW", "REJECTED", "DIRECTOR_READY"]:
        job = js.transition(job["id"], st)
    assert job["state"] == "DIRECTOR_READY"  # odrzucenie nie kasuje zadania ani plikow
