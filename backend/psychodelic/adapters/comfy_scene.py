"""Jedna scena H3 (Ref2VA) jako graf API ComfyUI.

Graf bazowy: studio_workflows/api/h3_ref2va_scene_api.json (zweryfikowany w workshopie, bez zmian).
Podmieniamy: prompt, dlugosc (17n+5 klatek), rozmiar, seed, referencje obrazow (LoadImage) i prefiks wyniku.
"""
import copy
import json
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from ..security import UnsafePath, safe_name
from .h3 import MAX_DURATION_S, MAX_IMAGE_REFS, PREFIX_RE

TEMPLATE = Path(__file__).resolve().parents[3] / "studio_workflows" / "api" / "h3_ref2va_scene_api.json"
LOCAL = ("http://127.0.0.1", "http://localhost")


class SceneError(ValueError):
    pass


def snap_frames(seconds):
    """Sekundy -> klatki w siatce H3 (17n+5 przy 24 fps), jak w planerze."""
    if not (0 < float(seconds) <= MAX_DURATION_S):
        raise SceneError(f"dlugosc poza zakresem (0; {MAX_DURATION_S}] s")
    raw = max(5, round(float(seconds) * 24))
    n = max(0, round((raw - 5) / 17))
    return 17 * n + 5


def build_scene_graph(prompt, seed, seconds, width, height, refs, prefix):
    if not prompt or not prompt.strip() or len(prompt) > 2000:
        raise SceneError("prompt: od 1 do 2000 znakow")
    if not (0 <= int(seed) <= 2**31 - 1):
        raise SceneError("seed poza zakresem")
    for name, v in (("width", width), ("height", height)):
        if int(v) % 32 or not (256 <= int(v) <= 4096):
            raise SceneError(f"{name}: wielokrotnosc 32 w zakresie 256-4096")
    if not (1 <= len(refs) <= MAX_IMAGE_REFS):
        raise SceneError(f"podaj od 1 do {MAX_IMAGE_REFS} referencji obrazow")
    for r in refs:
        try:
            safe_name(r)
        except UnsafePath as exc:
            raise SceneError(f"referencja {r!r}: {exc}")
    if not PREFIX_RE.match(prefix or ""):
        raise SceneError("prefiks: litery, cyfry, _ - / (max 64 znaki)")
    frames = snap_frames(seconds)

    g = copy.deepcopy(json.loads(TEMPLATE.read_text(encoding="utf-8")))
    g.pop("5", None)  # stale LoadImage z szablonu; referencje wstawiamy od nowa
    g.pop("6", None)
    node = g["7"]["inputs"]
    for k in [k for k in node if k.startswith("ref_image_")]:
        del node[k]
    for k, name in enumerate(refs):
        nid = str(100 + k)
        g[nid] = {"class_type": "LoadImage", "inputs": {"image": name}}
        node[f"ref_image_{k}"] = [nid, 0]
    node["prompt"] = prompt
    node["width"] = int(width)
    node["height"] = int(height)
    node["length"] = frames
    g["10"]["inputs"]["noise_seed"] = int(seed)
    g["14"]["inputs"]["filename_prefix"] = prefix
    return g, frames


def _local(url):
    if not url.startswith(LOCAL):
        raise SceneError("ComfyUI tylko lokalnie (127.0.0.1/localhost)")
    return url.rstrip("/")


def submit(comfy_url, graph, timeout=30.0):
    """POST /prompt. Zwraca prompt_id. Odrzucenie grafu przez ComfyUI -> SceneError z trescia."""
    body = json.dumps({"prompt": graph, "client_id": str(uuid.uuid4())}).encode("utf-8")
    req = urllib.request.Request(f"{_local(comfy_url)}/prompt", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as exc:
        raise SceneError(f"ComfyUI odrzucil graf ({exc.code}): {exc.read()[:300].decode('utf-8', 'replace')}")
    if "prompt_id" not in data:
        raise ValueError("ComfyUI nie zwrocil prompt_id")
    return data["prompt_id"]
