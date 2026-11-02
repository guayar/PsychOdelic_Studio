# M0: audyt środowiska (stan na 2026-11-02)

## 1. Co zrobiłem i czego nie mogłem zrobić

- **Nie mam dostępu do Twojego lokalnego Ubuntu.** W tej sesji nie istnieje `/media/sututrang/...` ani `~/comfyui-local`. Sesja działa w kontenerze w chmurze. Nie widzę Twojego ComfyUI, skryptów produkcyjnych, `_docs/`, `_PLAN/` ani plików wideo.
- **Serwer ComfyUI nie odpowiada** pod `127.0.0.1:8188`. Brak odpowiedzi to brak potwierdzenia, nie dowód braku modeli.
- **Nie widzę pliku `PsychOdelic_Studio_AUDYT_REPO_DLA_CLAUDE.md` ani `ARCHITEKTURA_2_0`**. Dostępny był tylko prompt startowy.
- Nie zmieniłem niczego w `guayar/H3_ComfyUI_MV_Workshop`, w ComfyUI ani w projekcie OUG.

Dlatego ten audyt jest **częściowy**. Dokładny stan Twojego pipeline'u musi potwierdzić skrypt `scripts/collect_local_audit.sh` uruchomiony u Ciebie (sekcja 5).

## 2. Co wiem z dokumentów, bez potwierdzenia na Twoim komputerze

Źródło: prompt startowy (załącznik) oraz publiczne repo workshopu.

| Element | Źródło | Status |
|---|---|---|
| `_docs/gen_extender_refine.py`, `_docs/oug_finish.sh`, `_docs/assemble_whole.py`, `_docs/gen_ltx_lip*.py` | prompt | NIEZWERYFIKOWANE (brak dostępu) |
| Argumenty `CONT`, `FULLRES`, `DURS`, `REFS` w `gen_extender_refine.py` | prompt | NIEZWERYFIKOWANE. Nie zgaduję opcji CLI; nie wolno ich dopisywać bez odczytu kodu |
| Node `MiniMaxH3Extender` (tritant), `continue_existing_video`, Motion Context | publiczne repo `tritant/ComfyUI_MiniMax_H3_Extender`, odczyt kodu (wersja `main` 3.0.14) | [CODE] dla upstream. Lokalnej wersji 3.0.12 **nie potwierdziłem** |
| Węzły natywne Ref2VA (`MiniMaxH3ReferenceToVideo`), Fun ControlNet, `LoadVideo`, `GetVideoComponents`, `LoadAudio` | kod `Comfy-Org/ComfyUI` (master) | [CODE] dla upstream. Zgodność z Twoją wersją ComfyUI **NIEZWERYFIKOWANA** |
| Wersja ROCm „10.1” | prompt | **NIEZWERYFIKOWANE i podejrzane**: nazewnictwo ROCm nie zgadza się z tym, co zwykle widać w `rocminfo`/`/opt/rocm/.info/version`. Sprawdź u siebie |
| Wersja LTX („2.5” lub „2.3”) | prompt, sam prompt zaznacza niepewność | NIEZWERYFIKOWANE. Nie zakładam wersji |
| Licencja modelu H3 | wcześniejszy research | **NIEZWERYFIKOWANE** (źródło wtórne); w wątku ustaliliśmy, że nie zajmujemy się tym teraz |

## 3. Co mam z własnego workshopu (`guayar/H3_ComfyUI_MV_Workshop`)

Narzędzia, które mogą być adaptowane (po testach zgodności, jak mówi prompt). Stan potwierdzony testami w tej sesji (CPU, dane syntetyczne):

- `scripts/stitch_shots.py` (LAB, dissolve, deflicker, BT.709, `--blur-match`) — **POTWIERDZONE TESTEM syntetycznym**, nie na H3.
- `scripts/measure_scene_drift.py` (affine i homografia) — **POTWIERDZONE TESTEM syntetycznym**.
- `scripts/audit_h3_runtime.py` — **POTWIERDZONE** na atrapie serwera; na prawdziwym ComfyUI nietestowane.
- `scripts/validate_graph_offline.py` — **POTWIERDZONE** na fiksturze schematu; prawdziwy `object_info` wymagany.
- `scripts/make_control.py` (demo klapy) — **POTWIERDZONE** testem; zachowanie H3 nietestowane.
- `scripts/build_ui_chain.py` — buduje łańcuch z ostatnią klatką przez `ImageFromBatch`. **To NIE jest zamiennik** Extender + Motion Context. Nie jest domyślnym pipeline'em.

Wady, które trzeba zapamiętać (wynikają z tego, co już zrobiliśmy):
- `audit_h3_runtime.py` oczekuje konkretnych nazw plików i może błędnie wymagać ControlNet, jeśli go nie używasz.
- `validate_graph_offline.py` zakłada strukturę schematu i ma ostrzeżenia dla autogrow; nie dowodzi działania.
- Lista plików wejściowych i nazwy modeli w generatorze są **sztywne** (np. `minimax_h3_ref2va_pruned_int8_convrot.safetensors`). Trzeba je wyłączyć z domyślnego pipeline'u Studio.

## 4. Ryzyka (do rozstrzygnięcia z Tobą)

1. **Brak potwierdzenia produkcji.** Dopóki nie zobaczę `_docs/` i `_PLAN/`, nie mogę napisać adaptera H3 1:1. Zgodnie z promptem nie będę tego zgadywać.
2. **Ryzyko cichej zmiany pipeline'u.** Nowy generator mógłby różnić się od Twojego (inne parametry, inny seed, inny zapis). Dlatego adapter M2 ma być wywołaniem Twoich skryptów, nie ich przepisaniem.
3. **Zgodność Extender/Motion Context z ROCm na Twojej maszynie** — nieznana. Tylko test na R9700 to rozstrzygnie.
4. **Trwałość cache Extendera** — prompt słusznie każe nie obiecywać wznowienia. Nie wiem, czy cache jest przenośny; to trzeba sprawdzić w kodzie Extendera u Ciebie.
5. **Dwa sterowniki kolejki (ComfyUI i Orchestrator).** Trzeba jasno zdefiniować, kto zwalnia VRAM. Nie wolno wywoływać `/free` ani resetować ComfyUI bez potwierdzenia.

## 5. Co uruchomić u siebie (tylko odczyt)

```bash
cd ~/PsychOdelic-Studio   # po sklonowaniu repo
./scripts/collect_local_audit.sh "/media/sututrang/New 11/teledysk/Psychedelic/Once Upon a Garden" ~/comfyui-local
```
Skrypt nie instaluje ani nie zmienia plików. Zapisuje raport do `audit_out/`. **Przejrzyj go przed wysłaniem**, bo zawiera ścieżki i nazwy plików.

Po tym raporcie aktualizuję `docs/AUDIT.md` i `docs/COMPATIBILITY.md`.
