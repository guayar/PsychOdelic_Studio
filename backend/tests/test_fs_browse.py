from pathlib import Path

from psychodelic.fs_browse import import_to_input, list_dir, resolve_file


def test_list_shows_media_and_dirs_only(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.png").write_bytes(b"x")
    (tmp_path / "notes.txt").write_text("x", encoding="utf-8")
    names = [e["name"] for e in list_dir(str(tmp_path))["entries"]]
    assert names == ["sub", "a.png"]


def test_relative_path_refused(tmp_path):
    import pytest
    with pytest.raises(ValueError):
        list_dir("relative/dir")


def test_import_copies_and_never_overwrites(tmp_path):
    src_dir, inp = tmp_path / "elsewhere", tmp_path / "input"
    src_dir.mkdir()
    (src_dir / "my ref.png").write_bytes(b"AAA")
    first = import_to_input(str(src_dir / "my ref.png"), inp)
    assert first == "my_ref.png" and (inp / first).read_bytes() == b"AAA"
    again = import_to_input(str(src_dir / "my ref.png"), inp)
    assert again == first  # ten sam plik: bez kopii
    (src_dir / "my ref.png").write_bytes(b"BBB")
    other = import_to_input(str(src_dir / "my ref.png"), inp)
    assert other == "my_ref_2.png" and (inp / first).read_bytes() == b"AAA"


def test_resolve_refuses_non_media(tmp_path):
    (tmp_path / "x.txt").write_text("x", encoding="utf-8")
    assert resolve_file(str(tmp_path / "x.txt")) is None
