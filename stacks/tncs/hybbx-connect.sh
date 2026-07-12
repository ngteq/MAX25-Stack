#!/bin/bash
# HyBBX user session — telnet to BBS (KISS/AX.25 is HyBBX ↔ TNC, not this link).
# Usage: ./hybbx-connect.sh [host] [port]
set -euo pipefail
HOST="${1:-127.0.0.1}"
PORT="${2:-2323}"

if ! pgrep -x hybbx >/dev/null; then
    echo "WARN: hybbx läuft nicht — erst ./hybbx-start-tnc2c.sh" >&2
fi

if command -v telnet >/dev/null 2>&1; then
    exec telnet "$HOST" "$PORT"
fi
if [[ -x /usr/local/hybbx/hybbx-telnet ]]; then
    exec /usr/local/hybbx/hybbx-telnet "$HOST" "$PORT"
fi
echo "FAIL: telnet nicht gefunden" >&2
exit 1
