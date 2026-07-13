#!/usr/bin/env python3
"""Offline tests for max25d TNC serial watch / stabilize."""
from __future__ import annotations

import configparser
import importlib.util
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[2]
DAEMON = ROOT / "stacks/daemon/max25d"


def load_max25d():
    from importlib.machinery import SourceFileLoader

    loader = SourceFileLoader("max25d", str(DAEMON))
    spec = importlib.util.spec_from_loader("max25d", loader)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["max25d"] = mod
    loader.exec_module(mod)
    return mod


def test_stack_serial_watch_config() -> None:
    mod = load_max25d()
    cp = configparser.ConfigParser()
    cp.read_string(
        """
[stack]
auto_start = yes
serial_watch = no
serial_watch_interval = 45
serial_repair_cooldown = 10
stack_recover_only = no
stack_retry_interval = 90
"""
    )
    cfg = mod.DaemonConfig()
    cfg.auto_start = mod._truthy(cp.get("stack", "auto_start"))
    cfg.serial_watch = mod._truthy(cp.get("stack", "serial_watch"))
    cfg.serial_watch_interval = cp.getint("stack", "serial_watch_interval")
    cfg.serial_repair_cooldown = cp.getint("stack", "serial_repair_cooldown")
    cfg.stack_recover_only = mod._truthy(cp.get("stack", "stack_recover_only"))
    cfg.stack_retry_interval = cp.getint("stack", "stack_retry_interval")
    assert cfg.serial_watch is False
    assert cfg.serial_watch_interval == 45
    assert cfg.stack_recover_only is False


def test_serial_repair_statuses() -> None:
    mod = load_max25d()
    assert "error-io" in mod.BACKEND_RETRY_STATUSES
    assert "error-host" in mod.SERIAL_REPAIR_STATUSES


def test_stabilize_session_probe_path() -> None:
    sys.path.insert(0, str(ROOT / "stacks/daemon"))
    from kiss_bridge import KissBridge, SerialProfile  # noqa: E402

    bridge = KissBridge(SerialProfile(), lambda _l: None, log=lambda _m: None)
    bridge._fd = 99
    bridge._kiss_active = True

    fake = MagicMock()
    fake.probe_info.return_value = (True, b"TheFirmware cmd:", False)
    fake.recover_terminal.return_value = (True, b"")

    with patch.object(bridge, "_write_unlocked"), patch.object(
        bridge, "_drain_unlocked", return_value=b""
    ), patch.object(bridge, "_set_mycall_unlocked", return_value=True), patch.object(
        bridge, "_enter_kiss_unlocked", return_value=True
    ), patch.object(bridge, "_load_recovery_mod", return_value=fake):
        ok = bridge.stabilize_session("CB-0")
    assert ok
    assert bridge.status == "ready"
    fake.recover_terminal.assert_not_called()


def main() -> int:
    test_stack_serial_watch_config()
    print("OK test_stack_serial_watch_config")
    test_serial_repair_statuses()
    print("OK test_serial_repair_statuses")
    test_stabilize_session_probe_path()
    print("OK test_stabilize_session_probe_path")
    print("All serial watch tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
