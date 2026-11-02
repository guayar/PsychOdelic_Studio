"""Ustawienia studia: model AI Directora (Ollama). Zapisywane w katalogu danych, atomowo."""
import json
import re
from pathlib import Path

from .fsio import atomic_write_json

DEFAULTS = {"director_model": ""}
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,99}$")
ROLES = {
    "director": "Qwen (Ollama): planowanie ujec i promptow, bez renderu",
    "lipsync": "LTX 2.5 22b: lipsync (ComfyUI)",
    "scenes_refs": "H3 MiniMax: sceny i referencje (ComfyUI)",
}


def _path(data_dir):
    return Path(data_dir) / "settings.json"


def load_settings(data_dir):
    p = _path(data_dir)
    if not p.is_file():
        return dict(DEFAULTS)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return dict(DEFAULTS)
    return {**DEFAULTS, **{k: v for k, v in raw.items() if k in DEFAULTS}}


def save_settings(data_dir, patch):
    current = load_settings(data_dir)
    if "director_model" in patch and patch["director_model"] is not None:
        model = str(patch["director_model"]).strip()
        if model and (not MODEL_RE.match(model) or ".." in model):
            raise ValueError("nazwa modelu: litery, cyfry, . _ : / - (max 100)")
        current["director_model"] = model
    atomic_write_json(_path(data_dir), current, overwrite=True)
    return current
