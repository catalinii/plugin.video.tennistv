#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADDON_DIR_NAME="$(basename "$SCRIPT_DIR")"
ZIP_NAME="${ADDON_DIR_NAME}.zip"

cd "$SCRIPT_DIR/.."

zip -r "$SCRIPT_DIR/$ZIP_NAME" "$ADDON_DIR_NAME" \
    -x "$ADDON_DIR_NAME/.git*" \
    -x "$ADDON_DIR_NAME/pack.sh" \
    -x "$ADDON_DIR_NAME/$ZIP_NAME" \
    -x "$ADDON_DIR_NAME/*.pyc" \
    -x "$ADDON_DIR_NAME/__pycache__/*" \
    -x "$ADDON_DIR_NAME/.vscode/*" \
    -x "$ADDON_DIR_NAME/.idea/*"

echo "Add-on successfully packed to $SCRIPT_DIR/$ZIP_NAME"
