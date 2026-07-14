#!/usr/bin/env python3
"""Offline unit tests for CrdopTcpBackend (no crdopc process)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "stacks" / "daemon"))

from device_backends import CrdopTcpBackend, DeviceBackendConfig  # noqa: E402


class _MockSock:
    """Minimal socket double for ctrl/data channels."""

    def __init__(self, term: str = "\n") -> None:
        self.sent: list[bytes] = []
        self._closed = False
        self._term = term

    def settimeout(self, _t: float) -> None:
        return None

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)

    def recv(self, _n: int) -> bytes:
        if self._closed:
            return b""
        return f"OK{self._term}".encode("ascii")

    def close(self) -> None:
        self._closed = True


def _mock_connections(ctrl: _MockSock, data: _MockSock):
    def _create(addr, timeout=5.0):
        _host, port = addr
        return ctrl if port == 8515 else data

    return _create


def _open_ctx(ctrl: _MockSock, data: _MockSock):
    mock_thread = MagicMock()
    return (
        patch("device_backends.socket.create_connection", side_effect=_mock_connections(ctrl, data)),
        patch("device_backends.threading.Thread", return_value=mock_thread),
    )


def test_crdop_backend_open_and_attach() -> None:
    ctrl = _MockSock()
    data = _MockSock()
    cfg = DeviceBackendConfig(
        device_id="soft-crdop",
        backend_type="crdop-tcp",
        crdop_host="127.0.0.1",
        crdop_port=8515,
        crdop_listen=True,
    )
    backend = CrdopTcpBackend(cfg, on_rx=lambda _l: None)
    p_sock, p_thread = _open_ctx(ctrl, data)
    with p_sock, p_thread:
        assert backend.open()
        assert backend.attach_session("CB-0")
    assert backend.status == "ready"
    joined = b"".join(ctrl.sent).decode("ascii")
    assert "INITIALIZE" in joined
    assert "PROTOCOLMODE KISS" in joined
    assert "LISTEN TRUE" in joined
    backend.close()
    assert backend.status == "closed"


def test_crdop_backend_transmit() -> None:
    ctrl = _MockSock()
    data = _MockSock()
    cfg = DeviceBackendConfig(
        device_id="soft-crdop",
        backend_type="crdop-tcp",
        crdop_host="127.0.0.1",
        crdop_port=8515,
    )
    backend = CrdopTcpBackend(cfg, on_rx=lambda _l: None)
    p_sock, p_thread = _open_ctx(ctrl, data)
    with p_sock, p_thread:
        assert backend.open()
        assert backend.attach_session("CB-0")
        ok, display = backend.transmit("CB-0", "QST", "hello", ax25_ui=True)
    assert ok, display
    assert len(data.sent) == 1
    assert "FECSEND" not in b"".join(ctrl.sent).decode("ascii")
    assert "[CRDOP AX25 UI CB-0>QST]" in display
    backend.close()
    assert backend.status == "closed"


def test_crdop_backend_connect_failure() -> None:
    cfg = DeviceBackendConfig(
        device_id="soft-crdop",
        backend_type="crdop-tcp",
        crdop_host="127.0.0.1",
        crdop_port=59999,
    )
    backend = CrdopTcpBackend(cfg, on_rx=lambda _l: None)
    with patch("device_backends.socket.create_connection", side_effect=OSError("refused")):
        assert not backend.open()
    assert backend.status == "error-connect"


def test_crdop_registry_tested() -> None:
    from device_backends import registry_tested  # noqa: E402

    assert registry_tested("soft-crdop") is True


def main() -> int:
    test_crdop_backend_connect_failure()
    test_crdop_backend_open_and_attach()
    test_crdop_backend_transmit()
    test_crdop_registry_tested()
    print("OK: crdop backend tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
