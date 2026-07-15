#!/usr/bin/env python3
"""Offline tests for USB/ttyUSB validation rules."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import baycom_validate_config as v  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "config" / "modems.ini"


def _write_ini(body: str) -> Path:
    fh = tempfile.NamedTemporaryFile("w", suffix=".ini", delete=False, encoding="utf-8")
    fh.write(body)
    fh.close()
    return Path(fh.name)


def test_usb_example_valid() -> None:
    ini = ROOT / "config" / "examples" / "baycom-pr.usb.ini"
    assert v.validate_site(ini) == 0


def test_ser12_on_ttyusb_rejected() -> None:
    ini = _write_ini(
        f"""
[stack]
catalog = {CATALOG}

[profile]
modems = a

[modem.a]
catalog = albrecht-pc-com
serial = /dev/ttyUSB0
iface = bcsf0
kiss_link = /var/run/baycom-pr/kiss
"""
    )
    try:
        assert v.validate_site(ini) != 0
    finally:
        ini.unlink(missing_ok=True)


def test_kiss_usb_catalog_ok() -> None:
    ini = _write_ini(
        f"""
[stack]
catalog = {CATALOG}

[profile]
modems = a

[modem.a]
catalog = kiss-serial-usb
serial = /dev/ttyUSB0
kiss_link = /var/run/baycom-pr/kiss
"""
    )
    try:
        assert v.validate_site(ini) == 0
    finally:
        ini.unlink(missing_ok=True)


def main() -> int:
    test_usb_example_valid()
    test_ser12_on_ttyusb_rejected()
    test_kiss_usb_catalog_ok()
    print("OK: baycom USB validation tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
