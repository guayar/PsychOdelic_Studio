import json
import os
import subprocess
from pathlib import Path

import pytest

from psychodelic.installer.comfy import apply_workflows, detect_comfy, missing_report, plan_workflows

STUDIO = Path(__file__).resolve().parents[2]


def fake_comfy(root):
    (root / "custom_nodes").mkdir(parents=True)
    (root / "main.py").write_text("# fake", encoding="utf-8")
    (root / "user" / "default" / "workflows").mkdir(parents=True)
    return root


def fake_source(root, files):
    root.mkdir(parents=True, exist_ok=True)
    for name, body in files.items():
        (root / name).write_text(json.dumps(body), encoding="utf-8")
    return root


def test_detect_comfy(tmp_path):
    comfy = fake_comfy(tmp_path / "ComfyUI")
    assert detect_comfy([str(tmp_path / "nie-ma"), str(comfy)]) == comfy.resolve()
    assert detect_comfy([str(tmp_path / "nie-ma")]) is None


def test_plan_copy_skip_conflict(tmp_path):
    comfy = fake_comfy(tmp_path / "ComfyUI")
    src = fake_source(tmp_path / "src", {"a.json": {"v": 1}, "b.json": {"v": 1}, "c.json": {"v": 1}})
    target = comfy / "user" / "default" / "workflows"
    (target / "b.json").write_text(json.dumps({"v": 1}), encoding="utf-8")  # identyczny
    (target / "c.json").write_text(json.dumps({"v": 999}), encoding="utf-8")  # inny: konflikt
    actions = {a["file"]: a["action"] for a in plan_workflows(comfy, src)}
    assert actions == {"a.json": "copy", "b.json": "skip", "c.json": "conflict"}


def test_apply_never_overwrites_and_keeps_user_file(tmp_path):
    comfy = fake_comfy(tmp_path / "ComfyUI")
    src = fake_source(tmp_path / "src", {"mine.json": {"studio": True}, "c.json": {"studio": True}})
    target = comfy / "user" / "default" / "workflows"
    (target / "c.json").write_text(json.dumps({"user": "moje"}), encoding="utf-8")
    apply_workflows(plan_workflows(comfy, src))
    assert json.loads((target / "mine.json").read_text(encoding="utf-8")) == {"studio": True}
    assert json.loads((target / "c.json").read_text(encoding="utf-8")) == {"user": "moje"}  # nietkniety
    assert json.loads((target / "c.studio.json").read_text(encoding="utf-8")) == {"studio": True}
    assert not list(target.glob("*.part"))


def test_apply_refuses_invalid_json(tmp_path):
    comfy = fake_comfy(tmp_path / "ComfyUI")
    src = tmp_path / "src"
    src.mkdir()
    (src / "zly.json").write_text("{nie json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        apply_workflows(plan_workflows(comfy, src))
    assert not (comfy / "user" / "default" / "workflows" / "zly.json").exists()


def test_missing_report_tells_what_to_install():
    rep = missing_report({}, ["h3_extender"])
    nodes = [r for r in rep if r["kind"] == "node"]
    files = [r for r in rep if r["kind"] == "file"]
    ext = next(r for r in nodes if r["name"] == "MiniMaxH3Extender")
    assert ext["repo"] == "https://github.com/tritant/ComfyUI_MiniMax_H3_Extender"
    unet = next(r for r in files if "ref2va" in r["name"])
    assert unet["folder"] == "models/diffusion_models" and "nie są pobierane" in unet["how"]
    vae = next(r for r in files if "video_vae" in r["name"])
    assert vae["folder"] == "models/vae"


def test_cli_dry_run_and_real_copy_without_weights(tmp_path):
    comfy = fake_comfy(tmp_path / "ComfyUI")
    info = tmp_path / "oi.json"
    info.write_text("{}", encoding="utf-8")
    report = tmp_path / "rep.json"
    env = dict(os.environ, PYTHONPATH=str(STUDIO / "backend"))
    import sys
    run = lambda extra: subprocess.run([sys.executable, "-m", "psychodelic.installer", "--comfy", str(comfy),
                                        "--object-info", str(info), "--report", str(report), *extra],
                                       capture_output=True, text=True, env=env, cwd=str(STUDIO))
    r = run(["--dry-run"])
    assert r.returncode == 0 and "dry-run" in r.stdout
    assert not any((comfy / "user" / "default" / "workflows").iterdir())
    r = run(["--yes"])
    assert r.returncode == 0, r.stderr
    rep = json.loads(report.read_text(encoding="utf-8"))
    assert rep["weights_downloaded"] is False and rep["nodes_installed"] is False
    assert rep["missing"], "brakujace elementy musza byc wypisane"
    shipped = sorted(p.name for p in (STUDIO / "studio_workflows").glob("*.json"))
    assert shipped and all((comfy / "user" / "default" / "workflows" / n).exists() for n in shipped)


def test_install_sh_creates_launcher_and_skips_ui(tmp_path):
    comfy = fake_comfy(tmp_path / "ComfyUI")
    home = tmp_path / "home"
    home.mkdir()
    env = dict(os.environ, HOME=str(home))
    r = subprocess.run(["bash", str(STUDIO / "install.sh"), "--comfy", str(comfy), "--yes", "--skip-ui"],
                       capture_output=True, text=True, env=env, cwd=str(STUDIO), timeout=600)
    assert r.returncode == 0, r.stdout + r.stderr
    desktop = (home / ".local/share/applications/psychodelic-studio.desktop").read_text(encoding="utf-8")
    assert f"Exec={STUDIO}/start.sh" in desktop and "Icon=" in desktop
    assert (comfy / "user" / "default" / "workflows" / "H3_Ref2VA_3_ujecia.json").exists()
