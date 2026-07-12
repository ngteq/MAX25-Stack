#!/bin/bash
# PK-TNC2 boot-wait — TheFirmware TNC-2 class, typically 9600 8N1
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=load-serial-env.sh
source "${ROOT}/load-serial-env.sh"
load_serial_env pktnc2 "${ROOT}" || true
apply_pktnc2_env
if [[ -n "${SERIAL_ENV_FILE:-}" ]]; then
  echo "Using serial env: ${SERIAL_ENV_FILE}" >&2
else
  echo "WARN: no pktnc2-serial.env found — using ${TNC_DEV} ${TNC_BAUD} ${TNC_LINE}" >&2
fi
exec python3 "${ROOT}/tnc2c-boot-wait.py" "${TNC_DEV}" --baud "${TNC_BAUD}" --line "${TNC_LINE}" "$@"
