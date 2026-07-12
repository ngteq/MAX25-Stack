#!/usr/bin/env python3
# BayCom PR-Stack — Copyright (C) 2026 BayCom PR-Stack contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Scan host for BayCom-capable serial, USB-KISS, and parallel-port hardware."""

from __future__ import annotations

import argparse
import configparser
import glob
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

COMMON_LPT = (0x378, 0x278, 0x3BC)
SETSERIAL = ("/sbin/setserial", "/usr/sbin/setserial")


@dataclass
class UartPort:
    dev: str
    iobase: int | None = None
    irq: int | None = None
    uart_type: str = ""


@dataclass
class UsbSerial:
    dev: str
    driver: str = ""


@dataclass
class ParPort:
    dev: str
    iobase: int | None = None
    hw: str = ""


@dataclass
class ProbeResult:
    uarts: list[UartPort] = field(default_factory=list)
    usb: list[UsbSerial] = field(default_factory=list)
    parports: list[ParPort] = field(default_factory=list)
    modules: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def find_setserial() -> str | None:
    for p in SETSERIAL:
        if Path(p).exists():
            return p
    return shutil.which("setserial")


def setserial_g(setserial: str, dev: str) -> tuple[int | None, int | None, str]:
    try:
        out = subprocess.check_output([setserial, "-g", dev], text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None, None, ""
    io_m = re.search(r"Port:\s*(0x[0-9a-fA-F]+)", out)
    irq_m = re.search(r"IRQ:\s*(\d+)", out)
    uart_m = re.search(r"UART:\s*(\S+)", out)
    io = int(io_m.group(1), 0) if io_m else None
    irq = int(irq_m.group(1)) if irq_m else None
    uart = uart_m.group(1) if uart_m else ""
    return io, irq, uart


def scan_uarts(setserial: str | None) -> list[UartPort]:
    ports: list[UartPort] = []
    for path in sorted(glob.glob("/dev/ttyS[0-9]*")):
        dev = path
        if not Path(dev).exists():
            continue
        io, irq, uart = (None, None, "")
        if setserial:
            io, irq, uart = setserial_g(setserial, dev)
        if io is None and irq is None:
            continue
        ports.append(UartPort(dev=dev, iobase=io, irq=irq, uart_type=uart))
    return ports


def usb_driver_name(dev: str) -> str:
    base = Path(dev).name
    link = Path(f"/sys/class/tty/{base}/device/driver")
    if link.is_symlink():
        return link.resolve().name
    return ""


def scan_usb() -> list[UsbSerial]:
    found: list[UsbSerial] = []
    for pattern in ("/dev/ttyUSB*", "/dev/ttyACM*"):
        for path in sorted(glob.glob(pattern)):
            if Path(path).exists():
                found.append(UsbSerial(dev=path, driver=usb_driver_name(path)))
    return found


def ioports_list() -> str:
    p = Path("/proc/ioports")
    if p.is_file():
        return p.read_text(encoding="utf-8", errors="replace")
    return ""


def scan_parports() -> list[ParPort]:
    found: list[ParPort] = []
    ioports = ioports_list().lower()
    for dev in sorted(glob.glob("/dev/parport*")):
        if not Path(dev).exists():
            continue
        io: int | None = None
        hw = ""
        sp = Path(f"/sys/class/parport/{Path(dev).name}/device")
        if sp.is_dir():
            for child in sp.iterdir():
                if child.name.startswith("parport"):
                    hw = child.name
        for candidate in COMMON_LPT:
            if f"{candidate:04x}" in ioports:
                if io is None:
                    io = candidate
        found.append(ParPort(dev=dev, iobase=io, hw=hw or Path(dev).name))
    if not found:
        for candidate in COMMON_LPT:
            if f"{candidate:04x}" in ioports:
                found.append(ParPort(dev="(no /dev/parport*)", iobase=candidate))
                break
    return found


def scan_modules() -> list[str]:
    try:
        out = subprocess.check_output(["lsmod"], text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    keys = ("baycom_ser_fdx", "baycom_par", "baycom_ser_hdx", "ax25", "parport", "parport_pc")
    return [k for k in keys if k in out.split()]


def run_probe() -> ProbeResult:
    res = ProbeResult()
    ss = find_setserial()
    if not ss:
        res.warnings.append("setserial not found — UART iobase/irq detection limited")
    res.uarts = scan_uarts(ss)
    res.usb = scan_usb()
    res.parports = scan_parports()
    res.modules = scan_modules()
    return res


def print_report(res: ProbeResult) -> None:
    print("=== BayCom hardware probe ===")
    if res.warnings:
        for w in res.warnings:
            print(f"WARN:  {w}")

    print("\n-- UART (kernel-ser12 / baycom_ser_fdx) --")
    if not res.uarts:
        print("  (no ttyS ports with setserial iobase/irq)")
    for u in res.uarts:
        note = ""
        if u.dev.endswith("S5") or u.dev.endswith("S6"):
            note = "  ← often 2nd PC-COM (check IRQ!)"
        print(f"  {u.dev}  iobase=0x{u.iobase:x} irq={u.irq} uart={u.uart_type}{note}")

    print("\n-- USB / async (kiss-serial) --")
    if not res.usb:
        print("  (no ttyUSB/ttyACM devices)")
    for u in res.usb:
        drv = f" driver={u.driver}" if u.driver else ""
        print(f"  {u.dev}{drv}")

    print("\n-- Parallel (kernel-par96 / baycom_par) --")
    if not res.parports:
        print("  (no parport — enable LPT in BIOS or modprobe parport_pc)")
    for p in res.parports:
        io = f"0x{p.iobase:x}" if p.iobase else "?"
        print(f"  {p.dev}  iobase={io} {p.hw}")

    print("\n-- Kernel modules (loaded) --")
    print("  " + (", ".join(res.modules) if res.modules else "(none of baycom/ax25/parport)"))

    print("\n-- Suggested minimal INI blocks --")
    if res.uarts:
        u = res.uarts[0]
        print(f"""
; ser12 on {u.dev} (auto-detected)
[modem.a]
catalog = albrecht-pc-com
label = Radio
serial = {u.dev}
; iobase/irq optional — auto from setserial if omitted:
; iobase = 0x{u.iobase:x}
; irq = {u.irq}
iface = bcsf0
kiss_link = /var/run/baycom-pr/kiss
callsign = N0CALL-0
txdelay = 35
""".strip())
    if res.usb and not res.uarts:
        u = res.usb[0]
        print(f"""
; USB KISS on {u.dev}
[modem.a]
catalog = kiss-serial-usb
label = USB KISS
serial = {u.dev}
kiss_baud = 9600
kiss_link = /var/run/baycom-pr/kiss
callsign = N0CALL-0
""".strip())
    if res.parports and res.parports[0].iobase:
        p = res.parports[0]
        print(f"""
; par96 on LPT iobase 0x{p.iobase:x}
[modem.a]
catalog = baycom-par96
label = Par96
iobase = 0x{p.iobase:x}
mode = par96
iface = bcp0
options = softdcd
kiss_link = /var/run/baycom-pr/kiss
callsign = N0CALL-0
txdelay = 20
""".strip())


def resolve_catalog(ini_path: Path) -> Path:
    cp = configparser.ConfigParser()
    cp.read(ini_path, encoding="utf-8")
    cat = Path(cp["stack"].get("catalog", "/etc/baycom/modems.ini"))
    for alt in (cat, ini_path.parent / "modems.ini", ini_path.parent.parent / "modems.ini"):
        if alt.is_file():
            return alt
    return cat


def apply_probe(ini_path: Path, dry_run: bool = False) -> int:
    """Fill missing iobase/irq/serial from hardware probe into site INI."""
    if not ini_path.is_file():
        print(f"error: {ini_path} not found", file=sys.stderr)
        return 1

    res = run_probe()
    cp = configparser.ConfigParser()
    cp.read(ini_path, encoding="utf-8")
    if "profile" not in cp:
        print("error: [profile] missing", file=sys.stderr)
        return 1

    uart_by_dev = {u.dev: u for u in res.uarts}
    changed = 0
    ids = [x.strip() for x in cp["profile"].get("modems", "").split(",") if x.strip()]

    for mid in ids:
        sec = f"modem.{mid}"
        if sec not in cp:
            continue
        m = cp[sec]
        cat = resolve_catalog(ini_path)
        cat_cp = configparser.ConfigParser()
        if cat.is_file():
            cat_cp.read(cat, encoding="utf-8")
        cat_id = m.get("catalog", "baycom-ser12").strip()
        driver = m.get("driver", cat_cp.get(f"modem.{cat_id}", "driver", fallback="baycom_ser_fdx"))

        if driver == "kiss_serial":
            if not m.get("serial", "").strip() and len(res.usb) == 1:
                m["serial"] = res.usb[0].dev
                print(f"OK:   [{sec}] serial={res.usb[0].dev} (only USB device found)")
                changed += 1
            continue

        if driver != "baycom_ser_fdx":
            if driver == "baycom_par" and not m.get("iobase", "").strip():
                if res.parports and res.parports[0].iobase:
                    m["iobase"] = hex(res.parports[0].iobase)
                    print(f"OK:   [{sec}] iobase={m['iobase']} (from probe)")
                    changed += 1
            continue

        serial = m.get("serial", "").strip()
        if not serial and res.uarts:
            serial = res.uarts[0].dev
            m["serial"] = serial
            print(f"OK:   [{sec}] serial={serial} (first UART)")
            changed += 1

        u = uart_by_dev.get(serial)
        if not u:
            if serial:
                print(f"WARN: [{sec}] {serial} not in setserial probe — plug in or fix path")
            continue

        if not m.get("iobase", "").strip() and u.iobase is not None:
            m["iobase"] = hex(u.iobase)
            print(f"OK:   [{sec}] iobase={m['iobase']} (from setserial)")
            changed += 1
        if not m.get("irq", "").strip() and u.irq is not None:
            m["irq"] = str(u.irq)
            print(f"OK:   [{sec}] irq={m['irq']} (from setserial)")
            changed += 1

    if changed == 0:
        print("No changes — INI already complete or no matching hardware")
        return 0

    if dry_run:
        print(f"\n(dry-run: would write {changed} field(s) to {ini_path})")
        return 0

    backup = ini_path.with_suffix(ini_path.suffix + ".bak")
    shutil.copy2(ini_path, backup)
    with ini_path.open("w", encoding="utf-8") as fh:
        cp.write(fh)
    print(f"\nWrote {ini_path} ({changed} field(s)); backup: {backup}")
    print("Next: baycom-pr-ctl preflight && baycom-pr-ctl start")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="BayCom hardware probe and auto-config helper")
    parser.add_argument("--apply", metavar="INI", help="fill missing fields in site INI from probe")
    parser.add_argument("--dry-run", action="store_true", help="with --apply, show changes only")
    args = parser.parse_args()

    if args.apply:
        return apply_probe(Path(args.apply), dry_run=args.dry_run)

    print_report(run_probe())
    print("\nTip: baycom-pr-ctl probe --apply /etc/baycom/baycom-pr.ini")
    return 0


if __name__ == "__main__":
    sys.exit(main())
