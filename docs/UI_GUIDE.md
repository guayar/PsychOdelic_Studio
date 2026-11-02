# Jak korzystać z PsychOdelic Studio (UI)

Aplikacja działa lokalnie na `127.0.0.1:8765`. Nic nie jest renderowane ani wysyłane do ComfyUI.

## Układ
- **Lewy pasek**: projekty (nazwy są unikalne) i tworzenie nowego.
- **Górny pasek**: stan „Render GPU: wyłączony”, odczyt VRAM i model lokalny. Najedź na chip, żeby zobaczyć szczegóły.
- **Zakładki**:
  1. **Plan ujęć**: wpisz czasy (`12.5` albo `1:02.5`), opisy i sprawdź klatki (17n+5). „Zapisz wszystkie prompty” tworzy `prompts/shot_NN.txt`.
  2. **H3 Extender**: wybierz prompt, dodaj referencje po kolei (limit 9, licznik), ustaw seed/prefiks/długości. „Przygotuj komendę” pokazuje dokładną komendę i zmienne środowiskowe. Nic nie jest uruchamiane.
  3. **LTX lipsync**: ogon, wycinek audio, prompt. Działa tak samo jak H3.
  4. **Zadania**: lista z aktualnym stanem i historią każdej zmiany.
  5. **Przegląd**: dodaj wynik (ścieżka względem projektu), zaakceptuj albo odrzuć z notatką. Decyzja nigdy nie kasuje pliku.
  6. **Oś montażowa**: klipy z zakresem `[początek, koniec)`, nakładania pokazane na osobnych ścieżkach, eksport CSV/JSON.
  7. **Stan systemu**: GPU, model lokalny i diagnostyka środowiska.

## Zasady, które UI pilnuje
- Odrzucone ujęcia zostają na dysku.
- Limity H3: 9 obrazów, 3 wideo, 3 audio. Ponad limit nie da się dodać.
- Ścieżki promptów i wyników muszą leżeć w katalogu projektu.
- Komenda jest pokazywana przed każdą akcją, a informacja „NIE została uruchomiona” jest zawsze widoczna.

## Uruchomienie
```bash
cd ~/PsychOdelic-Studio
python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
(cd frontend && npm install && npm run build)
PSYCHODELIC_DATA=~/psy-data python -m psychodelic     # http://127.0.0.1:8765
```
Test przeglądarki (wymaga działającego backendu na porcie 8799): patrz `frontend/e2e/smoke.mjs`.
