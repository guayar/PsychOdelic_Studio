"""Konsola: drzewo scen, ustawienia, komenda i uruchomienie. Domyslnie tylko pokazuje komende (--execute uruchamia)."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from .command import build
from .tree import Tree, TreeError

HERE = Path(__file__).resolve().parents[1]


def _val(text):
    try:
        return json.loads(text)
    except ValueError:
        return text


def main(argv=None):
    ap = argparse.ArgumentParser(prog="psy-extender")
    ap.add_argument("--chain", default=str(HERE / "chain.json"), help="plik drzewa scen")
    ap.add_argument("--oug", default="", help="katalog OUG z _docs/gen_extender_refine.py")
    ap.add_argument("--comfy-input", default=str(Path.home() / "ComfyUI" / "input"))
    ap.add_argument("--comfy-output", default=str(Path.home() / "ComfyUI" / "output"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="dodaj scene (bez --parent = korzen)")
    a.add_argument("title"); a.add_argument("--parent"); a.add_argument("--prompt", default=""); a.add_argument("--id")
    sub.add_parser("tree", help="pokaz drzewo")
    s = sub.add_parser("show", help="pokaz scene z dziedziczeniem"); s.add_argument("id")
    r = sub.add_parser("ref", help="postacie sceny"); r.add_argument("id"); r.add_argument("action", choices=["add", "remove"]); r.add_argument("name")
    st = sub.add_parser("set", help="ustawienie sceny, np. set ID sharpen.amount 0.6"); st.add_argument("id"); st.add_argument("path"); st.add_argument("value")
    sg = sub.add_parser("settings", help="ustawienia calego drzewa (root)"); sg.add_argument("path"); sg.add_argument("value")
    rn = sub.add_parser("run", help="komenda sceny; --execute uruchamia extender")
    rn.add_argument("id"); rn.add_argument("--execute", action="store_true"); rn.add_argument("--prefix", default="")
    args = ap.parse_args(argv)
    tree = Tree(args.chain)
    try:
        if args.cmd == "add":
            sid = tree.add(args.title, parent=args.parent, prompt=args.prompt, sid=args.id)
            print(sid)
        elif args.cmd == "tree":
            def walk(sid, depth):
                sc = tree.scene(sid)
                print("  " * depth + f"{sid}  {sc['title']}  [postacie: {len(tree.effective_refs(sid))}]")
                for c in tree.children(sid):
                    walk(c["id"], depth + 1)
            if tree.data["root"]:
                walk(tree.data["root"], 0)
        elif args.cmd == "show":
            print(json.dumps({"scene": tree.scene(args.id), "refs": tree.effective_refs(args.id),
                              "settings": tree.effective_settings(args.id)}, ensure_ascii=False, indent=2))
        elif args.cmd == "ref":
            tree.add_ref(args.id, args.name) if args.action == "add" else tree.remove_ref(args.id, args.name)
            print(tree.effective_refs(args.id))
        elif args.cmd == "set":
            tree.set_setting(args.id, args.path, _val(args.value))
        elif args.cmd == "settings":
            tree.data.setdefault("settings", {})
            node = tree.data["settings"]
            keys = args.path.split(".")
            for k in keys[:-1]:
                node = node.setdefault(k, {})
            node[keys[-1]] = _val(args.value)
            tree.save()
        elif args.cmd == "run":
            cmd_plan = build(tree, args.id, prefix=args.prefix or f"ext/{args.id}", oug_dir=args.oug or None)
            print(json.dumps(cmd_plan, ensure_ascii=False, indent=2))
            if not args.execute:
                print("\n(tylko podglad; dodaj --execute, zeby uruchomic)")
                return 0
            if not args.oug:
                print("brak --oug (katalog z gen_extender_refine.py)", file=sys.stderr); return 2
            env = {**os.environ, **cmd_plan["env"]}
            proc = subprocess.run(cmd_plan["argv"], cwd=args.oug, env=env, capture_output=True, text=True, check=False)
            print(proc.stdout[-2000:]); print(proc.stderr[-2000:], file=sys.stderr)
            if proc.returncode != 0:
                return proc.returncode
            return 0
    except TreeError as exc:
        print(f"blad: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
