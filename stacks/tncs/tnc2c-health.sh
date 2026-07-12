#!/bin/bash
# Full TNC2C health check — serial, host mode, KISS, optional TX.
# Usage:
#   ./tnc2c-health.sh              # safe, no transmit
#   ./tnc2c-health.sh --tx         # includes KISS send (PTT!)

set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$ROOT/tnc2c-health.py" "$@"
