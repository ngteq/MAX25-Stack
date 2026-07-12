#!/bin/bash
# PK-TNC2 boot-wait — 9600 8N1 on /dev/ttyS5
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
source "$ROOT/pktnc2-serial.env"
export TNC_DEV TNC_BAUD TNC_LINE
exec python3 "$ROOT/tnc2c-boot-wait.py" "$TNC_DEV" --baud "$TNC_BAUD" --line "$TNC_LINE" "$@"
