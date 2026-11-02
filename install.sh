#!/usr/bin/env bash
# Instalacja PsychOdelic Studio na czystym ComfyUI.
#  * buduje srodowisko studia i interfejs (wymaga Pythona 3.11+ i npm, jesli chcesz UI),
#  * kopiuje workflowy H3 (i LTX, jesli podasz) do ComfyUI/user/default/workflows (bez nadpisywania),
#  * tworzy ikonke w menu aplikacji,
#  * wypisuje, co dociągnąć ręcznie (nody i wagi). WAG NIE POBIERA.
# Uzycie: ./install.sh [--comfy ~/ComfyUI] [--ltx-workflow PLIK] [--yes] [--skip-ui]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

COMFY=""; LTX=""; YES=""; SKIP_UI=""
while [ $# -gt 0 ]; do
  case "$1" in
    --comfy) COMFY="$2"; shift 2 ;;
    --ltx-workflow) LTX="$2"; shift 2 ;;
    --yes) YES="--yes"; shift ;;
    --skip-ui) SKIP_UI=1; shift ;;
    *) echo "Nieznana opcja: $1" >&2; exit 2 ;;
  esac
done

echo "== 1/5 Python"
PY="$(command -v python3 || true)"
[ -n "$PY" ] || { echo "Brak python3."; exit 1; }
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || { echo "Potrzebny Python 3.11+."; exit 1; }

echo "== 2/5 Srodowisko studia (.venv)"
[ -x .venv/bin/python ] || "$PY" -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -e .

echo "== 3/5 Interfejs"
if [ -n "$SKIP_UI" ]; then
  echo "pominięto (--skip-ui)"
elif command -v npm >/dev/null; then
  (cd frontend && npm ci --silent && npm run build --silent)
  echo "zbudowano frontend/dist"
else
  echo "UWAGA: brak npm. Interfejs nie zostanie zbudowany. Zainstaluj Node.js (npm) i uruchom ponownie."
fi

echo "== 4/5 Workflowy w ComfyUI (bez wag, bez nodów)"
ARGS=(--report "$HERE/install_report.json")
[ -n "$COMFY" ] && ARGS+=(--comfy "$COMFY")
[ -n "$LTX" ] && ARGS+=(--ltx-workflow "$LTX")
[ -n "$YES" ] && ARGS+=("$YES")
PYTHONPATH="$HERE/backend" .venv/bin/python -m psychodelic.installer "${ARGS[@]}"  # blad = przerwanie instalacji

echo "== 5/5 Ikonka w menu aplikacji"
APPS="$HOME/.local/share/applications"
mkdir -p "$APPS"
sed "s#@STUDIO_DIR@#$HERE#g" desktop/psychodelic-studio.desktop.in > "$APPS/psychodelic-studio.desktop"
command -v update-desktop-database >/dev/null && update-desktop-database "$APPS" >/dev/null 2>&1 || true
echo "Gotowe. Uruchom: $HERE/start.sh  (albo ikonka 'PsychOdelic Studio')"
echo "Raport brakow: $HERE/install_report.json  (sekcja 'missing')"
