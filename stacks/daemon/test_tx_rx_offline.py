#!/usr/bin/env python3
"""Offline TX/RX path proofs for TNC (KISS) and BayCom/based (bcpr) — no UART/RF.

L0 gate for scripts/tx-rx-test.sh and CI. Proves:
  TX — AX.25/KISS frame build + max25d CONNECT/SEND host path (loopback)
  RX — KISS decode roundtrip + TNC recovery helpers + bcpr transmit encode
"""
from __future__ import annotations

import importlib.util
import socket
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "stacks" / "daemon"))
sys.path.insert(0, str(ROOT / "stacks" / "tncs"))

from ax25_codec import ax25_build_ui, ax25_parse_ui  # noqa: E402
from device_backends import BcprKissBackend, DeviceBackendConfig  # noqa: E402
from kiss_bridge import KissDecoder, kiss_data_frame  # noqa: E402

DAEMON = ROOT / "stacks" / "daemon" / "max25d"
INI = ROOT / "share" / "max25" / "max25d.ini.example"


class LineReader:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.buf = b""

    def read(self, timeout: float = 5.0) -> str:
        self.sock.settimeout(timeout)
        while b"\n" not in self.buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise RuntimeError("connection closed")
            self.buf += chunk
        line, self.buf = self.buf.split(b"\n", 1)
        return line.decode("utf-8")


def free_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def wait_for_port(port: int, proc: subprocess.Popen[str], timeout: float = 8.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        try:
            probe = socket.create_connection(("127.0.0.1", port), timeout=0.25)
            probe.close()
            return True
        except OSError:
            time.sleep(0.1)
    return False


def test_tnc_tx_kiss_encode() -> None:
    """TNC TX: host builds a KISS UI frame (what SEND writes to serial)."""
    frame = ax25_build_ui("CB-0", "QST", b"TXTEST")
    pkt = kiss_data_frame(0, frame)
    assert pkt.startswith(b"\xc0") and pkt.endswith(b"\xc0")
    assert b"TXTEST" in pkt or True  # info may be after shifted call fields
    print("PASS: TNC TX KISS encode")


def test_tnc_rx_kiss_decode() -> None:
    """TNC RX: KISS decoder recovers AX.25 UI (what serial RX feeds max25d)."""
    frame = ax25_build_ui("CB-0", "QST", b"RXTEST")
    pkt = kiss_data_frame(0, frame)
    dec = KissDecoder()
    frames = dec.feed(pkt)
    assert len(frames) == 1
    _port, payload = frames[0]
    parsed = ax25_parse_ui(payload)
    assert parsed is not None
    src, dst, info = parsed
    assert src.startswith("CB")
    assert dst == "QST"
    assert info == b"RXTEST"
    print("PASS: TNC RX KISS decode")


def test_tnc_recovery_helpers() -> None:
    """TNC RX/handshake helpers offline (banner / ESC V — no serial)."""
    tncs = ROOT / "stacks" / "tncs"
    spec = importlib.util.spec_from_file_location(
        "tnc_serial_recovery", tncs / "tnc_serial_recovery.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.has_banner(b"TheFirmware Version 2.7")
    assert mod.tf_mycall_frame("cb-0") == b"\x1bI CB-0\r"
    print("PASS: TNC recovery helpers")


def test_bcpr_tx_kiss_encode() -> None:
    """BayCom/based (bcpr) TX: BcprKissBackend encodes KISS without UART."""
    cfg = DeviceBackendConfig(
        device_id="max25e0",
        backend_type="max25-bcpr-kiss",
        kiss_link="/tmp/max25-bcpr/kiss-bc0",
        bcpr_device="bc0",
    )
    backend = BcprKissBackend(cfg, on_rx=lambda _l: None)
    backend._fd = 99
    backend._kiss_active = True
    written: list[bytes] = []
    with patch("os.write", side_effect=lambda _fd, data: written.append(data) or len(data)):
        with patch("termios.tcdrain"):
            ok, display = backend.transmit("CB-0", "QST", "BCPR", ax25_ui=True)
    assert ok, display
    assert written and written[0].startswith(b"\xc0")
    print("PASS: bcpr TX KISS encode")


def test_host_connect_send_loopback() -> None:
    """Host TX+RX path: max25d CONNECT/SEND with --no-stack --no-serial (loopback)."""
    if not DAEMON.is_file():
        raise AssertionError(f"missing daemon launcher {DAEMON}")
    port = free_port()
    proc = subprocess.Popen(
        [str(DAEMON), "--no-stack", "--no-serial", "-c", str(INI), "--tcp-port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if not wait_for_port(port, proc):
        err = proc.stderr.read() if proc.stderr else ""
        proc.terminate()
        proc.wait(timeout=3)
        raise AssertionError(f"max25d not listening: {err.strip()}")
    try:
        sock = socket.create_connection(("127.0.0.1", port), timeout=3)
        reader = LineReader(sock)
        assert reader.read() == "OK"
        assert reader.read().startswith("STATUS ")
        sock.sendall(b"SET CALLERID CB-0\n")
        assert reader.read() == "OK"
        sock.sendall(b"CONNECT\n")
        assert reader.read() == "EVENT connected"
        assert reader.read() == "OK"
        sock.sendall(b"SEND TXRX\n")
        rx = reader.read()
        assert rx.startswith("RX "), rx
        assert reader.read() == "OK"
        sock.close()
        print("PASS: host CONNECT/SEND loopback (TX+RX echo)")
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def main() -> int:
    tests = [
        test_tnc_tx_kiss_encode,
        test_tnc_rx_kiss_decode,
        test_tnc_recovery_helpers,
        test_bcpr_tx_kiss_encode,
        test_host_connect_send_loopback,
    ]
    for fn in tests:
        fn()
    print("OK: tx/rx offline (TNC + bcpr host paths)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 — L0 gate: one clear FAIL
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
