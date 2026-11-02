"""Runtime modelu lokalnego (opcjonalny). Domyslnie NullRuntime: Director dziala regulami.

OllamaRuntime sprawdza tylko, czy serwer odpowiada (GET /api/tags). NIE laduje ani nie zwalnia modelu
(to wymaga zgody i testu na GPU). Status: NIEZWERYFIKOWANE, dopoki uzytkownik nie uruchomi Ollamy.
"""
import json
import urllib.error
import urllib.request


class NullRuntime:
    name = "manual"

    def status(self):
        return {"runtime": "manual", "status": "POTWIERDZONE_TESTEM", "detail": "planer regulowy, bez LLM"}


class OllamaRuntime:
    name = "ollama"

    def __init__(self, base_url="http://127.0.0.1:11434", timeout=2.0):
        if not base_url.startswith("http://127.0.0.1") and not base_url.startswith("http://localhost"):
            raise ValueError("LLM tylko lokalnie (127.0.0.1/localhost)")
        self.base_url = base_url
        self.timeout = timeout

    def status(self):
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=self.timeout) as resp:
                tags = json.load(resp).get("models", [])
            return {"runtime": "ollama", "status": "POTWIERDZONE_TESTEM", "models": [m.get("name") for m in tags]}
        except (urllib.error.URLError, OSError, ValueError) as exc:
            return {"runtime": "ollama", "status": "NIEDOSTEPNE_LUB_WYMAGA_ZMIANY",
                    "detail": f"brak odpowiedzi ({type(exc).__name__})"}


LOCAL_PREFIXES = ("http://127.0.0.1", "http://localhost")


def _local(base_url):
    if not base_url.startswith(LOCAL_PREFIXES):
        raise ValueError("LLM tylko lokalnie (127.0.0.1/localhost)")
    return base_url


def list_models(base_url="http://127.0.0.1:11434", timeout=2.0):
    """Nazwy modeli zainstalowanych w Ollamie (tylko odczyt). Rzuca OSError, gdy serwer nie odpowiada."""
    with urllib.request.urlopen(f"{_local(base_url)}/api/tags", timeout=timeout) as resp:
        return [m.get("name") for m in json.load(resp).get("models", []) if m.get("name")]


def generate(model, prompt, base_url="http://127.0.0.1:11434", timeout=300.0):
    """Jednorazowe generowanie tekstu w Ollamie. Model nie jest ladowany ani zwalniany poza tym wywolaniem."""
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(f"{_local(base_url)}/api/generate", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return str(json.load(resp).get("response", "")).strip()


def unload(model, base_url="http://127.0.0.1:11434", timeout=30.0):
    """Zwalnia model z VRAM w Ollamie (keep_alive=0). Model wraca przy nastepnym uzyciu."""
    body = json.dumps({"model": model, "keep_alive": 0}).encode("utf-8")
    req = urllib.request.Request(f"{_local(base_url)}/api/generate", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        resp.read()
