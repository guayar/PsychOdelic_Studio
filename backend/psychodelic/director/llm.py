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
