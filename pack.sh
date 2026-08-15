#!/usr/bin/env bash
#
# Pack the Tennis TV addon into a Kodi-installable zip archive.
#
# Usage:
#   ./pack.sh
#
# This produces "plugin.video.tennistv-<version>.zip" in the current
# directory. Install it in Kodi via:
#   Settings -> Add-ons -> Install from zip file
#
# The version is read automatically from addon.xml.
#
set -euo pipefail

cd "$(dirname "$0")"

NAME="plugin.video.tennistv"
VERSION="$(grep -oE '<addon id="[^"]*"[^>]*version="[^"]*"' addon.xml | head -1 | grep -oE 'version="[^"]*"' | head -1 | sed 's/version="//; s/"//')"
ZIP="${NAME}-${VERSION}.zip"

if [ -z "$VERSION" ]; then
    echo "Error: could not determine version from addon.xml" >&2
    exit 1
fi

# Kodi expects addon.xml at the root of the archive.
rm -f "$ZIP"
zip -r "$ZIP" addon.xml default.py icon.png resources \
    -x '*/__pycache__/*' '*.pyc' '.DS_Store'

echo "Created $ZIP"
