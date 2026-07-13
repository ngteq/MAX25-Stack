#!/usr/bin/env python3
"""Acoustic engine loopback + audio-dummy backend smoke tests."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "stacks" / "daemon"))
sys.path.insert(0, str(ROOT / "stacks" / "crdop" / "lib"))

from acoustic_engine import AcousticEngine  # noqa: E402
from device_backends import AudioDummyBackend, DeviceBackendConfig, registry_tested  # noqa: E402


def test_loopback_decode() -> None:
    eng = AcousticEngine()
    rep = eng.loopback_self_test("TST-0", "QST")
    assert rep.symbols > 0
    assert rep.transitions > 0


def test_audio_dummy_backend_loopback_tx() -> None:
    cfg = DeviceBackendConfig(device_id="audio-dummy", backend_type="audio-dummy", audio_mode="loopback")
    rx: list[str] = []
    backend = AudioDummyBackend(cfg, on_rx=rx.append)
    assert backend.open()
    assert backend.attach_session("TST-0")
    ok, display = backend.transmit("TST-0", "QST", "hi", ax25_ui=True)
    assert ok
    assert "QST" in display
    backend.close()


def test_registry() -> None:
    assert registry_tested("audio-dummy") is True


def main() -> int:
    test_loopback_decode()
    test_audio_dummy_backend_loopback_tx()
    test_registry()
    print("OK: audio-dummy tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
