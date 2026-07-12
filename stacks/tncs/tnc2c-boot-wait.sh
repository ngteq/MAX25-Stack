#!/bin/bash
# TNC2C boot-wait — Landolt TNC2C, typically 19200 8N1, DTR during power-on
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=load-serial-env.sh
source "${ROOT}/load-serial-env.sh"
load_serial_env tnc2c "${ROOT}" || true
apply_tnc2c_env
if [[ -n "${SERIAL_ENV_FILE:-}" ]]; then
  echo "Using serial env: ${SERIAL_ENV_FILE}" >&2
else
  echo "WARN: no tnc2c-serial.env found — using ${TNC_DEV} ${TNC_BAUD} ${TNC_LINE}" >&2
fi
exec python3 "${ROOT}/tnc2c-boot-wait.py" "${TNC_DEV}" --baud "${TNC_BAUD}" --line "${TNC_LINE}" "$@"
