"""Przegladanie dowolnego katalogu dla pickerow (tylko pliki multimedialne) i import do ComfyUI/input.

Import KOPIUJE plik do ComfyUI/input pod bezpieczna nazwa; nie nadpisuje istniejacych plikow.
"""
import re
import shutil
from pathlib import Path

from .comfy_input import KINDS

MAX_ENTRIES = 1000


def _abs(path):
    p = Path(path).expanduser()
    if not p.is_absolute():
        raise ValueError("podaj pelna sciezke")
    return p


def list_dir(path, q=""):
    p = _abs(path)
    if not p.is_dir():
        raise FileNotFoundError(f"brak katalogu: {p}")
    needle = (q or "").strip().lower()
    dirs, files = [], []
    for c in sorted(p.iterdir(), key=lambda x: x.name.lower()):
        if c.name.startswith("."):
            continue
        if c.is_dir():
            dirs.append({"name": c.name, "kind": "dir", "path": str(c), "size": 0})
        elif c.is_file():
            kind = KINDS.get(c.suffix.lower())
            if kind is None or (needle and needle not in c.name.lower()):
                continue
            files.append({"name": c.name, "kind": kind, "path": str(c), "size": c.stat().st_size})
        if len(dirs) + len(files) >= MAX_ENTRIES:
            break
    return {"path": str(p), "parent": str(p.parent) if p.parent != p else None, "entries": dirs + files}


def resolve_file(path):
    try:
        p = _abs(path)
    except ValueError:
        return None
    if not p.is_file() or p.suffix.lower() not in KINDS:
        return None
    return p


def _safe(name):
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def import_to_input(path, input_root):
    src = resolve_file(path)
    if src is None:
        raise ValueError("to nie jest plik multimedialny")
    root = Path(input_root)
    root.mkdir(parents=True, exist_ok=True)
    base = _safe(src.name)
    target, n = root / base, 2
    stem, suffix = Path(base).stem, Path(base).suffix
    while target.exists():
        if target.resolve() == src.resolve() or (target.stat().st_size == src.stat().st_size and target.read_bytes() == src.read_bytes()):
            return target.name  # ten sam plik juz tam jest
        target = root / f"{stem}_{n}{suffix}"
        n += 1
    shutil.copy2(src, target)
    return target.name
