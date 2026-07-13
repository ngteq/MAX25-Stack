"""
HDLC framing for AX.25 — flags, bit-stuffing, CRC-16-CCITT.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_DAEMON = _ROOT / "stacks" / "daemon"
if str(_DAEMON) not in sys.path:
    sys.path.insert(0, str(_DAEMON))

from ax25_codec import ax25_crc  # noqa: E402

HDLC_FLAG = 0x7E
HDLC_ESCAPE = 0x7D
HDLC_XOR = 0x20


def bit_stuff(data: bytes) -> bytes:
    out = bytearray()
    ones = 0
    for b in data:
        for bit_i in range(7, -1, -1):
            bit = (b >> bit_i) & 1
            if bit:
                ones += 1
                out.append(1)
                if ones == 5:
                    out.append(0)
                    ones = 0
            else:
                ones = 0
                out.append(0)
    # pack bits to bytes MSB-first
    buf = bytearray()
    acc = 0
    n = 0
    for bit in out:
        acc = (acc << 1) | bit
        n += 1
        if n == 8:
            buf.append(acc)
            acc = 0
            n = 0
    if n:
        buf.append(acc << (8 - n))
    return bytes(buf)


def bit_unstuff(data: bytes) -> bytes:
    bits: list[int] = []
    for b in data:
        for bit_i in range(7, -1, -1):
            bits.append((b >> bit_i) & 1)
    out: list[int] = []
    ones = 0
    i = 0
    while i < len(bits):
        bit = bits[i]
        if bit:
            ones += 1
            out.append(1)
            if ones == 5 and i + 1 < len(bits) and bits[i + 1] == 0:
                i += 1
                ones = 0
            elif ones == 6:
                break
        else:
            ones = 0
            out.append(0)
        i += 1
    buf = bytearray()
    for j in range(0, len(out), 8):
        chunk = out[j : j + 8]
        if len(chunk) < 8:
            break
        val = 0
        for bit in chunk:
            val = (val << 1) | bit
        buf.append(val)
    return bytes(buf)


def build_hdlc_frame(ax25_body: bytes) -> bytes:
    """AX.25 body (no FCS) → on-air HDLC bit stream as bytes (pre tone encoding)."""
    crc = ax25_crc(ax25_body)
    payload = ax25_body + bytes((crc & 0xFF, crc >> 8))
    stuffed = bit_stuff(payload)
    return bytes([HDLC_FLAG]) + stuffed + bytes([HDLC_FLAG])


def parse_hdlc_stream(raw_bits: bytes) -> list[bytes]:
    """Extract AX.25 bodies (with FCS) from demodulated byte stream between flags."""
    frames: list[bytes] = []
    in_frame = False
    cur = bytearray()
    for b in raw_bits:
        if b == HDLC_FLAG:
            if in_frame and cur:
                unstuffed = bit_unstuff(bytes(cur))
                if len(unstuffed) >= 2:
                    frames.append(unstuffed)
            cur.clear()
            in_frame = True
            continue
        if in_frame:
            cur.append(b)
    return frames
