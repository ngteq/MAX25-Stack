#!/usr/bin/env python3
"""TX then RX diagnostic for TNC2C + CB — no HyBBX."""

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
        print("FAIL: hybbx läuft — bitte stoppen")
        return 2

    fd = open_port()
    print(f"Device: {DEV} 19200 8N1  {modem(fd)}")

    # --- Host check ---
    print("\n[1] Host-Check")
    passive = read_sec(fd, 2.0)
    write(fd, b"kiss off\r")
    time.sleep(0.5)
    pre = read_sec(fd, 1.0)
    write(fd, b"INFO\r")
    time.sleep(0.3)
    info = read_sec(fd, 4.0)
    all_host = passive + pre + info
    if has_fw(all_host):
        print("  OK: Firmware/Host erkannt")
    elif info.strip() in (b"INFO", b"INFO\r", b"INFO\r\n"):
        print("  WARN: nur Echo — ./tnc2c-boot-wait.sh + Strom-Zyklus empfohlen")
    else:
        print(f"  INFO-Antwort: {info[:120]!r}")

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
    print(f"  Gesendet: {len(pkt)} bytes KISS")
    print(f"  Seriell RX: {len(tx_rx)} bytes")
    if kiss_back:
        print("  OK: KISS-Frame auf Seriell gesehen")
    else:
        print("  WARN: kein KISS-Echo auf Seriell")
    print("  → JETZT prüfen: LED2 PTT + Modem-Ton am 2. CB-Funk")

    # --- RX (passiv, kein TX) ---
    print("\n[3] RX (passiv 12s, kiss off — lauscht auf Funk/Monitor)")
    termios.tcflush(fd, termios.TCIOFLUSH)
    write(fd, b"kiss off\r")
    time.sleep(0.5)
    read_sec(fd, 0.5)
    print("  Lausche 12s … (Funk-Rauschen/CD sollte LED3 an halten)")
    rx_data = read_sec(fd, 12.0)
    os.close(fd)

    print(f"  Passiv RX: {len(rx_data)} bytes")
    if rx_data:
        printable = sum(1 for b in rx_data if 32 <= b < 127 or b in (9, 10, 13))
        ratio = printable / len(rx_data)
        print(f"  Anteil druckbar: {ratio:.0%}")
        if b"\xc0" in rx_data:
            print("  OK: KISS-Frame(s) empfangen (Funk-Traffic oder Monitor)")
        else:
            print(f"  Sample: {rx_data[:80]!r}")
    else:
        print("  (kein Seriell-Traffic — normal bei leerem Band)")
        print("  → Hardware-RX: LED3 CD bei Rauschen/SQ offen?")

    print("\n" + "=" * 60)
    print("Hardware-Checkliste:")
    print("  TX: LED2 (PTT) blinkte? 2.CB hörte Modem-Ton?")
    print("  RX: LED3 (CD) an bei Rauschen? SQ zu → CD aus?")
    print("  DIN: Pin1=TX(weiß) Pin2=GND Pin3=PTT(rot) Pin4=RX(tip)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
