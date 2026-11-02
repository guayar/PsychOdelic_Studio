import os

import pytest

from psychodelic.security import UnsafePath, is_within, resolve_within, safe_name


@pytest.mark.parametrize("bad", ["../x", "a/b", "/abs", ".ukryty", "", "x" * 200, "zla\x00nazwa", "a..b/c"])
def test_safe_name_rejects(bad):
    with pytest.raises(UnsafePath):
        safe_name(bad)


def test_safe_name_accepts():
    assert safe_name("set plate_01.png") == "set plate_01.png"


def test_resolve_within_accepts_nested(tmp_path):
    (tmp_path / "a").mkdir()
    p = resolve_within(tmp_path, "a/plik.png")
    assert p == (tmp_path / "a" / "plik.png").resolve()


@pytest.mark.parametrize("rel", ["/etc/passwd", "../poza.png", "a/../../poza.png"])
def test_resolve_within_rejects_escape(tmp_path, rel):
    with pytest.raises(UnsafePath):
        resolve_within(tmp_path, rel)


def test_resolve_within_rejects_symlink_escape(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "root"
    root.mkdir()
    os.symlink(outside, root / "link")
    with pytest.raises(UnsafePath):
        resolve_within(root, "link/tajne.txt")
    assert not is_within(root, outside)
