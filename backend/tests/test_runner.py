import sys

import pytest

from psychodelic.orchestrator.runner import RenderNotAllowed, run_command


def make_cmd(tmp_path, script_body):
    script = tmp_path / "stub.py"
    script.write_text(script_body, encoding="utf-8")
    return {"cwd": str(tmp_path), "argv": [sys.executable, str(script)], "env": {"TEST_ENV": "1"}}


def test_render_blocked_without_consent(tmp_path):
    cmd = make_cmd(tmp_path, "print('x')")
    with pytest.raises(RenderNotAllowed):
        run_command(cmd, tmp_path / "log.txt", dry_run=False, allow_render=False)


def test_dry_run_default_does_not_execute(tmp_path):
    marker = tmp_path / "ran.txt"
    cmd = make_cmd(tmp_path, f"open(r'{marker}','w').write('x')")
    run_command(cmd, tmp_path / "log.txt")  # dry_run=True domyslnie: nic sie nie wykonuje
    assert not marker.exists()


def test_allowed_run_writes_log_and_env(tmp_path):
    cmd = make_cmd(tmp_path, "import os; print('ENV=' + os.environ.get('TEST_ENV',''))")
    res = run_command(cmd, tmp_path / "log.txt", dry_run=False, allow_render=True)
    assert res["status"] == "OK"
    assert "ENV=1" in (tmp_path / "log.txt").read_text(encoding="utf-8")


def test_failure_reported(tmp_path):
    cmd = make_cmd(tmp_path, "import sys; sys.exit(3)")
    res = run_command(cmd, tmp_path / "log.txt", dry_run=False, allow_render=True)
    assert res["status"] == "FAILED" and res["returncode"] == 3


def test_timeout_kills_process(tmp_path):
    cmd = make_cmd(tmp_path, "import time; time.sleep(30)")
    res = run_command(cmd, tmp_path / "log.txt", timeout_s=1, dry_run=False, allow_render=True)
    assert res["status"] == "TIMEOUT"
