from psychodelic.doctor import CONFIRMED, UNAVAILABLE, UNVERIFIED


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_project_create_list_get(client, app):
    r = client.post("/api/projects", json={"name": "Once Upon a Garden"})
    assert r.status_code == 201
    pid = r.json()["id"]
    assert [p["id"] for p in client.get("/api/projects").json()] == [pid]
    assert client.get(f"/api/projects/{pid}").json()["name"] == "Once Upon a Garden"
    assert client.get("/api/projects/nieistnieje").status_code == 404


def test_project_manifest_written(client, app):
    pid = client.post("/api/projects", json={"name": "P"}).json()["id"]
    manifest = app.state.data_dir / "projects" / pid / "manifest.json"
    assert manifest.exists()
    assert '"name": "P"' in manifest.read_text(encoding="utf-8")


def test_empty_name_rejected(client):
    assert client.post("/api/projects", json={"name": ""}).status_code == 422


def test_job_create_idempotent_and_404_for_unknown_project(client):
    pid = client.post("/api/projects", json={"name": "P"}).json()["id"]
    body = {"project_id": pid, "kind": "render", "idempotency_key": "abc", "payload": {"x": 1}}
    a = client.post("/api/jobs", json=body).json()
    b = client.post("/api/jobs", json=body).json()
    assert a["id"] == b["id"] and a["state"] == "PLAN_READY"
    assert client.get(f"/api/jobs/{a['id']}").json()["kind"] == "render"
    bad = dict(body, project_id="brak", idempotency_key="xyz")
    assert client.post("/api/jobs", json=bad).status_code == 404


def test_doctor_reports_comfy_down_honestly(client):
    report = client.get("/api/doctor").json()
    statuses = {it["name"]: it["status"] for it in report["items"]}
    assert statuses["ComfyUI"] == UNAVAILABLE
    assert "nie dowod braku modeli" in next(i for i in report["items"] if i["name"] == "ComfyUI")["detail"]
    assert statuses["data_dir zapisywalny"] == CONFIRMED
    assert set(statuses.values()) <= {CONFIRMED, UNVERIFIED, UNAVAILABLE}
