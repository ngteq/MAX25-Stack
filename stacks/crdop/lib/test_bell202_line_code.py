#!/usr/bin/env python3
"""Unit tests for Bell 202 frequency-toggle line code."""
from __future__ import annotations

import sys
from pathlib import Path

LIB = Path(__file__).resolve().parent
sys.path.insert(0, str(LIB))

from bell202_line_code import decode_tones_to_bits, encode_bits_to_tones  # noqa: E402


def test_roundtrip_single_byte() -> None:
    bits = bytes([0x55])  # 01010101 → many toggles
    tones = encode_bits_to_tones(bits, start_tone=0)
    back = decode_tones_to_bits(tones, start_tone=0)
    assert back == bits


def test_all_ones_no_toggle() -> None:
    tones = encode_bits_to_tones(bytes([0xFF]), start_tone=0)
    assert len(set(tones)) == 1


def main() -> int:
    test_roundtrip_single_byte()
    test_all_ones_no_toggle()
    print("OK: bell202_line_code tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
