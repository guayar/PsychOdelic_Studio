import os
import pytest
from fastapi.testclient import TestClient

from psy_extender.web import create_app


@pytest.fixture()
def client(tmp_path):
    return TestClient(create_app(str(tmp_path / "chain.json"), oug_dir="", comfy_output=str(tmp_path / "out")))


def test_add_tree_refs_and_settings(client):
    root = client.post("/api/scenes", json={"title": "Ogrod"}).json()["id"]
    child = client.post("/api/scenes", json={"title": "Scena 2", "parent": root}).json()["id"]
    client.post(f"/api/scenes/{root}/refs", json={"name": "gardener.png"})
    client.put(f"/api/scenes/{child}/setting", json={"path": "sharpen.enabled", "value": True})
    tree = client.get("/api/tree").json()
    c = next(s for s in tree["scenes"] if s["id"] == child)
    assert c["effective_refs"] == ["gardener.png"] and c["settings"]["sharpen"]["enabled"] is True


def test_delete_scene_needs_confirmation_for_children(client):
    root = client.post("/api/scenes", json={"title": "R"}).json()["id"]
    client.post("/api/scenes", json={"title": "C", "parent": root})
    assert client.delete(f"/api/scenes/{root}").status_code == 409
    assert client.delete(f"/api/scenes/{root}?cascade=true").status_code == 200
    assert client.get("/api/tree").json()["scenes"] == []


def test_generate_default_is_plan_only(client):
    sid = client.post("/api/scenes", json={"title": "A"}).json()["id"]
    r = client.post(f"/api/scenes/{sid}/generate", json={"execute": False}).json()
    assert r["executed"] is False and r["plan"]["argv"][2] == "_docs/gen_extender_refine.py"


def test_execute_needs_oug_dir(client):
    sid = client.post("/api/scenes", json={"title": "A"}).json()["id"]
    assert client.post(f"/api/scenes/{sid}/generate", json={"execute": True}).status_code == 422


def test_index_page_served(client):
    assert "Drzewo scen" in client.get("/").text


def test_execute_writes_prompt_and_records_output(tmp_path):
    oug = tmp_path / "oug"
    (oug / "_docs").mkdir(parents=True)
    out = tmp_path / "out"; out.mkdir()
    (oug / "_docs" / "gen_extender_refine.py").write_text(
        "import os, sys, pathlib\n"
        "refine, prefix, seed, prompt = sys.argv[1:5]\n"
        "pathlib.Path(os.environ['COMFY_OUT'], prefix.replace('/', '_') + '.mp4').write_bytes(open(prompt, 'rb').read())\n",
        encoding="utf-8")
    os.environ["COMFY_OUT"] = str(out)
    inp = tmp_path / "input"
    c = TestClient(create_app(str(tmp_path / "chain.json"), oug_dir=str(oug), comfy_output=str(out), comfy_input=str(inp)))
    sid = c.post("/api/scenes", json={"title": "A", "prompt": "The gardener stands still."}).json()["id"]
    r = c.post(f"/api/scenes/{sid}/generate", json={"execute": True}).json()
    assert r["ok"] is True and r["output"] == f"ext_{sid}.mp4"
    assert (oug / "_docs" / "studio_prompts" / f"{sid}.txt").read_text(encoding="utf-8") == "The gardener stands still."
    assert c.get("/api/file", params={"name": r["output"]}).status_code == 200
    assert (inp / r["output"]).is_file(), "wynik musi trafic do ComfyUI/input jako CONT nastepnej sceny"
    assert next(s for s in c.get("/api/tree").json()["scenes"] if s["id"] == sid)["output"] == r["output"]


def test_page_keeps_selection_separate_from_tree_state():
    from pathlib import Path
    html = (Path(__file__).resolve().parents[1] / "web" / "index.html").read_text(encoding="utf-8")
    assert "state.sel" not in html
    assert "let sel=null" in html


def test_media_inherit_limits_and_picker_list(tmp_path):
    inp = tmp_path / "input"; inp.mkdir()
    (inp / "a.png").write_bytes(b"x"); (inp / "v.mp4").write_bytes(b"x"); (inp / "s.wav").write_bytes(b"x")
    c = TestClient(create_app(str(tmp_path / "chain.json"), comfy_input=str(inp)))
    root = c.post("/api/scenes", json={"title": "R"}).json()["id"]
    child = c.post("/api/scenes", json={"title": "C", "parent": root}).json()["id"]
    c.post(f"/api/scenes/{root}/media", json={"kind": "video", "name": "v.mp4"})
    c.post(f"/api/scenes/{child}/media", json={"kind": "audio", "name": "s.wav"})
    scenes = c.get("/api/tree").json()["scenes"]
    cm = next(s for s in scenes if s["id"] == child)["effective_media"]
    assert cm == {"video": ["v.mp4"], "audio": ["s.wav"]}
    assert c.post(f"/api/scenes/{child}/media", json={"kind": "video", "name": "x.mp4"}).status_code == 200
    for n in ["a.mp4", "b.mp4"]:
        c.post(f"/api/scenes/{child}/media", json={"kind": "video", "name": n})
    assert c.post(f"/api/scenes/{child}/media", json={"kind": "video", "name": "c.mp4"}).status_code == 422
    items = {i["name"]: i["kind"] for i in c.get("/api/inputs").json()["items"]}
    assert items == {"a.png": "image", "v.mp4": "video", "s.wav": "audio"}
    assert [i["name"] for i in c.get("/api/inputs", params={"kind": "audio"}).json()["items"]] == ["s.wav"]
