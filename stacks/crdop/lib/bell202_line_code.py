"""
Bell 202 frequency-toggle line code (1200 baud AFSK layer).

On-air rule: bit 0 → toggle mark/space tone; bit 1 → hold current tone.
We avoid the legacy term in API names — this is Bell 202 / amateur packet radio.
"""
from __future__ import annotations

MARK_HZ = 1200.0
SPACE_HZ = 2200.0
BAUD_1200 = 1200

TONE_MARK = 1
TONE_SPACE = 0


def encode_bits_to_tones(bits: bytes, start_tone: int = TONE_SPACE) -> list[int]:
    """Map HDLC bit stream to mark/space tone sequence (one tone per bit)."""
    tone = start_tone
    out: list[int] = []
    for byte in bits:
        for bit_i in range(7, -1, -1):
            bit = (byte >> bit_i) & 1
            if bit == 0:
                tone ^= 1
            out.append(tone)
    return out


def decode_tones_to_bits(tones: list[int], start_tone: int = TONE_SPACE) -> bytes:
    """Recover bit stream from mark/space tone sequence."""
    if not tones:
        return b""
    prev = start_tone
    bits: list[int] = []
    for tone in tones:
        if tone not in (TONE_MARK, TONE_SPACE):
            continue
        bits.append(0 if tone != prev else 1)
        prev = tone
    buf = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i : i + 8]
        if len(chunk) < 8:
            break
        val = 0
        for b in chunk:
            val = (val << 1) | b
        buf.append(val)
    return bytes(buf)
