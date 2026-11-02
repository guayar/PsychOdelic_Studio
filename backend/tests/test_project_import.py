from pathlib import Path

from fastapi.testclient import TestClient

from psychodelic.app import create_app


def test_import_copies_into_project_renders(tmp_path):
    c = TestClient(create_app(data_dir=tmp_path / "d", comfy_url="http://127.0.0.1:9"))
    pid = c.post("/api/projects", json={"name": "Imp"}).json()["id"]
    root = Path(c.get(f"/api/projects/{pid}").json()["root_path"])
    src = tmp_path / "elsewhere"
    src.mkdir()
    (src / "take 1.mp4").write_bytes(b"VID")
    r = c.post(f"/api/projects/{pid}/import", json={"path": str(src / "take 1.mp4")})
    assert r.status_code == 201 and r.json()["name"] == "renders/take_1.mp4"
    assert (root / "renders" / "take_1.mp4").read_bytes() == b"VID"
    again = c.post(f"/api/projects/{pid}/import", json={"path": str(src / "take 1.mp4")}).json()["name"]
    assert again == "renders/take_1.mp4"
    (src / "take 1.mp4").write_bytes(b"NEW")
    other = c.post(f"/api/projects/{pid}/import", json={"path": str(src / "take 1.mp4")}).json()["name"]
    assert other == "renders/take_1_2.mp4" and (root / "renders" / "take_1.mp4").read_bytes() == b"VID"
    assert c.post(f"/api/projects/{pid}/import", json={"path": str(src / "missing.mp4")}).status_code == 422


def test_review_refuses_missing_file(tmp_path):
    c = TestClient(create_app(data_dir=tmp_path / "d", comfy_url="http://127.0.0.1:9"))
    pid = c.post("/api/projects", json={"name": "Rev"}).json()["id"]
    r = c.post(f"/api/projects/{pid}/variants", json={"rel_path": "renders/nope.mp4.", "kind": "other", "frames": 10, "fps": 24})
    assert r.status_code == 422 and "nie ma takiego pliku" in r.json()["detail"]


def test_only_rejected_entries_can_be_removed_and_file_stays(tmp_path):
    c = TestClient(create_app(data_dir=tmp_path / "d", comfy_url="http://127.0.0.1:9"))
    pid = c.post("/api/projects", json={"name": "Del"}).json()["id"]
    root = Path(c.get(f"/api/projects/{pid}").json()["root_path"])
    (root / "renders").mkdir(exist_ok=True)
    (root / "renders" / "a.mp4").write_bytes(b"V")
    (root / "renders" / "b.mp4").write_bytes(b"W")
    v1 = c.post(f"/api/projects/{pid}/variants", json={"rel_path": "renders/a.mp4", "kind": "other", "frames": 10, "fps": 24}).json()
    v2 = c.post(f"/api/projects/{pid}/variants", json={"rel_path": "renders/b.mp4", "kind": "other", "frames": 10, "fps": 24}).json()
    vid1 = v1.get("id") or v1.get("variant_id")
    vid2 = v2.get("id") or v2.get("variant_id")
    assert c.delete(f"/api/variants/{vid1}").status_code == 409  # jeszcze nieodrzucony
    c.post(f"/api/variants/{vid1}/review", json={"decision": "rejected", "note": "x"})
    assert c.delete(f"/api/variants/{vid1}").status_code == 200
    assert (root / "renders" / "a.mp4").read_bytes() == b"V"
    c.post(f"/api/variants/{vid2}/review", json={"decision": "accepted", "note": ""})
    assert c.delete(f"/api/variants/{vid2}").status_code == 409
    assert c.post(f"/api/projects/{pid}/variants/clear-rejected").json() == {"deleted": 0}


def test_import_of_file_already_in_project_gives_relative_path(tmp_path):
    c = TestClient(create_app(data_dir=tmp_path / "d", comfy_url="http://127.0.0.1:9"))
    pid = c.post("/api/projects", json={"name": "Rel"}).json()["id"]
    root = Path(c.get(f"/api/projects/{pid}").json()["root_path"])
    (root / "renders").mkdir(exist_ok=True)
    (root / "renders" / "clip_a.mp4").write_bytes(b"A")
    r = c.post(f"/api/projects/{pid}/import", json={"path": str(root / "renders" / "clip_a.mp4")})
    assert r.json()["name"] == "renders/clip_a.mp4"
    assert not (root / "renders" / "clip_a_2.mp4").exists()
