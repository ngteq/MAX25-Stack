#!/usr/bin/env python3
"""Offline unit tests for BayComKissBackend (no kernel hardware)."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "stacks" / "daemon"))

from device_backends import BayComKissBackend, DeviceBackendConfig  # noqa: E402
from kiss_bridge import KissDecoder, ax25_build_ui, ax25_parse_ui, kiss_data_frame  # noqa: E402


def test_baycom_kiss_default_link() -> None:
    cfg = DeviceBackendConfig(device_id="baycom-ser12", backend_type="baycom-kiss", baycom_modem="a")
    backend = BayComKissBackend(cfg, on_rx=lambda _l: None)
    assert backend._path in ("/var/run/baycom-pr/kiss", f"/var/run/baycom-pr/kiss-a")
    assert backend.backend_type == "baycom-kiss"
    assert backend._is_pty is True


def test_baycom_kiss_transmit_kiss_frame() -> None:
    cfg = DeviceBackendConfig(
        device_id="baycom-ser12",
        backend_type="baycom-kiss",
        kiss_link="/var/run/baycom-pr/kiss",
    )
    backend = BayComKissBackend(cfg, on_rx=lambda _l: None)
    backend._fd = 99
    backend._kiss_active = True
    written: list[bytes] = []

    with patch("os.write", side_effect=lambda _fd, data: written.append(data) or len(data)):
        with patch("termios.tcdrain"):
            ok, display = backend.transmit("CB-0", "QST", "hello", ax25_ui=True)
    assert ok, display
    assert written and written[0].startswith(b"\xc0")
    assert "hello" in display


def test_baycom_kiss_rx_decode_path() -> None:
    """RX path: KISS bytes → AX.25 UI → on_rx line (same decoder as _rx_loop)."""
    rx_lines: list[str] = []
    frame = ax25_build_ui("REMOTE-0", "CB-0", b"73")
    pkt = kiss_data_frame(0, frame)
    decoder = KissDecoder()
    for _port, payload in decoder.feed(pkt):
        parsed = ax25_parse_ui(payload)
        assert parsed is not None
        src, dst, info = parsed
        assert src == "REMOTE"
        assert dst == "CB"
        assert info == b"73"
        from kiss_bridge import format_rx_line

        rx_lines.append(format_rx_line(src, dst, info, ax25_ui=True))
    assert rx_lines and "73" in rx_lines[0]


def test_baycom_kiss_modem_b_link() -> None:
    cfg = DeviceBackendConfig(
        device_id="baycom-b",
        backend_type="baycom-kiss",
        baycom_modem="b",
        kiss_link="/var/run/baycom-pr/kiss-b",
    )
    backend = BayComKissBackend(cfg, on_rx=lambda _l: None)
    assert backend._path == "/var/run/baycom-pr/kiss-b"


def test_baycom_kiss_open_missing_path() -> None:
    backend = BayComKissBackend(
        DeviceBackendConfig(device_id="baycom-ser12", kiss_link="/nonexistent/kiss/path"),
        on_rx=lambda _l: None,
    )
    assert not backend.open()
    assert backend.status == "error-no-device"


def main() -> int:
    test_baycom_kiss_default_link()
    test_baycom_kiss_modem_b_link()
    test_baycom_kiss_transmit_kiss_frame()
    test_baycom_kiss_rx_decode_path()
    test_baycom_kiss_open_missing_path()
    print("OK: baycom backend tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
