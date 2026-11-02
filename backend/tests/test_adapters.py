import pytest

from psychodelic.adapters import h3, ltx


@pytest.fixture()
def root(tmp_path):
    (tmp_path / "ext_test").mkdir()
    (tmp_path / "ext_test" / "s1.txt").write_text("Positive prompt.", encoding="utf-8")
    (tmp_path / "ext_test" / "s2.txt").write_text("Second.", encoding="utf-8")
    return tmp_path


def spec(root, **kw):
    base = dict(project_root=str(root), prefix="shots/v3b_1", seed=1234, prompt_files=["ext_test/s1.txt"])
    base.update(kw)
    return h3.ExtenderSpec(**base)


def test_h3_argv_matches_production_usage(root):
    cmd = h3.build_command(spec(root, refs=["ref_gsheet2.png"], durs=[7.5], cont="ref_v3a_2.mp4"))
    assert cmd["argv"] == ["python3", "-u", "_docs/gen_extender_refine.py", "0", "shots/v3b_1", "1234",
                           "ext_test/s1.txt"]
    assert cmd["env"]["REFS"] == "ref_gsheet2.png"
    assert cmd["env"]["CONT"] == "ref_v3a_2.mp4"
    assert cmd["env"]["DURS"] == "7.5"
    assert cmd["env"]["FULLRES"] == "1"
    assert cmd["cwd"] == str(root)


def test_h3_refine_flag_and_no_shell(root):
    cmd = h3.build_command(spec(root, refine=True))
    assert cmd["argv"][3] == "1"
    assert all(isinstance(a, str) for a in cmd["argv"])


@pytest.mark.parametrize("bad_prefix", ["../x", "shots/a b", "/abs", "shots/" + "a" * 70])
def test_h3_prefix_rejected(root, bad_prefix):
    with pytest.raises(h3.H3ValidationError):
        h3.build_command(spec(root, prefix=bad_prefix))


def test_h3_prompt_outside_project_rejected(root):
    with pytest.raises(h3.H3ValidationError):
        h3.build_command(spec(root, prompt_files=["../secret.txt"]))


def test_h3_missing_prompt_rejected(root):
    with pytest.raises(h3.H3ValidationError):
        h3.build_command(spec(root, prompt_files=["ext_test/nope.txt"]))


def test_h3_max_nine_refs(root):
    with pytest.raises(h3.H3ValidationError):
        h3.build_command(spec(root, refs=[f"r{i}.png" for i in range(10)]))
    h3.build_command(spec(root, refs=[f"r{i}.png" for i in range(9)]))


def test_h3_duration_limits_and_grid_warning(root):
    with pytest.raises(h3.H3ValidationError):
        h3.build_command(spec(root, durs=[20.0]))
    cmd = h3.build_command(spec(root, durs=[7.5]))  # 7.5 s = 180 kl., nie 17n+5 -> ostrzezenie
    assert any("17n+5" in w for w in cmd["warnings"])


def test_h3_bad_unsafe_names_rejected(root):
    with pytest.raises(h3.H3ValidationError):
        h3.build_command(spec(root, cont="../../etc/passwd"))


def test_ltx_argv(root):
    (root / "lip").mkdir()
    (root / "lip" / "p.txt").write_text("x", encoding="utf-8")
    cmd = ltx.build_command(ltx.LtxSpec(project_root=str(root), tail="ref_tail.mp4", tail_frames=24,
                                        audio="ref_lip.wav", audio_frames=141, prompt_file="lip/p.txt",
                                        seed=282, prefix="shots/lip_r1"))
    assert cmd["argv"][:3] == ["python3", "-u", "_docs/gen_ltx_lip.py"]
    assert "--audio_frames" in cmd["argv"] and "141" in cmd["argv"]
    assert "--prompt_file" in cmd["argv"] and "lip/p.txt" in cmd["argv"]


def test_ltx_prompt_outside_rejected(root):
    with pytest.raises(h3.H3ValidationError):
        ltx.build_command(ltx.LtxSpec(project_root=str(root), tail="a.mp4", tail_frames=24, audio="a.wav",
                                      audio_frames=10, prompt_file="../x", seed=1, prefix="shots/x"))
