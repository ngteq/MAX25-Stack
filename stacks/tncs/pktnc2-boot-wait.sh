#!/bin/bash
# PK-TNC2 boot-wait — TheFirmware TNC-2 class, typically 9600 8N1
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
# Prefer local/pktnc2-serial.env on station; fall back to stacks/tncs/pktnc2-serial.env
for envfile in "${MAX25_ROOT:-}/local/pktnc2-serial.env" \
               "${ROOT}/../../local/pktnc2-serial.env" \
               "${ROOT}/pktnc2-serial.env"; do
  if [[ -f "${envfile}" ]]; then
    # shellcheck source=/dev/null
    source "${envfile}"
    break
  fi
done
export TNC_DEV="${PKTNC2_DEV:-${TNC_DEV:-/dev/ttyS5}}"
export TNC_BAUD="${PKTNC2_BAUD:-${TNC_BAUD:-9600}}"
export TNC_LINE="${PKTNC2_LINE:-${TNC_LINE:-8n1}}"
exec python3 "$ROOT/tnc2c-boot-wait.py" "$TNC_DEV" --baud "$TNC_BAUD" --line "$TNC_LINE" "$@"
