# PsychOdelic Studio

Lokalne studio do teledysków (AI Director, adaptery H3/LTX, timeline). **Status: M0 częściowo, M1 fundament.** Szczegóły: [docs/STATUS.md](docs/STATUS.md).

## Zasady
- Studio jest uniwersalne: nie zakłada żadnego konkretnego projektu. Istniejące pipeline'y użytkownika (skrypty, workflowy) nie są zmieniane bez zgody.
- Aplikacja słucha tylko na `127.0.0.1`.
- Nie wykonuj `git push` do repo użytkownika bez zgody.
- Każda funkcja jest opisana jednym z trzech statusów: `POTWIERDZONE_TESTEM`, `TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE`, `NIEDOSTEPNE_LUB_WYMAGA_ZMIANY`.

## Uruchomienie (backend)
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest -q
PSYCHODELIC_DATA=~/psy-data python -m psychodelic
```
Endpointy: `GET /api/health`, `GET /api/doctor`, `GET/POST /api/projects`, `GET /api/projects/{id}`, `POST /api/jobs`, `GET /api/jobs/{id}`.

## Instalacja (ComfyUI + studio)
Zobacz [docs/INSTALL.md](docs/INSTALL.md): `./install.sh --comfy ~/ComfyUI`. Wagi i nody nie są instalowane automatycznie; raport mówi, co dociągnąć.

## Uruchomienie UI
```bash
(cd frontend && npm install && npm run build)
PSYCHODELIC_DATA=~/psy-data python -m psychodelic    # http://127.0.0.1:8765
```
Opis ekranów: [docs/UI_GUIDE.md](docs/UI_GUIDE.md).

## Dokumentacja
- `docs/AUDIT.md`, `docs/COMPATIBILITY.md`, `docs/BASELINE.md` — audyt (M0)
- `docs/STATUS.md` — co działa i co nie (z kolumną sposobu sprawdzenia)
- `docs/UI_GUIDE.md` — jak korzystać z ekranów
- `scripts/collect_local_audit.sh` — audyt tylko do odczytu, uruchamiasz u siebie
