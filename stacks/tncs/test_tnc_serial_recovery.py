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


def test_format_rx_brief_and_classify() -> None:
    assert mod.format_rx_brief(b"") == "0 B silent"
    brief = mod.format_rx_brief(b"kiss off\rINFO\r")
    assert "14 B" in brief
    assert "markers=none" in brief
    assert "echo-only" in mod.classify_recovery_failure(b"kiss off\rINFO\r")
    assert "silent" in mod.classify_recovery_failure(b"")
    diag = mod.classify_recovery_failure(b"TheFirmware cmd:")
    assert "banner" in diag


def test_probe_tf_terminal() -> None:
    port = MockPort()
    port.responses = [b"TheFirmware Version 2.7 DAMA\r\nChecksum"]
    ok, combined, only_echo = mod.probe_tf_terminal(port.write_flush, port.read_for)
    assert ok
    assert not only_echo
    assert port.written[0] == mod.TF_ESC_V


def test_tf_mycall_frame() -> None:
    assert mod.tf_mycall_frame("cb-0") == b"\x1bI CB-0\r"


def test_recover_terminal_ok_on_passive_banner() -> None:
    port = MockPort()
    port.responses = [b"NORD TheFirmware Version 2.7\r\n"]
    ok, rx = mod.recover_terminal(
        port.write_flush, port.read_for, skip_kiss_frame=True, log=lambda _m: None
    )
    assert ok
    assert b"TheFirmware" in rx
    assert b"\xc0\xff\xc0" not in port.written


def test_recover_terminal_ok_after_kiss_return() -> None:
    port = MockPort()
    port.responses = [
        b"",
        b"TheFirmware Version 2.7\r\nChecksum (0000) = DC0A\r\n",
    ]
    ok, rx = mod.recover_terminal(
        port.write_flush, port.read_for, skip_kiss_frame=False, log=lambda _m: None
    )
    assert ok
    assert b"TheFirmware" in rx
    assert port.written[0] == b"\xc0\xff\xc0"


def test_recover_terminal_sends_qres_on_failure() -> None:
    port = MockPort()
    port.responses = [b""] * 40
    ok, _ = mod.recover_terminal(
        port.write_flush, port.read_for, skip_kiss_frame=True, log=lambda _m: None
    )
    assert not ok
    assert mod.TF_ESC_QRES in port.written
    assert b"RESTART\r" not in port.written


def test_enter_kiss_native() -> None:
    port = MockPort()
    port.responses = [b""]
    mod.enter_kiss(port.write_flush, port.read_for, entry="kiss_on")
    assert port.written[0] == mod.TF_ESC_AT_K


def main() -> int:
    tests = [
        test_has_banner,
        test_format_rx_brief_and_classify,
        test_probe_tf_terminal,
        test_tf_mycall_frame,
        test_recover_terminal_ok_on_passive_banner,
        test_recover_terminal_ok_after_kiss_return,
        test_recover_terminal_sends_qres_on_failure,
        test_enter_kiss_native,
    ]
    for fn in tests:
        fn()
        print(f"OK {fn.__name__}")
    print(f"All {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
