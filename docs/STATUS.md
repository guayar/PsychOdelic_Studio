# Status: PsychOdelic Studio

Stan na 2026-11-02. Wszystko poniżej działa **bez GPU i bez ComfyUI**. Render jest wyłączony z założenia.

## Co jest zrobione i sprawdzone

| Obszar | Status | Jak sprawdzone |
|---|---|---|
| Backend FastAPI, SQLite z migracjami (v1, v2), projekty z manifestem | POTWIERDZONE_TESTEM | 75 testów pytest (`backend/tests`) |
| Maszyna stanów zadań (§ 9), idempotencja, audyt zdarzeń | POTWIERDZONE_TESTEM | testy `test_jobs.py`, `test_api_full.py` |
| Bezpieczne ścieżki (bez `..`, bez symlinków wychodzących), zapis atomowy | POTWIERDZONE_TESTEM | `test_security.py`, `test_fsio.py` |
| Adapter H3 Extender: budowa komendy `gen_extender_refine.py` (argv bez powłoki, env z listy) | POTWIERDZONE_TESTEM na skrypcie-atrapie | `test_adapters.py`, `test_capture.py` |
| Adapter LTX lipsync: budowa komendy `gen_ltx_lip.py` | POTWIERDZONE_TESTEM na atrapie | `test_adapters.py` |
| Przechwycenie grafu produkcyjnego skryptu (dry-run, `urllib` podmieniony, bez ComfyUI) | POTWIERDZONE_TESTEM na atrapie | `test_capture.py` |
| Runner: `dry_run` domyślnie nic nie uruchamia; render wymaga jawnej zgody | POTWIERDZONE_TESTEM | `test_runner.py` |
| Planer ujęć (17n+5), walidacja nakładań i długości ujęć | POTWIERDZONE_TESTEM | `test_domain.py`, `test_api.py` |
| Rejestr narzędzi Directora: walidacja argumentów, uprawnienia READ/PREPARE/EXECUTE/HUMAN_ONLY | POTWIERDZONE_TESTEM | `test_domain.py` |
| Oś montażowa: `out` wyłączne, nakładania, eksport CSV/JSON, timecode | POTWIERDZONE_TESTEM | `test_domain.py`, `test_api_full.py` |
| Przegląd: akceptacja/odrzucenie **nie kasuje plików** | POTWIERDZONE_TESTEM | `test_api_full.py`, test przeglądarki |
| Brak endpointu renderu w API | POTWIERDZONE_TESTEM | `test_no_render_endpoint_exists` |
| UI React + TypeScript + Vite (plan, H3, LTX, zadania, przegląd, oś, stan) | POTWIERDZONE_TESTEM | `tsc` bez błędów, build, test przeglądarki |
| Test przeglądarki (7 kroków: projekt, plan, H3, status, przegląd, oś) | POTWIERDZONE_TESTEM | Chromium `/opt/pw-browsers/chromium`, `frontend/e2e/smoke.mjs` |
| Odczyt VRAM (`rocm-smi`, tylko odczyt) | TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE | parser testowany na tekście; na Twojej maszynie uruchomić |
| Doctor (python, sqlite, ffmpeg, ComfyUI, data_dir) | POTWIERDZONE_TESTEM | `test_doctor.py` |

## Czego NIE ma (celowo lub jeszcze nie)

| Obszar | Status | Dlaczego |
|---|---|---|
| Render H3/LTX na GPU z aplikacji | NIEDOSTEPNE_LUB_WYMAGA_ZMIANY | Brak zgody na GPU i ComfyUI w tej sesji; brak endpointu |
| Zwalnianie Directora z VRAM (unload/reload) | NIEDOSTEPNE_LUB_WYMAGA_ZMIANY | Wymaga testu na GPU; `decide_render` tylko czyta stan |
| Monitoring ComfyUI przez WebSocket | NIEDOSTEPNE_LUB_WYMAGA_ZMIANY | Wymaga działającego ComfyUI |
| Model lokalny (Ollama) | TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE | Adapter sprawdza tylko `/api/tags`; nic nie ładuje |
| Zgodność grafu z prawdziwym skryptem `gen_extender_refine.py` | NIEZWERYFIKOWANE | Wymaga `object_info.json` z Twojej maszyny (sekcja „Jak sprawdzić 1:1”) |
| Model Doctor (wykrywanie modeli z profilu workflow) | NIEDOSTEPNE_LUB_WYMAGA_ZMIANY | M7, nie zrobione |
| install.sh, start.sh, doctor.sh, update.sh, pakowanie ZIP | NIEDOSTEPNE_LUB_WYMAGA_ZMIANY | M7, nie zrobione |
| Tailwind / shadcn/ui | odstępstwo | UI w czystym CSS z tokenami; ten sam wygląd, mniej zależności |

## Jak sprawdzić 1:1 z produkcją (bez renderu)

1. Zapisz schemat z ComfyUI (tylko odczyt, bez zadań): `curl -s http://127.0.0.1:8188/object_info > object_info.json`.
2. Zapisz parametry w pliku `spec.json` (tak jak body API `h3/prepare`, z polami `project_root`, `prefix`, `seed`, `prompt_files`, `refs`, `durs`…).
3. Uruchom: `PYTHONPATH=backend python3 -m psychodelic.adapters.capture --object-info object_info.json --spec spec.json --out graf_adapter.json`
4. Porównaj z grafem, który daje Twój dotychczasowy przebieg (ten sam seed i prompt). Różnice w `classes` i `inputs` pokażą, czy adapter robi to samo.

Ten krok nie łączy się z ComfyUI: `urllib` jest podmieniony, a każdy inny adres jest blokowany.
