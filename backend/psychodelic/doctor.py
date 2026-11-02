"""Diagnostyka srodowiska. Kazda pozycja ma jeden z trzech statusow:

  POTWIERDZONE_TESTEM               - sprawdzone w tym uruchomieniu
  TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE - narzedzie wykryte, ale nie uruchomione/zmierzone (np. VRAM)
  NIEDOSTEPNE_LUB_WYMAGA_ZMIANY       - brak lub nie dziala

Brak serwera ComfyUI NIE oznacza braku modeli. Oznacza tylko brak potwierdzenia.
"""
import os
import shutil
import sqlite3
import sys
import urllib.error
import urllib.request

CONFIRMED = "POTWIERDZONE_TESTEM"
UNVERIFIED = "TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE"
UNAVAILABLE = "NIEDOSTEPNE_LUB_WYMAGA_ZMIANY"


def _item(name, status, detail):
    return {"name": name, "status": status, "detail": detail}


def run_doctor(data_dir, comfy_url="http://127.0.0.1:8188", timeout=3.0):
    items = []
    ok_py = sys.version_info >= (3, 11)
    items.append(_item("python>=3.11", CONFIRMED if ok_py else UNAVAILABLE, sys.version.split()[0]))
    items.append(_item("sqlite", CONFIRMED, sqlite3.sqlite_version))
    for tool in ("ffmpeg", "ffprobe"):
        path = shutil.which(tool)
        items.append(_item(tool, CONFIRMED if path else UNAVAILABLE, path or "nie znaleziono w PATH"))
    smi = shutil.which("rocm-smi")
    items.append(_item("rocm-smi", UNVERIFIED if smi else UNAVAILABLE,
                       f"wykryto: {smi}; odczyt VRAM nie byl wykonany" if smi else "brak narzedzia"))
    try:
        os.makedirs(data_dir, exist_ok=True)
        probe = os.path.join(data_dir, ".write-probe")
        with open(probe, "w") as fh:
            fh.write("ok")
        os.remove(probe)
        free_gb = shutil.disk_usage(data_dir).free / 1e9
        items.append(_item("data_dir zapisywalny", CONFIRMED, f"{data_dir} (wolne: {free_gb:.1f} GB)"))
    except OSError as exc:
        items.append(_item("data_dir zapisywalny", UNAVAILABLE, str(exc)))
    items.append(_comfy_item(comfy_url, timeout))
    return {"items": items, "summary": _summary(items)}


def _comfy_item(url, timeout):
    try:
        with urllib.request.urlopen(f"{url}/system_stats", timeout=timeout) as resp:
            return _item("ComfyUI", CONFIRMED, f"{url} odpowiada (HTTP {resp.status})")
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return _item("ComfyUI", UNAVAILABLE,
                     f"{url} nie odpowiada ({type(exc).__name__}); brak potwierdzenia, nie dowod braku modeli")


def _summary(items):
    counts = {CONFIRMED: 0, UNVERIFIED: 0, UNAVAILABLE: 0}
    for it in items:
        counts[it["status"]] += 1
    return counts
