#!/usr/bin/env bash
# Instaluje ikonke i launcher PsychOdelic Studio w katalogu uzytkownika (bez sudo).
# Uzycie: desktop/install_launcher.sh [KATALOG_STUDIA]
# Po instalacji ikonke "PsychOdelic Studio" mozna przypiac na pasek (prawy klik -> Dodaj do ulubionych).
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
[ "${1:-}" ] && HERE="$(cd "$1" && pwd)"

APPS="$HOME/.local/share/applications"
ICONS="$HOME/.local/share/icons/hicolor"
mkdir -p "$APPS" "$ICONS/scalable/apps" "$ICONS/256x256/apps"

cp "$HERE/desktop/psychodelic-studio.svg" "$ICONS/scalable/apps/psychodelic-studio.svg"
cp "$HERE/desktop/psychodelic-studio-256.png" "$ICONS/256x256/apps/psychodelic-studio.png"
sed "s#@STUDIO_DIR@#$HERE#g" "$HERE/desktop/psychodelic-studio.desktop.in" > "$APPS/psychodelic-studio.desktop"
chmod 644 "$APPS/psychodelic-studio.desktop"

command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -q -t "$ICONS" >/dev/null 2>&1 || true
command -v update-desktop-database >/dev/null && update-desktop-database "$APPS" >/dev/null 2>&1 || true
echo "Launcher: $APPS/psychodelic-studio.desktop"
echo "Ikonka:   $ICONS/256x256/apps/psychodelic-studio.png"
