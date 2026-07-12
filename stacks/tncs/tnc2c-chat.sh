#!/bin/bash
# Quick TNC2C terminal check on /dev/ttyS4 (no RF required).
# WARNING: kiss on / MONitor can KEY PTT and transmit on the radio!
# For passive RX only use: ./tnc2c-listen.sh
# Usage: ./tnc2c-chat.sh [baud] [line]
#   line: 7e1 | 8n1   (default from $TNC2C_LINE or 9600/7e1)

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
[[ -f "$ROOT/tnc2c-serial.env" ]] && source "$ROOT/tnc2c-serial.env"

DEV="${TNC2C_DEV:-/dev/ttyS4}"
BAUD="${1:-${TNC2C_BAUD:-19200}}"
LINE="${2:-${TNC2C_LINE:-7e1}}"

case "$LINE" in
7e1|7E1) STTY="cs7 parenb -cstopb" ;;
8n1|8N1) STTY="cs8 -parenb -cstopb" ;;
*) echo "Unknown line format: $LINE (use 7e1 or 8n1)" >&2; exit 1 ;;
esac

if [[ ! -r "$DEV" || ! -w "$DEV" ]]; then
    echo "Cannot access $DEV (dialout group?)" >&2
    exit 1
fi

echo "TNC2C chat: $DEV @ ${BAUD} ${LINE}"
stty -F "$DEV" "$BAUD" $STTY raw -echo -icanon min 0 time 10

exec 3<>"$DEV"

printf '\r' >&3
sleep 0.5
timeout 2 cat <&3 | xxd -g1 | head -8 || true

# Do NOT send kiss on — keys PTT. Only safe host echo probes:
for cmd in '' INFO HELP; do
    echo "--- $cmd ---"
    if [[ -n "$cmd" ]]; then
        printf '%s\r' "$cmd" >&3
    else
        printf '\r' >&3
    fi
    sleep 1
    timeout 4 cat <&3 | tee /tmp/tnc2c-last.bin | xxd -g1 | head -12
    strings -n 3 /tmp/tnc2c-last.bin || true
done

exec 3<&-
exec 3>&-
