#!/usr/bin/env python3
"""Offline unit tests for bcpr device parse + BcprKissBackend (no UART)."""
from __future__ import annotations

import configparser
import importlib.util
import sys
from pathlib import Path

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
        device_id="bcpr-bc0",
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
[device.bcpr-bc0]
kiss_link = /var/run/bcpr/kiss-bc0
bcpr_ini = /etc/max25/bcpr.ini
"""
    )
    dev = parse_device_spec("bcpr-bc0", "bcpr:bc0", cp, {"hardware": "tncs"})
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
default = bcpr-bc0
bcpr-bc0 = bcpr:bc0
"""
    )
    cfg = mod.DaemonConfig()
    cfg.feature_bcpr = False
    devices = mod.parse_devices(cp, cfg)
    # parse_devices itself may include; load_config filters by features
    assert any(d.device_id == "bcpr-bc0" for d in devices)
    filtered = [d for d in devices if mod._device_allowed_by_features(d, cfg)]
    assert filtered == []

    cfg.feature_bcpr = True
    filtered = [d for d in devices if mod._device_allowed_by_features(d, cfg)]
    assert len(filtered) == 1
    assert filtered[0].backend_type == "bcpr-kiss"


def main() -> int:
    test_bcpr_kiss_default_link()
    test_parse_bcpr_spec()
    test_feature_gate_bcpr()
    print("OK: bcpr backend tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
