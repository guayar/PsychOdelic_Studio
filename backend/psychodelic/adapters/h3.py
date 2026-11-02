"""Adapter H3 MiniMax Extender: buduje WYWOLANIE produkcyjnego skryptu `_docs/gen_extender_refine.py`.

Zasady (z promptu):
  * nie przepisujemy produkcyjnego skryptu i nie zgadujemy opcji CLI,
  * argumenty jako lista (bez powloki), zmienne srodowiskowe tylko z ustalonej listy,
  * wszystkie sciezki plikow projektu musza byc wewnatrz katalogu projektu,
  * refki H3 (Extender): co najwyzej 9 obrazow, sekwencja `<Picture N>` jak w skrypcie,
  * dlugosci segmentow w siatce 17n+5 przy 24 fps (zgodnie z walidacja H3),
  * ta klasa NIE wysyla niczego do ComfyUI; wykonanie robi runner, dopiero po jawnej zgodzie.

Status: POTWIERDZONE_TESTEM dla budowy komendy (na skrypcie-atrapie).
        NIEZWERYFIKOWANE: zgodnosc z prawdziwym skryptem (wymaga dry-run harnessu na maszynie uzytkownika).
"""
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..security import UnsafePath, resolve_within, safe_name

SCRIPT_REL = "_docs/gen_extender_refine.py"
MAX_IMAGE_REFS = 9
MAX_VIDEO_REFS = 3          # wg kodu tritant (MAX_VIDEO_REFS), klatki <= 362
MAX_AUDIO_REFS = 3          # wg kodu tritant (MAX_STANDALONE_AUDIO_REFS), kazdy 2-15 s, razem <= 15 s
MAX_MIXED_REFS = 12         # wg kodu tritant (MAX_MIXED_REF_ITEMS)
MAX_DURATION_S = 14.4
ALLOWED_ENV = {"REFS", "CONT", "FULLRES", "DURS", "RUNMODE", "VALIDATED", "CTRL", "CTRL_FRAMES", "CTRL_STRENGTH"}
PREFIX_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_\-/]{0,63}$")


class H3ValidationError(ValueError):
    pass


@dataclass
class ExtenderSpec:
    project_root: str
    prefix: str                  # np. "shots/shot_01" (wynik: shots_shot_01*.mp4 w output ComfyUI)
    seed: int
    prompt_files: list           # sciezki wzgledne wzgledem project_root
    refs: list = field(default_factory=list)       # nazwy plikow w ComfyUI input (nie sciezki)
    cont: str | None = None      # nazwa pliku w ComfyUI input (kontynuacja)
    fullres: bool = True
    durs: list = field(default_factory=list)       # sekundy na kazdy prompt
    runmode: str = "full_batch"  # full_batch | clip_by_clip
    validated: int = 0
    ctrl: str | None = None
    ctrl_frames: int | None = None
    ctrl_strength: float | None = None
    refine: bool = False
    ref_videos: list = field(default_factory=list)  # nazwy plikow w ComfyUI input
    ref_audios: list = field(default_factory=list)  # nazwy plikow w ComfyUI input


def _grid_ok(seconds):
    frames = round(seconds * 24)
    return frames >= 5 and (frames - 5) % 17 == 0


def build_command(spec: ExtenderSpec):
    """Zwraca slownik {cwd, argv, env, script, warnings}. Rzuca H3ValidationError przy bledach."""
    errors, warnings = [], []
    root = Path(spec.project_root)
    if not root.is_dir():
        raise H3ValidationError("katalog projektu nie istnieje")
    if not PREFIX_RE.match(spec.prefix or ""):
        raise H3ValidationError("prefix: litery, cyfry, _ - / (bez dwu kropek i spacji), max 64 znaki")
    if not (0 <= int(spec.seed) <= 2**31 - 1):
        raise H3ValidationError("seed poza zakresem")
    if not spec.prompt_files:
        raise H3ValidationError("brak plikow promptow")
    if len(spec.refs) > MAX_IMAGE_REFS:
        raise H3ValidationError(f"za duzo referencji: {len(spec.refs)} > {MAX_IMAGE_REFS}")
    if len(spec.ref_videos) > MAX_VIDEO_REFS:
        raise H3ValidationError(f"za duzo referencji wideo: {len(spec.ref_videos)} > {MAX_VIDEO_REFS}")
    if len(spec.ref_audios) > MAX_AUDIO_REFS:
        raise H3ValidationError(f"za duzo referencji audio: {len(spec.ref_audios)} > {MAX_AUDIO_REFS}")
    mixed = len(spec.refs) + len(spec.ref_videos) + len(spec.ref_audios)
    if mixed > MAX_MIXED_REFS:
        raise H3ValidationError(f"H3 przyjmuje najwyzej {MAX_MIXED_REFS} referencji lacznie, podano {mixed}")
    if spec.ref_audios and not (spec.refs or spec.ref_videos):
        raise H3ValidationError("referencja audio wymaga co najmniej jednego obrazu lub wideo")
    for name in list(spec.ref_videos) + list(spec.ref_audios):
        try:
            safe_name(name)
        except UnsafePath as exc:
            raise H3ValidationError(str(exc))
    if spec.runmode not in ("full_batch", "clip_by_clip"):
        raise H3ValidationError("runmode: full_batch albo clip_by_clip")
    if spec.durs and len(spec.durs) != len(spec.prompt_files):
        warnings.append("liczba DURS rozni sie od liczby promptow (skrypt powtorzy ostatnia wartosc)")

    prompt_paths = []
    for p in spec.prompt_files:
        try:
            resolved = resolve_within(root, p)
        except UnsafePath as exc:
            raise H3ValidationError(f"prompt poza projektem: {p} ({exc})")
        if not resolved.is_file():
            raise H3ValidationError(f"brak pliku promptu: {p}")
        prompt_paths.append(p)

    for d in spec.durs:
        if not (0 < float(d) <= MAX_DURATION_S):
            raise H3ValidationError(f"dlugosc {d} s poza zakresem (0; {MAX_DURATION_S}]")
        if not _grid_ok(float(d)):
            warnings.append(f"dlugosc {d} s nie jest w siatce 17n+5 klatek przy 24 fps (zaokragli H3)")

    for name in list(spec.refs) + [x for x in (spec.cont, spec.ctrl) if x]:
        try:
            safe_name(name)
        except UnsafePath as exc:
            raise H3ValidationError(str(exc))
    if spec.ctrl_strength is not None and not (0 <= spec.ctrl_strength <= 10):
        raise H3ValidationError("ctrl_strength poza zakresem 0..10")

    env = {}
    if spec.refs:
        env["REFS"] = ",".join(spec.refs)
    if spec.cont:
        env["CONT"] = spec.cont
    if spec.fullres:
        env["FULLRES"] = "1"
    if spec.durs:
        env["DURS"] = ",".join(str(float(x)) for x in spec.durs)
    env["RUNMODE"] = spec.runmode
    if spec.validated:
        env["VALIDATED"] = str(int(spec.validated))
    if spec.ctrl:
        env["CTRL"] = spec.ctrl
    if spec.ctrl_frames is not None:
        env["CTRL_FRAMES"] = str(int(spec.ctrl_frames))
    if spec.ctrl_strength is not None:
        env["CTRL_STRENGTH"] = str(float(spec.ctrl_strength))
    assert set(env) <= ALLOWED_ENV, "nieobslugiwana zmienna srodowiskowa"

    media = {"videos": list(spec.ref_videos), "audios": list(spec.ref_audios)}
    if media["videos"] or media["audios"]:
        warnings.append("referencje wideo/audio sa zapisane w zadaniu, ale NIE sa jeszcze podlaczone do wykonania "
                        "(produkcyjny skrypt nie ma tego wejscia w znanym interfejsie)")
    argv = ["python3", "-u", SCRIPT_REL, "1" if spec.refine else "0", spec.prefix, str(int(spec.seed))] + list(prompt_paths)
    return {"cwd": str(root), "argv": argv, "env": env, "script": SCRIPT_REL,
            "expected_output": f"~/ComfyUI/output/{spec.prefix.replace('/', '_')}.mp4",
            "media_refs": media, "warnings": warnings, "errors": errors}
