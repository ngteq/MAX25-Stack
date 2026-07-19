#!/usr/bin/env python3
"""Offline unit tests for bcpr device parse + BcprKissBackend (no UART)."""
from __future__ import annotations

import configparser
import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "stacks" / "daemon"))

from device_backends import (  # noqa: E402
    BcprKissBackend,
    DeviceBackendConfig,
    parse_device_spec,
)


def load_max25d():
    from importlib.machinery import SourceFileLoader

    loader = SourceFileLoader("max25d", str(ROOT / "stacks" / "daemon" / "max25d.py"))
    spec = importlib.util.spec_from_loader("max25d", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["max25d"] = mod
    loader.exec_module(mod)
    return mod


def test_bcpr_kiss_default_link() -> None:
    cfg = DeviceBackendConfig(
        device_id="max25e0",
        backend_type="bcpr-kiss",
        bcpr_device="bc0",
    )
    backend = BcprKissBackend(cfg, on_rx=lambda _l: None)
    assert backend._path == "/var/run/bcpr/kiss-bc0"
    assert backend.backend_type == "bcpr-kiss"
    assert backend._is_pty is True


def test_parse_bcpr_spec() -> None:
    cp = configparser.ConfigParser()
    cp.read_string(
        """
[device.max25e0]
kiss_link = /var/run/bcpr/kiss-bc0
bcpr_ini = /etc/max25/bcpr.ini
"""
    )
    dev = parse_device_spec("max25e0", "bcpr:bc0", cp, {"hardware": "tncs"})
    assert dev.backend_type == "bcpr-kiss"
    assert dev.bcpr_device == "bc0"
    assert dev.kiss_link == "/var/run/bcpr/kiss-bc0"
    assert dev.bcpr_ini == "/etc/max25/bcpr.ini"


def test_feature_gate_bcpr() -> None:
    mod = load_max25d()
    cp = configparser.ConfigParser()
    cp.read_string(
        """
[features]
bcpr = no
[devices]
default = max25e0
max25e0 = bcpr:bc0
"""
    )
    cfg = mod.DaemonConfig()
    cfg.feature_bcpr = False
    devices = mod.parse_devices(cp, cfg)
    # parse_devices itself may include; load_config filters by features
    assert any(d.device_id == "max25e0" for d in devices)
    filtered = [d for d in devices if mod._device_allowed_by_features(d, cfg)]
    assert filtered == []

    cfg.feature_bcpr = True
    filtered = [d for d in devices if mod._device_allowed_by_features(d, cfg)]
    assert len(filtered) == 1
    assert filtered[0].backend_type == "bcpr-kiss"


def test_bcpr_kiss_pty_skips_tcdrain() -> None:
    cfg = DeviceBackendConfig(
        device_id="max25e0",
        backend_type="bcpr-kiss",
        kiss_link="/tmp/bcpr/kiss-bc0",
        bcpr_device="bc0",
    )
    backend = BcprKissBackend(cfg, on_rx=lambda _l: None)
    backend._fd = 99
    backend._kiss_active = True
    written: list[bytes] = []
    drained = {"n": 0}

    def fake_drain(_fd: int) -> None:
        drained["n"] += 1

    with patch("os.write", side_effect=lambda _fd, data: written.append(data) or len(data)):
        with patch("termios.tcdrain", side_effect=fake_drain):
            ok, display = backend.transmit("CB-0", "QST", "hello", ax25_ui=True)
    assert ok, display
    assert written and written[0].startswith(b"\xc0")
    assert drained["n"] == 0


def test_bcpr_kiss_stabilize_reopens_on_inode_mismatch() -> None:
    cfg = DeviceBackendConfig(
        device_id="max25e0",
        backend_type="bcpr-kiss",
        kiss_link="/tmp/bcpr/kiss-bc0",
        bcpr_device="bc0",
    )
    backend = BcprKissBackend(cfg, on_rx=lambda _l: None)
    backend._fd = 7
    backend._kiss_active = True
    backend.status = "ready"
    backend._mycall = "CB-0"
    calls: list[str] = []

    class _St:
        def __init__(self, ino: int) -> None:
            self.st_ino = ino
            self.st_dev = 1

    with patch("os.path.exists", return_value=True):
        with patch("os.stat", return_value=_St(200)):
            with patch("os.fstat", return_value=_St(100)):
                with patch.object(backend, "close", side_effect=lambda: calls.append("close")):
                    with patch.object(backend, "open", side_effect=lambda: calls.append("open") or True):
                        with patch.object(
                            backend,
                            "attach_session",
                            side_effect=lambda c: calls.append(f"attach:{c}") or True,
                        ):
                            ok = backend.stabilize_session("CB-0", force=False)
    assert ok
    assert calls == ["close", "open", "attach:CB-0"]


def main() -> int:
    test_bcpr_kiss_default_link()
    test_parse_bcpr_spec()
    test_feature_gate_bcpr()
    test_bcpr_kiss_pty_skips_tcdrain()
    test_bcpr_kiss_stabilize_reopens_on_inode_mismatch()
    print("OK: bcpr backend tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
