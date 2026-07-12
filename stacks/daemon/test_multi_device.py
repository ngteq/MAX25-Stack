#!/usr/bin/env python3
"""Multi-device config and M25/1 protocol tests for max25d (no serial hardware)."""
from __future__ import annotations

import configparser
import importlib.util
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
DAEMON = ROOT / "stacks/daemon/max25d"
BASE_INI = ROOT / "share/max25/max25d.ini.example"


def load_max25d_module():
    from importlib.machinery import SourceFileLoader

    loader = SourceFileLoader("max25d", str(DAEMON))
    spec = importlib.util.spec_from_loader("max25d", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["max25d"] = mod
    loader.exec_module(mod)
    return mod


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


def test_parse_legacy_single_device() -> None:
    mod = load_max25d_module()
    cp = configparser.ConfigParser()
    cp.read_string(
        """
[daemon]
device = tnc2c
hardware = tncs
[serial]
device = /dev/ttyS4
baud = 19200
"""
    )
    cfg = mod.DaemonConfig(device="tnc2c", hardware="tncs")
    devices = mod.parse_devices(cp, cfg)
    assert len(devices) == 1
    assert devices[0].device_id == "tnc2c"
    assert devices[0].serial_device == "/dev/ttyS4"
    assert devices[0].serial_baud == 19200


def test_parse_multi_devices() -> None:
    mod = load_max25d_module()
    cp = configparser.ConfigParser()
    cp.read_string(
        """
[devices]
default = tnc2c
tnc2c = /dev/ttyS4
pktnc2 = /dev/ttyS5
dev3 = /dev/ttyUSB0
dev4 = /dev/ttyUSB1
dev5 = /dev/ttyUSB2
[serial.dev3]
baud = 9600
"""
    )
    cfg = mod.DaemonConfig()
    devices = mod.parse_devices(cp, cfg)
    assert len(devices) == 5
    ids = {d.device_id for d in devices}
    assert ids == {"tnc2c", "pktnc2", "dev3", "dev4", "dev5"}
    by_id = {d.device_id: d for d in devices}
    assert by_id["tnc2c"].serial_device == "/dev/ttyS4"
    assert by_id["dev3"].serial_baud == 9600
    assert cfg.default_device == "tnc2c"


def test_parse_enabled_filter() -> None:
    mod = load_max25d_module()
    cp = configparser.ConfigParser()
    cp.read_string(
        """
[devices]
enabled = tnc2c,pktnc2
tnc2c = /dev/ttyS4
pktnc2 = /dev/ttyS5
extra = /dev/ttyUSB9
"""
    )
    cfg = mod.DaemonConfig()
    devices = mod.parse_devices(cp, cfg)
    enabled = {d.device_id for d in devices if d.enabled}
    disabled = {d.device_id for d in devices if not d.enabled}
    assert enabled == {"tnc2c", "pktnc2"}
    assert disabled == {"extra"}


def test_five_mock_bridges() -> None:
    """Five concurrent KissBridge instances with mocked serial open."""
    mod = load_max25d_module()
    opened: list[str] = []

    class FakeBridge:
        def __init__(self, profile, on_rx, log=None):
            self.profile = profile
            self._on_rx = on_rx
            self.status = "ready"

        def open(self):
            opened.append(self.profile.device)
            return True

        def attach_session(self, mycall):
            return True

        def transmit(self, src, dst, text, ax25_ui):
            return True, f"[AX25 UI {src}>{dst}] {text}"

        def close(self):
            self.status = "closed"

        def detach_session(self):
            pass

    cp = configparser.ConfigParser()
    cp.read_string(
        """
[devices]
default = d1
d1 = /dev/fake0
d2 = /dev/fake1
d3 = /dev/fake2
d4 = /dev/fake3
d5 = /dev/fake4
"""
    )
    cfg = mod.DaemonConfig(hardware="tncs", serial_enabled=True)
    cfg.devices = [
        mod.DeviceConfig(device_id=f"d{i}", serial_device=f"/dev/fake{i - 1}", enabled=True)
        for i in range(1, 6)
    ]
    cfg.default_device = "d1"
    state = mod.DaemonState(cfg=cfg)
    mod.init_device_runtimes(state)

    with patch.object(mod, "KissBridge", FakeBridge):
        with patch.object(mod, "tnc_serial_enabled", return_value=True):
            assert mod.attach_all_sessions(state)
            assert len(opened) == 5
            assert set(opened) == {f"/dev/fake{i}" for i in range(5)}

            state.selected_device = "d3"
            dev_id = mod.resolve_selected_device(state)
            assert dev_id == "d3"
            rt = state.devices["d3"]
            ok, display = rt.bridge.transmit("CB-0", "QST", "hi", True)
            assert ok
            assert "hi" in display


def run_daemon_test(ini_text: str, fn: Callable[[LineReader, socket.socket], None]) -> None:
    port = free_port()
    with tempfile.NamedTemporaryFile("w", suffix=".ini", delete=False) as tmp:
        tmp.write(ini_text)
        ini_path = Path(tmp.name)

    proc = subprocess.Popen(
        [
            sys.executable,
            str(DAEMON),
            "--no-stack",
            "--no-serial",
            "-c",
            str(ini_path),
            "--tcp-port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(0.6)
    try:
        sock = socket.create_connection(("127.0.0.1", port), timeout=3)
    except OSError as exc:
        proc.terminate()
        proc.wait(timeout=3)
        ini_path.unlink(missing_ok=True)
        raise RuntimeError(f"connect failed: {exc}") from exc

    reader = LineReader(sock)
    try:
        assert reader.read() == "OK"
        fn(reader, sock)
    finally:
        sock.close()
        proc.terminate()
        proc.wait(timeout=5)
        ini_path.unlink(missing_ok=True)


def test_protocol_multi_device() -> None:
    ini = BASE_INI.read_text()

    def exercise(reader: LineReader, sock: socket.socket) -> None:
        status = reader.read()
        assert status.startswith("STATUS ")
        assert "devices=tnc2c,pktnc2" in status
        assert "device=tnc2c" in status

        sock.sendall(b"GET DEVICES\n")
        lines = []
        while True:
            line = reader.read()
            lines.append(line)
            if line == "OK":
                break
        device_lines = [l for l in lines if l.startswith("DEVICE ")]
        assert len(device_lines) == 2
        assert any("id=tnc2c" in l for l in device_lines)
        assert any("id=pktnc2" in l for l in device_lines)

        sock.sendall(b"SET DEVICE pktnc2\n")
        assert reader.read() == "OK"

        sock.sendall(b"GET STATUS\n")
        st = reader.read()
        assert "device=pktnc2" in st
        assert reader.read() == "OK"

        sock.sendall(b"SELECT DEVICE tnc2c\n")
        assert reader.read() == "OK"

        sock.sendall(b"CONNECT\n")
        assert reader.read() == "EVENT connected"
        assert reader.read() == "OK"

        sock.sendall(b"SEND 73\n")
        rx = reader.read()
        assert rx.startswith("RX ")
        assert reader.read() == "OK"

        sock.sendall(b"DISCONNECT\n")
        assert reader.read() == "EVENT disconnected"
        assert reader.read() == "OK"

    run_daemon_test(ini, exercise)


def test_protocol_legacy_single() -> None:
    ini = """
[daemon]
mode = standalone
hardware = tncs
device = tnc2c
[network]
tcp_host = 127.0.0.1
tcp_port = 7325
[modem]
callerid = CB-0
callid = QST
[stack]
auto_start = no
"""

    def exercise(reader: LineReader, sock: socket.socket) -> None:
        status = reader.read()
        assert "device=tnc2c" in status
        assert "devices=tnc2c" in status

        sock.sendall(b"SET DEVICE tnc2c\n")
        assert reader.read() == "OK"

    run_daemon_test(ini, exercise)


def main() -> int:
    tests = [
        test_parse_legacy_single_device,
        test_parse_multi_devices,
        test_parse_enabled_filter,
        test_five_mock_bridges,
        test_protocol_multi_device,
        test_protocol_legacy_single,
    ]
    for fn in tests:
        fn()
    print("OK: multi-device tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
