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
