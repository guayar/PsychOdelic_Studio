import pytest

from psychodelic.director.llm import OllamaRuntime
from psychodelic.director.planner import plan_shots
from psychodelic.director.tools import EXECUTE, READ, Tool, ToolError, ToolRegistry
from psychodelic.media.grid import frames_to_timecode, is_h3_grid, seconds_to_frames, snap_frames
from psychodelic.media.timeline import Clip, TimelineError, export_csv, export_json, validate
from psychodelic.orchestrator.gpu import decide_render, parse_rocm_smi


def test_grid_snapping():
    assert snap_frames(5.17) == 124 and snap_frames(10.125) == 243
    assert is_h3_grid(124) and not is_h3_grid(120)
    assert seconds_to_frames(1.0) == 24 and seconds_to_frames(1.0001) == 25


def test_timecode():
    assert frames_to_timecode(0) == "00:00:00:00"
    assert frames_to_timecode(24 * 65 + 5) == "00:01:05:05"
    with pytest.raises(ValueError):
        frames_to_timecode(-1)


def test_planner_snaps_and_warns_on_negation():
    out = plan_shots([{"start_s": 0, "end_s": 5.17, "text": "Gardener walks in, no speech"}])
    assert out["shots"][0]["frames"] == 124
    assert any("przeczenie" in w for w in out["warnings"])


def test_planner_rejects_overlap_and_bad_range():
    with pytest.raises(ValueError):
        plan_shots([{"start_s": 0, "end_s": 5, "text": "a"}, {"start_s": 4, "end_s": 9, "text": "b"}])
    with pytest.raises(ValueError):
        plan_shots([{"start_s": 5, "end_s": 5, "text": "a"}])


def test_timeline_out_is_exclusive_and_overlap_detected():
    ok = [Clip("a", "x.mp4", 0, 124, 0), Clip("b", "y.mp4", 0, 243, 124)]
    assert validate(ok) == []
    bad = [Clip("a", "x.mp4", 0, 124, 0), Clip("b", "y.mp4", 0, 10, 100)]
    assert any("nakladaja" in e for e in validate(bad))
    with pytest.raises(TimelineError):
        export_json([Clip("a", "x.mp4", 10, 10, 0)])


def test_timeline_csv_export_content():
    csv = export_csv([Clip("a", "x.mp4", 0, 124, 0)])
    assert csv.splitlines()[1] == "a,x.mp4,0,124,0,00:00:00:00,124"


def test_tool_registry_validation_and_permissions():
    reg = ToolRegistry()
    reg.register(Tool("plan.read", READ, {"x": "int"}, lambda a: a["x"] + 1))
    assert reg.call("plan.read", {"x": 1}) == 2
    with pytest.raises(ToolError):
        reg.call("plan.read", {"x": "1"})
    with pytest.raises(ToolError):
        reg.call("plan.read", {"x": 1, "y": 2})
    reg.register(Tool("render.submit", EXECUTE, {"job": "str"}, lambda a: "queued"))
    with pytest.raises(ToolError):
        reg.call("render.submit", {"job": "a"})
    assert reg.call("render.submit", {"job": "a"}, approved_by_human=True) == "queued"
    with pytest.raises(ToolError):
        reg.register(Tool("shell.run", READ, {}, None))


def test_gpu_parse_and_decision_conservative():
    text = ("GPU[0]\t\t: VRAM Total Memory (B): 34208743424\n"
            "GPU[0]\t\t: VRAM Total Used Memory (B): 16697217024\n")
    gpus = parse_rocm_smi(text)
    assert gpus == [{"gpu": 0, "total_b": 34208743424, "used_b": 16697217024}]
    assert decide_render({"status": "NIEZWERYFIKOWANE"})["allowed"] is False
    assert decide_render({"status": "POTWIERDZONE_TESTEM", "gpus": gpus})["allowed"] is False  # 17 GB wolne < 20 GB


def test_ollama_only_local():
    with pytest.raises(ValueError):
        OllamaRuntime("http://10.0.0.5:11434")
    st = OllamaRuntime("http://127.0.0.1:9", timeout=0.5).status()
    assert st["status"] == "NIEDOSTEPNE_LUB_WYMAGA_ZMIANY"
