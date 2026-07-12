#!/bin/bash
# HyBBX + TNC2C only (/dev/ttyS4). Run as user hybbx (or sudo -u hybbx).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

if pgrep -x hybbx >/dev/null; then
    echo "hybbx läuft bereits ($(pgrep -x hybbx))" >&2
    exit 1
fi
if fuser -s /dev/ttyS4 2>/dev/null; then
    echo "WARN: /dev/ttyS4 belegt — minicom stoppen" >&2
    fuser -v /dev/ttyS4 2>&1 || true
fi

echo "=== boot-wait TNC2C (Strom AUS → Skript → AN) ==="
"$ROOT/tnc2c-boot-wait.sh" || {
    echo "FAIL: kein HOST — boot-wait wiederholen (TNC aus vor Skript)" >&2
    exit 1
}

echo "=== HyBBX start ==="
exec /usr/local/hybbx/hybbx-start
