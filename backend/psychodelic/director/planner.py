"""Planer ujec OPARTY NA REGULACH (bez LLM). Dziala zawsze, takze gdy model lokalny jest wylaczony.

Wejscie: lista beatow {start_s, end_s, text}. Wyjscie: ShotPlan z dlugosciami w siatce 17n+5 (H3)
i ostrzezeniami zgodnymi z zasadami promptow (pozytywne zdania, jeden ruch kamery, bohater milczy).
"""
import re

from ..adapters.h3 import MAX_DURATION_S
from ..media.grid import snap_frames

NEGATION = re.compile(r"\b(no|not|don't|do not|without|never|nie)\b", re.IGNORECASE)


def plan_shots(beats):
    if not isinstance(beats, list) or not beats:
        raise ValueError("brak beatow")
    shots, warnings = [], []
    prev_end = None
    for i, b in enumerate(beats, 1):
        start, end = float(b["start_s"]), float(b["end_s"])
        if not end > start:
            raise ValueError(f"beat {i}: koniec musi byc po poczatku")
        if prev_end is not None and start < prev_end - 1e-9:
            raise ValueError(f"beat {i} nachodzi na poprzedni")
        if end - start > MAX_DURATION_S:
            warnings.append(f"ujecie {i} dluzsze niz {MAX_DURATION_S} s: podziel na mniejsze")
        text = str(b.get("text", "")).strip()
        if NEGATION.search(text):
            warnings.append(f"ujecie {i}: prompt zawiera przeczenie; H3 lepiej czyta opis pozytywny")
        if not text:
            warnings.append(f"ujecie {i}: pusty prompt")
        shots.append({"index": i, "start_s": start, "end_s": end, "frames": snap_frames(end - start),
                      "prompt": text})
        prev_end = end
    return {"shots": shots, "warnings": warnings}
