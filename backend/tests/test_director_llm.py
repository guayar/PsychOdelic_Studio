import json
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from fastapi.testclient import TestClient

from psychodelic.app import create_app


SEEN = []


class _Stub(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, obj):
        raw = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/tags":
            self._send({"models": [{"name": "qwen3.6:27b"}, {"name": "gemma4:31b"}]})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/api/generate":
            SEEN.append(body.get("prompt", ""))
            self._send({"response": f"STUB model={body.get('model')} stream={body.get('stream')}", "done": True})
        else:
            self.send_response(404)
            self.end_headers()


@pytest.fixture()
def stub_url():
    srv = HTTPServer(("127.0.0.1", 0), _Stub)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def _client(tmp_path, llm_url):
    return TestClient(create_app(data_dir=tmp_path / "data", comfy_url="http://127.0.0.1:9", llm_url=llm_url))


def test_director_model_set_and_plan_uses_it(tmp_path, stub_url):
    c = _client(tmp_path, stub_url)
    assert c.get("/api/settings").json()["settings"]["director_model"] == ""
    assert c.put("/api/settings", json={"director_model": "qwen3.6:27b"}).status_code == 200
    assert c.get("/api/settings").json()["settings"]["director_model"] == "qwen3.6:27b"
    r = c.post("/api/director/llm-plan", json={"brief": "Ogrodnik stoi i patrzy na roze."})
    assert r.status_code == 200
    assert r.json()["model"] == "qwen3.6:27b"
    assert r.json()["text"] == "STUB model=qwen3.6:27b stream=False"


def test_plan_without_model_is_refused(tmp_path, stub_url):
    c = _client(tmp_path, stub_url)
    assert c.post("/api/director/llm-plan", json={"brief": "x"}).status_code == 422


def test_bad_model_name_refused(tmp_path, stub_url):
    c = _client(tmp_path, stub_url)
    assert c.put("/api/settings", json={"director_model": "../../etc"}).status_code == 422


def test_ollama_down_is_503_not_500(tmp_path):
    c = _client(tmp_path, "http://127.0.0.1:9")
    c.put("/api/settings", json={"director_model": "qwen3.6:27b"})
    assert c.post("/api/director/llm-plan", json={"brief": "x"}).status_code == 503


def test_remote_llm_address_is_refused(tmp_path):
    c = _client(tmp_path, "http://10.0.0.5:11434")
    c.put("/api/settings", json={"director_model": "qwen3.6:27b"})
    assert c.post("/api/director/llm-plan", json={"brief": "x"}).status_code == 503


def test_plan_gets_previous_scenes_as_context(tmp_path, stub_url):
    c = _client(tmp_path, stub_url)
    c.put("/api/settings", json={"director_model": "qwen3.6:27b"})
    pid = c.post("/api/projects", json={"name": "Kontekst"}).json()["id"]
    root = Path(c.get(f"/api/projects/{pid}").json()["root_path"])
    (root / "prompts").mkdir(exist_ok=True)
    (root / "prompts" / "shot_01.txt").write_text("Ogrodnik stoi w ogrodzie.", encoding="utf-8")
    r = c.post("/api/director/llm-plan", json={"brief": "Ogrodnik odwraca sie do okna.", "project_id": pid})
    assert r.status_code == 200
    sent = SEEN[-1]
    assert "[shot_01] Ogrodnik stoi w ogrodzie." in sent
    assert sent.index("[shot_01]") < sent.index("Opis:") < sent.index("Ogrodnik odwraca")


def test_director_gets_rules_for_chosen_target(tmp_path, stub_url):
    c = _client(tmp_path, stub_url)
    c.put("/api/settings", json={"director_model": "qwen3.6:27b"})
    c.post("/api/director/llm-plan", json={"brief": "Ogrodnik.", "target": "scene"})
    scene = SEEN[-1]
    assert "RULES FOR A MINIMAX H3 SCENE" in scene and "RULES FOR LTX" not in scene
    assert "Write every video PROMPT in English" in scene
    c.post("/api/director/llm-plan", json={"brief": "Ogrodnik.", "target": "ltx"})
    ltx = SEEN[-1]
    assert "RULES FOR LTX 2.5 LIPSYNC" in ltx and "RULES FOR A MINIMAX H3 SCENE" not in ltx
    assert c.post("/api/director/llm-plan", json={"brief": "x", "target": "bad"}).status_code == 422
