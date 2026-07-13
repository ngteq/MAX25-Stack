#!/usr/bin/env python3
"""Offline unit tests for kiss_bridge (no serial hardware)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ax25_codec import ax25_build_ui, ax25_crc, ax25_parse_ui, parse_callsign  # noqa: E402
from kiss_bridge import (  # noqa: E402
    KissDecoder,
    format_rx_line,
    kiss_data_frame,
    kiss_encode,
    serial_profile_for_device,
)


def test_callsign_parse() -> None:
    assert parse_callsign("DG1ABC") == ("DG1ABC", 0)
    assert parse_callsign("DK0WC-7") == ("DK0WC", 7)


def test_ax25_roundtrip() -> None:
    frame = ax25_build_ui("DG1ABC", "CQ", b"73")
    parsed = ax25_parse_ui(frame)
    assert parsed is not None
    src, dst, payload = parsed
    assert src == "DG1ABC"
    assert dst == "CQ"
    assert payload == b"73"


def test_kiss_fcs_strip() -> None:
    frame = ax25_build_ui("CB-0", "QST", b"hi")
    pkt = kiss_data_frame(0, frame)
    assert pkt.startswith(b"\xc0")
    assert pkt.endswith(b"\xc0")
    dec = KissDecoder()
    frames = dec.feed(pkt)
    assert len(frames) == 1
    _port, payload = frames[0]
    assert len(payload) == len(frame) - 2
    parsed = ax25_parse_ui(payload)
    assert parsed is not None
    src, dst, info = parsed
    assert src == "CB"
    assert dst == "QST"
    assert info == b"hi"


def test_kiss_escape_roundtrip() -> None:
    raw = bytes([0xC0, 0xDB, 0x00, 0xFF])
    pkt = kiss_encode(0, 0x00, raw)
    dec = KissDecoder()
    frames = dec.feed(pkt)
    assert frames[0][1] == raw


def test_format_rx() -> None:
    line = format_rx_line("DG1ABC", "QST", b"73", ax25_ui=True)
    assert line == "[AX25 UI DG1ABC>QST] 73"


def test_serial_profile_tnc2c() -> None:
    root = str(Path(__file__).resolve().parents[2])
    prof = serial_profile_for_device("tnc2c", root, {})
    assert prof.baud == 19200
    assert prof.dtr_rts is True
    assert prof.kiss_entry == "kiss_on"


def test_serial_profile_pktnc2() -> None:
    root = str(Path(__file__).resolve().parents[2])
    prof = serial_profile_for_device("pktnc2", root, {})
    assert prof.baud == 9600
    assert prof.dtr_rts is False
    assert prof.kiss_entry == "auto"


def test_crc_known_vector() -> None:
    body = bytes(range(256))
    assert ax25_crc(body) == 0x303C


def test_kiss_non_data_ignored() -> None:
    pkt = kiss_encode(0, 0x06, b"ignored")  # TXDELAY cmd
    dec = KissDecoder()
    assert dec.feed(pkt) == []


def test_invalid_callsign_tx() -> None:
    from kiss_bridge import KissBridge, SerialProfile

    bridge = KissBridge(SerialProfile(), on_rx=lambda _m: None)
    bridge._kiss_active = True
    bridge._fd = -1  # not used — validate before write
    ok, msg = bridge.transmit("BAD!", "CQ", "hi", ax25_ui=True)
    assert not ok
    assert "invalid" in msg.lower()


def test_rx_thread_not_started_on_open() -> None:
    from kiss_bridge import KissBridge, SerialProfile

    bridge = KissBridge(SerialProfile(), on_rx=lambda _m: None)
    bridge._fd = 1
    bridge.status = "open"
    assert bridge._thread is None


def main() -> int:
    tests = [
        test_callsign_parse,
        test_ax25_roundtrip,
        test_kiss_fcs_strip,
        test_kiss_escape_roundtrip,
        test_format_rx,
        test_serial_profile_tnc2c,
        test_serial_profile_pktnc2,
        test_crc_known_vector,
        test_kiss_non_data_ignored,
        test_invalid_callsign_tx,
        test_rx_thread_not_started_on_open,
    ]
    for fn in tests:
        fn()
    print("OK: kiss_bridge unit tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
