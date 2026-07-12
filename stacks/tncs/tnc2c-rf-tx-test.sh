#!/bin/bash
# Send N AX.25 UI frames via KISS (HyBBX must be stopped).
# Usage: ./tnc2c-rf-tx-test.sh [count] [message-prefix] [src] [dst]
# Example (root): pkill hybbx; ./tnc2c-rf-tx-test.sh 3 "TX test" CB-0 QST

set -euo pipefail

COUNT="${1:-3}"
PREFIX="${2:-TX test}"
SRC="${3:-CB-0}"
DST="${4:-QST}"
GAP="${TNC2C_TX_GAP:-8}"
ROOT="$(cd "$(dirname "$0")" && pwd)"

if pgrep -x hybbx >/dev/null 2>&1; then
    echo "ERROR: hybbx läuft — als root: pkill hybbx" >&2
    exit 1
fi

echo "RF TX: ${COUNT}× ${SRC} -> ${DST}, ${GAP}s Abstand (SQ zu, CD aus)"
for i in $(seq 1 "$COUNT"); do
    echo "=== SEND ${i}/${COUNT} $(date +%H:%M:%S) ==="
    "$ROOT/tnc2c-send-test.sh" "${PREFIX} ${i}/${COUNT}" "$SRC" "$DST"
    if [[ "$i" -lt "$COUNT" ]]; then
        sleep "$GAP"
    fi
done
echo "Fertig — PTT-LED / Modemton am Funk prüfen."
