#!/usr/bin/env python3
"""
Hold /dev/ttyS4 open with DTR+RTS during TNC power-on, then kiss off + INFO.

Usage:
  1. Run this FIRST (waits for port):
     ./tnc2c-boot-wait.sh
  2. While it says "waiting", power-cycle the TNC (off 10s, on).
  3. Script detects banner or runs kiss off + INFO automatically.
"""

from __future__ import annotations

import argparse
import fcntl
import os
import struct
import sys
import time
import termios

FIRMWARE_MARKERS = (
    b"TheFirmware",
    b"NORD",
    b"Version 2.7",
    b"Checksum",
    b"Copyright",
)


def has_banner(data: bytes) -> bool:
    lower = data.lower()
    return any(m.lower() in lower for m in FIRMWARE_MARKERS)


def parse_line(line: str) -> tuple[int, int]:
    line = line.lower()
    if line == "7e1":
        return termios.CS7, termios.PARENB
    if line == "8n1":
        return termios.CS8, 0
    raise ValueError(f"unsupported serial line: {line}")


def parse_baud(baud: int) -> int:
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
    os.write(fd, data)
    termios.tcdrain(fd)


def show(data: bytes) -> None:
    if data:
        print(data.decode("ascii", errors="replace"))


def is_cmd_echo(cmd: bytes, reply: bytes) -> bool:
    c = cmd.strip(b"\r\n")
    r = reply.strip()
    return r in (c, c + b"\r", c + b"\n", c + b"\r\n")


def run_tx_rx(fd: int) -> None:
    """TX KISS frame + passive RX on same open fd (before port close)."""
    print("\n--- TX (KISS TEST-0 -> CQ, TXRX) ---")
    write_flush(fd, b"kiss on\r")
    time.sleep(0.5)
    read_for(fd, 0.3)

    def kiss_escape(data: bytes) -> bytes:
        out = bytearray()
        for b in data:
            if b == 0xC0:
                out.extend((0xDB, 0xDC))
            elif b == 0xDB:
                out.extend((0xDB, 0xDD))
            else:
                out.append(b)
        return bytes(out)

    def ax25_addr(call: str, last: bool) -> bytes:
        call = call.upper().ljust(6)[:6]
        raw = bytes((ord(c) << 1) for c in call)
        ssid = ((0 & 0x0F) << 1) | (0x01 if last else 0x00)
        return raw + bytes([ssid])

    def ax25_crc(data: bytes) -> int:
        crc = 0xFFFF
        for b in data:
            crc ^= b
            for _ in range(8):
                crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
        return crc ^ 0xFFFF

    body = ax25_addr("CQ", False) + ax25_addr("TEST-0", True) + b"\x03\xF0TXRX"
    crc = ax25_crc(body)
    payload = body + bytes((crc & 0xFF, crc >> 8))
    pkt = b"\xC0\x00" + kiss_escape(payload) + b"\xC0"
    write_flush(fd, pkt)
    time.sleep(3.0)
    tx_rx = read_for(fd, 1.0)
    print(f"  Sent {len(pkt)} B, serial RX {len(tx_rx)} B")
    print("  -> CHECK: LED2 PTT + modem tone on 2m CB")

    write_flush(fd, b"kiss off\r")
    time.sleep(0.5)
    read_for(fd, 0.5)

    print("\n--- RX (passive 10s) ---")
    print("  Listening ... (empty band = 0 bytes OK; LED3 CD with noise?)")
    rx = read_for(fd, 10.0)
    print(f"  Passive RX: {len(rx)} bytes")
    if rx and b"\xc0" in rx:
        print("  OK: KISS frame received")


def verify_hybbx_ready(fd: int) -> tuple[bool, bytes, bool]:
    """kiss off + INFO on open fd. Returns (banner_in_reply, data, only_echo)."""
    write_flush(fd, b"kiss off\r")
    time.sleep(0.6)
    prelude = read_for(fd, 1.0)
    write_flush(fd, b"INFO\r")
    time.sleep(0.3)
    info = read_for(fd, 5.0)
    combined = prelude + info
    only_echo = is_cmd_echo(b"kiss off\r", prelude) and is_cmd_echo(b"INFO\r", info)
    return has_banner(combined), combined, only_echo


def finish_host(fd: int, hybbx_ready: bool, do_tx_rx: bool) -> int:
    if hybbx_ready:
        print("\n--- HyBBX-Verify (kiss off + INFO) ---")
        ok, verify, only_echo = verify_hybbx_ready(fd)
        show(verify)
        host_ok = ok or only_echo
        if not host_ok:
            if do_tx_rx:
                run_tx_rx(fd)
            os.close(fd)
            print("\nWARN: unexpected kiss/INFO response")
            return 1
    else:
        host_ok = True

    if do_tx_rx:
        run_tx_rx(fd)

    os.close(fd)
    if host_ok:
        print("\nOK: HOST - HyBBX-ready" + (" + TX/RX tested" if do_tx_rx else ""))
        return 0
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Hold DTR during TNC boot")
    default_dev = (
        os.environ.get("TNC_DEV")
        or os.environ.get("TNC2C_DEV")
        or os.environ.get("PKTNC2_DEV")
        or "/dev/ttyS4"
    )
    default_baud = int(
        os.environ.get("TNC_BAUD")
        or os.environ.get("TNC2C_BAUD")
        or os.environ.get("PKTNC2_BAUD")
        or "19200"
    )
    default_line = (
        os.environ.get("TNC_LINE")
        or os.environ.get("TNC2C_LINE")
        or os.environ.get("PKTNC2_LINE")
        or "8n1"
    )

    parser.add_argument("device", nargs="?", default=default_dev)
    parser.add_argument("--baud", type=int, default=default_baud)
    parser.add_argument("--line", default=default_line, choices=("8n1", "7e1"))
    parser.add_argument("--wait", type=int, default=45, help="seconds to listen for boot")
    parser.add_argument(
        "--no-hybbx-ready",
        action="store_true",
        help="only detect boot banner, skip kiss off + INFO verify",
    )
    parser.add_argument(
        "--tx-rx",
        action="store_true",
        help="TX KISS + passive RX on same port before close (with power cycle)",
    )
    args = parser.parse_args()
    hybbx_ready = not args.no_hybbx_ready
    do_tx_rx = args.tx_rx

    if not os.access(args.device, os.R_OK | os.W_OK):
        print(f"FAIL: no access to {args.device}", file=sys.stderr)
        return 2

    print(f"=== TNC boot-wait @ {args.device} {args.baud} {args.line.upper()} ===")
    print("DTR+RTS HIGH - power OFF the TNC now (10s), then power ON.")
    print("CB: squelch CLOSED (CD off) - otherwise TX/boot may be disturbed.")
    print(f"Listening {args.wait}s for boot banner ...\n")

    fd = open_serial(args.device, args.baud, args.line)
    buf = read_for(fd, args.wait)

    if has_banner(buf):
        print("--- Boot banner (passive) ---")
        show(buf)
        return finish_host(fd, hybbx_ready, do_tx_rx)

    print(f"(no banner in {args.wait}s - trying kiss off + INFO)\n")
    write_flush(fd, b"kiss off\r")
    time.sleep(0.6)
    buf += read_for(fd, 1.0)
    write_flush(fd, b"INFO\r")
    time.sleep(0.4)
    info = read_for(fd, 4.0)
    buf += info

    print("--- kiss off + INFO ---")
    show(info if info else buf[-500:])

    if has_banner(buf):
        return finish_host(fd, hybbx_ready, do_tx_rx)
    os.close(fd)
    print("\nDEGRADED: echo only - try minicom or repeat power reset")
    return 1


if __name__ == "__main__":
    sys.exit(main())
