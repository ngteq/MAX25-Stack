#!/usr/bin/env python3
"""
tnc2c-host-reset - recover TNC-2 class terminal/host mode over serial.

Uses full software recovery ladder (KISS-return, JHOST0, RESTART) — no power
cycle required unless DTR was low at cold boot.

Usage:
  ./tnc2c-host-reset.sh
  ./tnc2c-host-reset.sh /dev/ttyS4
  ./tnc2c-host-reset.sh --kiss          # recover + enter KISS
  ./tnc2c-host-reset.sh --power-hint    # remind to cycle TNC power first
  ./tnc2c-host-reset.sh --no-kiss       # skip KISS reset frame (step 2 only)
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import time

BAUD_DEFAULT = 19200
LINE_DEFAULT = "8n1"

FIRMWARE_MARKERS = (
    b"TheFirmware",
    b"NORD",
    b"Version 2.7",
    b"Checksum",
    b"Copyright",
    b"DAMA",
    b"SMACK",
)


def load_recovery():
    root = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(root, "tnc_serial_recovery.py")
    spec = importlib.util.spec_from_file_location("tnc_serial_recovery", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_env(path: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def parse_line(line: str) -> tuple[int, int]:
    import termios

    line = line.lower()
    if line == "7e1":
        return termios.CS7, termios.PARENB
    if line == "8n1":
        return termios.CS8, 0
    raise ValueError(f"unsupported serial line: {line}")


def parse_baud(baud: int) -> int:
    import termios

    table = {
        1200: termios.B1200,
        2400: termios.B2400,
        4800: termios.B4800,
        9600: termios.B9600,
        19200: termios.B19200,
    }
    if baud not in table:
        raise ValueError(f"unsupported baud: {baud}")
    return table[baud]


def open_serial(dev: str, baud: int, line: str) -> int:
    import fcntl
    import struct
    import termios

    speed = parse_baud(baud)
    databits, parity = parse_line(line)
    fd = os.open(dev, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    t = termios.tcgetattr(fd)
    t[0] = t[1] = 0
    t[2] = termios.CLOCAL | termios.CREAD | databits | parity
    t[3] = t[4] = t[5] = speed
    t[6][termios.VMIN] = 0
    t[6][termios.VTIME] = 5
    termios.tcsetattr(fd, termios.TCSANOW, t)
    termios.tcflush(fd, termios.TCIOFLUSH)
    flags = struct.unpack("I", fcntl.ioctl(fd, 0x5415, struct.pack("I", 0)))[0]
    flags |= 0x004 | 0x002
    fcntl.ioctl(fd, 0x5416, struct.pack("I", flags))
    return fd


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
    import termios

    os.write(fd, data)
    termios.tcdrain(fd)


POWER_HINT = """\
Note: If recovery fails (echo only), disconnect TNC power (10-15 s), reconnect
while DTR+RTS stay high — run tnc2c-boot-wait.sh or this script immediately.
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="TNC host-mode recovery with DTR+RTS (TheFirmware ladder)"
    )
    parser.add_argument("device", nargs="?", default=None)
    parser.add_argument("--baud", type=int, default=None)
    parser.add_argument("--line", default=None, choices=("8n1", "7e1"))
    parser.add_argument("--kiss", action="store_true", help="enter KISS after recover")
    parser.add_argument(
        "--kiss-entry",
        default="kiss_on",
        choices=("kiss_on", "auto"),
        help="KISS entry method with --kiss",
    )
    parser.add_argument("--power-hint", action="store_true")
    parser.add_argument(
        "--no-kiss",
        action="store_true",
        help="skip KISS return frame in recovery ladder",
    )
    args = parser.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    env = load_env(os.path.join(root, "tnc2c-serial.env"))
    dev = (
        args.device
        or env.get("TNC_DEV")
        or env.get("TNC2C_DEV")
        or env.get("PKTNC2_DEV")
        or "/dev/ttyS4"
    )
    baud = args.baud or int(
        env.get("TNC_BAUD") or env.get("TNC2C_BAUD") or env.get("PKTNC2_BAUD") or BAUD_DEFAULT
    )
    line = args.line or env.get("TNC_LINE") or env.get("TNC2C_LINE") or LINE_DEFAULT

    if args.power_hint:
        print(POWER_HINT)

    if not os.path.exists(dev):
        print(f"FAIL: {dev} does not exist", file=sys.stderr)
        return 2
    if not os.access(dev, os.R_OK | os.W_OK):
        print(f"FAIL: no access to {dev}", file=sys.stderr)
        return 2

    recovery = load_recovery()

    print(f"TNC host-reset @ {dev} {baud} {line.upper()} (DTR+RTS high)")
    try:
        fd = open_serial(dev, baud, line)
    except OSError as e:
        print(f"FAIL: {dev}: {e}", file=sys.stderr)
        return 2

    def wf(data: bytes) -> None:
        write_flush(fd, data)

    def rf(seconds: float) -> bytes:
        return read_for(fd, seconds)

    def log(msg: str) -> None:
        print(f"  {msg}")

    ok, received = recovery.recover_terminal(
        wf, rf, skip_kiss_frame=args.no_kiss, log=log
    )

    if ok and args.kiss:
        recovery.enter_kiss(wf, rf, args.kiss_entry)
        print("  KISS entry sent")

    os.close(fd)

    print()
    if ok:
        label = "HOST+KISS" if args.kiss else "HOST"
        print(f"OK: {label} - terminal mode active (software recovery)")
        if received:
            text = received.decode("ascii", errors="replace")
            if "NORD" in text or "TheFirmware" in text:
                for line_out in text.splitlines():
                    if any(m.decode() in line_out for m in FIRMWARE_MARKERS[:5]):
                        print(f"  | {line_out.strip()}")
        return 0

    print("FAIL: software recovery exhausted")
    print("  -> Power-cycle with DTR high: ./tnc2c-boot-wait.sh")
    return 1


if __name__ == "__main__":
    sys.exit(main())
