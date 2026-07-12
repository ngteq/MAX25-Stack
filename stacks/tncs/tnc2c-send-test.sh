#!/bin/bash
# Send one AX.25 UI frame via KISS on TNC2C — keys PTT / transmits on radio.
# Requires: antenna or dummyload, VOX off, HyBBX stopped.
# Usage: ./tnc2c-send-test.sh [message] [src] [dst]

set -euo pipefail

MSG="${1:-HI}"
SRC="${2:-TEST-0}"
DST="${3:-CQ}"

ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
[[ -f "$ROOT/tnc2c-serial.env" ]] && source "$ROOT/tnc2c-serial.env"

if pgrep -x hybbx >/dev/null 2>&1; then
    echo "ERROR: hybbx läuft — erst stoppen" >&2
    exit 1
fi

export TNC2C_DEV TNC2C_LINE
python3 - "$MSG" "$SRC" "$DST" <<'PY'
import fcntl, os, struct, sys, time, termios

msg, src, dst = sys.argv[1:4]
dev = os.environ.get("TNC2C_DEV", "/dev/ttyS4")
line = os.environ.get("TNC2C_LINE", "8n1").lower()
seven_e1 = line.startswith("7e")

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

def ax25_addr(call: str, ssid: int, last: bool) -> bytes:
    call = call.upper().ljust(6)[:6]
    raw = bytes((ord(c) << 1) for c in call)
    ssid_b = ((ssid & 0x0F) << 1) | (0x01 if last else 0x00)
    return raw + bytes([ssid_b])

def ax25_crc(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
    return crc ^ 0xFFFF

def ax25_ui(src, dst, info: bytes) -> bytes:
    body = ax25_addr(dst, 0, False) + ax25_addr(src, 0, True)
    body += b"\x03\xF0" + info
    crc = ax25_crc(body)
    return body + bytes((crc & 0xFF, crc >> 8))

def kiss_frame(port: int, payload: bytes) -> bytes:
    return b"\xC0" + bytes([port & 0x0F]) + kiss_escape(payload) + b"\xC0"

print(f"Serial: {dev} 19200 {line}")

fd = os.open(dev, os.O_RDWR | os.O_NOCTTY)
t = termios.tcgetattr(fd)
t[0] = t[1] = 0
t[2] = termios.CLOCAL | termios.CREAD | (termios.CS7 if seven_e1 else termios.CS8)
if seven_e1:
    t[2] |= termios.PARENB
t[3] = t[4] = t[5] = termios.B19200
t[6][termios.VMIN] = 0
t[6][termios.VTIME] = 5
termios.tcsetattr(fd, termios.TCSANOW, t)
termios.tcflush(fd, termios.TCIOFLUSH)
flags = struct.unpack("I", fcntl.ioctl(fd, 0x5415, struct.pack("I", 0)))[0] | 0x006
fcntl.ioctl(fd, 0x5416, struct.pack("I", flags))

for cmd in (b"kiss off\r", b"kiss on\r"):
    os.write(fd, cmd)
    termios.tcdrain(fd)
    time.sleep(0.5)

pkt = kiss_frame(0, ax25_ui(src, dst, msg.encode("ascii", errors="replace")))
print(f"TX {src} -> {dst}: {msg!r} ({len(pkt)} bytes KISS)")
os.write(fd, pkt)
termios.tcdrain(fd)
time.sleep(3.0)
try:
    rx = os.read(fd, 4096)
    if rx:
        print(f"RX {len(rx)} bytes: {rx[:80]!r}")
except BlockingIOError:
    pass
os.write(fd, b"kiss off\r")
termios.tcdrain(fd)
os.close(fd)
print("Prüfe LED 2 (PTT) am TNC und S-Meter am Funk.")
PY
