#!/bin/bash
# picocom → KISS PTY (modem a). Stack must be running.
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail

KISS="${KISS_A:-/var/run/baycom-pr/kiss-a}"

command -v picocom >/dev/null || { echo "install picocom" >&2; exit 1; }
[[ -e "${KISS}" ]] || { echo "missing ${KISS} — run: baycom-pr-ctl start" >&2; exit 1; }

exec picocom -b "${BAUD_KISS:-9600}" -r -l "${KISS}"
