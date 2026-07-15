#!/usr/bin/env python3
# BayCom PR-Stack — Copyright (C) 2026 BayCom PR-Stack contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validate baycom-pr.ini + modems.ini before starting the stack."""

from __future__ import annotations

import configparser
import re
import sys
from pathlib import Path

SUPPORTED_DRIVERS = {"baycom_ser_fdx", "kiss_serial", "baycom_par"}
KISS_SERIAL_DRIVERS = {"kiss_serial"}
PAR_DRIVERS = {"baycom_par"}
SER12_MODE_RE = re.compile(r"^ser(12|3)[*+]?$", re.I)
PAR_MODE_RE = re.compile(r"^par96\*?$|^picpar$", re.I)
USB_SERIAL_RE = re.compile(r"^/dev/tty(USB|ACM)", re.I)
SER12_CATALOG_KINDS = frozenset({"ser12"})
KISS_CATALOG_KINDS = frozenset({"kiss"})
FAIL = 0
WARN = 0


def is_usb_serial(path: str) -> bool:
    return bool(USB_SERIAL_RE.match(path.strip()))


def err(msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"ERROR: {msg}", file=sys.stderr)


def warn(msg: str) -> None:
    global WARN
    WARN += 1
    print(f"WARN:  {msg}", file=sys.stderr)


def ok(msg: str) -> None:
    print(f"OK:   {msg}")


def parse_hex(s: str) -> int:
    return int(s.strip(), 0)


def resolve_backend(driver: str, backend: str) -> str:
    if backend:
        return backend.strip()
    if driver in KISS_SERIAL_DRIVERS:
        return "kiss-serial"
    if driver in PAR_DRIVERS:
        return "kernel-par96"
    return "kernel-ser12"


def load_ini(path: Path) -> configparser.ConfigParser:
    cp = configparser.ConfigParser()
    cp.read(path, encoding="utf-8")
    return cp


def validate_catalog(cat: configparser.ConfigParser, cat_id: str, modem_sec: str) -> dict[str, str]:
    cat_sec = f"modem.{cat_id}"
    if cat_sec not in cat:
        err(f"[{modem_sec}] catalog '{cat_id}' missing in modems.ini")
        return {}
    entry = cat[cat_sec]
    stack = entry.get("stack", "").strip().lower()
    driver = entry.get("driver", "baycom_ser_fdx").strip()
    if stack == "unsupported":
        err(f"[{modem_sec}] catalog '{cat_id}' is marked unsupported")
    elif stack == "planned":
        warn(f"[{modem_sec}] catalog '{cat_id}' is planned — may not work in v0.5.0")
    if driver not in SUPPORTED_DRIVERS:
        err(f"[{modem_sec}] driver '{driver}' not supported by this stack yet")
    mode = entry.get("mode", "")
    if driver == "baycom_ser_fdx" and mode and not SER12_MODE_RE.match(mode.split(",")[0].strip()):
        warn(f"[{modem_sec}] mode '{mode}' looks unusual for ser12")
    if driver == "baycom_par" and mode and not PAR_MODE_RE.match(mode.split(",")[0].strip()):
        warn(f"[{modem_sec}] mode '{mode}' looks unusual for baycom_par (expected par96 or picpar)")
    return dict(entry)


def validate_site(ini_path: Path) -> int:
    global FAIL, WARN
    FAIL = WARN = 0

    if not ini_path.is_file():
        err(f"site config not found: {ini_path}")
        return 1

    cp = load_ini(ini_path)
    for sec in ("stack", "profile"):
        if sec not in cp:
            err(f"[{sec}] section missing")
            return 1

    stack = cp["stack"]
    profile = cp["profile"]
    catalog_path = Path(stack.get("catalog", "/etc/baycom/modems.ini"))
    if not catalog_path.is_file():
        for alt in (
            ini_path.parent / "modems.ini",
            ini_path.parent.parent / "modems.ini",
        ):
            if alt.is_file():
                catalog_path = alt
                break
    if not catalog_path.is_file():
        err(f"modem catalog not found: {catalog_path}")
        return 1

    cat = load_ini(catalog_path)
    modem_ids = [x.strip() for x in profile.get("modems", "").split(",") if x.strip()]
    if not modem_ids:
        err("profile.modems is empty")
        return 1

    ok(f"profile '{profile.get('name', '?')}' with {len(modem_ids)} modem(s)")
    ok(f"catalog: {catalog_path}")

    seen_serial: dict[str, str] = {}
    seen_iface: dict[str, str] = {}
    seen_kiss: dict[str, str] = {}
    seen_hw: dict[tuple[int, int], str] = {}
    seen_par_io: dict[int, str] = {}

    for mid in modem_ids:
        sec = f"modem.{mid}"
        if sec not in cp:
            err(f"[{sec}] missing")
            continue
        m = cp[sec]
        serial = m.get("serial", "").strip()
        parport = m.get("parport", "").strip()
        iface = m.get("iface", "").strip()
        kiss = m.get("kiss_link", f"/var/run/baycom-pr/kiss-{mid}").strip()
        cat_id = m.get("catalog", "baycom-ser12").strip()
        cat_sec = f"modem.{cat_id}"
        cat_entry = cat[cat_sec] if cat_sec in cat else {}
        driver = m.get("driver", cat_entry.get("driver", "baycom_ser_fdx")).strip()
        backend = resolve_backend(driver, m.get("backend", cat_entry.get("backend", "")))

        if backend == "kernel-ser12":
            if not serial:
                err(f"[{sec}] serial is required for kernel-ser12")
            elif not Path(serial).exists():
                warn(f"[{sec}] serial device {serial} not found (plug in modem / fix path)")
            elif serial in seen_serial:
                err(f"[{sec}] duplicate serial {serial} (also {seen_serial[serial]})")
            else:
                seen_serial[serial] = sec
        elif backend == "kernel-par96":
            if serial:
                warn(f"[{sec}] serial= ignored for kernel-par96 (parallel port has no tty)")
            if parport and not Path(parport).exists():
                warn(f"[{sec}] parport device {parport} not found")
        elif not serial:
            err(f"[{sec}] serial is required for kiss-serial")
        elif not Path(serial).exists():
            warn(f"[{sec}] serial device {serial} not found (plug in modem / fix path)")
        elif serial in seen_serial:
            err(f"[{sec}] duplicate serial {serial} (also {seen_serial[serial]})")
        else:
            seen_serial[serial] = sec

        if backend == "kernel-ser12":
            if not iface:
                err(f"[{sec}] iface is required for kernel-ser12")
            elif not re.match(r"^bcsf[0-3]$", iface):
                warn(f"[{sec}] iface '{iface}' — expected bcsf0..bcsf3")
            elif iface in seen_iface:
                err(f"[{sec}] duplicate iface {iface} (also {seen_iface[iface]})")
            else:
                seen_iface[iface] = sec
        elif backend == "kernel-par96":
            if not iface:
                err(f"[{sec}] iface is required for kernel-par96")
            elif not re.match(r"^bcp[0-3]$", iface):
                warn(f"[{sec}] iface '{iface}' — expected bcp0..bcp3")
            elif iface in seen_iface:
                err(f"[{sec}] duplicate iface {iface} (also {seen_iface[iface]})")
            else:
                seen_iface[iface] = sec
        elif iface and iface in seen_iface:
            warn(f"[{sec}] iface '{iface}' unused for kiss-serial backend")

        if kiss in seen_kiss:
            err(f"[{sec}] duplicate kiss_link {kiss}")
        else:
            seen_kiss[kiss] = sec

        iobase_s = m.get("iobase", "").strip()
        irq_s = m.get("irq", "").strip()
        mode = m.get("mode", cat_entry.get("mode", "")).strip()

        if backend == "kernel-ser12":
            if iobase_s and irq_s:
                try:
                    hw = (parse_hex(iobase_s), int(irq_s))
                    irq_val = int(irq_s)
                    if irq_val < 2 or irq_val > 31:
                        err(f"[{sec}] irq {irq_val} out of range (2–31)")
                    if hw in seen_hw:
                        err(f"[{sec}] duplicate iobase/irq as {seen_hw[hw]} (causes freeze)")
                    seen_hw[hw] = sec
                except ValueError:
                    err(f"[{sec}] invalid iobase/irq")
            elif not iobase_s or not irq_s:
                warn(f"[{sec}] iobase/irq omitted — needs setserial for {serial}")
        elif backend == "kernel-par96":
            if irq_s:
                warn(f"[{sec}] irq ignored for kernel-par96 (parport assigns IRQ)")
            if not iobase_s:
                warn(f"[{sec}] iobase omitted — default 0x378 (LPT1) assumed")
            else:
                try:
                    io = parse_hex(iobase_s)
                    if io in seen_par_io:
                        err(f"[{sec}] duplicate parport iobase 0x{io:x} (also {seen_par_io[io]})")
                    seen_par_io[io] = sec
                except ValueError:
                    err(f"[{sec}] invalid iobase")
            if mode and not PAR_MODE_RE.match(mode.split(",")[0].strip()):
                err(f"[{sec}] mode '{mode}' invalid for baycom_par (use par96 or picpar)")
        elif iobase_s or irq_s:
            warn(f"[{sec}] iobase/irq ignored for kiss-serial backend")

        entry = validate_catalog(cat, cat_id, sec)
        if entry:
            ok(f"[{sec}] catalog={cat_id} ({entry.get('name', cat_id)})")
            cat_kind = entry.get("kind", "").strip().lower()
            cat_stack = entry.get("stack", "").strip().lower()
            if cat_id == "unsupported-ser12-usb-adapter":
                err(
                    f"[{sec}] catalog '{cat_id}' is unsupported — "
                    f"use kiss-serial-usb on {serial or 'ttyUSB/ttyACM'}"
                )
            if backend == "kernel-ser12" and serial and is_usb_serial(serial):
                err(
                    f"[{sec}] kernel-ser12 cannot use USB serial {serial} — "
                    f"use catalog=kiss-serial-usb and kiss-serial backend"
                )
            if cat_kind in SER12_CATALOG_KINDS and serial and is_usb_serial(serial):
                err(
                    f"[{sec}] ser12 catalog '{cat_id}' on USB {serial} — "
                    f"use kiss-serial-usb (kernel bit-bang needs hardware UART)"
                )
            if backend == "kiss-serial" and cat_kind in SER12_CATALOG_KINDS:
                err(
                    f"[{sec}] kiss-serial backend requires kiss catalog "
                    f"(got '{cat_id}' kind={cat_kind or '?'})"
                )
            if backend == "kiss-serial" and cat_stack == "unsupported":
                err(f"[{sec}] catalog '{cat_id}' is unsupported for kiss-serial")
            if backend == "kiss-serial" and serial and not is_usb_serial(serial):
                if not Path(serial).name.startswith("ttyS"):
                    warn(
                        f"[{sec}] kiss-serial on {serial} — "
                        f"expected /dev/ttyUSB* or /dev/ttyACM* or RS-232 kiss-serial-rs232"
                    )

    print(f"\n== Config validation: {FAIL} error(s), {WARN} warning(s) ==")
    return 1 if FAIL else 0


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: baycom_validate_config.py <baycom-pr.ini>", file=sys.stderr)
        return 2
    return validate_site(Path(sys.argv[1]))


if __name__ == "__main__":
    sys.exit(main())
