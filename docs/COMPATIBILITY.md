# Zgodność (statusy: POTWIERDZONE_TESTEM / TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE / NIEDOSTEPNE_LUB_WYMAGA_ZMIANY)

Stan na 2026-11-02. Kolumna „gdzie sprawdzono” mówi, na jakiej maszynie.

| Element | Status | Gdzie sprawdzono | Uwagi |
|---|---|---|---|
| Python ≥ 3.11 (backend) | POTWIERDZONE_TESTEM | sesja w chmurze (3.13) | u Ciebie: sprawdź `python3 --version` |
| FastAPI 0.162, uvicorn, pytest | POTWIERDZONE_TESTEM | sesja w chmurze | wersje z venv sesji |
| SQLite (sqlite3 3.53) | POTWIERDZONE_TESTEM | sesja w chmurze | u Ciebie wersja może być inna |
| ffmpeg / ffprobe | POTWIERDZONE_TESTEM | sesja w chmurze | **nie na Twojej maszynie** |
| `rocm-smi` (odczyt VRAM) | NIEDOSTEPNE_LUB_WYMAGA_ZMIANY (w sesji) | sesja | u Ciebie: `collect_local_audit.sh` |
| Ubuntu 24.04.4 | NIEDOSTEPNE_LUB_WYMAGA_ZMIANY | — | nie mogę sprawdzić stąd |
| Radeon AI PRO R9700 (gfx1201) | TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE | — | potrzebny `rocminfo` u Ciebie |
| ROCm „10.1” | TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE | — | **wersja podejrzana**; zweryfikuj |
| ComfyUI (lokalne, wersja?) | NIEDOSTEPNE_LUB_WYMAGA_ZMIANY (w sesji) | — | serwer nie odpowiada; wersja z `system_stats` u Ciebie |
| Extender `MiniMaxH3Extender` (lokalnie 3.0.12) | TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE | — | upstream `main` 3.0.14 **[CODE]**; lokalnie nie porównane |
| Motion Context | TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE | — | |
| LTX (wersja i checkpoint) | NIEDOSTEPNE_LUB_WYMAGA_ZMIANY | — | nie wiadomo, która wersja |
| Skrypty OUG (`gen_extender_refine.py` itd.) | NIEDOSTEPNE_LUB_WYMAGA_ZMIANY | — | brak dostępu; nie znam argumentów |
| Frontend React/Vite | NIEDOSTEPNE_LUB_WYMAGA_ZMIANY | — | nie zbudowany w M1; npm rejestr dostępny (react 19.3.1) |
| Migracje SQLite (schemat v1) | POTWIERDZONE_TESTEM | sesja | 0001_init.sql |
| Maszyna stanów zadań (§ 9) | POTWIERDZONE_TESTEM | sesja | przejścia zgodne z promptem |
| Serwer uvicorn na 127.0.0.1 | POTWIERDZONE_TESTEM | sesja | smoke test: health, projekt, doctor |
| Render H3/LTX | NIEDOSTEPNE_LUB_WYMAGA_ZMIANY | — | **nie wykonano** (koszt, brak zgody) |
