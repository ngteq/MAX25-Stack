#!/usr/bin/env python3
"""TX then RX diagnostic for TNC2C + CB - no HyBBX."""

from __future__ import annotations

import fcntl
import os
import struct
import sys
import time
import termios

DEV = "/dev/ttyS4"
BAUD = termios.B19200

FIRMWARE = (b"TheFirmware", b"NORD", b"Version 2.7", b"Checksum")


def open_port() -> int:
    fd = os.open(DEV, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    t = termios.tcgetattr(fd)
    t[0] = t[1] = 0
    t[2] = termios.CLOCAL | termios.CREAD | termios.CS8
    t[3] = t[4] = t[5] = BAUD
    t[6][termios.VMIN] = 0
    t[6][termios.VTIME] = 5
    termios.tcsetattr(fd, termios.TCSANOW, t)
    termios.tcflush(fd, termios.TCIOFLUSH)
    flags = struct.unpack("I", fcntl.ioctl(fd, 0x5415, struct.pack("I", 0)))[0]
    flags |= 0x006
    fcntl.ioctl(fd, 0x5416, struct.pack("I", flags))
    return fd


def modem(fd: int) -> str:
    f = struct.unpack("I", fcntl.ioctl(fd, 0x5415, struct.pack("I", 0)))[0]
    return f"RTS={int(bool(f&4))} CTS={int(bool(f&8))} DSR={int(bool(f&0x100))} DCD={int(bool(f&0x80))}"


def read_sec(fd: int, sec: float) -> bytes:
    end = time.time() + sec
    chunks: list[bytes] = []
    while time.time() < end:
        try:
            b = os.read(fd, 4096)
            if b:
                chunks.append(b)
        except BlockingIOError:
            time.sleep(0.02)
    return b"".join(chunks)


def write(fd: int, data: bytes) -> None:
    os.write(fd, data)
    termios.tcdrain(fd)


def has_fw(data: bytes) -> bool:
    lo = data.lower()
    return any(m.lower() in lo for m in FIRMWARE)


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
    return raw + bytes([((0 & 0x0F) << 1) | (0x01 if last else 0x00)])


def ax25_crc(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
    return crc ^ 0xFFFF


def ax25_ui(src: str, dst: str, info: bytes) -> bytes:
    body = ax25_addr(dst, False) + ax25_addr(src, True) + b"\x03\xF0" + info
    crc = ax25_crc(body)
    return body + bytes((crc & 0xFF, crc >> 8))


def kiss_frame(payload: bytes) -> bytes:
    return b"\xC0\x00" + kiss_escape(payload) + b"\xC0"


def main() -> int:
    print("=" * 60)
    print("TNC2C TX/RX Test")
    print("=" * 60)

    if os.system("pgrep -x hybbx >/dev/null 2>&1") == 0:
        print("FAIL: hybbx is running - stop it first")
        return 2

    fd = open_port()
    print(f"Device: {DEV} 19200 8N1  {modem(fd)}")

    # --- Host check ---
    print("\n[1] Host check")
    passive = read_sec(fd, 2.0)
    write(fd, b"kiss off\r")
    time.sleep(0.5)
    pre = read_sec(fd, 1.0)
    write(fd, b"INFO\r")
    time.sleep(0.3)
    info = read_sec(fd, 4.0)
    all_host = passive + pre + info
    if has_fw(all_host):
        print("  OK: firmware/host detected")
    elif info.strip() in (b"INFO", b"INFO\r", b"INFO\r\n"):
        print("  WARN: echo only - ./tnc2c-boot-wait.sh + power cycle recommended")
    else:
        print(f"  INFO reply: {info[:120]!r}")

    # --- TX ---
    print("\n[2] TX (KISS UI TEST-0 -> CQ, Msg=TXRX)")
    write(fd, b"kiss on\r")
    time.sleep(0.5)
    read_sec(fd, 0.3)
    pkt = kiss_frame(ax25_ui("TEST-0", "CQ", b"TXRX"))
    t0 = time.time()
    write(fd, pkt)
    time.sleep(3.0)
    tx_rx = read_sec(fd, 1.0)
    write(fd, b"kiss off\r")
    time.sleep(0.3)

    kiss_back = b"\xc0" in tx_rx or b"TXRX" in tx_rx
    print(f"  Sent: {len(pkt)} bytes KISS")
    print(f"  Serial RX: {len(tx_rx)} bytes")
    if kiss_back:
        print("  OK: KISS frame seen on serial")
    else:
        print("  WARN: no KISS echo on serial")
    print("  -> CHECK NOW: LED2 PTT + modem tone on 2m CB radio")

    # --- RX (passive, no TX) ---
    print("\n[3] RX (passive 12s, kiss off - listening on radio/monitor)")
    termios.tcflush(fd, termios.TCIOFLUSH)
    write(fd, b"kiss off\r")
    time.sleep(0.5)
    read_sec(fd, 0.5)
    print("  Listening 12s ... (RF noise/CD should keep LED3 on)")
    rx_data = read_sec(fd, 12.0)
    os.close(fd)

    print(f"  Passive RX: {len(rx_data)} bytes")
    if rx_data:
        printable = sum(1 for b in rx_data if 32 <= b < 127 or b in (9, 10, 13))
        ratio = printable / len(rx_data)
        print(f"  Printable ratio: {ratio:.0%}")
        if b"\xc0" in rx_data:
            print("  OK: KISS frame(s) received (RF traffic or monitor)")
        else:
            print(f"  Sample: {rx_data[:80]!r}")
    else:
        print("  (no serial traffic - normal on empty band)")
        print("  -> Hardware RX: LED3 CD with noise/SQ open?")

    print("\n" + "=" * 60)
    print("Hardware checklist:")
    print("  TX: LED2 (PTT) blinked? 2m CB heard modem tone?")
    print("  RX: LED3 (CD) on with noise? SQ closed -> CD off?")
    print("  DIN: Pin1=TX(white) Pin2=GND Pin3=PTT(red) Pin4=RX(tip)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
