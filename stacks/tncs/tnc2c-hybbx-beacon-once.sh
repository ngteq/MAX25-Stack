#!/bin/bash
# One-shot AX.25 beacon like INI [broadcast] - stop HyBBX briefly, then restart.
# Auto-beacon (300s) runs from new HyBBX start.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
MSG="${1:-Broadcast: CB-0 online}"
SRC="${2:-CB-0}"
DST="${3:-*}"

echo "Manual beacon: ${SRC} -> ${DST}: ${MSG}"
if pgrep -x hybbx >/dev/null; then
    echo "Stopping HyBBX ..."
    pkill -x hybbx || sudo -u hybbx pkill -x hybbx
    sleep 2
fi
"$ROOT/tnc2c-send-test.sh" "$MSG" "$SRC" "$DST"
echo "Starting HyBBX ... (auto-beacon in ~300s)"
sudo -u hybbx /etc/hybbx/hybbx-start &
sleep 3
pgrep -a hybbx || echo "WARN: hybbx not started - try boot-wait + hybbx-start"
echo "Log: tail -f /etc/hybbx/logs/*.log  - expect: [broadcast] ax25"
