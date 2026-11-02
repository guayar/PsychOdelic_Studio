"""Menedzer zasobow GPU: tylko ODCZYT stanu i decyzje. Zwalnianie modelu NIE jest wykonywane w tej wersji.

Zwalnianie (unload Directora, /free ComfyUI) wymaga zgody i testu na maszynie uzytkownika.
Odczyt VRAM: rocm-smi (lista argumentow, bez powloki); brak narzedzia = status NIEZWERYFIKOWANE.
"""
import re
import shutil
import subprocess

VRAM_TOTAL = re.compile(r"VRAM Total Memory \(B\):\s*(\d+)")
VRAM_USED = re.compile(r"VRAM Total Used Memory \(B\):\s*(\d+)")


def parse_rocm_smi(text):
    """Zwraca liste {gpu, total_b, used_b} z wyjscia `rocm-smi --showmeminfo vram`."""
    totals = VRAM_TOTAL.findall(text)
    useds = VRAM_USED.findall(text)
    return [{"gpu": i, "total_b": int(t), "used_b": int(u)} for i, (t, u) in enumerate(zip(totals, useds))]


def read_vram(timeout=5):
    tool = shutil.which("rocm-smi")
    if tool is None:
        return {"status": "NIEDOSTEPNE_LUB_WYMAGA_ZMIANY", "detail": "brak rocm-smi"}
    try:
        out = subprocess.run([tool, "--showmeminfo", "vram"], capture_output=True, text=True, timeout=timeout,
                             shell=False).stdout
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"status": "NIEZWERYFIKOWANE", "detail": type(exc).__name__}
    gpus = parse_rocm_smi(out)
    if not gpus:
        return {"status": "NIEZWERYFIKOWANE", "detail": "nie udalo sie sparsowac wyjscia"}
    return {"status": "POTWIERDZONE_TESTEM", "gpus": gpus}


def decide_render(vram, required_free_b=20 * 1024**3):
    """Decyzja: czy mozna startowac render. Bez potwierdzonego VRAM -> nie."""
    if vram.get("status") != "POTWIERDZONE_TESTEM":
        return {"allowed": False, "reason": "brak potwierdzonego stanu VRAM"}
    gpu0 = vram["gpus"][0]
    free = gpu0["total_b"] - gpu0["used_b"]
    if free < required_free_b:
        return {"allowed": False, "reason": f"za malo wolnego VRAM ({free} B)"}
    return {"allowed": True, "reason": "ok"}
