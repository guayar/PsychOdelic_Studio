"""Adapter LTX lipsync: buduje wywolanie produkcyjnego `_docs/gen_ltx_lip.py` (argumenty jak w jego usage).

Status: POTWIERDZONE_TESTEM dla budowy komendy. NIEZWERYFIKOWANE: zgodnosc z prawdziwym skryptem
oraz istnienie bazowego grafu `~/ComfyUI/user/default/workflows/oug_ltx_director_api.json`.
Siatka dlugosci LTX (8n+1) jest liczona przez produkcyjny skrypt; tu tylko sprawdzamy wejscia.
"""
from dataclasses import dataclass
from pathlib import Path

from ..security import UnsafePath, resolve_within, safe_name
from .h3 import H3ValidationError

SCRIPT_REL = "_docs/gen_ltx_lip.py"


@dataclass
class LtxSpec:
    project_root: str
    tail: str                 # nazwa pliku w ComfyUI input
    tail_frames: int
    audio: str                # nazwa pliku wav w ComfyUI input
    audio_frames: int
    prompt_file: str          # wzgledem project_root
    seed: int
    prefix: str
    audio_shift: int = 0


def build_command(spec: LtxSpec):
    root = Path(spec.project_root)
    if not root.is_dir():
        raise H3ValidationError("katalog projektu nie istnieje")
    for name in (spec.tail, spec.audio):
        try:
            safe_name(name)
        except UnsafePath as exc:
            raise H3ValidationError(str(exc))
    try:
        p = resolve_within(root, spec.prompt_file)
    except UnsafePath as exc:
        raise H3ValidationError(f"prompt poza projektem: {exc}")
    if not p.is_file():
        raise H3ValidationError("brak pliku promptu")
    if spec.tail_frames < 1 or spec.audio_frames < 1:
        raise H3ValidationError("liczby klatek musza byc dodatnie")
    argv = ["python3", "-u", SCRIPT_REL, "--tail", spec.tail, "--tail_frames", str(spec.tail_frames),
            "--audio", spec.audio, "--audio_frames", str(spec.audio_frames), "--prompt_file", spec.prompt_file,
            "--seed", str(spec.seed), "--prefix", spec.prefix]
    if spec.audio_shift:
        argv += ["--audio_shift", str(spec.audio_shift)]
    return {"cwd": str(root), "argv": argv, "env": {}, "script": SCRIPT_REL, "warnings": [], "errors": []}
