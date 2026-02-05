#!/usr/bin/env bash
# daily-scan.sh — convenience wrapper; starts watchdog (which launches searcher).
# Meant to be called from CI or a cron job.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

exec python3 "$SCRIPT_DIR/watchdog.py"
