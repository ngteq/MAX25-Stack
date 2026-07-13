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
DAEMON = ROOT / "stacks/daemon/max25d.py"


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
    assert "open" not in mod.SERIAL_REPAIR_STATUSES


def test_inline_tnc_prep() -> None:
    mod = load_max25d()
    cfg = mod.DaemonConfig(stack_recover_only=True)
    state = mod.DaemonState(cfg=cfg)
    from device_backends import DeviceBackendConfig  # noqa: E402

    state.devices["tnc2c"] = mod.DeviceRuntime(
        cfg=DeviceBackendConfig(device_id="tnc2c", backend_type="kiss-serial")
    )
    state.devices["baycom-ser12"] = mod.DeviceRuntime(
        cfg=DeviceBackendConfig(device_id="baycom-ser12", backend_type="baycom-kiss")
    )
    assert mod.uses_inline_tnc_prep(state, "tnc2c")
    assert not mod.uses_inline_tnc_prep(state, "baycom-ser12")


def test_stabilize_ready_kiss_skips_probe() -> None:
    from kiss_bridge import KissBridge, SerialProfile  # noqa: E402

    bridge = KissBridge(SerialProfile(), lambda _l: None, log=lambda _m: None)
    bridge._fd = 99
    bridge._kiss_active = True
    bridge.status = "ready"

    fake = MagicMock()

    with patch.object(bridge, "_stop_rx_thread") as stop_rx, patch.object(
        bridge, "_load_recovery_mod", return_value=fake
    ), patch.object(bridge, "_start_rx_thread") as start_rx:
        ok = bridge.stabilize_session("CB-0", force=False)

    assert ok
    assert bridge.status == "ready"
    fake.probe_info.assert_not_called()
    fake.recover_terminal.assert_not_called()
    stop_rx.assert_not_called()
    start_rx.assert_not_called()


def test_poll_serial_stability_skips_ready() -> None:
    mod = load_max25d()
    cfg = mod.DaemonConfig(serial_watch=True, stack_recover_only=True)
    state = mod.DaemonState(cfg=cfg)
    state.started_at = 0
    from device_backends import DeviceBackendConfig  # noqa: E402

    state.devices["tnc2c"] = mod.DeviceRuntime(
        cfg=DeviceBackendConfig(device_id="tnc2c", backend_type="kiss-serial")
    )
    rt = state.devices["tnc2c"]
    rt.stack_status = "ready"
    rt.last_watch = 0
    backend = MagicMock()
    backend.status = "ready"
    rt.backend = backend

    mod.poll_serial_stability(state)

    backend.stabilize_session.assert_not_called()


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
    ), patch.object(bridge, "_load_recovery_mod", return_value=fake), patch.object(
        bridge, "_start_rx_thread"
    ):
        ok = bridge.stabilize_session("CB-0")
    assert ok
    assert bridge.status == "ready"
    fake.recover_terminal.assert_not_called()


def test_rx_thread_deferred_until_ready() -> None:
    from kiss_bridge import KissBridge, SerialProfile  # noqa: E402

    bridge = KissBridge(SerialProfile(), lambda _l: None, log=lambda _m: None)
    bridge._fd = 99
    bridge._kiss_active = True
    assert bridge._thread is None
    bridge._start_rx_thread()
    assert bridge._thread is not None
    bridge._stop_rx_thread()
    assert bridge._thread is None


def test_stabilize_stops_rx_during_recovery() -> None:
    from kiss_bridge import KissBridge, SerialProfile  # noqa: E402

    bridge = KissBridge(SerialProfile(), lambda _l: None, log=lambda _m: None)
    bridge._fd = 99
    bridge._kiss_active = True
    bridge._start_rx_thread()
    assert bridge._thread is not None

    fake = MagicMock()
    fake.probe_info.return_value = (True, b"TheFirmware cmd:", False)
    fake.recover_terminal.return_value = (True, b"")

    with patch.object(bridge, "_write_unlocked"), patch.object(
        bridge, "_drain_unlocked", return_value=b""
    ), patch.object(bridge, "_set_mycall_unlocked", return_value=True), patch.object(
        bridge, "_enter_kiss_unlocked", return_value=True
    ), patch.object(bridge, "_load_recovery_mod", return_value=fake), patch.object(
        bridge, "_start_rx_thread"
    ) as start_rx:
        ok = bridge.stabilize_session("CB-0")
    assert ok
    start_rx.assert_called_once()


def test_bootwait_escalate_config() -> None:
    mod = load_max25d()
    cfg = mod.DaemonConfig()
    assert cfg.serial_bootwait_escalate is True
    assert cfg.serial_bootwait_escalate_after == 3
    assert cfg.serial_bootwait_escalate_cooldown == 300


def test_prep_escalates_on_error_host() -> None:
    mod = load_max25d()
    cfg = mod.DaemonConfig(stack_recover_only=True, serial_bootwait_escalate=True)
    state = mod.DaemonState(cfg=cfg)
    from device_backends import DeviceBackendConfig  # noqa: E402

    state.devices["tnc2c"] = mod.DeviceRuntime(
        cfg=DeviceBackendConfig(device_id="tnc2c", backend_type="kiss-serial")
    )
    backend = MagicMock()
    backend.status = "error-host"
    backend.stabilize_session.return_value = False
    rt = state.devices["tnc2c"]
    rt.backend = backend

    with patch.object(mod, "open_backend", return_value=True), patch.object(
        mod, "escalate_to_bootwait_stack"
    ) as escalate:
        mod.prep_inline_serial_device(state, "tnc2c")
    escalate.assert_called_once_with(state, "tnc2c")


def main() -> int:
    test_stack_serial_watch_config()
    print("OK test_stack_serial_watch_config")
    test_serial_repair_statuses()
    print("OK test_serial_repair_statuses")
    test_inline_tnc_prep()
    print("OK test_inline_tnc_prep")
    test_stabilize_ready_kiss_skips_probe()
    print("OK test_stabilize_ready_kiss_skips_probe")
    test_poll_serial_stability_skips_ready()
    print("OK test_poll_serial_stability_skips_ready")
    test_stabilize_session_probe_path()
    print("OK test_stabilize_session_probe_path")
    test_rx_thread_deferred_until_ready()
    print("OK test_rx_thread_deferred_until_ready")
    test_stabilize_stops_rx_during_recovery()
    print("OK test_stabilize_stops_rx_during_recovery")
    test_bootwait_escalate_config()
    print("OK test_bootwait_escalate_config")
    test_prep_escalates_on_error_host()
    print("OK test_prep_escalates_on_error_host")
    print("All serial watch tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
