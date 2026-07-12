#!/usr/bin/env python3
"""
tnc2c-host-reset - recover Landolt TNC2C terminal/host mode over serial.

Unlike raw shell redirects (printf > /dev/ttyS4), this keeps DTR+RTS asserted
so the TNC sees an attached terminal - same as minicom.

Usage:
  ./tnc2c-host-reset.sh
  ./tnc2c-host-reset.sh /dev/ttyS4
  ./tnc2c-host-reset.sh --power-hint      # remind to cycle TNC power first
  ./tnc2c-host-reset.sh --no-kiss         # skip KISS reset frame
"""

from __future__ import annotations

import argparse
import fcntl
import os
import struct
import sys
import time
import termios

BAUD = 19200

FIRMWARE_MARKERS = (
    b"TheFirmware",
    b"NORD",
    b"Version 2.7",
    b"Checksum",
    b"Copyright",
    b"DAMA",
    b"SMACK",
)

POWER_HINT = """\
Note: For echo-only, disconnect TNC power first (10-15 s), then reconnect.
Run this script immediately after (within ~30 s of LED blink).
"""


def load_env(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("TNC2C_DEV="):
                return line.split("=", 1)[1].strip()
    return None


def open_serial(dev: str) -> int:
    fd = os.open(dev, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    t = termios.tcgetattr(fd)
    t[0] = t[1] = 0
    t[2] = termios.CLOCAL | termios.CREAD | termios.CS8
    t[3] = t[4] = t[5] = termios.B19200
    t[6][termios.VMIN] = 0
    t[6][termios.VTIME] = 5
    termios.tcsetattr(fd, termios.TCSANOW, t)
    termios.tcflush(fd, termios.TCIOFLUSH)
    flags = struct.unpack("I", fcntl.ioctl(fd, 0x5415, struct.pack("I", 0)))[0]
    flags |= 0x004 | 0x002  # RTS + DTR
    fcntl.ioctl(fd, 0x5416, struct.pack("I", flags))
    return fd


def modem_lines(fd: int) -> tuple[bool, bool, bool]:
    flags = struct.unpack("I", fcntl.ioctl(fd, 0x5415, struct.pack("I", 0)))[0]
    return bool(flags & 0x004), bool(flags & 0x008), bool(flags & 0x100)


def read_for(fd: int, seconds: float) -> bytes:
    end = time.time() + seconds
    chunks: list[bytes] = []
    while time.time() < end:
        try:
            b = os.read(fd, 4096)
            if b:
                chunks.append(b)
        except BlockingIOError:
            time.sleep(0.02)
    return b"".join(chunks)


def write_flush(fd: int, data: bytes) -> None:
    os.write(fd, data)
    termios.tcdrain(fd)


def decode(data: bytes) -> str:
    return data.decode("ascii", errors="replace")


def has_banner(data: bytes) -> bool:
    lower = data.lower()
    return any(m.lower() in lower for m in FIRMWARE_MARKERS)


def is_echo_only(info_reply: bytes) -> bool:
    stripped = info_reply.strip()
    return stripped in (b"INFO", b"INFO\r", b"INFO\n", b"INFO\r\n")


def print_block(label: str, data: bytes) -> None:
    print(f"--- {label} ({len(data)} B) ---")
    if data:
        print(decode(data), end="" if data.endswith(b"\n") else "\n")
    else:
        print("(empty)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="TNC2C host-mode reset with DTR+RTS (replaces printf > tty)"
    )
    parser.add_argument("device", nargs="?", default=None, help="serial device")
    parser.add_argument(
        "--power-hint",
        action="store_true",
        help="print power-cycle reminder before running",
    )
    parser.add_argument(
        "--no-kiss",
        action="store_true",
        help="skip KISS reset frame (only kiss off + INFO)",
    )
    args = parser.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    dev = args.device or load_env(os.path.join(root, "tnc2c-serial.env")) or "/dev/ttyS4"

    if args.power_hint:
        print(POWER_HINT)

    if os.system("pgrep minicom >/dev/null 2>&1") == 0:
        print("FAIL: minicom is running - exit it first (pkill minicom)", file=sys.stderr)
        return 2

    if not os.path.exists(dev):
        print(f"FAIL: {dev} does not exist", file=sys.stderr)
        return 2
    if not os.access(dev, os.R_OK | os.W_OK):
        print(f"FAIL: no access to {dev} (dialout group?)", file=sys.stderr)
        return 2

    print(f"TNC2C host-reset @ {dev} {BAUD} 8N1 (DTR+RTS high)")
    received = b""

    try:
        fd = open_serial(dev)
    except OSError as e:
        print(f"FAIL: {dev}: {e}", file=sys.stderr)
        return 2

    rts, cts, dsr = modem_lines(fd)
    print(f"Modem: RTS={int(rts)} CTS={int(cts)} DSR={int(dsr)}")

    passive = read_for(fd, 2.0)
    received += passive
    print_block("passive (2s)", passive)

    if not args.no_kiss:
        write_flush(fd, b"\xc0\xff\xc0")
        time.sleep(1.0)
        after_kiss = read_for(fd, 1.0)
        received += after_kiss
        print_block("after KISS-reset", after_kiss)

    write_flush(fd, b"kiss off\r")
    time.sleep(1.0)
    after_kiss_off = read_for(fd, 1.0)
    received += after_kiss_off
    print_block("kiss off", after_kiss_off)

    write_flush(fd, b"INFO\r")
    info_reply = read_for(fd, 5.0)
    received += info_reply
    print_block("INFO", info_reply)

    os.close(fd)

    print()
    if has_banner(received):
        print("OK: firmware banner detected - host/terminal mode active")
        return 0
    if is_echo_only(info_reply):
        print("ECHO: INFO -> echo only - TNC not in host mode")
        print("  -> Disconnect TNC power (10 s), reconnect, then immediately:")
        print("     ./tnc2c-host-reset.sh --power-hint")
        return 1
    if received:
        print("PARTIAL: reply without firmware banner")
        return 1
    print("SILENT: no response")
    return 1


if __name__ == "__main__":
    sys.exit(main())
