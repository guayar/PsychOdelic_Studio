from pathlib import Path


def make_project(client, name="Mój projekt"):
    return client.post("/api/projects", json={"name": name}).json()["id"]


def make_prompt(client, pid, app, rel="ext_test/s1.txt"):
    root = Path(client.get(f"/api/projects/{pid}").json()["root_path"])
    (root / "ext_test").mkdir(exist_ok=True)
    (root / rel).write_text("Gardener stands still; camera locked off.", encoding="utf-8")
    return rel


def test_h3_prepare_returns_command_and_state(client, app):
    pid = make_project(client)
    rel = make_prompt(client, pid, app)
    r = client.post(f"/api/projects/{pid}/h3/prepare", json={
        "prefix": "shots/v3b_1", "seed": 1234, "prompt_files": [rel], "refs": ["ref_gsheet2.png"],
        "durs": [7.5], "cont": "ref_v3a_2.mp4"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["job"]["state"] == "PREPARED"
    assert body["command"]["argv"][2] == "_docs/gen_extender_refine.py"
    assert body["command"]["env"]["CONT"] == "ref_v3a_2.mp4"


def test_h3_prepare_idempotent_no_double_transition(client, app):
    pid = make_project(client)
    rel = make_prompt(client, pid, app)
    body = {"prefix": "shots/x1", "seed": 1, "prompt_files": [rel]}
    a = client.post(f"/api/projects/{pid}/h3/prepare", json=body).json()["job"]
    b = client.post(f"/api/projects/{pid}/h3/prepare", json=body).json()["job"]
    assert a["id"] == b["id"] and b["state"] == "PREPARED"


def test_h3_prepare_rejects_prompt_outside_project(client, app):
    pid = make_project(client)
    r = client.post(f"/api/projects/{pid}/h3/prepare", json={
        "prefix": "shots/x", "seed": 1, "prompt_files": ["../../etc/passwd"]})
    assert r.status_code == 422


def test_h3_prepare_rejects_ten_refs(client, app):
    pid = make_project(client)
    rel = make_prompt(client, pid, app)
    r = client.post(f"/api/projects/{pid}/h3/prepare", json={
        "prefix": "shots/x", "seed": 1, "prompt_files": [rel], "refs": [f"r{i}.png" for i in range(10)]})
    assert r.status_code == 422


def test_no_render_endpoint_exists(client):
    spec = client.get("/openapi.json").json()["paths"]
    assert not any("render" in p or "execute" in p or "submit" in p for p in spec), list(spec)


def test_review_never_deletes_files(client, app):
    pid = make_project(client)
    root = Path(client.get(f"/api/projects/{pid}").json()["root_path"])
    (root / "ext_test").mkdir(exist_ok=True)
    f = root / "ext_test" / "v.mp4"
    f.write_bytes(b"fake")
    vid = client.post(f"/api/projects/{pid}/variants", json={"kind": "new_only", "rel_path": "ext_test/v.mp4",
                                                              "frames": 119}).json()["id"]
    assert client.post(f"/api/variants/{vid}/review", json={"decision": "rejected", "note": "za miekko"}).json()[
        "review_status"] == "rejected"
    assert f.exists(), "odrzucenie nie moze kasowac pliku"
    assert client.post(f"/api/variants/{vid}/review", json={"decision": "accepted"}).json()["review_status"] == "accepted"
    assert f.exists()


def test_variant_path_must_stay_inside_project(client):
    pid = make_project(client)
    r = client.post(f"/api/projects/{pid}/variants", json={"kind": "raw", "rel_path": "../../x.mp4"})
    assert r.status_code == 422


def test_timeline_roundtrip_and_overlap_rejected(client):
    pid = make_project(client)
    ok = {"clips": [{"clip_id": "a", "source_path": "x.mp4", "source_in": 0, "source_out": 124, "timeline_start": 0},
                    {"clip_id": "b", "source_path": "y.mp4", "source_in": 0, "source_out": 243, "timeline_start": 124}]}
    assert client.put(f"/api/projects/{pid}/timeline", json=ok).status_code == 200
    got = client.get(f"/api/projects/{pid}/timeline").json()["clips"]
    assert [c["clip_id"] for c in got] == ["a", "b"]
    csv = client.get(f"/api/projects/{pid}/timeline/export?format=csv").json()["content"]
    assert "00:00:05:04" in csv
    bad = {"clips": [{"clip_id": "a", "source_path": "x", "source_in": 0, "source_out": 124, "timeline_start": 0},
                     {"clip_id": "b", "source_path": "y", "source_in": 0, "source_out": 50, "timeline_start": 50}]}
    assert client.put(f"/api/projects/{pid}/timeline", json=bad).status_code == 422


def test_director_plan_endpoint(client):
    r = client.post("/api/director/plan", json={"beats": [{"start_s": 0, "end_s": 5.17, "text": "Walks in."}]})
    assert r.status_code == 200 and r.json()["shots"][0]["frames"] == 124


def test_system_status_render_disabled(client):
    st = client.get("/api/system/status").json()
    assert st["render_enabled"] is False
    assert st["llm"]["runtime"] in ("ollama", "manual")
    assert "vram" in st and "render" in st


def test_projects_summary_counts(client):
    pid = make_project(client, "Liczniki")
    s = [p for p in client.get("/api/projects-summary").json() if p["id"] == pid][0]
    assert s["jobs"] == 0 and s["variants"] == 0


def test_h3_media_refs_api_limit(client, app):
    pid = make_project(client)
    rel = make_prompt(client, pid, app)
    r = client.post(f"/api/projects/{pid}/h3/prepare", json={
        "prefix": "shots/x1", "seed": 1, "prompt_files": [rel], "ref_videos": ["a.mp4"] * 4})
    assert r.status_code == 422
    ok = client.post(f"/api/projects/{pid}/h3/prepare", json={
        "prefix": "shots/x1", "seed": 1, "prompt_files": [rel], "refs": ["r.png"],
        "ref_videos": ["a.mp4"], "ref_audios": ["a.wav"]})
    assert ok.status_code == 201
    assert ok.json()["command"]["media_refs"] == {"videos": ["a.mp4"], "audios": ["a.wav"]}


def test_project_delete_removes_rows_keeps_files(client, app):
    pid = make_project(client)
    rel = make_prompt(client, pid, app)
    root = Path(client.get(f"/api/projects/{pid}").json()["root_path"])
    assert client.post(f"/api/projects/{pid}/h3/prepare", json={
        "prefix": "shots/d1", "seed": 1, "prompt_files": [rel]}).status_code == 201
    r = client.delete(f"/api/projects/{pid}")
    assert r.status_code == 200 and r.json()["files_kept"] == str(root)
    assert client.get(f"/api/projects/{pid}").status_code == 404
    assert all(p["id"] != pid for p in client.get("/api/projects").json())
    assert root.exists(), "pliki projektu nie moga byc kasowane"
    assert client.delete(f"/api/projects/{pid}").status_code == 404


def test_project_delete_allows_same_name_again(client):
    pid = make_project(client)
    client.delete(f"/api/projects/{pid}")
    assert make_project(client) != pid


def test_project_media_serves_inside_project_only(client, app):
    pid = make_project(client)
    root = Path(client.get(f"/api/projects/{pid}").json()["root_path"])
    (root / "renders").mkdir(exist_ok=True)
    (root / "renders" / "a.mp4").write_bytes(b"0123456789")
    (root / "renders" / "note.txt").write_text("x", encoding="utf-8")
    ok = client.get(f"/api/projects/{pid}/media", params={"path": "renders/a.mp4"})
    assert ok.status_code == 200 and ok.content == b"0123456789"
    assert client.get(f"/api/projects/{pid}/media", params={"path": "../x.mp4"}).status_code == 422
    assert client.get(f"/api/projects/{pid}/media", params={"path": "renders/none.mp4"}).status_code == 404
    assert client.get(f"/api/projects/{pid}/media", params={"path": "renders/note.txt"}).status_code == 404
    assert client.get("/api/projects/nope/media", params={"path": "renders/a.mp4"}).status_code == 404


def test_project_media_check_reports_existence(client, app):
    pid = make_project(client)
    root = Path(client.get(f"/api/projects/{pid}").json()["root_path"])
    (root / "renders").mkdir(exist_ok=True)
    (root / "renders" / "a.mp4").write_bytes(b"x")
    assert client.get(f"/api/projects/{pid}/media/check", params={"path": "renders/a.mp4"}).json() == {"exists": True}
    assert client.get(f"/api/projects/{pid}/media/check", params={"path": "renders/b.mp4"}).json() == {"exists": False}
    assert client.get(f"/api/projects/{pid}/media/check", params={"path": "../x.mp4"}).json() == {"exists": False}
