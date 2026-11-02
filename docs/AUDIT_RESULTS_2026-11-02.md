# Wyniki audytu lokalnego (maszyna użytkownika, 2026-11-02)

Źródło: wynik `scripts/collect_for_claude.sh` uruchomiony przez użytkownika (tylko odczyt).
Status: **POTWIERDZONE_TESTEM** = widziane w wyniku skryptu na tej maszynie. Pozostałe punkty są opisane jako niezweryfikowane.

## 1. System i GPU
- Ubuntu 24.04.5 LTS, kernel 6.17.0-42-generic, systemowy `python3` 3.12.3. **POTWIERDZONE**.
- GPU[0]: AMD Radeon AI PRO R9700, gfx1201, VRAM 34 208 743 424 B (≈31,9 GiB). **POTWIERDZONE** (rocm-smi, rocminfo, ComfyUI `system_stats`).
- GPU[1]: iGPU Raphael (gfx1036), VRAM 64 MB. Start wymusza `ROCR_VISIBLE_DEVICES=0` (POTWIERDZONE w skrypcie); że indeks 0 to R9700, wynika z `system_stats` (device 0).
- ROCm (POTWIERDZONE, `check-environment.sh` w venv ComfyUI): `torch.version.hip` = **7.16.26385**; torch `2.14.0+rocm10.1.0` (tag w nazwie buildu nie oznacza wersji runtime'u). GPU widoczne w tym skrypcie: „AMD Radeon AI PRO R9700”, liczba GPU 2 (skrypt nie ustawia `ROCR_VISIBLE_DEVICES`, a start-comfy.sh tak; w trakcie startu ComfyUI widzi kartę 0). Triton 3.8.0.
- `/opt/rocm` istnieje, bez `.info/version`. dpkg pokazuje pakiety `amdrocm-core10.0-gfx1201 10.0.0-4`. Którego runtime'u używa torch (7.16 z venv czy 10.0 z systemu), **NIEZWERYFIKOWANE**; do sprawdzenia przez `ldd` na bibliotekach torcha.
- Systemowy `torch` 2.14.1+cu130 (CUDA, nie ROCm) — **nie jest** środowiskiem ComfyUI; ignorować przy audycie.
- ffmpeg/ffprobe 6.1.1 dostępne. **POTWIERDZONE**.

## 2. ComfyUI
- Katalog: `/home/sututrang/ComfyUI` (repo git, HEAD `ba994879`, 2026-10-14, origin Comfy-Org). Venv: `/home/sututrang/ComfyUI/venv` (python 3.12). **POTWIERDZONE**.
- Wersje (`system_stats`): ComfyUI 0.40.0, frontend 1.55.17, templates 0.11.82, comfy-kitchen 0.2.37. **POTWIERDZONE**.
- Argumenty startowe: `main.py --enable-manager --enable-manager-legacy-ui --disable-smart-memory --use-ck-attention`. **POTWIERDZONE**. Uwaga: `--disable-smart-memory` wpływa na zwalnianie VRAM (ważne dla M6).
- **Start ComfyUI (POTWIERDZONE, odczyt skryptu):** `~/comfyui-local/scripts/start-comfy.sh` ustawia `ROCR_VISIBLE_DEVICES=0`, wchodzi do `~/ComfyUI`, aktywuje `venv` i wykonuje `exec python main.py --enable-manager --enable-manager-legacy-ui --disable-smart-memory --use-ck-attention`. Brak `--port`/`--listen`, więc serwer działa na domyślnym `127.0.0.1:8188`. Ścieżka istnieje (wcześniejsze stwierdzenie o jej braku było błędem skryptu zbierającego, naprawionym). Skrypt `check-environment.sh` pokazuje wersje torch/ROCm/GPU (do uruchomienia przez użytkownika).
- Uwaga: użytkownik nie startuje ComfyUI od zera; serwer był już uruchomiony. Komendy `queue` i `interrupt` z `CLAUDE_QUICKREF` są poprawne.
- Serwer odpowiada na `127.0.0.1:8188`. **POTWIERDZONE**.
- `object_info`: 1700 węzłów (plik `~/psychodelic_object_info_20261102_085434.json`, 3,6 MB).

## 3. Węzły (z `object_info`)
Obecne: `MiniMaxH3ReferenceToVideo`, `MiniMaxH3Extender`, `MiniMaxH3FunControlNetApply`, `ModelPatchLoader`, `MiniMaxH3AddGuide`, `LoadVideo`, `GetVideoComponents`, `LoadAudio`, `ImageFromBatch`, `SaveImage`, `SaveVideo`, `VAEDecode`, `SamplerCustomAdvanced`, `BasicScheduler`, `KSamplerSelect`, `RandomNoise`, `BasicGuider`, `UNETLoader`, `CLIPLoader`, `VAELoader`, `LoraLoaderModelOnly`, `LTXAVTextEncoderLoader`, `LTXV*` (wiele). **POTWIERDZONE**.
Brak: `MiniMaxH3TextEncoderLoader` (wariant pruned24 niedostępny), `H3HybridWindows`, `MMH3HybridWindowSampler`. **POTWIERDZONE**.
Niesprawdzone (lista w wyniku skryptu była obcięta do 80 pozycji): `MiniMaxH3DirectorCS` (używa go `gen_h3_director.py`). **NIEZWERYFIKOWANE**.

## 4. Pliki modeli (listy wyboru w ComfyUI)
- UNET: `minimax_h3_ref2va_pruned_int8_convrot`, `minimax_h3_fl2va_pruned_int8_convrot`, `minimax_h3_fl2va_pruned_w4a8_mixed`, `ltx-2.5-22b-dev/distilled-transformer-comfy-int8-convrot`. **POTWIERDZONE**.
- **VAE wideo: tylko `minimax_h3_video_vae_fp16.safetensors`.** Nasze grafy (`workflows/h3_chain_*.json`) używają `minimax_h3_video_vae_int8_convrot.safetensors`, którego **nie ma** → te grafy się nie uruchomią. Produkcyjne skrypty (`gen_extender_refine.py`, `gen_ref2va.py`, `gen_h3_director.py`) używają fp16. **NIEZGODNOŚĆ, do naprawy w repo warsztatu.**
- VAE audio: `minimax_h3_audio_vae_fp32.safetensors`. **POTWIERDZONE**.
- CLIP: tylko `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`. Brak wariantu pruned24. **POTWIERDZONE**.
- ModelPatch (ControlNet): dokładnie jedna pozycja: `minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors`. **POTWIERDZONE** (zgodne z naszą domyślną nazwą).
- LoRA H3: `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16`, `minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_resized_avg_rank_64_bf16`, `minimax_h3_lms_v1.0_r64`, `minimax_h3_fl2v_turbo_*`. **POTWIERDZONE**. Produkcja używa 8step v1.0.
- LTX: `ltx-2.5-22b-*` (LTX 2.5 potwierdzone, nie 2.3). **POTWIERDZONE**.
- Input: 320 plików obrazów (lista `LoadImage`). **POTWIERDZONE**.

## 5. Custom nodes (34 katalogi) — ryzyko kolizji
Wiele wtyczek dotyka pipeline'u H3 jednocześnie: `ComfyUI_MiniMax_H3_Extender` (tritant), `ComfyUI-H3-Motion-Context` (0.7.1), `ComfyUI-MiniMaxH3-Director`, `ComfyUI_MiniMaxH3_Director` (inny autor), `MiniMaxH3-Director-Seed-Hunt`, `Muse-MiniMax-H3-Refine`, `ComfyUI-Spectrum-MiniMax-H3`, `ComfyUI-VDN-H3`, `ComfyUI-MiniMaxH3-ToneCompensate`, `mateusz_h3_*`, `LTX-2.5-Director`, `ComfyUI-LTXVideo`, `ComfyUI-LTX2.5-MSR`. Dodatkowo `ComfyUI-CGlide` (commit: „remove the old H3 director, superseded by H3 Studio”).
Ryzyko: nadpisywanie tych samych patchy modelu. Do sprawdzenia przed M2 (brief z workshopu wymaga porównania monkey-patchy). **NIEZWERYFIKOWANE**.
Nazwa naszej wtyczki `H3Director` nie koliduje z widocznymi nazwami (`ComfyMiniMaxH3Director`), ale przed instalacją trzeba to sprawdzić w `object_info`.

## 6. Projekt OUG
- Ścieżka: `/media/sututrang/New 11/teledysk/Psychedelic/Once Upon a Garden`. 2393 plików, 19 GB. **POTWIERDZONE**.
- `_docs/`: 35 pozycji (skrypty + kopie `.bak_*`). `_PLAN/`: handoffy, `accepted_clips.txt` (12 wpisów). **POTWIERDZONE**.
- **Baseline**: `~/oug_baseline_20261102.sha256` ma 55 linii, wszystkie **OK**. Baseline wykonany. **POTWIERDZONE**.
- Niespójne stany w handoffach: `START_HERE.md` (zaakceptowane do 117 s) vs `HANDOFF_NEXT_CHAT_2026-11-02.md` (do 184,4 s). Źródłem prawdy jest `_PLAN/accepted_clips.txt` + `video_chunks/` — **do potwierdzenia z Tobą**.
- Produkcyjne skrypty mają zakodowane ścieżki (`/media/sututrang/New 11/...`, `/home/sututrang/ComfyUI/...`). Adapter Studio musi je parametryzować, nie kopiować.
- `gen_extender_refine.py` (58 linii): `usage <refine 0|1> <prefix> <seed> <prompt...>`, env: `REFS, CONT, FULLRES, DURS, RUNMODE, VALIDATED, CTRL, CTRL_FRAMES, CTRL_STRENGTH`. Buduje graf i wysyła przez API; nie ma flagi „tylko zbuduj”.
- Odwołanie do `~/ComfyUI/user/default/workflows/oug_ltx_director_api.json` (`gen_ltx_lip.py`) — **NIEZWERYFIKOWANE** (nie było w wyniku).

## 7. Wnioski dla planu M0/M1
1. Adapter H3 (M2) = wywołanie `gen_extender_refine.py` z tym samym env; test 1:1 **bez renderu**: uruchomić skrypt w harnessie, który przechwytuje POST `/prompt`, zapisuje graf i kończy proces. Porównać z plikiem referencyjnym wygenerowanym raz z obecnego skryptu.
2. Naprawić VAE w grafach warsztatu (fp16) przed jakimkolwiek testem.
3. ~~Ustalić komendę startu ComfyUI~~ — ustalone: `start-comfy.sh`.
4. ~~Sprawdzić `torch.version.hip`~~ — 7.16.26385. Pozostaje: ustalić, z której biblioteki HIP korzysta torch (`ldd`).
5. Sprawdzić kolizje patchy H3 (lista w sekcji 5).
