#!/usr/bin/env bash
# Build the single-file binary for the host OS.
# Result: dist/bios (Linux/macOS) or dist/bios.exe (Windows).

set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install pygame numpy pyinstaller

rm -rf build dist
pyinstaller bios.spec

echo
echo "Build complete. Output:"
ls -la dist/
