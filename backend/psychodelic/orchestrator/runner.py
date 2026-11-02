"""Uruchamianie komend produkcyjnych: bez powloki (shell=False), z limitem czasu, logiem i anulowaniem.

Zasada bezpieczenstwa: Runner wykonuje WYLACZNIE komendy zbudowane przez adaptery i tylko gdy
`allow_render=True` (domyslnie False). W tej wersji aplikacji uzytkownik nie ma zgody na render
na GPU, wiec domyslna sciezka to tylko `dry_run` (uruchamia skrypt-atrape wskazany jawnie w testach).
"""
import os
import subprocess
from pathlib import Path


class RenderNotAllowed(RuntimeError):
    pass


def run_command(command: dict, log_path, timeout_s=3600, allow_render=False, dry_run=True, extra_env=None):
    """dry_run=True (domyslnie): NIC nie jest uruchamiane, zwracamy tylko to, co zostaloby wykonane."""
    if dry_run:
        return {"returncode": None, "status": "DRY_RUN", "argv": command["argv"], "env": command.get("env", {})}
    if not allow_render:
        raise RenderNotAllowed("render wylaczony: ustaw jawna zgode (PSYCHODELIC_ALLOW_RENDER=1) i uruchom bez dry_run")
    env = dict(os.environ)
    env.update(command.get("env", {}))
    if extra_env:
        env.update(extra_env)
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as log:
        proc = subprocess.Popen(command["argv"], cwd=command["cwd"], env=env, stdout=log,
                                stderr=subprocess.STDOUT, shell=False)
        try:
            rc = proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            return {"returncode": None, "status": "TIMEOUT", "log": str(log_path)}
    return {"returncode": rc, "status": "OK" if rc == 0 else "FAILED", "log": str(log_path)}
