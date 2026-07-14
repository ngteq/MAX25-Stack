#!/usr/bin/env python3
"""INI reporting switches — error= / voice= in STATUS."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from device_backends import DeviceBackendConfig  # noqa: E402
import max25d  # noqa: E402


def _state(
    *,
    error_on: bool = True,
    voice_on: bool = True,
    link: str = "ready",
    signal_valid: bool | None = None,
    backend_type: str = "kiss-serial",
    hardware: str = "tncs",
) -> max25d.DaemonState:
    cfg = max25d.DaemonConfig(
        report_error_transmissions=error_on,
        report_voice_transmissions=voice_on,
    )
    dev = DeviceBackendConfig(
        device_id="tnc2c",
        enabled=True,
        backend_type=backend_type,
        hardware=hardware,
    )
    rt = max25d.DeviceRuntime(cfg=dev, link_status=link, signal_valid=signal_valid)
    state = max25d.DaemonState(cfg=cfg)
    state.devices["tnc2c"] = rt
    state.selected_device = "tnc2c"
    return state


def test_error_valid_when_enabled_and_ready() -> None:
    line = max25d.status_line(_state())
    assert "error=valid" in line


def test_error_invalid_when_disabled() -> None:
    line = max25d.status_line(_state(error_on=False))
    assert "error=invalid" in line


def test_error_invalid_on_link_fault() -> None:
    line = max25d.status_line(_state(link="error-io"))
    assert "error=invalid" in line


def test_error_invalid_on_bad_frame() -> None:
    line = max25d.status_line(_state(signal_valid=False))
    assert "error=invalid" in line


def test_voice_valid_tnc_only() -> None:
    line = max25d.status_line(_state())
    assert "voice=valid" in line


def test_voice_invalid_when_disabled() -> None:
    line = max25d.status_line(_state(voice_on=False))
    assert "voice=invalid" in line


def test_voice_invalid_crdop_not_ready() -> None:
    line = max25d.status_line(
        _state(
            backend_type="crdop-tcp",
            hardware="soft-modems",
            link="error-connect",
        )
    )
    assert "voice=invalid" in line


def test_device_line_includes_reporting() -> None:
    state = _state()
    dev = max25d.device_line(state, "tnc2c")
    assert "error=valid" in dev
    assert "voice=n/a" in dev


if __name__ == "__main__":
    test_error_valid_when_enabled_and_ready()
    test_error_invalid_when_disabled()
    test_error_invalid_on_link_fault()
    test_error_invalid_on_bad_frame()
    test_voice_valid_tnc_only()
    test_voice_invalid_when_disabled()
    test_voice_invalid_crdop_not_ready()
    test_device_line_includes_reporting()
    print("test_reporting: ok")
