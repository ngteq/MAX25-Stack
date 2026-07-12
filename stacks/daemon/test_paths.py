#!/usr/bin/env python3
"""Offline tests for install/dev path resolution."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import (  # noqa: E402
    ctl_path,
    default_ini_candidates,
    resolve_layout,
    serial_env_candidates,
    share_max25_dir,
    stacks_dir,
)

REPO = Path(__file__).resolve().parents[2]


def test_dev_layout() -> None:
    exe = REPO / "stacks/daemon/max25d"
    tree, prefix = resolve_layout(exe)
    assert prefix is None
    assert tree == REPO
    assert (stacks_dir(tree, prefix) / "tncs").is_dir()
    assert ctl_path(tree, prefix, exe) == REPO / "scripts/max25-ctl"


def test_installed_layout() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "usr/local"
        bindir = prefix / "bin"
        share = prefix / "share/max25"
        bindir.mkdir(parents=True)
        share.mkdir(parents=True)
        (share / "max25d.ini.example").write_text("; test\n", encoding="utf-8")
        (bindir / "max25d").write_text("#!/bin/sh\n", encoding="utf-8")
        (bindir / "max25-ctl").write_text("#!/bin/sh\n", encoding="utf-8")

        tree, detected = resolve_layout(bindir / "max25d")
        assert detected == prefix
        assert tree == prefix

        cands = default_ini_candidates(tree, detected)
        assert share / "max25d.ini.example" in cands
        assert ctl_path(tree, detected, bindir / "max25d") == bindir / "max25-ctl"


def test_max25_root_override() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "opt/max25"
        bindir = prefix / "bin"
        share = prefix / "share/max25"
        bindir.mkdir(parents=True)
        share.mkdir(parents=True)
        (bindir / "max25d").write_text("#!/bin/sh\n", encoding="utf-8")

        checkout = Path(tmp) / "checkout"
        (checkout / "stacks/tncs").mkdir(parents=True)
        (checkout / "plugins").mkdir()
        (checkout / "plugins/manifest.yaml").write_text("plugins: []\n", encoding="utf-8")

        old = os.environ.get("MAX25_ROOT")
        os.environ["MAX25_ROOT"] = str(checkout)
        try:
            tree, detected = resolve_layout(bindir / "max25d")
            assert detected == prefix
            assert tree == checkout
            assert stacks_dir(tree, detected) == checkout / "stacks"
        finally:
            if old is None:
                os.environ.pop("MAX25_ROOT", None)
            else:
                os.environ["MAX25_ROOT"] = old


def test_serial_env_order() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "usr/local"
        etc = Path(tmp) / "etc/max25"
        etc.mkdir(parents=True)
        (etc / "tnc2c-serial.env").write_text("TNC2C_BAUD=38400\n", encoding="utf-8")
        share = prefix / "share/max25/serial"
        share.mkdir(parents=True)
        (share / "tnc2c-serial.env").write_text("TNC2C_BAUD=19200\n", encoding="utf-8")

        # /etc/max25 is checked first when present on disk
        cands = serial_env_candidates("tnc2c", REPO, prefix)
        assert cands[0] == Path("/etc/max25/tnc2c-serial.env")
        assert prefix / "share/max25/serial/tnc2c-serial.env" in cands


def main() -> int:
    tests = [
        test_dev_layout,
        test_installed_layout,
        test_max25_root_override,
        test_serial_env_order,
    ]
    for fn in tests:
        fn()
    print("OK: paths unit tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
