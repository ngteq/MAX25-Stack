#!/bin/bash
# TNC2C host-mode recovery — DTR+RTS high (unlike raw printf > /dev/ttyS4).
#
# Usage:
#   ./tnc2c-host-reset.sh
#   ./tnc2c-host-reset.sh --power-hint    # remind to cycle TNC power first
#   ./tnc2c-host-reset.sh --no-kiss       # skip KISS reset frame

set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$ROOT/tnc2c-host-reset.py" "$@"
