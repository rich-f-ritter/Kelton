#!/usr/bin/env bash
# Install the rent-comps-high-level skill into the user-global skills dir so it's
# available in every project. Run from anywhere; re-run to update.
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="${HOME}/.claude/skills/rent-comps-high-level"
mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -r "$SRC" "$DEST"
echo "Installed rent-comps-high-level -> $DEST"
