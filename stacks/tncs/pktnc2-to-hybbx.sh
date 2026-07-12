#!/bin/bash
# AX.25 UI frame PK-TNC2 → HyBBX/TNC2C over the air.
# HyBBX must be running on Unit A (ttyS4). PK-TNC2: boot-wait first.
#
# Usage: ./pktnc2-to-hybbx.sh [message] [src] [dst]
# Default: "CONNECT" UN1TME-2 UN1TME

set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
source "$ROOT/pktnc2-serial.env"

MSG="${1:-CONNECT}"
SRC="${2:-UN1TME-2}"
DST="${3:-UN1TME}"

if pgrep -x hybbx >/dev/null && fuser -s "$TNC_DEV" 2>/dev/null; then
    echo "WARN: HyBBX belegt evtl. ttyS5 — nur ttyS4 sollte aktiv sein" >&2
fi

echo "ON-AIR TX: $SRC -> $DST: $MSG"
echo "Funk: beide auf gleicher MHz (z. B. 27.235 K24), SQ zu vor Senden"
export TNC2C_DEV="$TNC_DEV" TNC2C_BAUD="$TNC_BAUD" TNC2C_LINE="$TNC_LINE"
exec "$ROOT/tnc2c-send-test.sh" "$MSG" "$SRC" "$DST"
