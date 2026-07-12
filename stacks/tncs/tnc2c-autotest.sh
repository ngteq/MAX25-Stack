#!/bin/bash
# Exhaustive safe TNC2C autotest — no PTT unless --tx.
# Usage:
#   ./tnc2c-autotest.sh --host-check          # after power reset (~6s, DTR stays high)
#   ./tnc2c-autotest.sh --host-check --write-env
#   ./tnc2c-autotest.sh --quick               # full sweep, 19200 first (~2 min)
#   ./tnc2c-autotest.sh --write-env

set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$ROOT/tnc2c-autotest.py" "$@"
