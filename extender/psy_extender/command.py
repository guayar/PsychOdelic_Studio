"""Komenda produkcyjnego extendera (_docs/gen_extender_refine.py) z ustawien sceny. Argumenty jako lista, bez powloki."""
from pathlib import Path

from .tree import Tree

SCRIPT_REL = "_docs/gen_extender_refine.py"
ALLOWED_ENV = {"REFS", "CONT", "FULLRES", "DURS", "RUNMODE", "VALIDATED", "CTRL", "CTRL_FRAMES", "CTRL_STRENGTH"}


def frames_for(seconds):
    raw = max(5, round(seconds * 24))
    n = max(0, round((raw - 5) / 17))
    return 17 * n + 5


def build(tree: Tree, sid, prefix, seed=None, prompt_rel=None, cont=None, oug_dir=None):
    """Zwraca {cwd, argv, env, expected_output}. cont = nazwa pliku w ComfyUI/input (wynik poprzedniej sceny)."""
    s = tree.scene(sid)
    cfg = tree.effective_settings(sid)
    refs = tree.effective_refs(sid)
    media = tree.effective_media(sid)
    parent = s["parent"]
    if cont is None and parent is not None:
        cont = tree.scene(parent).get("output")
    env = {}
    if refs:
        env["REFS"] = ",".join(refs)
    if cont:
        env["CONT"] = cont
    if cfg["fullres"]:
        env["FULLRES"] = "1"
    if cfg["durs"]:
        env["DURS"] = ",".join(str(float(x)) for x in cfg["durs"])
    env["RUNMODE"] = cfg["runmode"]
    if cfg["validated"]:
        env["VALIDATED"] = str(int(cfg["validated"]))
    cn = cfg["controlnet"]
    if cn["enabled"] and cn["ctrl"]:
        env["CTRL"] = cn["ctrl"]
        if cn["frames"] is not None:
            env["CTRL_FRAMES"] = str(int(cn["frames"]))
        if cn["strength"] is not None:
            env["CTRL_STRENGTH"] = str(float(cn["strength"]))
    assert set(env) <= ALLOWED_ENV
    prompt_rel = prompt_rel or s.get("prompt_file") or f"_docs/studio_prompts/{sid}.txt"
    refine = "1" if cfg["refine"] else "0"
    seed = int(seed if seed is not None else s.get("seed", 1234))
    argv = ["python3", "-u", SCRIPT_REL, refine, prefix, str(seed), prompt_rel]
    root = Path(oug_dir) if oug_dir else None
    warnings = []
    if media["video"] or media["audio"]:
        warnings.append("wideo/audio sa zapisane w scenie, ale NIE sa przekazywane do gen_extender_refine.py "
                        "(skrypt zna tylko REFS/CONT/CTRL); sprawdz w skrypcie, czy ma wejscia na wideo i audio")
    return {"cwd": str(root) if root else None, "argv": argv, "env": env, "script": SCRIPT_REL,
            "media": media, "warnings": warnings,
            "expected_output": f"ComfyUI/output/{prefix.replace('/', '_')}*.mp4"}
