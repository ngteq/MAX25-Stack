#!/usr/bin/env python3
"""Platform helpers for max25d."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from max25_platform import (  # noqa: E402
    crdop_audio_backend,
    default_bans_file,
    default_unix_socket,
    is_freebsd,
    is_linux,
    max25d_supported,
    supported_device_ids,
)


def test_linux_defaults() -> None:
  # Run on Linux CI — skip assertions on other hosts
    if not is_linux():
        return
    assert max25d_supported()
    assert "tnc2c" in supported_device_ids()
    assert "baycom-kiss" in supported_device_ids()
    assert "pccom-kiss" in supported_device_ids()
    assert "max25e0" in supported_device_ids()
    assert "max25e0" in supported_device_ids()
    assert "max25e0:bc1" in supported_device_ids()
    assert "baycom-ser12" not in supported_device_ids()
    assert "baycom-a" not in supported_device_ids()
    assert crdop_audio_backend() == "alsa"
    assert default_unix_socket() == "/run/max25/modem.sock"
    assert default_bans_file() == "/var/lib/max25/bans.txt"


def test_freebsd_profile() -> None:
    if not is_freebsd():
        return
    assert max25d_supported()
    assert "soft-crdop" in supported_device_ids()
    assert "tnc2c" not in supported_device_ids()
    assert "max25e0" not in supported_device_ids()
    assert "max25e0" not in supported_device_ids()
    assert crdop_audio_backend() == "oss"
    assert default_unix_socket() == "/var/run/max25/modem.sock"
    assert default_bans_file() == "/var/db/max25/bans.txt"


if __name__ == "__main__":
    test_linux_defaults()
    test_freebsd_profile()
    print("test_max25_platform: ok")
