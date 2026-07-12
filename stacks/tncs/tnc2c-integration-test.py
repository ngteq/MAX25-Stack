#!/usr/bin/env python3
"""
HyBBX-ready check — must use same open port as boot-wait (DTR must stay high).

After boot-wait closes the port, DTR drops and the TNC often returns to echo mode.
Use:  ./tnc2c-boot-wait.sh   (includes HyBBX verify by default)
Or:   ./tnc2c-integration-test.sh --boot   (boot-wait + verify in one process)
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))


def load_module(name: str, filename: str):
    path = os.path.join(ROOT, filename)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def preflight() -> int | None:
    if os.system("pgrep -x hybbx >/dev/null 2>&1") == 0:
        print("FAIL: hybbx läuft")
        return 2
    if os.system("pgrep minicom >/dev/null 2>&1") == 0:
        print("FAIL: minicom läuft")
        return 2
    return None


def run_quick_check(dev: str) -> int:
    hr = load_module("host_reset", "tnc2c-host-reset.py")

    print(f"TNC2C integration-test @ {dev}")
    print("(Port war geschlossen — DTR war weg; Echo ist wahrscheinlich)\n")

    try:
        fd = hr.open_serial(dev)
    except OSError as e:
        print(f"FAIL: {e}")
        return 2

    received = b""
    received += hr.read_for(fd, 1.0)
    hr.write_flush(fd, b"kiss off\r")
    time.sleep(0.6)
    received += hr.read_for(fd, 1.0)
    hr.write_flush(fd, b"INFO\r")
    time.sleep(0.3)
    received += hr.read_for(fd, 5.0)
    os.close(fd)

    if hr.has_banner(received):
        print("OK: HOST — HyBBX darf starten")
        print(received.decode("ascii", errors="replace")[:500])
        return 0

    print("FAIL: ECHO oder kein Banner")
    print("  → Port-Schließen nach boot-wait lässt DTR fallen.")
    print("  → Nutze EINEN Befehl:")
    print("       ./tnc2c-boot-wait.sh")
    print("     (Strom aus/an während Skript läuft — prüft HyBBX-ready vor Schließen)")
    print("  oder:")
    print("       ./tnc2c-integration-test.sh --boot")
    return 1


def run_with_boot(dev: str) -> int:
    print("Starte boot-wait + HyBBX-verify in einem Prozess …\n")
    script = os.path.join(ROOT, "tnc2c-boot-wait.sh")
    return subprocess.call([script, dev])


def main() -> int:
    parser = argparse.ArgumentParser(description="TNC2C HyBBX-ready check")
    parser.add_argument("device", nargs="?", default=None)
    parser.add_argument(
        "--boot",
        action="store_true",
        help="run boot-wait (power-cycle TNC while script runs)",
    )
    args = parser.parse_args()

    fail = preflight()
    if fail is not None:
        return fail

    hr = load_module("host_reset", "tnc2c-host-reset.py")
    dev = args.device or hr.load_env(os.path.join(ROOT, "tnc2c-serial.env")) or "/dev/ttyS4"

    if args.boot:
        return run_with_boot(dev)
    return run_quick_check(dev)


if __name__ == "__main__":
    sys.exit(main())
