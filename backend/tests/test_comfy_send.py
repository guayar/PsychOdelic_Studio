import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from psychodelic.adapters.comfy_scene import SceneError, build_scene_graph, snap_frames
from psychodelic.app import create_app

COMFY_SEEN, OLLAMA_SEEN = [], []
COMFY_MODE = {"reject": False}


def _server(handler_cls):
    srv = HTTPServer(("127.0.0.1", 0), handler_cls)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


class _Base(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        raw = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")


class _Comfy(_Base):
    def do_POST(self):
        body = self._body()
        if COMFY_MODE["reject"]:
            return self._json(400, {"error": {"message": "Prompt has invalid inputs"}, "node_errors": {}})
        COMFY_SEEN.append(body)
        self._json(200, {"prompt_id": "pid-123", "number": 1})


class _Ollama(_Base):
    def do_POST(self):
        OLLAMA_SEEN.append(self._body())
        self._json(200, {"response": "", "done": True})


@pytest.fixture()
def servers():
    COMFY_SEEN.clear(); OLLAMA_SEEN.clear(); COMFY_MODE["reject"] = False
    comfy, ollama = _server(_Comfy), _server(_Ollama)
    yield (f"http://127.0.0.1:{comfy.server_address[1]}", f"http://127.0.0.1:{ollama.server_address[1]}")
    comfy.shutdown(); ollama.shutdown()


def _project(c, text="Ogrodnik stoi i patrzy na roze."):
    pid = c.post("/api/projects", json={"name": f"Scena {len(text)}"}).json()["id"]
    root = Path(c.get(f"/api/projects/{pid}").json()["root_path"])
    (root / "prompts").mkdir(exist_ok=True)
    (root / "prompts" / "shot_01.txt").write_text(text, encoding="utf-8")
    return pid


def _body(**kw):
    base = {"prompt_name": "shot_01", "seed": 42, "seconds": 10, "refs": ["set_plate.png", "character_sheet.png"],
            "prefix": "shots/scena_01"}
    base.update(kw)
    return base


def test_frames_snap_to_grid():
    assert snap_frames(5) == 124 and snap_frames(10) == 243 and snap_frames(7.5) == 175
    assert snap_frames(0.1) == 5


def test_graph_has_refs_prompt_and_prefix():
    g, frames = build_scene_graph("Ogrodnik stoi.", 7, 10, 1344, 768, ["a.png", "b.png", "c.png"], "shots/x")
    assert frames == 243
    n = g["7"]["inputs"]
    assert n["prompt"] == "Ogrodnik stoi." and n["length"] == 243 and n["width"] == 1344
    assert n["ref_image_0"] == ["100", 0] and n["ref_image_2"] == ["102", 0] and "ref_image_3" not in n
    assert "5" not in g and "6" not in g
    assert n["ref_image_size"] == "match", "pole ref_image_size musi zostac w wezle 7"
    assert g["100"]["inputs"]["image"] == "a.png" and g["10"]["inputs"]["noise_seed"] == 7
    assert g["14"]["inputs"]["filename_prefix"] == "shots/x"


@pytest.mark.parametrize("kw", [
    {"refs": []}, {"refs": ["../x.png"]}, {"width": 1000}, {"prefix": "../bad"}, {"seconds": 99},
])
def test_graph_rejects_bad_input(kw):
    args = dict(prompt="x", seed=1, seconds=10, width=1344, height=768, refs=["a.png"], prefix="shots/x")
    args.update(kw)
    with pytest.raises(SceneError):
        build_scene_graph(**args)


def test_send_refused_when_render_disabled(tmp_path, servers):
    comfy, ollama = servers
    c = TestClient(create_app(data_dir=tmp_path / "d", comfy_url=comfy, llm_url=ollama))
    pid = _project(c)
    assert c.post(f"/api/projects/{pid}/h3/send-comfy", json=_body()).status_code == 403
    assert COMFY_SEEN == []


def test_send_unloads_director_then_queues_scene(tmp_path, servers):
    comfy, ollama = servers
    c = TestClient(create_app(data_dir=tmp_path / "d", comfy_url=comfy, llm_url=ollama))
    c.put("/api/settings", json={"director_model": "qwen3.6:27b", "render_enabled": True})
    pid = _project(c)
    r = c.post(f"/api/projects/{pid}/h3/send-comfy", json=_body())
    assert r.status_code == 201, r.text
    assert r.json()["prompt_id"] == "pid-123" and r.json()["frames"] == 243
    assert OLLAMA_SEEN and OLLAMA_SEEN[-1] == {"model": "qwen3.6:27b", "keep_alive": 0}
    sent = COMFY_SEEN[-1]["prompt"]
    assert sent["7"]["inputs"]["prompt"] == "Ogrodnik stoi i patrzy na roze." and sent["7"]["inputs"]["length"] == 243
    assert sent["100"]["inputs"]["image"] == "set_plate.png" and sent["101"]["inputs"]["image"] == "character_sheet.png"
    job = c.get(f"/api/projects/{pid}/jobs").json()[0]
    assert job["state"] == "RENDER_QUEUED"


def test_comfy_down_cancels_job_and_says_so(tmp_path, servers):
    _, ollama = servers
    c = TestClient(create_app(data_dir=tmp_path / "d", comfy_url="http://127.0.0.1:9", llm_url=ollama))
    c.put("/api/settings", json={"render_enabled": True})
    pid = _project(c)
    r = c.post(f"/api/projects/{pid}/h3/send-comfy", json=_body())
    assert r.status_code == 503
    assert c.get(f"/api/projects/{pid}/jobs").json()[0]["state"] == "CANCELLED"


def test_comfy_rejected_graph_is_422_with_reason(tmp_path, servers):
    comfy, ollama = servers
    COMFY_MODE["reject"] = True
    c = TestClient(create_app(data_dir=tmp_path / "d", comfy_url=comfy, llm_url=ollama))
    c.put("/api/settings", json={"render_enabled": True})
    pid = _project(c)
    r = c.post(f"/api/projects/{pid}/h3/send-comfy", json=_body())
    assert r.status_code == 422 and "odrzucil" in r.json()["detail"]
