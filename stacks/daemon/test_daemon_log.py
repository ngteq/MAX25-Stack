#!/usr/bin/env python3
"""Unit tests for max25d structured logging."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "stacks" / "daemon"))

from daemon_log import DaemonLogger, emit_startup_banner  # noqa: E402
from device_backends import DeviceBackendConfig  # noqa: E402


def test_structured_levels() -> None:
    lines: list[str] = []
    log = DaemonLogger(emit=lines.append)
    log.ok("prep complete", area="serial", device="tnc2c")
    log.recovery("JHOST 0 — banner", device="pktnc2")
    log.warn("no password", area="security")
    assert lines[0] == "max25d [OK] [serial] [tnc2c] prep complete"
    assert lines[1] == "max25d [RECOVERY] [serial] [pktnc2] JHOST 0 — banner"
    assert lines[2] == "max25d [WARN] [security] no password"


def test_emit_unstructured_device_prefix() -> None:
    lines: list[str] = []
    log = DaemonLogger(emit=lines.append)
    log.emit_unstructured("tnc2c: recovery: OK after JHOST 0")
    assert "[tnc2c]" in lines[0]
    assert "[RECOVERY]" in lines[0]
    assert "OK after JHOST 0" in lines[0]


def test_startup_banner_sections() -> None:
    from dataclasses import dataclass

    @dataclass
    class Cfg:
        mode: str = "standalone"
        device: str = "tnc2c"
        default_device: str = "tnc2c"
        tcp_host: str = "0.0.0.0"
        tcp_port: int = 7325
        unix_socket: str = "/run/max25/modem.sock"
        tcp_password: str = ""
        callerid: str = "CB-0"
        callid: str = "QST"
        ax25_ui: bool = True
        bans_file: str = ""
        auto_start: bool = True
        serial_enabled: bool = True
        stack_recover_only: bool = True
        serial_watch: bool = True
        serial_watch_interval: int = 60
        serial_watch_startup_grace: int = 45
        serial_bootwait_escalate: bool = True
        hardware: str = "tncs"

    lines: list[str] = []
    from daemon_log import LOGGER

    orig = LOGGER._emit
    try:
        LOGGER._emit = lines.append
        dev = DeviceBackendConfig(device_id="tnc2c", backend_type="kiss-serial")
        dev.serial_device = "/dev/ttyS4"
        dev.serial_baud = 19200
        dev.serial_line = "8n1"
        emit_startup_banner(
            config_path="/etc/max25/max25d.ini",
            cfg=Cfg(),
            devices=[dev],
            tested_fn=lambda _d: True,
        )
    finally:
        LOGGER._emit = orig

    text = "\n".join(lines)
    assert "=== MAX25d starting ===" in text
    assert "[config]" in text
    assert "ini=/etc/max25/max25d.ini" in text
    assert "[devices]" in text
    assert "tnc2c=" in text


def main() -> int:
    test_structured_levels()
    print("OK test_structured_levels")
    test_emit_unstructured_device_prefix()
    print("OK test_emit_unstructured_device_prefix")
    test_startup_banner_sections()
    print("OK test_startup_banner_sections")
    print("All daemon_log tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
