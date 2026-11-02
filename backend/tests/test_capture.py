"""Test przechwytywania grafu na skrypcie-atrapie: graf zapisany, a zadna inna komunikacja nie jest mozliwa."""
import json
from pathlib import Path

from psychodelic.adapters import capture
from psychodelic.adapters.h3 import ExtenderSpec, build_command

STUB = '''
import json, os, sys, urllib.request
obj = json.load(urllib.request.urlopen("http://127.0.0.1:8188/object_info"))
refine, prefix, seed, prompts = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4:]
graph = {"1": {"class_type": "MiniMaxH3Extender", "inputs": {"prefix": prefix, "seed": seed,
         "prompt": open(prompts[0]).read().strip(), "refs": os.environ.get("REFS", ""),
         "known_nodes": len(obj)}}}
req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=json.dumps({"prompt": graph}).encode())
urllib.request.urlopen(req)
print("NEVER REACHED")
'''

LEAK = '''
import urllib.request
urllib.request.urlopen("http://127.0.0.1:8188/queue")
'''


def make_project(tmp_path, script_body, name="_docs/gen_extender_refine.py"):
    (tmp_path / "_docs").mkdir(exist_ok=True)
    (tmp_path / "_docs" / name.split("/")[-1]).write_text(script_body, encoding="utf-8")
    (tmp_path / "ext_test").mkdir(exist_ok=True)
    (tmp_path / "ext_test" / "s1.txt").write_text("Gardener stands still.", encoding="utf-8")
    return tmp_path


def test_capture_produces_graph_without_server(tmp_path):
    root = make_project(tmp_path, STUB)
    oi = tmp_path / "object_info.json"
    oi.write_text(json.dumps({"MiniMaxH3Extender": {}, "UNETLoader": {}}), encoding="utf-8")
    cmd = build_command(ExtenderSpec(project_root=str(root), prefix="shots/v3b_1", seed=1234,
                                     prompt_files=["ext_test/s1.txt"], refs=["ref_gsheet2.png"], durs=[7.5]))
    res = capture.capture(cmd, oi, tmp_path / "graph.json")
    assert res["status"] == "CAPTURED", res
    graph = json.loads(Path(res["graph_path"]).read_text(encoding="utf-8"))["prompt"]
    inputs = graph["1"]["inputs"]
    assert inputs["prefix"] == "shots/v3b_1" and inputs["seed"] == 1234
    assert inputs["prompt"] == "Gardener stands still."
    assert inputs["refs"] == "ref_gsheet2.png"
    assert inputs["known_nodes"] == 2
    assert capture.summarize(res["graph_path"])["classes"] == {"MiniMaxH3Extender": 1}


def test_blocked_connection_is_reported_not_sent(tmp_path):
    root = make_project(tmp_path, LEAK)
    oi = tmp_path / "object_info.json"
    oi.write_text("{}", encoding="utf-8")
    cmd = build_command(ExtenderSpec(project_root=str(root), prefix="shots/x", seed=1,
                                     prompt_files=["ext_test/s1.txt"]))
    res = capture.capture(cmd, oi, tmp_path / "graph.json")
    assert res["status"] == "NOT_CAPTURED"
    assert "BLOCKED" in res["stderr_tail"]
