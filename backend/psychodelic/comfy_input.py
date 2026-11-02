"""Podglad katalogu ComfyUI/input (tylko odczyt): lista plikow i ich udostepnienie do miniatur."""
from pathlib import Path

from .security import UnsafePath, resolve_within

KINDS = {".png": "image", ".jpg": "image", ".jpeg": "image", ".webp": "image",
         ".mp4": "video", ".mov": "video", ".webm": "video",
         ".wav": "audio", ".mp3": "audio", ".flac": "audio"}
MAX_ITEMS = 1000


def default_input_dir():
    return Path.home() / "ComfyUI" / "input"


def list_inputs(root, q="", limit=MAX_ITEMS):
    root = Path(root)
    if not root.is_dir():
        return {"exists": False, "root": str(root), "items": []}
    needle = (q or "").strip().lower()
    items = []
    for p in sorted(root.iterdir(), key=lambda x: x.name.lower()):
        kind = KINDS.get(p.suffix.lower())
        if not p.is_file() or kind is None:
            continue
        if needle and needle not in p.name.lower():
            continue
        items.append({"name": p.name, "kind": kind, "size": p.stat().st_size})
        if len(items) >= limit:
            break
    return {"exists": True, "root": str(root), "items": items}


def resolve_input_file(root, name):
    """Sciezka do pliku w katalogu wejsciowym. Zwraca None dla blednych nazw i nieobslugiwanych typow."""
    try:
        target = resolve_within(root, name)
    except UnsafePath:
        return None
    if not target.is_file() or target.suffix.lower() not in KINDS:
        return None
    return target
