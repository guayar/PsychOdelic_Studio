import pytest

from psy_extender.command import build, frames_for
from psy_extender.post import ffmpeg_command, lms_command
from psy_extender.tree import DEFAULTS, MAX_REFS, Tree, TreeError


@pytest.fixture()
def tree(tmp_path):
    t = Tree(tmp_path / "chain.json")
    t.add("root", sid="r")
    t.add("s2", parent="r", sid="s2")
    t.add("s3", parent="s2", sid="s3")
    return t


def test_refs_are_inherited_in_order(tree):
    tree.add_ref("r", "gardener.png")
    tree.add_ref("s2", "hall.png")
    tree.add_ref("s3", "thistle.png")
    assert tree.effective_refs("s3") == ["gardener.png", "hall.png", "thistle.png"]
    assert tree.effective_refs("r") == ["gardener.png"]  # rodzic nie widzi dzieci


def test_ref_limit_is_enforced(tree):
    for i in range(MAX_REFS):
        tree.add_ref("r", f"r{i}.png")
    with pytest.raises(TreeError):
        tree.add_ref("s3", "too_many.png")


def test_settings_inherit_and_override(tree):
    tree.set_setting("r", "sharpen.enabled", True)
    tree.set_setting("s2", "sharpen.amount", 0.5)
    cfg = tree.effective_settings("s3")
    assert cfg["sharpen"] == {"enabled": True, "amount": 0.5}
    assert tree.effective_settings("r")["sharpen"]["amount"] == DEFAULTS["sharpen"]["amount"]


def test_only_one_root_and_unknown_parent_refused(tmp_path):
    t = Tree(tmp_path / "c.json")
    t.add("a", sid="a")
    with pytest.raises(TreeError):
        t.add("b", sid="b")
    with pytest.raises(TreeError):
        t.add("c", parent="nope", sid="c")


def test_tree_persists_to_disk(tmp_path):
    t = Tree(tmp_path / "c.json"); t.add("a", sid="a"); t.add_ref("a", "x.png")
    again = Tree(tmp_path / "c.json")
    assert again.effective_refs("a") == ["x.png"]


def test_command_uses_parent_output_as_cont_and_env_whitelist(tree):
    tree.add_ref("r", "gardener.png")
    tree.scene("r")["output"] = "r_out.mp4"
    tree.set_setting("s2", "controlnet", {"enabled": True, "ctrl": "ctrl.png", "frames": 24, "strength": 1.5})
    plan = build(tree, "s2", prefix="ext/s2", oug_dir="/tmp/oug")
    assert plan["argv"][:3] == ["python3", "-u", "_docs/gen_extender_refine.py"]
    assert plan["env"]["CONT"] == "r_out.mp4" and plan["env"]["REFS"] == "gardener.png"
    assert plan["env"]["CTRL"] == "ctrl.png" and plan["env"]["CTRL_FRAMES"] == "24"
    assert set(plan["env"]) <= {"REFS", "CONT", "FULLRES", "DURS", "RUNMODE", "VALIDATED", "CTRL", "CTRL_FRAMES", "CTRL_STRENGTH"}


def test_frames_grid():
    assert frames_for(5) == 124 and frames_for(10) == 243 and frames_for(7.5) == 175


def test_ffmpeg_post_only_when_enabled(tree):
    assert ffmpeg_command("a.mp4", "b.mp4", tree.effective_settings("r")) is None
    tree.set_setting("r", "sharpen.enabled", True)
    cmd = ffmpeg_command("a.mp4", "b.mp4", tree.effective_settings("r"))
    assert cmd[0] == "ffmpeg" and "unsharp" in cmd[cmd.index("-vf") + 1]


def test_lms_needs_switch_and_command(tree):
    assert lms_command("a.png", "b.png", tree.effective_settings("r")) is None
    tree.set_setting("r", "lms", {"enabled": True, "command": "python3 lms.py {in} {out}"})
    assert lms_command("a.png", "b.png", tree.effective_settings("r")) == ["python3", "lms.py", "a.png", "b.png"]
