# Status: PsychOdelic Studio (M0 częściowo, M1 fundament)

## M0: audyt
- **Częściowo.** Brak dostępu do lokalnego Ubuntu i ComfyUI z tej sesji. Szczegóły: `docs/AUDIT.md`, `docs/COMPATIBILITY.md`.
- Gotowy skrypt tylko do odczytu: `scripts/collect_local_audit.sh` (uruchom u siebie).
- Baseline OUG: **wykonany** (55/55 OK). Wyniki lokalnego audytu: `docs/AUDIT_RESULTS_2026-11-02.md`.

## M1: fundament
| Element | Stan |
|---|---|
| Repo Git (lokalne, bez pusha) | gotowe |
| FastAPI + uvicorn na 127.0.0.1 | POTWIERDZONE_TESTEM (testy + smoke) |
| SQLite + migracje (schemat v1, § 11) | POTWIERDZONE_TESTEM |
| Projekty (SQLite + manifest JSON, zapis atomowy) | POTWIERDZONE_TESTEM |
| Maszyna stanów zadań (§ 9), idempotentne zadania, audyt | POTWIERDZONE_TESTEM |
| Bezpieczne ścieżki (bez `..`, bez symlinków wychodzących) | POTWIERDZONE_TESTEM |
| Doctor z trzema statusami | POTWIERDZONE_TESTEM (ComfyUI: NIEDOSTEPNE w sesji) |
| Monitoring ComfyUI (WebSocket) | **NIEZROBIONE** (wymaga działającego ComfyUI) |
| Frontend React/TS/Vite/Tailwind | **NIEZROBIONE** — nie buduję makiet |
| Model Doctor (wykrywanie modeli z profilu workflow) | **NIEZROBIONE** (M7) |
| install.sh / start.sh / doctor.sh / update.sh | **NIEZROBIONE** (M7) |

## Warunki MUST PASS (§ 13) — stan
- OUG bez zmian: **nie da się potwierdzić** bez baseline'u u Ciebie.
- Baza zachowuje warianty i gałęzie po restarcie: **częściowo** (schemat jest; brak logiki wariantów, M4).
- Dokładna liczba klatek, brak powielenia `CONT`: **nie dotyczy M1** (brak adaptera H3, M2).
- H3/LTX z parametrami realnie obsługiwanymi: **nie dotyczy M1**.
- Użytkownik zatwierdza jakość; odrzucenie nie usuwa plików: **schemat tego pilnuje** (`review_status`), logika M2.
- AI Director unload nie zatrzymuje backendu: **nie dotyczy M1** (M6).
- Testy offline nie są dowodem GPU: **przestrzegane** (żadnych renderów).

## Następny krok
1. Uruchom `scripts/collect_local_audit.sh` u siebie i wrzuć wynik (lub podaj ścieżki do `_docs/`).
2. Zrób baseline OUG (`docs/BASELINE.md`).
3. Po audycie: adapter H3 (M2) jako wywołanie Twoich skryptów, z testem na dryrun, bez renderu bez zgody.

## Uruchamianie (dev)
```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
pytest -q                     # 35 testów backendu
PSYCHODELIC_DATA=~/psy-data python -m psychodelic   # 127.0.0.1:8765
```
