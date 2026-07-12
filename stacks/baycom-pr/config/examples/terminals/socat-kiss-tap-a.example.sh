#!/bin/bash
# socat hex tap on KISS PTY (modem a). Stack must be running.
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail

KISS="${KISS_A:-/var/run/baycom-pr/kiss-a}"

command -v socat >/dev/null || { echo "install socat" >&2; exit 1; }
[[ -e "${KISS}" ]] || { echo "missing ${KISS} — run: baycom-pr-ctl start" >&2; exit 1; }

exec socat -x "OPEN:${KISS},raw,echo=0" STDIO
