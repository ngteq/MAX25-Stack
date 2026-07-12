#!/bin/bash
# picocom → raw UART (modem a). Stack must be STOPPED.
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail

SERIAL="${SERIAL_A:-/dev/ttyS0}"

command -v picocom >/dev/null || { echo "install picocom" >&2; exit 1; }
if baycom-pr-ctl status 2>/dev/null | grep -q 'baycom_ser_fdx'; then
	echo "stop stack first: baycom-pr-ctl stop" >&2
	exit 1
fi

exec picocom -b "${BAUD_SER12:-1200}" -r -l "${SERIAL}"
