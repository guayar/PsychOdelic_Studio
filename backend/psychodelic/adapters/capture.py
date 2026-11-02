"""Przechwycenie grafu bez ComfyUI i bez GPU.

Uruchamia produkcyjny skrypt (np. `_docs/gen_extender_refine.py`) w podprocesie, w ktorym `urllib`
jest podmieniony tak, ze:
  * GET  .../object_info           -> zwraca zapisany wczesniej schemat (plik z ComfyUI),
  * POST .../prompt                -> ZAPISUJE graf do pliku i konczy proces (nic nie jest wysylane),
  * kazdy inny adres               -> BLOKOWANY (blad), wiec skrypt nie moze dotknac serwera.

Dzieki temu mozna porownac graf z adaptera z grafem, ktory generuje produkcyjny skrypt, na tej samej maszynie.
Status: POTWIERDZONE_TESTEM na skrypcie-atrapie. NIEZWERYFIKOWANE na prawdziwym skrypcie (wymaga pliku
object_info z Twojej maszyny).
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BOOT = r'''
import io, json, runpy, sys
import urllib.request as ur
OBJ, OUT, SCRIPT = sys.argv[1], sys.argv[2], sys.argv[3]
sys.argv = [SCRIPT] + sys.argv[4:]
class _Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False
def _url(req):
    return req if isinstance(req, str) else req.full_url
def fake_urlopen(req, timeout=None, **kw):
    url = _url(req)
    if url.endswith("/object_info"):
        return _Resp(open(OBJ, "rb").read())
    if "/object_info/" in url:
        full = json.load(open(OBJ, encoding="utf-8"))
        node = url.rsplit("/", 1)[1]
        return _Resp(json.dumps({node: full[node]}).encode("utf-8"))
    if url.endswith("/prompt") and not isinstance(req, str):
        with open(OUT, "wb") as fh:
            fh.write(req.data)
        print("CAPTURED", flush=True)
        raise SystemExit(0)
    raise RuntimeError("BLOCKED: " + url)
ur.urlopen = fake_urlopen
runpy.run_path(SCRIPT, run_name="__main__")
'''


def capture(command: dict, object_info_path, out_path, timeout_s=120):
    """command = wynik adapters.h3/ltx.build_command. Zwraca {status, graph_path|error}."""
    out = Path(out_path)
    if out.exists():
        out.unlink()  # nie nadpisujemy po cichu starego wyniku
    env = dict(os.environ)
    env.update(command.get("env", {}))
    script = str(Path(command["cwd"]) / command["script"])
    argv = command["argv"][3:]  # po "python3 -u <script>"
    proc = subprocess.run([sys.executable, "-c", BOOT, str(object_info_path), str(out), script] + argv,
                          cwd=command["cwd"], env=env, capture_output=True, text=True, timeout=timeout_s)
    if out.is_file():
        graph = json.loads(out.read_text(encoding="utf-8"))
        return {"status": "CAPTURED", "graph_path": str(out), "nodes": len(graph.get("prompt", {})),
                "stdout_tail": proc.stdout[-500:]}
    return {"status": "NOT_CAPTURED", "returncode": proc.returncode, "stderr_tail": proc.stderr[-800:]}


def summarize(graph_path):
    """Skrot grafu do porownania: klasy wezlow i ich liczba (bez calych promptow)."""
    prompt = json.loads(Path(graph_path).read_text(encoding="utf-8"))["prompt"]
    counts = {}
    for node in prompt.values():
        counts[node["class_type"]] = counts.get(node["class_type"], 0) + 1
    return {"nodes": len(prompt), "classes": dict(sorted(counts.items()))}


def main():
    import argparse
    from .h3 import ExtenderSpec, build_command
    ap = argparse.ArgumentParser(description="Dry-run: adapter H3 -> produkcyjny skrypt -> przechwycony graf (bez ComfyUI).")
    ap.add_argument("--object-info", required=True, help="plik object_info.json zapisany z ComfyUI")
    ap.add_argument("--spec", required=True, help="JSON z parametrami ExtenderSpec (project_root, prefix, seed, prompt_files, ...)")
    ap.add_argument("--out", required=True, help="plik wyjsciowy z grafem")
    args = ap.parse_args()
    spec_data = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    cmd = build_command(ExtenderSpec(**spec_data))
    res = capture(cmd, args.object_info, args.out)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    if res["status"] == "CAPTURED":
        print(json.dumps(summarize(args.out), ensure_ascii=False, indent=2))
    return 0 if res["status"] == "CAPTURED" else 1


if __name__ == "__main__":
    sys.exit(main())
