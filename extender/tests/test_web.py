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
