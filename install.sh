#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.opticode_venv"

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install -e "$ROOT_DIR"

cat <<EOF
Opticode installed into:
  $VENV_DIR

Run with:
  $VENV_DIR/bin/opticode --help
EOF
