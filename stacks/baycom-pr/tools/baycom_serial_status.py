#!/usr/bin/env python3
# BayCom PR-Stack — Copyright (C) 2026 BayCom PR-Stack contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Passive serial-line check for a BayCom ser12 UART (read-only)."""

from __future__ import annotations

import argparse
import array
import fcntl
import os
import sys
import termios

TIOCMGET = 0x5415
TIOCM_DTR = 2
TIOCM_RTS = 4
TIOCM_CTS = 8
TIOCM_DSR = 16
TIOCM_CD = 64


def read_lines(fd: int) -> dict[str, bool]:
    buf = array.array("I", [0])
    fcntl.ioctl(fd, TIOCMGET, buf, True)
    v = buf[0]
    return {
        "DTR": bool(v & TIOCM_DTR),
        "RTS": bool(v & TIOCM_RTS),
        "CTS": bool(v & TIOCM_CTS),
        "DSR": bool(v & TIOCM_DSR),
        "CD": bool(v & TIOCM_CD),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="BayCom ser12 serial line status (passive)")
    parser.add_argument("device", nargs="?", default="/dev/ttyS0")
    args = parser.parse_args()

    if not os.path.exists(args.device):
        print(f"Device not found: {args.device}", file=sys.stderr)
        return 1

    fd = os.open(args.device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        attrs = termios.tcgetattr(fd)
        print(f"Device:    {args.device}")
        print(f"Baudrate:  ispeed={attrs[4]} ospeed={attrs[5]} (termios constants)")
        print(f"Modem:     {read_lines(fd)}")
        print()
        print("Expected BayCom ser12 DE-9 mapping:")
        print("  DTR = TX data, RTS = PTT, CTS = RX data, TXD = modem power")
        print("  Without active BayCom software CTS usually stays idle.")
    finally:
        os.close(fd)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
