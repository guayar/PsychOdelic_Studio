"""CLI instalatora: python -m psychodelic.installer --comfy DIR [--object-info FILE] [--yes] [--dry-run]

Bez --yes pyta przed kazdym kopiowaniem. Zapisuje raport JSON (install_report.json) obok studia.
"""
import argparse
import json
import sys
from pathlib import Path

from .comfy import (MODEL_FOLDERS, apply_workflows, detect_comfy, missing_report, plan_workflows,
                    write_report, workflows_dir)

STUDIO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS_SRC = STUDIO_ROOT / "studio_workflows"
PROFILE_NAMES = ["h3_extender", "h3_controlnet"]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Instalator PsychOdelic Studio: workflowy + raport brakow (bez wag).")
    ap.add_argument("--comfy", help="katalog ComfyUI (np. ~/ComfyUI)")
    ap.add_argument("--object-info", help="zapisany plik object_info.json z ComfyUI (zamiast serwera)")
    ap.add_argument("--yes", action="store_true", help="nie pytaj o kopiowanie")
    ap.add_argument("--dry-run", action="store_true", help="tylko pokaz plan")
    ap.add_argument("--ltx-workflow", help="plik workflow LTX z produkcji (np. oug_ltx_director_api.json); kopiowany bez zmian")
    ap.add_argument("--report", default=str(STUDIO_ROOT / "install_report.json"))
    args = ap.parse_args(argv)

    comfy = detect_comfy([args.comfy] if args.comfy else [])
    if comfy is None:
        comfy = detect_comfy([str(Path.home() / "ComfyUI"), str(Path.home() / "comfyui")])
    if comfy is None:
        print("NIE ZNALEZIONO ComfyUI. Podaj katalog: --comfy ~/ComfyUI (musi zawierac main.py i custom_nodes/).")
        return 2
    print(f"ComfyUI: {comfy}")

    actions = plan_workflows(comfy, WORKFLOWS_SRC)
    if args.ltx_workflow:
        src = Path(args.ltx_workflow).expanduser()
        if not src.is_file():
            print(f"Brak pliku LTX: {src}")
            return 2
        import tempfile
        staged = Path(tempfile.mkdtemp(prefix="psy-ltx-"))
        (staged / src.name).write_bytes(src.read_bytes())
        actions += plan_workflows(comfy, staged)
    print("Workflowy studia:")
    for a in actions:
        print(f"  [{a['action']}] {a['file']} -> {a['dst']}" + (f"  ({a['note']})" if a.get("note") else ""))

    if args.dry_run:
        print("(dry-run: nic nie zapisano)")
        done = []
    else:
        pending = [a for a in actions if a["action"] in ("copy", "conflict")]
        if pending and not args.yes:
            if input(f"Skopiować {len(pending)} plik(ów) do {workflows_dir(comfy)}? [t/N] ").strip().lower() not in ("t", "tak", "y", "yes"):
                print("Anulowano kopiowanie.")
                pending = []
        done = apply_workflows(pending) if pending else []
        print(f"Skopiowano: {len(done)}")

    info = None
    if args.object_info:
        info = json.loads(Path(args.object_info).read_text(encoding="utf-8"))
    else:
        import urllib.request
        try:
            with urllib.request.urlopen("http://127.0.0.1:8188/object_info", timeout=5) as resp:
                info = json.load(resp)
        except OSError:
            print("Serwer ComfyUI nie odpowiada: nie sprawdzam nodów (podaj --object-info, aby sprawdzić offline).")

    missing = missing_report(info, PROFILE_NAMES) if info is not None else None
    if missing is not None:
        print(f"\nDo dociągnięcia ręcznie ({len(missing)}):")
        for m in missing:
            print(f"  - [{m['kind']}] {m['name']}  ({m['title']})")
            print(f"      jak: {m['how']}")
            if m.get("repo"):
                print(f"      repo: {m['repo']}")
            if m.get("folder"):
                print(f"      folder: ComfyUI/{m['folder']}/   (źródło: {m['hub']})")
    write_report(args.report, {"comfy": str(comfy), "copied": done, "plan": actions, "missing": missing,
                               "weights_downloaded": False, "nodes_installed": False})
    print(f"\nRaport: {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
