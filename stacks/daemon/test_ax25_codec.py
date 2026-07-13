#!/usr/bin/env python3
"""Unit tests for ax25_codec (RFC 1171 FCS + libax25 address rules)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ax25_codec import (  # noqa: E402
    ax25_build_ui,
    ax25_crc,
    ax25_crc_valid,
    ax25_encode_address,
    ax25_parse_ui,
    format_callsign,
    parse_callsign,
    validate_callsign,
)


def test_rfc1171_crc_vector() -> None:
    body = bytes(range(256))
    crc = ax25_crc(body)
    frame = body + bytes((crc & 0xFF, crc >> 8))
    assert ax25_crc_valid(frame)
    assert crc == 0x303C


def test_address_roundtrip() -> None:
    raw = ax25_encode_address("DG1ABC", 7, last=True)
    frame = ax25_build_ui("DG1ABC-7", "CQ", b"73")
    parsed = ax25_parse_ui(frame)
    assert parsed == ("DG1ABC-7", "CQ", b"73")


def test_format_callsign_omit_zero_ssid() -> None:
    assert format_callsign("DG1ABC", 0) == "DG1ABC"
    assert format_callsign("CB", 0) == "CB"


def test_parse_callsign_legacy() -> None:
    assert parse_callsign("DK0WC-7") == ("DK0WC", 7)
    assert parse_callsign("bad-ssid") == ("BAD", 0)


def test_validate_callsign_strict() -> None:
    assert validate_callsign("CB-0") == ("CB", 0)
    assert validate_callsign("N0CALL-15") == ("N0CALL", 15)
    try:
        validate_callsign("CB_0")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_ui_frame_without_fcs() -> None:
    frame = ax25_build_ui("DG1ABC", "QST", b"hi")
    body = frame[:-2]
    parsed = ax25_parse_ui(body)
    assert parsed == ("DG1ABC", "QST", b"hi")


def test_invalid_callsign_build() -> None:
    try:
        ax25_build_ui("BAD_CALL", "CQ", b"x")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_non_ui_rejected() -> None:
    frame = ax25_build_ui("A", "B", b"x")
    frame = bytearray(frame)
    frame[14] = 0x00  # not UI control
    assert ax25_parse_ui(bytes(frame)) is None


def main() -> int:
    tests = [
        test_rfc1171_crc_vector,
        test_address_roundtrip,
        test_format_callsign_omit_zero_ssid,
        test_parse_callsign_legacy,
        test_validate_callsign_strict,
        test_ui_frame_without_fcs,
        test_invalid_callsign_build,
        test_non_ui_rejected,
    ]
    for fn in tests:
        fn()
    print("OK: ax25_codec unit tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
