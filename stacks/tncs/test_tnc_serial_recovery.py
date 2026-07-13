#!/usr/bin/env python3
"""Offline unit tests for tnc_serial_recovery (no serial hardware)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "tnc_serial_recovery", ROOT / "tnc_serial_recovery.py"
)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class MockPort:
    def __init__(self) -> None:
        self.written: list[bytes] = []
        self.responses: list[bytes] = []
        self._read_idx = 0

    def write_flush(self, data: bytes) -> None:
        self.written.append(data)

    def read_for(self, seconds: float) -> bytes:
        del seconds
        if self._read_idx < len(self.responses):
            chunk = self.responses[self._read_idx]
            self._read_idx += 1
            return chunk
        return b""


def test_has_banner() -> None:
    assert mod.has_banner(b"NORD><LINK TheFirmware Version 2.7")
    assert mod.has_banner(b"cmd: ")
    assert not mod.has_banner(b"INFO\r\nINFO")


def test_is_echo_only() -> None:
    assert mod.is_echo_only(b"INFO\r", b"INFO")
    assert mod.is_echo_only(b"kiss off\r", b"kiss off\r\n")
    assert not mod.is_echo_only(b"INFO\r", b"TheFirmware 2.7\r\ncmd:")


def test_probe_info_banner() -> None:
    port = MockPort()
    port.responses = [b"", b"TheFirmware 2.7\r\ncmd: "]
    ok, combined, only_echo = mod.probe_info(port.write_flush, port.read_for, pause=0.01)
    assert ok
    assert not only_echo
    assert b"TheFirmware" in combined
    assert port.written[0] == b"kiss off\r"
    assert port.written[1] == b"INFO\r"


def test_probe_info_echo_only() -> None:
    port = MockPort()
    port.responses = [b"kiss off\r", b"INFO\r"]
    ok, _, only_echo = mod.probe_info(port.write_flush, port.read_for, pause=0.01)
    assert not ok
    assert only_echo


def test_recover_terminal_success_after_jhost() -> None:
    port = MockPort()
    # passive, kiss return, jhost, probe (banner)
    port.responses = [b"", b"", b"", b"", b"NORD TheFirmware\r\ncmd: "]
    ok, rx = mod.recover_terminal(
        port.write_flush, port.read_for, skip_kiss_frame=False, log=lambda _m: None
    )
    assert ok
    assert b"TheFirmware" in rx
    assert b"\xc0\xff\xc0" in port.written[0]
    assert any(b"JHOST 0" in w for w in port.written)


def test_recover_terminal_restart_path() -> None:
    port = MockPort()
    # passive, kiss, jhost, probe echo (2 reads), restart drain, probe banner (2 reads)
    port.responses = [
        b"",
        b"",
        b"",
        b"kiss off\r",
        b"INFO\r",
        b"",
        b"",
        b"TheFirmware cmd:\r\n",
    ]
    ok, _ = mod.recover_terminal(
        port.write_flush, port.read_for, skip_kiss_frame=False, log=lambda _m: None
    )
    assert ok
    assert b"RESTART\r" in port.written


def test_enter_kiss_auto_esc() -> None:
    port = MockPort()
    port.responses = [b"kiss on\r"]
    mod.enter_kiss(port.write_flush, port.read_for, entry="auto")
    assert port.written[0] == b"kiss on\r"
    assert port.written[1] == b"\x1b@K"


def test_enter_kiss_on() -> None:
    port = MockPort()
    port.responses = [b"ok\r\n"]
    mod.enter_kiss(port.write_flush, port.read_for, entry="kiss_on")
    assert port.written == [b"kiss on\r"]


def main() -> int:
    tests = [
        test_has_banner,
        test_is_echo_only,
        test_probe_info_banner,
        test_probe_info_echo_only,
        test_recover_terminal_success_after_jhost,
        test_recover_terminal_restart_path,
        test_enter_kiss_auto_esc,
        test_enter_kiss_on,
    ]
    for fn in tests:
        fn()
        print(f"OK {fn.__name__}")
    print(f"All {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
