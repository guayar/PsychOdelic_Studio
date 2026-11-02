# PsychOdelic Studio: jak używać

Lokalne studio do teledysków: planowanie ujęć, przygotowanie komend dla H3 Extender i LTX lipsync,
przegląd wyników i oś montażową. **Studio niczego nie renderuje i nie pobiera wag.** Render na GPU
jest wyłączony w tej wersji.

Legenda statusów: `POTWIERDZONE_TESTEM`, `TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE`,
`NIEDOSTEPNE_LUB_WYMAGA_ZMIANY`.

## 1. Instalacja

Wymagania: Ubuntu, Python 3.11+, opcjonalnie Node.js z npm (interfejs graficzny), ComfyUI (np. `~/ComfyUI`).

```bash
git clone https://github.com/guayar/psychodelic_studio ~/PsychOdelic-Studio
cd ~/PsychOdelic-Studio
./install.sh --comfy ~/ComfyUI
```

`install.sh`:
- tworzy `.venv` i instaluje zależności backendu,
- buduje interfejs (`frontend/dist`), jeśli jest npm (opcja `--skip-ui` pomija ten krok),
- kopiuje workflowy H3 z `studio_workflows/` do `ComfyUI/user/default/workflows/`. Nic nie jest nadpisywane;
  konflikt trafia obok jako `*.studio.json`,
- tworzy ikonkę **PsychOdelic Studio** w menu aplikacji,
- zapisuje `install_report.json` z listą tego, co zostało skopiowane i czego brakuje.

Opcje: `--yes` (bez pytań), `--ltx-workflow PLIK` (własny workflow LTX, kopiowany bez zmian),
`--skip-ui` (bez budowania interfejsu).
Status: `TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE` na świeżym ComfyUI u Ciebie. Testy instalatora działają na sztucznej instalacji.

## 2. Co dociągnąć ręcznie

Studio nie instaluje custom nodes ani wag. Lista jest w `install_report.json`, w sekcji `missing`:
- **node**: nazwa oraz repo do zainstalowania (np. `ComfyUI_MiniMax_H3_Extender`, `ComfyUI-LTXVideo`)
  albo informacja, że węzeł wymaga aktualizacji ComfyUI,
- **weight (waga)**: nazwa pliku, folder w `ComfyUI/models/…` i źródło (Hugging Face, `Comfy-Org/MiniMax-H3`).

Pobierasz wagi i instalujesz nody sam, świadomie. Po zmianach uruchom studio ponownie i w zakładce
**Stan systemu** kliknij „Sprawdź ComfyUI”.

## 3. Uruchomienie

- Ikonka **PsychOdelic Studio** w menu albo `./start.sh`.
- Studio działa na `http://127.0.0.1:8765` (tylko lokalnie), przeglądarka otwiera się sama.
- Studio **nie uruchamia** ComfyUI. Jeśli chcesz generować, uruchom ComfyUI jak zwykle.

## 4. Interfejs

Język: przełącznik **PL / EN** w prawym górnym rogu (zapamiętywany w przeglądarce). Komunikaty błędów
z backendu są po polsku także w trybie EN.

| Zakładka | Do czego |
|---|---|
| Plan ujęć | Ujęcia z czasem `12.5` albo `1:02.5`. Studio liczy klatki w siatce H3 (17n+5 przy 24 fps) i zapisuje prompty w `prompts/`. |
| H3 Extender | Prompt, referencje obrazów (limit 9, kolejność = `<Picture N>`), seed, prefiks, długości. „Przygotuj komendę” pokazuje polecenie i zmienne środowiskowe. **Nic nie jest uruchamiane.** |
| LTX lipsync | Ogon poprzedniego klipu, wycinek audio, prompt, przesunięcie audio. Działa jak H3. |
| Zadania | Lista przygotowanych zadań z historią zmian stanu. |
| Przegląd | Dodajesz wynik (ścieżka względem projektu), akceptujesz lub odrzucasz z notatką. **Decyzja nigdy nie kasuje pliku.** |
| Oś montażowa | Klipy z zakresem `[początek, koniec)` (koniec wyłączny), nakładania na osobnych ścieżkach. Eksport CSV/JSON. |
| Stan systemu | Chipy GPU (tylko odczyt), model lokalny, sprawdzenie zgodności z ComfyUI (wymagane nody i pliki), diagnostyka. |

### Prefiks wyniku

Dozwolone: litery, cyfry, `_`, `-` i `/`. Maks. 64 znaki. Bez `..`, spacji i wiodącego `/`.
Przykład: `shots/shot_01`. Nazwa projektu nie jest w prefiksie wymagana.

## 5. Typowy przebieg

1. Utwórz projekt (lewy pasek).
2. W **Plan ujęć** wpisz ujęcia i opisy, kliknij „Sprawdź plan”, potem „Zapisz wszystkie prompty”.
3. W **H3 Extender** wybierz prompt, dodaj referencje (pliki muszą leżeć w `ComfyUI/input/`), ustaw parametry
   i kliknij „Przygotuj komendę (bez renderu)”. Polecenie skopiujesz i uruchomisz sam, jeśli chcesz.
4. Wynik (wideo z ComfyUI) dodaj w **Przegląd**, oceń i zaakceptuj albo odrzuć.
5. Zaakceptowane klipy ułóż w **Oś montażowa** i wyeksportuj listę.

## 6. Ograniczenia (świadomie)

- Render H3 i LTX z poziomu studia jest wyłączony. Studio tylko przygotowuje komendy.
- Studio nie ocenia jakości wideo. Ocenia człowiek w zakładce Przegląd.
- „Sprawdź ComfyUI” odpytuje działający serwer ComfyUI (tylko odczyt, `GET /object_info`).
  Walidacja grafów offline działa na zapisanym pliku `object_info`, bez GPU.

## 7. Co jest sprawdzone

| Element | Status |
|---|---|
| Testy backendu (88) | POTWIERDZONE_TESTEM (ostatni przebieg po zmianie prefiksów: wszystkie przechodzą) |
| Kontrola typów frontu (`tsc`) | POTWIERDZONE_TESTEM (ostatni przebieg po zmianie prefiksów) |
| Test przeglądarki (`frontend/e2e/smoke.mjs`, PL/EN, cały przepływ) | POTWIERDZONE_TESTEM dla wersji sprzed zmiany prefiksów. Po zmianie nieuruchomiony, do powtórzenia |
| Zgodność workflow H3 z Twoim ComfyUI | TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE: do sprawdzenia na Twoim `object_info` |
| Workflow LTX | TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE: studio kopiuje produkcyjny plik, nie tworzy go |
| Ikonka i uruchomienie na Twoim pulpicie | TECHNICZNIE_MOZLIWE_NIEZWERYFIKOWANE |
| Render na GPU | NIEDOSTEPNE_LUB_WYMAGA_ZMIANY (wyłączony z założenia) |

Zgłaszając problem, podaj: numer kroku, treść błędu z terminala oraz `install_report.json`.
