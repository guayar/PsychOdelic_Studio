# PsychOdelic Studio: jak używać

Lokalne studio do teledysków: planowanie ujęć, przygotowanie komend dla H3 Extender i LTX lipsync,
przegląd wyników, oś montażowa. **Studio niczego nie renderuje i nie pobiera wag.** Render na GPU jest
wyłączony w tej wersji.

## 1. Instalacja

Wymagania: Ubuntu, Python 3.11+, opcjonalnie Node.js z npm (do interfejsu graficznego), ComfyUI
(np. `~/ComfyUI`).

```bash
git clone https://github.com/guayar/psychodelic_studio ~/PsychOdelic-Studio-v3
cd ~/PsychOdelic-Studio-v3
./install.sh --comfy ~/ComfyUI
```

`install.sh`:
- tworzy `.venv` studia i instaluje zależności (pip),
- buduje interfejs (`frontend/dist`), jeśli jest npm,
- kopiuje workflowy H3 z `studio_workflows/` do `ComfyUI/user/default/workflows/` (nic nie nadpisuje;
  konflikt trafia obok jako `*.studio.json`),
- tworzy ikonkę **PsychOdelic Studio** w menu aplikacji,
- zapisuje `install_report.json`: co zostało skopiowane i czego brakuje.

Opcje: `--yes` (bez pytań), `--ltx-workflow PLIK` (produkcyjny workflow LTX, kopiowany bez zmian),
`--skip-ui` (bez budowania interfejsu).

## 2. Co dociągnąć ręcznie

Studio nie instaluje custom nodes ani wag. Lista jest w `install_report.json`, w sekcji `missing`:
- **node**: nazwa, repo do zainstalowania (np. `ComfyUI_MiniMax_H3_Extender`, `ComfyUI-LTXVideo`)
  albo informacja, że węzeł jest wbudowany i wymaga aktualizacji ComfyUI,
- **weight (waga)**: nazwa pliku, folder w `ComfyUI/models/…` i źródło (`Comfy-Org/MiniMax-H3` na Hugging Face).

Pobieranie wag i instalację nodów wykonujesz sam, świadomie. Po każdej zmianie uruchom ponownie
`./start.sh`: studio pokaże aktualny stan w zakładce **Stan systemu** (przycisk „Sprawdź ComfyUI”).

## 3. Uruchomienie

- Ikonka **PsychOdelic Studio** w menu, albo `./start.sh`.
- Studio działa na `http://127.0.0.1:8765` (tylko lokalnie). Przeglądarka otwiera się sama.
- ComfyUI **nie jest** uruchamiane przez studio. Jeśli chcesz generować, uruchom ComfyUI tak, jak zwykle.

## 4. Interfejs

Język: przełącznik **PL / EN** w prawym górnym rogu (zapamiętywany w przeglądarce).

| Zakładka | Do czego |
|---|---|
| Plan ujęć | Opisz ujęcia (czas jako `12.5` lub `1:02.5`). Studio liczy klatki w siatce H3 (17n+5 przy 24 fps) i zapisuje prompty jako pliki w projekcie. |
| H3 Extender | Wybierz prompt, dodaj referencje po kolei (limit 9), ustaw seed, prefiks i długości. „Przygotuj komendę” pokazuje dokładne polecenie i zmienne środowiskowe. **Nic nie zostaje uruchomione.** |
| LTX lipsync | Ogon, wycinek audio, prompt. Działa jak H3. |
| Zadania | Lista przygotowanych zadań i ich historia zmian stanu. |
| Przegląd | Dodaj wynik (ścieżka względem projektu), zaakceptuj lub odrzuć z notatką. **Decyzja nigdy nie kasuje pliku.** |
| Oś montażowa | Klipy z zakresem `[początek, koniec)` (koniec wyłączny), nakładania są widoczne na osobnych ścieżkach. Eksport CSV/JSON. |
| Stan systemu | Karta GPU (tylko odczyt), model lokalny, zgodność z ComfyUI (wymagane nody i pliki), diagnostyka. |

## 5. Typowy przebieg

1. Utwórz projekt (lewy pasek).
2. W **Plan ujęć** wpisz ujęcia i opisy, kliknij „Sprawdź plan”, potem „Zapisz wszystkie prompty”.
3. W **H3 Extender** wybierz prompt, dodaj referencje z katalogu `ComfyUI/input/`, ustaw parametry,
   kliknij „Przygotuj komendę”. Skopiuj polecenie, jeśli chcesz uruchomić je sam.
4. Wynik (plik wideo wygenerowany przez ComfyUI) dodaj w **Przegląd**, oceń i zaakceptuj lub odrzuć.
5. Zaakceptowane klipy ułóż w **Oś montażowa** i wyeksportuj listę.

## 6. Ograniczenia (świadomie)

- Render H3 i LTX z poziomu studia jest **wyłączony**. Studio tylko przygotowuje komendy.
- Studio nie sprawdza jakości wideo. Ocenia ją człowiek w zakładce Przegląd.
- Zgodność workflow z Twoim ComfyUI jest sprawdzana względem zapisanego `object_info`, a nie na żywym
  serwerze ani na GPU.
- Komunikaty błędów z serwera są po polsku nawet w trybie EN.

## 7. Co jest sprawdzone, a co nie

| Element | Status |
|---|---|
| Testy backendu (88) i instalatora | POTWIERDZONE_TESTEM (na sztucznym ComfyUI i w sandboksie) |
| Test interfejsu w przeglądarce (PL/EN, cały przepływ) | POTWIERDZONE_TESTEM |
| Zgodność workflow H3 z Twoim ComfyUI | NIEZWERYFIKOWANE, do sprawdzenia dry-runem na Twoim `object_info` |
| Workflow LTX | NIEZWERYFIKOWANE; studio nie tworzy go samo, kopiuje produkcyjny plik |
| Uruchomienie ikonki i interfejsu na Twoim pulpicie | NIEZWERYFIKOWANE |
| Render na GPU | NIEDOSTĘPNE (wyłączone z założenia) |

Zgłaszając problem, podaj: numer kroku, treść błędu z terminala i wynik `install_report.json`.
