import json
import os

import pytest

from psychodelic.fsio import atomic_write_json, atomic_write_text


def test_atomic_write_creates_file_without_leftovers(tmp_path):
    target = tmp_path / "sub" / "plik.txt"
    atomic_write_text(target, "tekst")
    assert target.read_text(encoding="utf-8") == "tekst"
    assert [p.name for p in target.parent.iterdir()] == ["plik.txt"]


def test_no_overwrite_flag_protects_existing(tmp_path):
    target = tmp_path / "artefakt.json"
    atomic_write_json(target, {"v": 1})
    with pytest.raises(FileExistsError):
        atomic_write_json(target, {"v": 2}, overwrite=False)
    assert json.loads(target.read_text(encoding="utf-8")) == {"v": 1}


def test_failed_write_leaves_no_tmp_file(tmp_path, monkeypatch):
    target = tmp_path / "x.txt"

    def boom(*a, **k):
        raise OSError("symulowana awaria")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        atomic_write_text(target, "dane")
    assert not target.exists()
    assert [p for p in tmp_path.iterdir() if p.name.startswith(".tmp-")] == []
