"""Drzewo scen. Kazda scena dziedziczy od rodzica: postacie (referencje) i ustawienia. Zapis atomowy do JSON."""
import json
import os
import tempfile
import uuid
from pathlib import Path

MAX_REFS = 9
MEDIA_LIMITS = {"video": 3, "audio": 3}   # limity H3 wg kodu tritant
DEFAULTS = {
    "fullres": True,              # 1344x768
    "width": 1344,
    "height": 768,
    "durs": [7.5],                # sekundy na segment (17n+5 klatek przy 24 fps)
    "refine": False,
    "runmode": "full_batch",
    "validated": 0,
    "sharpen": {"enabled": False, "amount": 0.8},        # unsharp w ffmpeg
    "color": {"enabled": False, "brightness": 0.0, "contrast": 1.0, "saturation": 1.0, "gamma": 1.0},
    "lms": {"enabled": False, "command": ""},            # wlasna komenda (szablon z {in} {out}); pusta = wylaczone
    "controlnet": {"enabled": False, "ctrl": "", "frames": None, "strength": None},
}


class TreeError(ValueError):
    pass


def _merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


class Tree:
    def __init__(self, path):
        self.path = Path(path)
        self.data = {"schema": 1, "scenes": {}, "root": None, "settings": {}}
        if self.path.is_file():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".chain-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp, self.path)

    # --- drzewo
    def scene(self, sid):
        if sid not in self.data["scenes"]:
            raise TreeError(f"brak sceny: {sid}")
        return self.data["scenes"][sid]

    def add(self, title, parent=None, prompt="", sid=None):
        sid = sid or uuid.uuid4().hex[:8]
        if sid in self.data["scenes"]:
            raise TreeError(f"scena {sid} juz istnieje")
        if parent is None:
            if self.data["root"] is not None:
                raise TreeError("drzewo ma juz korzen; podaj --parent")
            self.data["root"] = sid
        else:
            self.scene(parent)
        self.data["scenes"][sid] = {"id": sid, "title": title, "parent": parent, "prompt": prompt,
                                    "seed": 1234, "own_refs": [], "own_media": {"video": [], "audio": []}, "own_settings": {}, "output": None}
        self.save()
        return sid

    def children(self, sid):
        return [s for s in self.data["scenes"].values() if s["parent"] == sid]

    def ancestors(self, sid):
        """Lancuch od korzenia do sceny (wlacznie)."""
        chain, cur = [], sid
        while cur is not None:
            s = self.scene(cur)
            chain.append(s)
            cur = s["parent"]
        return list(reversed(chain))

    # --- dziedziczenie
    def effective_refs(self, sid):
        """Postacie: najpierw od przodkow (kolejnosc root->scena), bez powtorzen. Limit 9."""
        refs = []
        for s in self.ancestors(sid):
            for r in s["own_refs"]:
                if r not in refs:
                    refs.append(r)
        if len(refs) > MAX_REFS:
            raise TreeError(f"scena {sid}: {len(refs)} referencji, limit to {MAX_REFS}")
        return refs

    def effective_media(self, sid):
        """Wideo i audio dziedziczone jak postacie. Limity: 3 wideo, 3 audio."""
        out = {"video": [], "audio": []}
        for s in self.ancestors(sid):
            for kind in out:
                for name in s.get("own_media", {}).get(kind, []):
                    if name not in out[kind]:
                        out[kind].append(name)
        for kind, lim in MEDIA_LIMITS.items():
            if len(out[kind]) > lim:
                raise TreeError(f"scena {sid}: {len(out[kind])} referencji {kind}, limit {lim}")
        return out

    def add_media(self, sid, kind, name):
        if kind not in MEDIA_LIMITS:
            raise TreeError("rodzaj: video albo audio (obrazy idą przez add_ref)")
        s = self.scene(sid)
        s.setdefault("own_media", {"video": [], "audio": []}).setdefault(kind, [])
        if name not in s["own_media"][kind]:
            s["own_media"][kind].append(name)
        self.effective_media(sid)  # sprawdza limit
        self.save()

    def remove_media(self, sid, kind, name):
        s = self.scene(sid)
        s.setdefault("own_media", {"video": [], "audio": []})[kind] = [x for x in s["own_media"].get(kind, []) if x != name]
        self.save()

    def effective_settings(self, sid):
        """Ustawienia: DEFAULTS <- ustawienia calego drzewa <- przodkowie <- ta scena."""
        cfg = _merge(DEFAULTS, self.data.get("settings", {}))
        for s in self.ancestors(sid):
            cfg = _merge(cfg, s["own_settings"])
        return cfg

    # --- edycja
    def add_ref(self, sid, name):
        s = self.scene(sid)
        if name not in s["own_refs"]:
            s["own_refs"].append(name)
        self.effective_refs(sid)  # sprawdza limit
        self.save()

    def remove_ref(self, sid, name):
        s = self.scene(sid)
        s["own_refs"] = [r for r in s["own_refs"] if r != name]
        self.save()

    def set_setting(self, sid, path, value):
        """path np. 'sharpen.amount'. Zapisuje w ustawieniach sceny."""
        s = self.scene(sid)
        node = s["own_settings"]
        keys = path.split(".")
        for k in keys[:-1]:
            node = node.setdefault(k, {})
        node[keys[-1]] = value
        self.save()
