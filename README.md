# PsychOdelic Studio

Lokalne studio do teledysków AI na ComfyUI: plan ujęć, przygotowanie komend H3 Extender i LTX lipsync,
przegląd wyników i oś montażowa. Działa na czystym ComfyUI, nie pobiera wag i niczego nie renderuje.

## Szybki start

```bash
git clone https://github.com/guayar/psychodelic_studio ~/PsychOdelic-Studio
cd ~/PsychOdelic-Studio
./install.sh --comfy ~/ComfyUI
./start.sh          # http://127.0.0.1:8765
```

## Dokumentacja

- **[Jak używać (instalacja, interfejs, przebieg pracy, ograniczenia) → docs/UZYCIE.md](docs/UZYCIE.md)**
- [Instalacja i raport brakujących elementów → docs/INSTALL.md](docs/INSTALL.md)
- [Opis ekranów → docs/UI_GUIDE.md](docs/UI_GUIDE.md)
- [Co działa, a co nie → docs/STATUS.md](docs/STATUS.md)

## Zasady

- Studio jest uniwersalne i nie zakłada żadnego konkretnego projektu.
- Istniejące pipeline'y użytkownika (skrypty, workflowy) nie są zmieniane bez zgody.
- Aplikacja słucha tylko na `127.0.0.1`.
- Studio nie pobiera wag ani nie instaluje custom nodes. Raport `install_report.json` mówi, co dociągnąć.
