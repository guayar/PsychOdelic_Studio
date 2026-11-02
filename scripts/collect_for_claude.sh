#!/usr/bin/env bash
# Zbiera wszystko potrzebne do audytu PsychOdelic Studio. TYLKO ODCZYT:
#   - nie instaluje niczego, nie zmienia plikow projektu, nie uruchamia ComfyUI/renderow,
#   - nie wysyla danych nigdzie (wynik zostaje na Twoim dysku).
# Uzycie:
#   bash collect_for_claude.sh ["/sciezka/do/Once Upon a Garden"] [/sciezka/do/ComfyUI]
# Wynik: ~/psychodelic_collect_<data>.txt (oraz ~/psychodelic_object_info_<data>.json).
# Przed wyslaniem przejrzyj plik: zawiera sciezki i nazwy plikow. Linie z "token/key/password" sa maskowane.

OUG="${1:-/media/sututrang/New 11/teledysk/Psychedelic/Once Upon a Garden}"
COMFY_ARG="${2:-}"
COMFY_URL="${PSYCHODELIC_COMFY_URL:-http://127.0.0.1:8188}"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$HOME/psychodelic_collect_${STAMP}.txt"
OBJ="$HOME/psychodelic_object_info_${STAMP}.json"

exec > >(tee "$OUT") 2>&1

hr()  { printf '\n==================== %s ====================\n' "$1"; }
head_file() { # plik, maks linii
  if [ -f "$1" ]; then echo "--- $1 (linii: $(wc -l < "$1"), bajtow: $(stat -c%s "$1"))"; sed -n "1,${2:-150}p" "$1"; else echo "--- BRAK: $1"; fi
}

hr "META"
echo "data: $(date -Is)"; echo "uzytkownik: $(whoami)@$(hostname)"; echo "OUG: $OUG"; echo "ComfyUI arg: ${COMFY_ARG:-<nie podano>}"

hr "SYSTEM"
uname -a; (lsb_release -ds 2>/dev/null || grep PRETTY /etc/os-release); echo "python3: $(python3 --version 2>&1)"
echo "--- ROCm:"
ls -d /opt/rocm* 2>/dev/null; cat /opt/rocm/.info/version 2>/dev/null || echo "/opt/rocm/.info/version: brak"
dpkg -l 2>/dev/null | awk '/rocm-core|hip-runtime-amd|rocm-libs/{print $2, $3}' | head -10
command -v rocminfo >/dev/null && rocminfo 2>/dev/null | grep -E "Marketing Name|gfx" | sort -u | head -6
command -v rocm-smi >/dev/null && rocm-smi --showproductname --showmeminfo vram 2>/dev/null | head -30
echo "--- ffmpeg:"; (ffmpeg -version 2>/dev/null | head -1) || echo "brak ffmpeg"
echo "--- GPU/pci:"; lspci 2>/dev/null | grep -iE "vga|display|radeon|amd" | head -5

hr "COMFYUI: lokalizacja i instalacja"
CANDS=()
[ -n "$COMFY_ARG" ] && CANDS+=("$COMFY_ARG")
CANDS+=("$HOME/comfyui-local" "$HOME/ComfyUI" "$HOME/comfyui")
for c in "${CANDS[@]}"; do [ -f "$c/main.py" ] && echo "znaleziono: $c"; done
echo "--- szukanie main.py (glebokosc 4, bez cache):"
find "$HOME" -maxdepth 4 -name main.py -path '*omfy*' -not -path '*/node_modules/*' 2>/dev/null | head -5
for c in "${CANDS[@]}"; do
  if [ -f "$c/main.py" ]; then
    echo "--- katalog: $c"; ls -la "$c" | head -40
    echo "--- custom_nodes:"; ls "$c/custom_nodes" 2>/dev/null
    echo "--- extra_model_paths.yaml:"; cat "$c/extra_model_paths.yaml" 2>/dev/null | sed -E 's/(token|key|password|secret)[^:]*:.*/\1: <maskowane>/I' || echo "brak"
    echo "--- scripts/:"; ls "$c/scripts" 2>/dev/null
    head_file "$c/scripts/start-comfy.sh" 80
    for r in "$c" "$c"/custom_nodes/*/; do
      [ -d "$r/.git" ] && { echo "--- git: $r"; git -C "$r" log -1 --format='%H %ci %s' 2>/dev/null; git -C "$r" remote -v 2>/dev/null | head -1; }
    done
    break
  fi
done

hr "COMFYUI: serwer (tylko GET)"
if curl -sS -m 5 "$COMFY_URL/system_stats" 2>/dev/null; then echo; else echo "serwer nie odpowiada pod $COMFY_URL (brak potwierdzenia)"; fi
if curl -sS -m 20 "$COMFY_URL/object_info" -o "$OBJ" 2>/dev/null && [ -s "$OBJ" ]; then
  echo "object_info zapisany: $OBJ ($(stat -c%s "$OBJ") bajtow, wezlow: $(python3 -c "import json;print(len(json.load(open('$OBJ'))))" 2>/dev/null))"
  echo "--- obecnosc wezlow z planu (1 = jest, 0 = brak):"
  python3 - "$OBJ" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
want = ["MiniMaxH3ReferenceToVideo","MiniMaxH3Extender","MiniMaxH3FunControlNetApply","ModelPatchLoader",
        "LoadVideo","GetVideoComponents","LoadAudio","ImageFromBatch","SaveImage","SaveVideo","VAEDecode",
        "SamplerCustomAdvanced","BasicScheduler","KSamplerSelect","RandomNoise","BasicGuider","UNETLoader",
        "CLIPLoader","VAELoader","LoraLoaderModelOnly","MiniMaxH3TextEncoderLoader","MiniMaxH3AddGuide",
        "H3HybridWindows","MMH3HybridWindowSampler","LTXVideo","LTXVLoader","LTXAVTextEncoderLoader"]
for w in want:
    print(f"  {int(w in d)} {w}")
extra = sorted(k for k in d if any(s in k.lower() for s in ("minimax","h3","ltx","motion","extend")))
print("--- inne wezly z h3/ltx/motion/extend w nazwie (pierwsze 80):")
for k in extra[:80]: print("  ", k)
PY
  echo "--- listy wyboru (pierwsze 25 wartosci) dla kluczowych wejsc:"
  python3 - "$OBJ" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
checks = {"UNETLoader":"unet_name","CLIPLoader":"clip_name","VAELoader":"vae_name","ModelPatchLoader":"name",
          "LoadVideo":"file","LoadAudio":"audio","LoraLoaderModelOnly":"lora_name","LoadImage":"image"}
for node, inp in checks.items():
    spec = d.get(node, {}).get("input", {}).get("required", {}).get(inp)
    if spec and isinstance(spec[0], list):
        vals = spec[0]
        print(f"  {node}.{inp}: {len(vals)} pozycji")
        for v in vals[:25]: print("     -", v)
    else:
        print(f"  {node}.{inp}: brak listy wyboru / wezla")
PY
else
  echo "object_info: NIE POBRANO (serwer nie odpowiada)"
fi

hr "OUG: struktura"
if [ -d "$OUG" ]; then
  echo "katalog istnieje"
  echo "--- _docs (nazwa, bajty):"; (cd "$OUG/_docs" 2>/dev/null && ls -la) 2>/dev/null
  echo "--- _PLAN (nazwa, bajty):"; (cd "$OUG/_PLAN" 2>/dev/null && ls -la) 2>/dev/null
  echo "--- liczba plikow w calym projekcie: $(find "$OUG" -type f 2>/dev/null | wc -l)"
  echo "--- rozmiar: $(du -sh "$OUG" 2>/dev/null | cut -f1)"
  [ -d "$OUG/.git" ] && { echo "--- git OUG:"; git -C "$OUG" log -3 --format='%h %ci %s' 2>/dev/null; git -C "$OUG" status --short 2>/dev/null | head -20; }
else
  echo "KATALOG OUG NIE ISTNIEJE: $OUG"
fi

hr "OUG: dokumenty (poczatek; dane wrazliwe nie sa tu potrzebne)"
for f in START_HERE.md HANDOFF_NEXT_CHAT_2026-11-02.md STATE_HANDOFF.md CLAUDE_QUICKREF.md HANDOFF_UI_COMFYUI.md HANDOFF_RECZNE_ODPALANIE.md JAK_ROBIC_PRZEDLUZANIE_RECZNIE.md; do
  head_file "$OUG/_PLAN/$f" 160
done
head_file "$OUG/_PLAN/accepted_clips.txt" 80

hr "OUG: skrypty produkcyjne - naglowki i argumenty (kluczowe)"
for f in gen_extender_refine.py oug_finish.sh assemble_whole.py gen_ltx_lip_seg.py gen_ltx_lip.py gen_h3_director.py gen_ref2va.py; do
  p="$OUG/_docs/$f"
  if [ -f "$p" ]; then
    echo "--- $f ($(wc -l < "$p") linii)"
    echo "[argumenty / ENV / sys.argv / argparse]"
    grep -nE "add_argument|sys\.argv|os\.environ|getenv|argv\[|argparse|usage" "$p" | head -60
    echo "[pierwsze 40 linii]"; sed -n '1,40p' "$p"
  else echo "--- BRAK: $f"; fi
done
echo "--- wszystkie ENV uzywane w _docs:"
grep -rhoE "os\.environ(\.get)?\(\s*['\"][A-Z_0-9]+['\"]|getenv\(\s*['\"][A-Z_0-9]+['\"]" "$OUG/_docs" 2>/dev/null | sort | uniq -c | head -40
echo "--- sciezki bezwzgledne w _docs (unikalne):"
grep -rhoE "(/home/[^\"' ]+|/media/[^\"' ]+|~/[^\"' ]+)" "$OUG/_docs" 2>/dev/null | sort -u | head -40

hr "BASELINE (sumy kontrolne)"
B="$(ls -t $HOME/oug_baseline_*.sha256 2>/dev/null | head -1)"
if [ -n "$B" ]; then
  echo "plik: $B, linii: $(wc -l < "$B")"
  (cd "$OUG" && sha256sum -c "$B" 2>/dev/null | awk -F: '{print $2}' | sort | uniq -c)
else echo "brak pliku oug_baseline_*.sha256 w $HOME"; fi

hr "PYTHON / PAKIETY (wersje)"
for m in torch numpy PIL cv2 fastapi; do python3 -c "import $m; print('$m', getattr($m,'__version__','?'))" 2>/dev/null || echo "$m: brak w python3"; done
command -v ffprobe >/dev/null && echo "ffprobe: tak"

hr "KONIEC"
echo "Wynik: $OUT"
[ -f "$OBJ" ] && echo "object_info: $OBJ"
