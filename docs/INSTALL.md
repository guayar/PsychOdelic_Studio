# Instalacja PsychOdelic Studio

Studio **nie pobiera wag modeli** i **nie instaluje custom nodes**. Robi trzy rzeczy: buduje siebie,
kopiuje workflowy do ComfyUI (bez nadpisywania istniejących plików) i tworzy ikonkę w menu. Na końcu
wypisuje listę tego, co musisz dociągnąć ręcznie.

## Wymagania
- Ubuntu z ComfyUI (np. `~/ComfyUI`, z plikami `main.py` i katalogiem `custom_nodes/`).
- Python 3.11+ (`python3 --version`).
- Node.js z npm, jeśli chcesz interfejs graficzny (`sudo apt install nodejs npm`). Bez npm studio działa tylko jako API.

## Krok po kroku
```bash
git clone <repo studia> ~/PsychOdelic-Studio      # albo rozpakuj paczkę/bundle
cd ~/PsychOdelic-Studio
./install.sh --comfy ~/ComfyUI                     # z potwierdzeniem kopiowania
# na czystym ComfyUI bez pytań:  ./install.sh --comfy ~/ComfyUI --yes
# z workflow LTX z produkcji:    ./install.sh --comfy ~/ComfyUI --ltx-workflow ~/ComfyUI/user/default/workflows/oug_ltx_director_api.json
```
Po instalacji: ikonka **PsychOdelic Studio** w menu albo `./start.sh`. Studio otworzy się na `http://127.0.0.1:8765`.

## Co instalator robi, a czego nie
| Robi | Nie robi |
|---|---|
| tworzy `.venv` studia, instaluje zależności | nie uruchamia ComfyUI |
| buduje interfejs (`frontend/dist`), jeśli jest npm | nie pobiera wag modeli |
| kopiuje `studio_workflows/*.json` do `ComfyUI/user/default/workflows/` | nie instaluje custom nodes |
| przy konflikcie zapisuje obok jako `*.studio.json` | nie nadpisuje istniejących plików |
| tworzy ikonkę w `~/.local/share/applications` | nie zmienia ComfyUI poza plikami workflow |
| wypisuje brakujące nody i wagi (`install_report.json`) | nie łączy się z internetem poza pip/npm |

## Raport: co dociągnąć ręcznie
Po instalacji zobacz `install_report.json`, sekcja `missing`. Każda pozycja mówi:
- **node**: co zainstalować (repo z Twojej listy custom nodes albo „wbudowany, zaktualizuj ComfyUI”),
- **file (waga)**: nazwę pliku, folder w `ComfyUI/models/…` i źródło (`Comfy-Org/MiniMax-H3` na Hugging Face).
Studio nie pobiera niczego z tej listy. Pobieranie wag i instalację nodów robisz świadomie.

## Workflowy
- `H3_Ref2VA_3_ujecia.json`: trzy ujęcia Ref2VA, fp16 VAE (jak w produkcji).
- `H3_Ref2VA_3_ujecia_ControlNet.json`: to samo z ControlNet (wymaga pliku ControlNet na liście).
- LTX: studio nie tworzy workflow LTX. Podaj produkcyjny plik `--ltx-workflow` (patrz `studio_workflows/README_LTX.md`).

Zgodność workflow z Twoim ComfyUI sprawdzisz offline (po zapisaniu schematu):
```bash
curl -s http://127.0.0.1:8188/object_info > object_info.json
PYTHONPATH=backend python3 -m psychodelic.installer --comfy ~/ComfyUI --object-info object_info.json --dry-run
```
Status: POTWIERDZONE_TESTEM na sztucznym ComfyUI (testy instalatora). NIEZWERYFIKOWANE na Twoim ComfyUI
(wymaga uruchomienia powyższego i przejrzenia raportu).
