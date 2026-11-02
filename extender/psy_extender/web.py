"""Podglad drzewa scen: lista, dodawanie, usuwanie, ustawienia i generowanie segmentu. Tylko 127.0.0.1."""
import argparse
import os
import shutil
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from .command import build
from .tree import Tree, TreeError

HERE = Path(__file__).resolve().parents[1]


class SceneIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    parent: str | None = None
    prompt: str = ""


class SettingIn(BaseModel):
    path: str = Field(min_length=1, max_length=120)
    value: object


class RefIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class GenIn(BaseModel):
    execute: bool = False
    prefix: str = ""


def create_app(chain_path, oug_dir="", comfy_output=None, comfy_input=None):
    tree = Tree(chain_path)
    app = FastAPI(title="PsychOdelic Extender")
    comfy_output = Path(comfy_output or Path.home() / "ComfyUI" / "output")
    comfy_input = Path(comfy_input or Path.home() / "ComfyUI" / "input")

    def _err(exc):
        raise HTTPException(422, str(exc))

    def _scene(sid):
        try:
            tree.scene(sid)
        except TreeError:
            raise HTTPException(404, "brak sceny")

    def _descendants(sid):
        out = []
        for c in tree.children(sid):
            out.append(c["id"]); out.extend(_descendants(c["id"]))
        return out

    @app.get("/", response_class=HTMLResponse)
    def index():
        return (HERE / "web" / "index.html").read_text(encoding="utf-8")

    @app.get("/api/tree")
    def get_tree():
        scenes = []
        for sid, sc in tree.data["scenes"].items():
            try:
                refs = tree.effective_refs(sid)
                cfg = tree.effective_settings(sid)
            except TreeError as exc:
                refs, cfg = [], {"error": str(exc)}
            scenes.append({**sc, "effective_refs": refs, "settings": cfg,
                           "children": [c["id"] for c in tree.children(sid)]})
        return {"root": tree.data.get("root"), "scenes": scenes, "oug_dir": oug_dir}

    @app.post("/api/scenes", status_code=201)
    def add_scene(body: SceneIn):
        try:
            return {"id": tree.add(body.title, parent=body.parent, prompt=body.prompt)}
        except TreeError as exc:
            _err(exc)

    @app.delete("/api/scenes/{sid}")
    def delete_scene(sid: str, cascade: bool = False):
        _scene(sid)
        kids = _descendants(sid)
        if kids and not cascade:
            raise HTTPException(409, f"scena ma {len(kids)} scen potomnych; potwierdz usuniecie calej galezi")
        doomed = set(kids + [sid])
        for x in doomed:
            tree.data["scenes"].pop(x, None)
        if tree.data.get("root") in doomed:
            tree.data["root"] = None
        tree.save()
        return {"deleted": sorted(doomed)}

    @app.put("/api/scenes/{sid}/setting")
    def set_setting(sid: str, body: SettingIn):
        _scene(sid)
        try:
            tree.set_setting(sid, body.path, body.value)
        except TreeError as exc:
            _err(exc)
        return {"ok": True}

    @app.put("/api/scenes/{sid}/prompt")
    def set_prompt(sid: str, body: SceneIn):
        _scene(sid)
        tree.scene(sid)["prompt"] = body.prompt
        tree.scene(sid)["title"] = body.title
        tree.save()
        return {"ok": True}

    @app.post("/api/scenes/{sid}/refs")
    def add_ref(sid: str, body: RefIn):
        _scene(sid)
        try:
            tree.add_ref(sid, body.name)
        except TreeError as exc:
            _err(exc)
        return {"refs": tree.effective_refs(sid)}

    @app.delete("/api/scenes/{sid}/refs/{name}")
    def remove_ref(sid: str, name: str):
        _scene(sid)
        tree.remove_ref(sid, name)
        return {"refs": tree.effective_refs(sid)}

    @app.post("/api/scenes/{sid}/generate")
    def generate(sid: str, body: GenIn):
        _scene(sid)
        prefix = body.prefix or f"ext/{sid}"
        try:
            plan = build(tree, sid, prefix=prefix, oug_dir=oug_dir or None)
        except (TreeError, AssertionError) as exc:
            _err(exc)
        if not oug_dir:
            if body.execute:
                raise HTTPException(422, "brak katalogu OUG (uruchom z --oug)")
            return {"executed": False, "plan": plan}
        # prompt sceny trafia do pliku, ktorego oczekuje produkcyjny skrypt (tylko plik studia, nadpisywany)
        prompt_file = Path(oug_dir) / "_docs" / "studio_prompts" / f"{sid}.txt"
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text(tree.scene(sid).get("prompt", ""), encoding="utf-8")
        if not body.execute:
            return {"executed": False, "plan": plan, "prompt_file": str(prompt_file)}
        proc = subprocess.run(plan["argv"], cwd=oug_dir, env={**os.environ, **plan["env"]},
                              capture_output=True, text=True, check=False)
        log = (proc.stdout + "\n" + proc.stderr)[-4000:]
        if proc.returncode != 0:
            return {"executed": True, "ok": False, "returncode": proc.returncode, "log": log, "plan": plan}
        output = prefix.replace("/", "_") + ".mp4"
        # kontynuacja (CONT) czyta plik z ComfyUI/input: kopiujemy wynik tam (bez nadpisywania istniejacego)
        src = comfy_output / output
        if src.is_file():
            comfy_input.mkdir(parents=True, exist_ok=True)
            if not (comfy_input / output).exists():
                shutil.copy2(src, comfy_input / output)
        sc = tree.scene(sid)
        sc["output"] = output
        tree.save()
        return {"executed": True, "ok": True, "output": output, "log": log, "plan": plan}

    @app.get("/api/file")
    def file(name: str):
        target = (comfy_output / name).resolve()
        if comfy_output.resolve() not in target.parents or not target.is_file() or target.suffix.lower() not in {".mp4", ".png"}:
            raise HTTPException(404, "brak pliku wyjsciowego")
        return FileResponse(target)

    return app


if __name__ == "__main__":
    import uvicorn
    ap = argparse.ArgumentParser()
    ap.add_argument("--chain", default=str(HERE / "chain.json"))
    ap.add_argument("--oug", default="")
    ap.add_argument("--comfy-output", default=str(Path.home() / "ComfyUI" / "output"))
    ap.add_argument("--comfy-input", default=str(Path.home() / "ComfyUI" / "input"))
    ap.add_argument("--port", type=int, default=8790)
    a = ap.parse_args()
    uvicorn.run(create_app(a.chain, a.oug, a.comfy_output, a.comfy_input), host="127.0.0.1", port=a.port)
