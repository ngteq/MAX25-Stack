#!/bin/bash
# Preflight: HyBBX off? handshake OK? quick echo on TNC2C.
# Usage: ./tnc2c-check.sh [device]

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
[[ -f "$ROOT/tnc2c-serial.env" ]] && source "$ROOT/tnc2c-serial.env"

DEV="${1:-${TNC2C_DEV:-/dev/ttyS4}}"
BAUD="${TNC2C_BAUD:-19200}"
LINE="${TNC2C_LINE:-7e1}"

echo "=== TNC2C check: $DEV (${BAUD} ${LINE}) ==="

if pgrep -x hybbx >/dev/null 2>&1; then
    echo "WARN: hybbx is running ($(pgrep -x hybbx | tr '\n' ' ')) - port may be in use"
fi

if fuser -s "$DEV" 2>/dev/null; then
    echo "WARN: $DEV in use:"
    fuser -v "$DEV" 2>&1 || true
else
    echo "OK: $DEV not in use"
fi

if [[ ! -r "$DEV" || ! -w "$DEV" ]]; then
    echo "FAIL: no access to $DEV (dialout group?)" >&2
    exit 1
fi

case "$LINE" in
7e1|7E1) STTY="cs7 parenb -cstopb" ;;
8n1|8N1) STTY="cs8 -parenb -cstopb" ;;
*) echo "Unknown line: $LINE" >&2; exit 1 ;;
esac

stty -F "$DEV" "$BAUD" $STTY raw -echo min 0 time 5

python3 <<PY
import fcntl, os, struct, time

TIOCMGET = 0x5415
fd = os.open("$DEV", os.O_RDWR | os.O_NOCTTY)
flags = struct.unpack("I", fcntl.ioctl(fd, TIOCMGET, struct.pack("I", 0)))[0]
names = [(0x004, "RTS"), (0x008, "CTS"), (0x002, "DTR"), (0x100, "DSR")]
for bit, name in names:
    print(f"  {name}={'1' if flags & bit else '0'}")
os.write(fd, b"INFO\r")
time.sleep(0.8)
data = os.read(fd, 512)
os.close(fd)
print(f"  RX {len(data)} bytes:", data[:80])
PY

if [[ -x "$ROOT/tnc2c-probe" ]]; then
    echo "--- tnc2c-probe (single port) ---"
    "$ROOT/tnc2c-probe" "$DEV" 2>&1 | tail -20
fi

echo "=== done ==="
