#!/usr/bin/env bash
# notify.sh — run scorer to refresh recommendations, then exit.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

python3 "$SCRIPT_DIR/scorer.py"
