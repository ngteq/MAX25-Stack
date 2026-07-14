#!/usr/bin/env python3
"""Offline tests for modular_tcp_server."""
from __future__ import annotations

import configparser
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from modular_tcp_server import load_modular_tcp  # noqa: E402


def test_load_main_secondaries() -> None:
    cp = configparser.ConfigParser()
    cp.read_string(
        """
[modular_tcp]
enabled = yes
role = main

[modular_tcp.secondaries]
a = 127.0.0.1:7326
b = 127.0.0.1:7327
"""
    )
    cfg = load_modular_tcp(cp)
    assert cfg.enabled is True
    assert cfg.role == "main"
    assert len(cfg.secondaries) == 2
    assert cfg.secondaries[0].port == 7326


if __name__ == "__main__":
    test_load_main_secondaries()
    print("test_modular_tcp: ok")
