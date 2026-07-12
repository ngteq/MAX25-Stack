#!/bin/bash
# Manual kernel baycom test (legacy). Prefer: baycom-pr-ctl start
# Requires root. Set BAYCOM_IOBASE, BAYCOM_IRQ, BAYCOM_TTY.

set -euo pipefail

TTY="${BAYCOM_TTY:-${PCCOM_TTY:-/dev/ttyS0}}"
IOBASE="${BAYCOM_IOBASE:-${PCCOM_IOBASE:-}}"
IRQ="${BAYCOM_IRQ:-${PCCOM_IRQ:-}}"
BAUD="${BAYCOM_BAUD:-${PCCOM_BAUD:-1200}}"
CALLSIGN="${BAYCOM_CALL:-${PCCOM_CALL:-TEST-0}}"

if [[ "$(id -u)" -ne 0 ]]; then
	echo "This script must run as root." >&2
	exit 1
fi

if [[ -z "$IOBASE" || -z "$IRQ" ]]; then
	echo "Set BAYCOM_IOBASE and BAYCOM_IRQ (see: setserial -a $TTY)" >&2
	exit 1
fi

echo "=== 1. Release UART: $TTY ==="
if command -v setserial >/dev/null; then
	setserial "$TTY" uart none
elif [[ -x /sbin/setserial ]]; then
	/sbin/setserial "$TTY" uart none
else
	echo "WARN: setserial not installed" >&2
fi

echo "=== 2. Load baycom_ser_fdx ==="
modprobe -r baycom_ser_fdx 2>/dev/null || true
modprobe baycom_ser_fdx mode=ser12* iobase="$IOBASE" irq="$IRQ" baud="$BAUD"

IFACE=bcsf0
echo "=== 3. Bring up $IFACE (use baycom_sethdlc, not sethdlc) ==="
ip link set "$IFACE" up
baycom_sethdlc "$IFACE" 35 2>/dev/null || /usr/local/sbin/baycom_sethdlc "$IFACE" 35

echo ""
echo "Example /etc/baycom/axports/axports line:"
echo "  cb0  $CALLSIGN  $BAUD  255  2  BayCom on $TTY"
echo ""
ip link show "$IFACE" 2>/dev/null || true
echo ""
echo "Unload: modprobe -r baycom_ser_fdx; setserial $TTY uart 16550A"
