#!/usr/bin/env bash
# Audyt TYLKO ODCZYT. Nie instaluje, nie zmienia plikow, nie uruchamia renderow.
# Uzycie: ./scripts/collect_local_audit.sh [KATALOG_OUG] [KATALOG_COMFYUI]
# Wynik: ./audit_out/audit_<data>.txt  (przejrzyj przed wyslaniem: zawiera sciezki i nazwy plikow)
set -u
OUG="${1:-}"
COMFY="${2:-$HOME/comfyui-local}"
COMFY_URL="${PSYCHODELIC_COMFY_URL:-http://127.0.0.1:8188}"
OUT_DIR="$(pwd)/audit_out"
mkdir -p "$OUT_DIR"
REPORT="$OUT_DIR/audit_$(date +%Y%m%d_%H%M%S).txt"

section() { echo; echo "===== $1 ====="; }
{
  section "system"
  uname -a
  (command -v lsb_release >/dev/null && lsb_release -a) 2>/dev/null || cat /etc/os-release 2>/dev/null

  section "gpu (tylko odczyt)"
  (command -v rocminfo >/dev/null && rocminfo | grep -E 'Marketing Name|gfx' | head -8) || echo "rocminfo: brak"
  (command -v rocm-smi >/dev/null && rocm-smi --showmeminfo vram 2>/dev/null | head -20) || echo "rocm-smi: brak"

  section "ComfyUI: katalog i konfiguracja (odczyt)"
  if [ -d "$COMFY" ]; then
    echo "katalog: $COMFY"
    ls -la "$COMFY" 2>/dev/null | head -40
    echo "--- custom_nodes:"; ls "$COMFY/custom_nodes" 2>/dev/null
    echo "--- extra_model_paths.yaml:"; cat "$COMFY/extra_model_paths.yaml" 2>/dev/null || echo "brak"
    echo "--- start script:"; cat "$COMFY/scripts/start-comfy.sh" 2>/dev/null || echo "brak scripts/start-comfy.sh"
    for repo in "$COMFY" "$COMFY"/custom_nodes/*/; do
      if [ -d "$repo/.git" ]; then
        echo "--- git: $repo"; git -C "$repo" log -1 --format='%H %ci %s' 2>/dev/null
      fi
    done
    echo "--- wersja ComfyUI (plik, jesli jest):"; grep -rhoE "__version__ *= *\"[^\"]+\"" "$COMFY/comfyui_version.py" 2>/dev/null || echo "nieznana z pliku"
  else
    echo "katalog ComfyUI nie istnieje: $COMFY (podaj jako drugi argument)"
  fi

  section "serwer ComfyUI (tylko GET)"
  if curl -sS -m 5 "$COMFY_URL/system_stats" -o "$OUT_DIR/system_stats.json" 2>/dev/null; then
    echo "system_stats: zapisany do $OUT_DIR/system_stats.json"
    curl -sS -m 10 "$COMFY_URL/object_info" -o "$OUT_DIR/object_info.json" 2>/dev/null && echo "object_info: zapisany do $OUT_DIR/object_info.json"
  else
    echo "serwer nie odpowiada pod $COMFY_URL: BRAK POTWIERDZENIA (to nie dowod, ze modeli brak)"
  fi

  section "projekt Once Upon a Garden (tylko nazwy plikow, bez tresci)"
  if [ -n "$OUG" ] && [ -d "$OUG" ]; then
    echo "katalog: $OUG"
    find "$OUG" -maxdepth 2 -type f \( -name '*.md' -o -name '*.py' -o -name '*.sh' -o -name '*.json' -o -name '*.txt' \) | sed "s#^$OUG/##" | sort | head -200
    echo "--- _docs/ (skrypty produkcyjne):"; ls "$OUG/_docs" 2>/dev/null
    echo "--- _PLAN/:"; ls "$OUG/_PLAN" 2>/dev/null
    if [ -d "$OUG/.git" ]; then echo "--- git OUG:"; git -C "$OUG" log -3 --format='%H %ci %s'; fi
  else
    echo "nie podano katalogu OUG (pierwszy argument)"
  fi

  section "python / pakiety (tylko wersje)"
  python3 --version
  for mod in torch numpy PIL fastapi; do
    python3 -c "import $mod,sys; print('$mod', getattr($mod,'__version__','?'))" 2>/dev/null || echo "$mod: niedostepny w python3"
  done
  command -v ffmpeg >/dev/null && ffmpeg -version | head -1
  command -v ffprobe >/dev/null && echo "ffprobe: obecny" || echo "ffprobe: brak"
} > "$REPORT" 2>&1
echo "Raport zapisany: $REPORT"
echo "Przejrzyj go przed wyslaniem (zawiera sciezki)."
