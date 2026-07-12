#!/bin/bash
# Expose KISS PTY (modem a) on TCP port 8001. Stack must be running.
# Firewall / trust boundary is your responsibility.
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail

KISS="${KISS_A:-/var/run/baycom-pr/kiss-a}"
PORT="${KISS_TCP_PORT:-8001}"

command -v socat >/dev/null || { echo "install socat" >&2; exit 1; }
[[ -e "${KISS}" ]] || { echo "missing ${KISS} — run: baycom-pr-ctl start" >&2; exit 1; }

echo "KISS ${KISS} → TCP :${PORT} (Ctrl-C to stop)"
exec socat "TCP-LISTEN:${PORT},reuseaddr,fork" "OPEN:${KISS},raw,echo=0"
