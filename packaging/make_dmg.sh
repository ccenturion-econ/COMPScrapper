#!/usr/bin/env bash
# Arma dist/COMPScrapper.dmg para arrastrar a Aplicaciones (Mac).
# Lo usan tanto el CI como la compilación local. Requiere dist/COMPScrapper.app.
set -euo pipefail

APP="dist/COMPScrapper.app"
DMG="dist/COMPScrapper.dmg"

[ -d "$APP" ] || { echo "No existe $APP (compilá primero con PyInstaller)"; exit 1; }

STAGE="$(mktemp -d)"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"   # acceso directo para arrastrar
xattr -cr "$STAGE" 2>/dev/null || true       # limpiar detritus (iCloud)

rm -f "$DMG"
hdiutil create -volname "COMPScrapper" -srcfolder "$STAGE" -ov -format UDZO "$DMG" >/dev/null
rm -rf "$STAGE"
echo "Creado $DMG"
