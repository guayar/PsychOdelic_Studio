"""Bezpieczenstwo sciezek: zadna sciezka z danych ( ani z promptu LLM) nie wychodzi poza wskazany root."""
import os
import re
from pathlib import Path

SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-. ]{0,127}$")


class UnsafePath(ValueError):
    pass


def safe_name(name):
    """Nazwa pliku/projektu: bez separatorow, bez '..', bez ukrytych plikow, ograniczona dlugosc."""
    if not isinstance(name, str) or not SAFE_NAME.match(name) or ".." in name:
        raise UnsafePath(f"niedozwolona nazwa: {name!r}")
    return name


def resolve_within(root, relative):
    """Rozwiazuje relative pod root. Odrzuca: sciezke absolutna, '..', symlink wychodzacy poza root."""
    root = Path(root).resolve()
    rel = Path(relative)
    if rel.is_absolute():
        raise UnsafePath("sciezka absolutna niedozwolona")
    if any(part == ".." for part in rel.parts):
        raise UnsafePath("'..' niedozwolone")
    candidate = (root / rel)
    # realpath rozwiazuje symlinki na kazdym poziomie istniejacej czesci
    resolved = Path(os.path.realpath(candidate))
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise UnsafePath("sciezka wychodzi poza root (symlink?)") from exc
    return resolved


def is_within(root, path):
    try:
        Path(os.path.realpath(path)).relative_to(Path(os.path.realpath(root)))
        return True
    except ValueError:
        return False
