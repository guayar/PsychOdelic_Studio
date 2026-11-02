# PsychOdelic Studio

Lokalne studio do teledysków (AI Director, adaptery H3/LTX, timeline). **Status: M0 częściowo, M1 fundament.** Szczegóły: [docs/STATUS.md](docs/STATUS.md).

## Zasady
- Działający pipeline „Once Upon a Garden” ma pierwszeństwo. Studio go **nie zastępuje** i **nie zmienia** jego skryptów bez zgody.
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

## Dokumentacja
- `docs/AUDIT.md`, `docs/COMPATIBILITY.md`, `docs/BASELINE.md` — audyt (M0)
- `docs/STATUS.md` — co działa i co nie
- `scripts/collect_local_audit.sh` — audyt tylko do odczytu, uruchamiasz u siebie
