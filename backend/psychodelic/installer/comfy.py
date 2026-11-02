"""Wykrywanie ComfyUI i planowanie kopiowania workflow. Wszystko odwracalne; bez sieci."""
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from ..workflows.profiles import PROFILES, check_profile, summary

WORKFLOW_SUBDIR = Path("user", "default", "workflows")

# Skad wziac brakujacy custom node (repozytoria z remote'ow uzytkownika; wbudowane wezly maja wpis "core").
NODE_SOURCES = {
    "MiniMaxH3Extender": {"repo": "https://github.com/tritant/ComfyUI_MiniMax_H3_Extender", "how": "custom node (ComfyUI Manager: wyszukaj 'MiniMax H3 Extender' lub git clone)"},
    "LTXAVTextEncoderLoader": {"repo": "https://github.com/Lightricks/ComfyUI-LTXVideo", "how": "custom node (ComfyUI Manager: 'LTXVideo')"},
    "MiniMaxH3ReferenceToVideo": {"repo": None, "how": "wbudowany w ComfyUI (nowsza wersja z nodes_minimax_h3); jesli brak, zaktualizuj ComfyUI"},
    "MiniMaxH3FunControlNetApply": {"repo": None, "how": "wbudowany w ComfyUI (nodes_minimax_h3); jesli brak, zaktualizuj ComfyUI"},
}
# Gdzie wrzucic brakujacy plik wagi (folder w models/ ComfyUI). Zrodlo pobrania: Hugging Face, wskazane w materialach projektu.
MODEL_FOLDERS = {
    "UNETLoader": "models/diffusion_models",
    "CLIPLoader": "models/text_encoders",
    "VAELoader": "models/vae",
    "LoraLoaderModelOnly": "models/loras",
    "ModelPatchLoader": "models/model_patches",
}
WEIGHTS_HUB = "https://huggingface.co/Comfy-Org/MiniMax-H3"


def detect_comfy(candidates):
    """Zwraca pierwszy katalog, ktory wyglada jak ComfyUI (main.py + custom_nodes), albo None."""
    for c in candidates:
        p = Path(c).expanduser()
        if (p / "main.py").is_file() and (p / "custom_nodes").is_dir():
            return p.resolve()
    return None


def workflows_dir(comfy):
    return Path(comfy) / WORKFLOW_SUBDIR


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def plan_workflows(comfy, source_dir):
    """Dla kazdego *.json z source_dir: copy | skip (identyczny) | conflict (zapis jako *.studio.json)."""
    target = workflows_dir(comfy)
    actions = []
    for src in sorted(Path(source_dir).glob("*.json")):
        dst = target / src.name
        if not dst.exists():
            actions.append({"file": src.name, "action": "copy", "src": str(src), "dst": str(dst)})
        elif _sha(dst) == _sha(src):
            actions.append({"file": src.name, "action": "skip", "src": str(src), "dst": str(dst)})
        else:
            alt = target / (src.stem + ".studio.json")
            actions.append({"file": src.name, "action": "conflict", "src": str(src), "dst": str(alt),
                            "note": f"istnieje inny plik {src.name}; zapisuję jako {alt.name}, nic nie nadpisuję"})
    return actions


def apply_workflows(actions):
    """Wykonuje plan. Kopiuje przez plik tymczasowy; nie kasuje niczego."""
    done = []
    for a in actions:
        if a["action"] not in ("copy", "conflict"):
            continue
        dst = Path(a["dst"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            raise FileExistsError(f"nie nadpisuję: {dst}")
        tmp = dst.with_suffix(dst.suffix + ".part")
        shutil.copyfile(a["src"], tmp)
        json.loads(tmp.read_text(encoding="utf-8"))  # sprawdz, ze to poprawny JSON zanim udostepnimy
        tmp.replace(dst)
        done.append(str(dst))
    return done


def missing_report(object_info, profile_names):
    """Lista brakow dla wybranych profili, z instrukcja: co, skad, gdzie. Folder bierzemy z wejscia profilu."""
    report = []
    for name in profile_names:
        prof = PROFILES[name]
        for it in check_profile(name, object_info):
            if it["status"] == "FOUND":
                continue
            entry = {"profile": name, "title": prof["title"], "kind": it["kind"], "name": it["name"]}
            if it["kind"] == "node":
                src = NODE_SOURCES.get(it["name"], {"repo": None, "how": "sprawdź źródło w materiałach projektu"})
                entry.update({"how": src["how"], "repo": src["repo"]})
            else:
                node, _inp, _fname, _src = next(f for f in prof["files"] if f[2] == it["name"])
                folder = MODEL_FOLDERS.get(node, "models")
                entry.update({"how": f"pobierz samodzielnie (wagi nie są pobierane przez studio) i umieść w ComfyUI/{folder}/",
                              "folder": folder, "hub": WEIGHTS_HUB})
            report.append(entry)
    return report


def write_report(path, data):
    data = dict(data, created_at=datetime.now().isoformat(timespec="seconds"))
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
