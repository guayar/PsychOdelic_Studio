#!/usr/bin/env bash
# Uruchamia studio (tylko backend + UI) i otwiera przegladarke. NIE uruchamia ComfyUI.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
if [ ! -x .venv/bin/python ]; then
  echo "Brak instalacji. Uruchom najpierw: ./install.sh" >&2
  exit 1
fi
# Ikonka w menu i na pasku: odtwarzana przy kazdym starcie (idempotentne, bez sudo).
if [ -x desktop/install_launcher.sh ]; then
  bash desktop/install_launcher.sh "$HERE" >/dev/null 2>&1 || echo "Nie udalo sie zainstalowac ikonki (launcher)." >&2
fi
export PSYCHODELIC_DATA="${PSYCHODELIC_DATA:-$HOME/.local/share/psychodelic-studio}"
export PSYCHODELIC_UI_DIR="$HERE/frontend/dist"
PORT="${PSYCHODELIC_PORT:-8765}"
URL="http://127.0.0.1:${PORT}"
( sleep 2; command -v xdg-open >/dev/null && xdg-open "$URL" >/dev/null 2>&1 ) &
PYTHONPATH="$HERE/backend" PSYCHODELIC_PORT="$PORT" exec .venv/bin/python -m psychodelic
