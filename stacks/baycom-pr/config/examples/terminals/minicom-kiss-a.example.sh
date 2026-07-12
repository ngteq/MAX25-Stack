#!/bin/bash
# minicom → KISS PTY (modem a). Stack must be running.
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail

KISS="${KISS_A:-/var/run/baycom-pr/kiss-a}"

command -v minicom >/dev/null || { echo "install minicom" >&2; exit 1; }
[[ -e "${KISS}" ]] || { echo "missing ${KISS} — run: baycom-pr-ctl start" >&2; exit 1; }

exec minicom baycom-kiss -D "${KISS}" -b "${BAUD_KISS:-9600}"
