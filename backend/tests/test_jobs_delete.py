import pytest

from psychodelic.db import connect, migrate
from psychodelic.jobs import ACTIVE, JobActive, JobStore
from psychodelic.projects import create_project


@pytest.fixture()
def store(tmp_path):
    conn = connect(tmp_path / "s.db")
    migrate(conn)
    proj = create_project(conn, tmp_path / "data", "Test")
    return JobStore(conn), proj["id"], conn


def test_delete_idle_job_and_its_leases(store):
    js, pid, conn = store
    j = js.create(pid, "h3_scene", "k1", {})
    assert js.delete(j["id"]) == pid
    assert js.get(j["id"]) is None
    assert conn.execute("SELECT COUNT(*) FROM audit_events WHERE event='job_deleted'").fetchone()[0] == 1


def test_active_job_is_protected(store):
    js, pid, conn = store
    j = js.create(pid, "h3_scene", "k2", {})
    js.transition(j["id"], "PREPARED")
    js.transition(j["id"], "GPU_FREE_VERIFIED")
    js.transition(j["id"], "RENDER_QUEUED")
    assert "RENDER_QUEUED" in ACTIVE
    with pytest.raises(JobActive):
        js.delete(j["id"])
    assert js.get(j["id"]) is not None


def test_clear_keeps_active_and_removes_rest(store):
    js, pid, conn = store
    idle = js.create(pid, "h3_scene", "k3", {})
    busy = js.create(pid, "h3_scene", "k4", {})
    js.transition(busy["id"], "PREPARED")
    js.transition(busy["id"], "GPU_FREE_VERIFIED")
    js.transition(busy["id"], "RENDER_QUEUED")
    assert js.clear(pid) == {"deleted": 1, "kept_active": 1}
    assert js.get(idle["id"]) is None and js.get(busy["id"]) is not None
