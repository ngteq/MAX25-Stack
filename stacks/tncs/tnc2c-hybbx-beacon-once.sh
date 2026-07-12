#!/bin/bash
# Einmaliger AX.25-Beacon wie INI [broadcast] — HyBBX kurz stoppen, dann neu starten.
# Auto-Beacon (300s) läuft ab neuem HyBBX-Start.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
MSG="${1:-Broadcast: CB-0 online}"
SRC="${2:-CB-0}"
DST="${3:-*}"

echo "Manueller Beacon: ${SRC} -> ${DST}: ${MSG}"
if pgrep -x hybbx >/dev/null; then
    echo "Stoppe HyBBX …"
    pkill -x hybbx || sudo -u hybbx pkill -x hybbx
    sleep 2
fi
"$ROOT/tnc2c-send-test.sh" "$MSG" "$SRC" "$DST"
echo "Starte HyBBX … (Auto-Beacon in ~300s)"
sudo -u hybbx /etc/hybbx/hybbx-start &
sleep 3
pgrep -a hybbx || echo "WARN: hybbx nicht gestartet — ggf. boot-wait + hybbx-start"
echo "Log: tail -f /etc/hybbx/logs/*.log  — Erwartung: [broadcast] ax25"
