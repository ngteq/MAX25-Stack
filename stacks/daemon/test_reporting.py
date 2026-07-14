#!/usr/bin/env python3
"""INI reporting switches — error= / voice= in STATUS."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from device_backends import DeviceBackendConfig  # noqa: E402
import max25d  # noqa: E402
from reporting_quality import DataQualityTracker, RxOutcome  # noqa: E402

T0 = 2_000_000.0
WIN = 20


def _close_pass(rt: max25d.DeviceRuntime, index: int, start: float = T0) -> None:
    rt.quality.tick(start + (index + 1) * WIN + 1)


def _fill_good(rt: max25d.DeviceRuntime, count: int = 3, window: int = WIN) -> None:
    for i in range(count):
        rt.quality.record(RxOutcome.GOOD, T0 + i * window + 1)
        rt.quality.tick(T0 + (i + 1) * window + 1)


def _state(
    *,
    error_on: bool = True,
    voice_on: bool = True,
    link: str = "ready",
    passes: int = 3,
    quality_min: int = 50,
    pass_seconds: int = 20,
    backend_type: str = "kiss-serial",
    hardware: str = "tncs",
    prefill_good: bool = True,
) -> max25d.DaemonState:
    cfg = max25d.DaemonConfig(
        report_error_transmissions=error_on,
        report_voice_transmissions=voice_on,
        report_data_passes=passes,
        report_data_quality_min=quality_min,
        report_data_pass_seconds=pass_seconds,
    )
    dev = DeviceBackendConfig(
        device_id="tnc2c",
        enabled=True,
        backend_type=backend_type,
        hardware=hardware,
    )
    rt = max25d.DeviceRuntime(
        cfg=dev,
        link_status=link,
        quality=DataQualityTracker(
            passes_required=passes,
            min_good_percent=quality_min,
            pass_window_sec=pass_seconds,
        ),
    )
    if prefill_good:
        _fill_good(rt, passes, pass_seconds)
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


def test_error_invalid_before_passes_complete() -> None:
    line = max25d.status_line(_state(prefill_good=False))
    assert "error=invalid" in line


def test_error_invalid_on_bad_frame_ratio() -> None:
    state = _state(prefill_good=False)
    rt = state.devices["tnc2c"]
    rt.quality.record(RxOutcome.BAD, T0 + 1)
    _close_pass(rt, 0)
    rt.quality.record(RxOutcome.BAD, T0 + 21)
    _close_pass(rt, 1)
    rt.quality.record(RxOutcome.GOOD, T0 + 41)
    _close_pass(rt, 2)
    line = max25d.status_line(state)
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


def test_on_backend_rx_tracks_callid_in_pass_window() -> None:
    state = _state(prefill_good=False)
    max25d.on_backend_rx(state, "tnc2c", "[AX25 UI DG1ABC>QST] 73")
    max25d.on_backend_rx(state, "tnc2c", "[AX25 UI DG1ABC>CB-0] bad")
    max25d.on_backend_rx(state, "tnc2c", "[CRDOP RX soft-crdop] noise")
    rt = state.devices["tnc2c"]
    start = rt.quality.current.started_at
    assert rt.quality.current.good == 1
    assert rt.quality.current.bad == 1
    rt.quality.tick(start + WIN + 1)
    assert list(rt.quality.passes) == ["bad"]
    max25d.on_backend_rx(state, "tnc2c", "[AX25 UI DG1ABC>QST] ok")
    start = rt.quality.current.started_at
    rt.quality.tick(start + WIN + 1)
    max25d.on_backend_rx(state, "tnc2c", "[AX25 UI DG1ABC>QST] ok2")
    start = rt.quality.current.started_at
    rt.quality.tick(start + WIN + 1)
    line = max25d.status_line(state)
    assert "error=valid" in line


if __name__ == "__main__":
    test_error_valid_when_enabled_and_ready()
    test_error_invalid_when_disabled()
    test_error_invalid_on_link_fault()
    test_error_invalid_before_passes_complete()
    test_error_invalid_on_bad_frame_ratio()
    test_voice_valid_tnc_only()
    test_voice_invalid_when_disabled()
    test_voice_invalid_crdop_not_ready()
    test_device_line_includes_reporting()
    test_on_backend_rx_tracks_callid_in_pass_window()
    print("test_reporting: ok")
