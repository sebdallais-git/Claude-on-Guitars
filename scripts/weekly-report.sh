#!/usr/bin/env bash
# weekly-report.sh — placeholder for a weekly summary digest.
# TODO: aggregate sold / new / on-hold stats and top recommendations
#       into a single email or Telegram message.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Weekly report not yet implemented.  Run scorer for recommendations:"
echo "  python3 $SCRIPT_DIR/scorer.py"
