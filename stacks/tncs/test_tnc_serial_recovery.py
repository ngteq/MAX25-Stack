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


def test_probe_combined_banner() -> None:
    port = MockPort()
    port.responses = [b"NORD TheFirmware 2.7\r\ncmd: "]
    ok, combined, only_echo = mod.probe_combined(port.write_flush, port.read_for)
    assert ok
    assert not only_echo
    assert b"TheFirmware" in combined


def test_recover_terminal_success_after_jhost() -> None:
    port = MockPort()
    # passive, kiss, esc@k, jhost, flush, probe banner (2 reads in probe_info)
    port.responses = [b"", b"", b"", b"", b"", b"", b"NORD TheFirmware\r\ncmd: "]
    ok, rx = mod.recover_terminal(
        port.write_flush, port.read_for, skip_kiss_frame=False, log=lambda _m: None
    )
    assert ok
    assert b"TheFirmware" in rx
    assert b"\xc0\xff\xc0" in port.written[0]
    assert b"\x1b@K" in port.written[1]


def test_recover_terminal_sends_restart_on_echo() -> None:
    port = MockPort()
    port.responses = [b""] * 40
    ok, _ = mod.recover_terminal(
        port.write_flush, port.read_for, skip_kiss_frame=True, log=lambda _m: None
    )
    assert not ok
    assert b"RESTART\r" in port.written
    assert b"\x1b@K" not in port.written[0:1]  # skipped kiss frame


def main() -> int:
    tests = [
        test_has_banner,
        test_format_rx_brief_and_classify,
        test_probe_combined_banner,
        test_recover_terminal_success_after_jhost,
        test_recover_terminal_sends_restart_on_echo,
    ]
    for fn in tests:
        fn()
        print(f"OK {fn.__name__}")
    print(f"All {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
