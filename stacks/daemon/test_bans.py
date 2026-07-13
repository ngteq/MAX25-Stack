#!/usr/bin/env python3
"""Unit and protocol tests for max25d AX.25 source ban list."""
from __future__ import annotations

import importlib.util
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "stacks/daemon/max25d"
DAEMON = ROOT / "stacks/daemon/max25d.py"

sys.path.insert(0, str(DAEMON.parent))
from banlist import BanList, callsign_banned, extract_ax25_source  # noqa: E402


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


def test_extract_ax25_source() -> None:
    assert extract_ax25_source("[AX25 UI DG1ABC>QST] 73") == "DG1ABC"
    assert extract_ax25_source("[AX25 UI DK0WC-7>CB-0] hi") == "DK0WC-7"
    assert extract_ax25_source("plain text") is None
    assert extract_ax25_source("[CRDOP RX soft-crdop] hello") is None


def test_callsign_banned_matching() -> None:
    assert callsign_banned("DG1ABC", "DG1ABC")
    assert callsign_banned("DG1ABC", "DG1ABC-7")
    assert not callsign_banned("DG1ABC", "DG1ABD")
    assert callsign_banned("DK0WC-7", "DK0WC-7")
    assert not callsign_banned("DK0WC-7", "DK0WC")
    assert not callsign_banned("DK0WC-7", "DK0WC-8")


def test_banlist_file_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "bans.txt"
        path.write_text("# ignored comment\nDG1ABC\n\nDK0WC-7\n", encoding="utf-8")
        bans = BanList(path)
        assert bans.list() == ["DG1ABC", "DK0WC-7"]
        assert bans.is_banned("DG1ABC-3")
        assert bans.is_banned("DK0WC-7")
        assert not bans.is_banned("DK0WC")

        bans.add("DL1TEST")
        bans.remove("DG1ABC")
        assert bans.list() == ["DK0WC-7", "DL1TEST"]
        reloaded = BanList(path)
        assert reloaded.list() == ["DK0WC-7", "DL1TEST"]


def test_on_backend_rx_silent_drop() -> None:
    mod = load_max25d_module()
    with tempfile.TemporaryDirectory() as tmp:
        bans_path = Path(tmp) / "bans.txt"
        bans_path.write_text("DG1ABC\n", encoding="utf-8")
        cfg = mod.DaemonConfig(bans_file=str(bans_path))
        state = mod.DaemonState(cfg=cfg, bans=BanList(bans_path))
        mod.init_device_runtimes(state)

        sent: list[str] = []

        def capture(_state, line, skip=None):
            sent.append(line)

        with patch.object(mod, "broadcast", side_effect=capture), patch.object(mod, "log"):
            mod.on_backend_rx(state, "tnc2c", "[AX25 UI DG1ABC>QST] blocked")
            assert sent == []

            mod.on_backend_rx(state, "tnc2c", "[AX25 UI DK0WC>QST] allowed")
            assert sent == ["RX device=tnc2c [AX25 UI DK0WC>QST] allowed"]


def test_ban_commands_protocol() -> None:
    port = free_port()
    with tempfile.TemporaryDirectory() as tmp:
        bans_path = Path(tmp) / "bans.txt"
        ini_path = Path(tmp) / "max25d.ini"
        ini_path.write_text(
            f"""
[daemon]
device = tnc2c
hardware = tncs
[network]
tcp_host = 127.0.0.1
tcp_port = {port}
[modem]
bans_file = {bans_path}
[stack]
auto_start = no
""",
            encoding="utf-8",
        )

        proc = subprocess.Popen(
            [
                str(LAUNCHER),
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
            raise RuntimeError(f"connect failed: {exc}") from exc

        reader = LineReader(sock)
        try:
            assert reader.read() == "OK"
            reader.read()  # STATUS

            sock.sendall(b"BAN DG1ABC\n")
            assert reader.read() == "OK"
            assert bans_path.read_text(encoding="utf-8").strip() == "DG1ABC"

            sock.sendall(b"BANS\n")
            assert reader.read() == "BAN DG1ABC"
            assert reader.read() == "OK"

            sock.sendall(b"UNBAN DG1ABC\n")
            assert reader.read() == "OK"
            assert bans_path.read_text(encoding="utf-8") == ""

            sock.sendall(b"UNBAN DG1ABC\n")
            assert reader.read() == "ERR not banned"

            sock.sendall(b"BAN BAD!\n")
            assert reader.read() == "ERR invalid callsign"
        finally:
            sock.close()
            proc.terminate()
            proc.wait(timeout=5)


def main() -> int:
    tests = [
        test_extract_ax25_source,
        test_callsign_banned_matching,
        test_banlist_file_roundtrip,
        test_on_backend_rx_silent_drop,
        test_ban_commands_protocol,
    ]
    for test in tests:
        test()
        print(f"OK: {test.__name__}")
    print("OK: banlist tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
