#!/usr/bin/env python3
# BayCom PR-Stack — Copyright (C) 2026 BayCom PR-Stack contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Load baycom-pr.ini + modems.ini and emit shell variables for baycom-pr-ctl."""

from __future__ import annotations

import configparser
import re
import shlex
import subprocess
import sys
from pathlib import Path

PAR_MODE_RE = re.compile(r"^par96\*?$|^picpar$", re.I)
DEFAULT_PAR_IOBASE = "0x378"


def parse_hex(s: str) -> int:
    return int(s.strip(), 0)


def resolve_backend(driver: str, backend: str) -> str:
    if backend:
        return backend.strip()
    if driver == "kiss_serial":
        return "kiss-serial"
    if driver == "baycom_par":
        return "kernel-par96"
    return "kernel-ser12"


def default_iface(cat: dict, idx: int, backend: str, explicit: str) -> str:
    if explicit:
        return explicit
    prefix = cat.get("iface_prefix", "").strip()
    if prefix:
        return f"{prefix}{idx}"
    if backend == "kernel-par96":
        return f"bcp{idx}"
    return f"bcsf{idx}"


def setserial_query(dev: str) -> tuple[int | None, int | None]:
    for bin_path in ("/sbin/setserial", "/usr/sbin/setserial"):
        p = Path(bin_path)
        if not p.exists():
            continue
        try:
            out = subprocess.check_output([str(p), "-g", dev], text=True, stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        m = re.search(r"Port:\s*(0x[0-9a-fA-F]+)", out)
        n = re.search(r"IRQ:\s*(\d+)", out)
        if m and n:
            return parse_hex(m.group(1)), int(n.group(1))
    return None, None


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: baycom_ini_load.py <baycom-pr.ini>", file=sys.stderr)
        return 2

    ini_path = Path(sys.argv[1])
    if not ini_path.is_file():
        print(f"error: {ini_path} not found", file=sys.stderr)
        return 1

    cp = configparser.ConfigParser()
    cp.read(ini_path, encoding="utf-8")

    if "stack" not in cp:
        print("error: [stack] section missing", file=sys.stderr)
        return 1
    if "profile" not in cp:
        print("error: [profile] section missing", file=sys.stderr)
        return 1

    stack = cp["stack"]
    profile = cp["profile"]
    catalog_path = stack.get("catalog", "/etc/baycom/modems.ini")
    cat = configparser.ConfigParser()
    cat_file = Path(catalog_path)
    if not cat_file.is_file():
        for alt in (
            ini_path.parent / "modems.ini",
            ini_path.parent.parent / "modems.ini",
        ):
            if alt.is_file():
                cat_file = alt
                break
    if cat_file.is_file():
        cat.read(cat_file, encoding="utf-8")

    modem_ids = [x.strip() for x in profile.get("modems", "").split(",") if x.strip()]
    if not modem_ids:
        print("error: profile.modems is empty", file=sys.stderr)
        return 1

    lines: list[str] = []

    def emit(key: str, val: str) -> None:
        lines.append(f"{key}={shlex.quote(str(val))}")

    emit("BP_INI_FILE", str(ini_path))
    emit("BP_PROFILE", profile.get("name", "default"))
    emit("BP_STATE_DIR", stack.get("state_dir", "/var/run/baycom-pr"))
    emit("BP_KISS_BRIDGE", stack.get("kiss_bridge", "yes"))
    emit("BP_BINDIR", stack.get("bindir", "/usr/local/sbin"))
    lines.append(f"BP_MODEM_COUNT={len(modem_ids)}")

    for idx, mid in enumerate(modem_ids):
        sec = f"modem.{mid}"
        if sec not in cp:
            print(f"error: [{sec}] missing", file=sys.stderr)
            return 1
        m = cp[sec]
        cat_id = m.get("catalog", "baycom-ser12").strip()
        cat_sec = f"modem.{cat_id}"
        c = cat[cat_sec] if cat_sec in cat else {}

        driver = m.get("driver", c.get("driver", "baycom_ser_fdx"))
        backend = resolve_backend(driver, m.get("backend", c.get("backend", "")))
        mode = m.get("mode", c.get("mode", "ser12*"))
        baud = m.get("baud", c.get("baud", "1200"))
        kiss_baud = m.get("kiss_baud", c.get("kiss_baud", c.get("serial_baud", "9600")))
        txd = m.get("txdelay", c.get("txdelay", "20"))
        serial = m.get("serial", "").strip()
        parport = m.get("parport", "").strip()
        options = m.get("options", "").strip()
        label = m.get("label", mid)
        kiss = m.get("kiss_link", f"/var/run/baycom-pr/kiss-{mid}")
        iface = default_iface(c, idx, backend, m.get("iface", "").strip())

        iobase_s = m.get("iobase", "").strip()
        irq_s = m.get("irq", "").strip()

        if backend == "kernel-ser12":
            if not iobase_s or not irq_s:
                if serial:
                    auto_io, auto_irq = setserial_query(serial)
                    if not iobase_s and auto_io is not None:
                        iobase_s = hex(auto_io)
                    if not irq_s and auto_irq is not None:
                        irq_s = str(auto_irq)
            if not iobase_s or not irq_s:
                print(
                    f"error: [{sec}] kernel-ser12 needs iobase/irq or setserial for {serial}",
                    file=sys.stderr,
                )
                return 1
        elif backend == "kernel-par96":
            if not iobase_s:
                iobase_s = c.get("iobase", DEFAULT_PAR_IOBASE).strip() or DEFAULT_PAR_IOBASE
            if not PAR_MODE_RE.match(mode.split(",")[0].strip()):
                print(f"error: [{sec}] kernel-par96 mode must be par96 or picpar (got {mode})", file=sys.stderr)
                return 1
            irq_s = ""
            if not options and mode.lower().startswith("par96"):
                options = "softdcd"
        elif not serial:
            print(f"error: [{sec}] kiss-serial needs serial= device path", file=sys.stderr)
            return 1

        prefix = f"BP_M{idx}"
        emit(f"{prefix}_ID", mid)
        emit(f"{prefix}_LABEL", label)
        emit(f"{prefix}_CATALOG", cat_id)
        emit(f"{prefix}_BACKEND", backend)
        emit(f"{prefix}_DRIVER", driver)
        emit(f"{prefix}_SERIAL", serial)
        emit(f"{prefix}_PARPORT", parport)
        emit(f"{prefix}_IOBASE", iobase_s)
        emit(f"{prefix}_IRQ", irq_s)
        emit(f"{prefix}_IFACE", iface)
        emit(f"{prefix}_MODE", mode)
        emit(f"{prefix}_OPTIONS", options)
        emit(f"{prefix}_BAUD", baud)
        emit(f"{prefix}_KISS_BAUD", kiss_baud)
        emit(f"{prefix}_TXD", txd)
        emit(f"{prefix}_KISS", kiss)
        emit(f"{prefix}_PORT", m.get("ax25_port", ""))
        emit(f"{prefix}_CALL", m.get("callsign", ""))

    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
