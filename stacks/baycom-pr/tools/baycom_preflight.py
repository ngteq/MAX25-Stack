#!/usr/bin/env python3
# BayCom PR-Stack — Copyright (C) 2026 BayCom PR-Stack contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pre-start safety checks — reduce freeze risk from wrong IRQ/UART conflicts."""

from __future__ import annotations

import configparser
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Import validation from sibling module
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baycom_validate_config as validator  # noqa: E402

FAIL = 0
WARN = 0

COMMON_LPT_IOBASES = (0x378, 0x278, 0x3BC)


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


def resolve_backend(driver: str, backend: str) -> str:
    if backend:
        return backend.strip()
    if driver == "kiss_serial":
        return "kiss-serial"
    if driver == "baycom_par":
        return "kernel-par96"
    return "kernel-ser12"


def _setserial_bins() -> list[str]:
    """Debian/Kali: /usr/bin/setserial; older docs assumed /sbin."""
    bins: list[str] = []
    for p in ("/usr/bin/setserial", "/bin/setserial", "/sbin/setserial", "/usr/sbin/setserial"):
        if Path(p).exists():
            bins.append(p)
    which = shutil.which("setserial")
    if which and which not in bins:
        bins.append(which)
    return bins


def setserial_query(dev: str) -> tuple[int | None, int | None]:
    for bin_path in _setserial_bins():
        try:
            out = subprocess.check_output(
                [bin_path, "-g", dev], text=True, stderr=subprocess.DEVNULL
            )
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            continue
        m = re.search(r"Port:\s*(0x[0-9a-fA-F]+)", out)
        n = re.search(r"IRQ:\s*(\d+)", out)
        if m and n:
            return int(m.group(1), 0), int(n.group(1))
    return None, None


def lsof_serial(dev: str) -> list[str]:
    try:
        out = subprocess.check_output(["lsof", dev], text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    lines = out.strip().splitlines()
    return lines[1:4] if len(lines) > 1 else []


def check_serial_idle(dev: str, label: str) -> None:
    if not Path(dev).exists():
        err(f"{label}: serial {dev} not found")
        return
    users = lsof_serial(dev)
    if users:
        err(f"{label}: {dev} open by another process — stop userspace serial owner (fuser {dev})")
        for u in users:
            print(f"       {u}", file=sys.stderr)
        return
    ok(f"{label}: {dev} not held by userspace (lsof)")


def check_setserial_match(dev: str, label: str, expect_io: int, expect_irq: int) -> None:
    io, irq = setserial_query(dev)
    if io is None:
        err(f"{label}: setserial unavailable — install setserial before kernel-ser12 start")
        return
    if io != expect_io:
        err(f"{label}: iobase mismatch INI=0x{expect_io:x} setserial=0x{io:x} on {dev}")
    else:
        ok(f"{label}: iobase 0x{expect_io:x} matches setserial")
    if irq != expect_irq:
        err(
            f"{label}: IRQ mismatch INI={expect_irq} setserial={irq} on {dev} "
            f"(wrong IRQ can freeze the host)"
        )
    else:
        ok(f"{label}: IRQ {expect_irq} matches setserial")


def check_irq_notes(dev: str, label: str, irq: int, *, multi_modem: bool) -> None:
    if irq >= 16:
        warn(
            f"{label}: IRQ {irq} on {dev} uses APIC routing — must match "
            f"'setserial -g' exactly (wrong IRQ freezes the host)"
        )
    if multi_modem and (re.search(r"ttyS[5-9]$", dev) or dev.endswith("ttyS5")):
        warn(
            f"{label}: {dev} is often the second PC-COM port (typ. IRQ 30, not COM2/IRQ3) — "
            f"verify: setserial -g {dev}"
        )
    elif not multi_modem and re.search(r"ttyS[4-5]$", dev):
        warn(
            f"{label}: {dev} is often used for TNC serial on multi-port cards — "
            f"prefer a dedicated PC-COM port (e.g. /dev/ttyS0) in single-modem INI"
        )


def check_duplicate_irqs(modems: list[dict]) -> None:
    seen: dict[int, str] = {}
    for m in modems:
        if m.get("backend") != "kernel-ser12":
            continue
        irq = m.get("irq")
        if irq is None:
            continue
        if irq in seen:
            err(f"duplicate IRQ {irq}: {m['label']} and {seen[irq]} (will freeze or fail)")
        else:
            seen[irq] = m["label"]


def check_duplicate_par_iobase(modems: list[dict]) -> None:
    seen: dict[int, str] = {}
    for m in modems:
        if m.get("backend") != "kernel-par96":
            continue
        io = m.get("iobase")
        if io is None:
            continue
        if io in seen:
            err(f"duplicate parport iobase 0x{io:x}: {m['label']} and {seen[io]}")
        else:
            seen[io] = m["label"]


def ioports_has_iobase(iobase: int) -> bool:
    ioports = Path("/proc/ioports")
    if not ioports.is_file():
        return False
    needle = f"{iobase:04x}"
    try:
        text = ioports.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return needle in text.lower()


def check_parport_stack(label: str, iobase: int | None, mode: str) -> None:
    try:
        lsmod = subprocess.check_output(["lsmod"], text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        lsmod = ""

    if "parport" not in lsmod:
        warn(
            f"{label}: parport module not loaded — "
            f"baycom-pr-ctl start will modprobe parport_pc if needed"
        )
    else:
        ok(f"{label}: parport subsystem available")

    if iobase is not None:
        if ioports_has_iobase(iobase):
            ok(f"{label}: iobase 0x{iobase:x} listed in /proc/ioports")
        else:
            warn(
                f"{label}: iobase 0x{iobase:x} not in /proc/ioports — "
                f"check LPT BIOS/address (common: 0x378, 0x278, 0x3bc)"
            )

    if mode.lower().startswith("par96"):
        ok(f"{label}: par96 uses software DCD (kernel softdcd)")
    elif mode.lower().startswith("picpar"):
        ok(f"{label}: picpar — hardware DCD recommended if wired")


def modprobe_hint_par(modems: list[dict]) -> None:
    par = [m for m in modems if m.get("backend") == "kernel-par96"]
    if not par:
        return
    modes = ",".join(m.get("mode", "par96") for m in par)
    ios = ",".join(f"0x{m['iobase']:x}" if m.get("iobase") is not None else "0x378" for m in par)
    ok(f"par modprobe hint: modprobe baycom_par mode={modes} iobase={ios}")


def load_modems(ini_path: Path) -> list[dict]:
    cp = configparser.ConfigParser()
    cp.read(ini_path, encoding="utf-8")
    catalog_path = Path(cp["stack"].get("catalog", "/etc/baycom/modems.ini"))
    if not catalog_path.is_file():
        catalog_path = ini_path.parent / "modems.ini"
    cat = configparser.ConfigParser()
    if catalog_path.is_file():
        cat.read(catalog_path, encoding="utf-8")

    ids = [x.strip() for x in cp["profile"].get("modems", "").split(",") if x.strip()]
    out: list[dict] = []
    for idx, mid in enumerate(ids):
        sec = f"modem.{mid}"
        m = cp[sec]
        cat_id = m.get("catalog", "baycom-ser12").strip()
        cat_sec = f"modem.{cat_id}"
        c = cat[cat_sec] if cat_sec in cat else {}
        driver = m.get("driver", c.get("driver", "baycom_ser_fdx"))
        backend = resolve_backend(driver, m.get("backend", c.get("backend", "")))
        iobase_s = m.get("iobase", "").strip()
        irq_s = m.get("irq", "").strip()
        mode = m.get("mode", c.get("mode", "par96" if backend == "kernel-par96" else "ser12*"))
        io = int(iobase_s, 0) if iobase_s else None
        irq = int(irq_s) if irq_s else None
        if backend == "kernel-ser12" and (io is None or irq is None):
            auto_io, auto_irq = setserial_query(m.get("serial", ""))
            io = io if io is not None else auto_io
            irq = irq if irq is not None else auto_irq
        if backend == "kernel-par96" and io is None:
            default_io = c.get("iobase", "0x378").strip()
            io = int(default_io, 0) if default_io else 0x378
        out.append(
            {
                "id": mid,
                "label": m.get("label", mid),
                "serial": m.get("serial", ""),
                "parport": m.get("parport", ""),
                "backend": backend,
                "iobase": io,
                "irq": irq,
                "mode": mode,
                "iface": m.get("iface", f"bcp{idx}" if backend == "kernel-par96" else f"bcsf{idx}"),
            }
        )
    return out


def main() -> int:
    global FAIL, WARN
    if len(sys.argv) < 2:
        print("usage: baycom_preflight.py <baycom-pr.ini>", file=sys.stderr)
        return 2

    ini_path = Path(sys.argv[1])
    print(f"=== baycom preflight: {ini_path} ===")

    if validator.validate_site(ini_path) != 0:
        err("INI validation failed — fix config before start")
        return 1

    modems = load_modems(ini_path)
    kernel_ser = [m for m in modems if m["backend"] == "kernel-ser12"]
    kernel_par = [m for m in modems if m["backend"] == "kernel-par96"]
    multi_modem = len(modems) > 1

    if multi_modem and len(kernel_ser) > 1:
        warn(
            f"dual kernel-ser12 profile ({len(kernel_ser)} ports) — "
            f"service mode only; verify IRQ/IO on each UART"
        )
    if multi_modem and len(kernel_par) > 1:
        warn(
            f"dual kernel-par96 profile ({len(kernel_par)} LPT ports) — "
            f"service mode only; verify distinct iobase"
        )
    if kernel_ser and kernel_par:
        ok("mixed ser12 + par96 profile — loads baycom_ser_fdx and baycom_par separately")

    check_duplicate_irqs(modems)
    check_duplicate_par_iobase(modems)

    for m in kernel_ser:
        if m["iobase"] is None or m["irq"] is None:
            err(f"{m['label']}: missing iobase/irq for kernel-ser12")
            continue
        check_serial_idle(m["serial"], m["label"])
        check_setserial_match(m["serial"], m["label"], m["iobase"], m["irq"])
        check_irq_notes(m["serial"], m["label"], m["irq"], multi_modem=multi_modem)

    for m in kernel_par:
        check_parport_stack(m["label"], m["iobase"], m.get("mode", "par96"))

    modprobe_hint_par(modems)

    kiss_serial = [m for m in modems if m["backend"] == "kiss-serial"]
    for m in kiss_serial:
        dev = m["serial"]
        if not dev:
            err(f"{m['label']}: missing serial for kiss-serial")
            continue
        check_serial_idle(dev, m["label"])
        if validator.is_usb_serial(dev):
            ok(f"{m['label']}: USB KISS path — no setserial/iobase required")
        elif dev.startswith("/dev/ttyS"):
            warn(
                f"{m['label']}: kiss-serial on {dev} — "
                f"prefer kiss-serial-rs232 catalog or hardware UART ser12"
            )

    try:
        lsmod = subprocess.check_output(["lsmod"], text=True)
        if "baycom_ser_fdx" in lsmod:
            warn("baycom_ser_fdx already loaded — run 'baycom-pr-ctl stop' or 'recover' before re-start")
        if "baycom_par" in lsmod:
            warn("baycom_par already loaded — run 'baycom-pr-ctl stop' or 'recover' before re-start")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    print(f"\n== Preflight: {FAIL} error(s), {WARN} warning(s) ==")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
