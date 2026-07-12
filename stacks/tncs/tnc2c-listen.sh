#!/bin/bash
# Passive listen on TNC2C - NO commands that can key PTT (no kiss on, no MONitor).
# Usage: ./tnc2c-listen.sh [seconds] [device]

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
[[ -f "$ROOT/tnc2c-serial.env" ]] && source "$ROOT/tnc2c-serial.env"

DEV="${2:-${TNC2C_DEV:-/dev/ttyS4}}"
SECS="${1:-5}"
BAUD="${TNC2C_BAUD:-19200}"
LINE="${TNC2C_LINE:-7e1}"

case "$LINE" in
7e1|7E1) STTY="cs7 parenb -cstopb" ;;
8n1|8N1) STTY="cs8 -parenb -cstopb" ;;
*) echo "Unknown line: $LINE" >&2; exit 1 ;;
esac

if pgrep -x hybbx >/dev/null 2>&1; then
    echo "WARN: hybbx is running - port may be in use" >&2
fi

echo "Passive listen: $DEV @ ${BAUD} ${LINE} for ${SECS}s (no TX commands)"
stty -F "$DEV" "$BAUD" $STTY raw -echo min 0 time 5

python3 <<PY
import fcntl, os, struct, time, termios

fd = os.open("$DEV", os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
TIOCM_RTS, TIOCM_DTR = 0x004, 0x002
TIOCMGET, TIOCMSET = 0x5415, 0x5416
flags = struct.unpack("I", fcntl.ioctl(fd, TIOCMGET, struct.pack("I", 0)))[0]
flags |= TIOCM_RTS | TIOCM_DTR
fcntl.ioctl(fd, TIOCMSET, struct.pack("I", flags))
termios.tcflush(fd, termios.TCIOFLUSH)

end = time.time() + float("$SECS")
chunks = []
while time.time() < end:
    try:
        b = os.read(fd, 4096)
        if b:
            chunks.append(b)
            print(f"+{len(b)} bytes")
    except BlockingIOError:
        time.sleep(0.05)

data = b"".join(chunks)
os.close(fd)
print(f"Total: {len(data)} bytes")
if data:
    print(data[:256].hex(" "))
PY
