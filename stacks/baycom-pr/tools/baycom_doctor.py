#!/usr/bin/env python3
# BayCom PR-Stack — Copyright (C) 2026 BayCom PR-Stack contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Unified health check: config, hardware, stack state, and next-step hints."""

from __future__ import annotations

import argparse
import configparser
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import baycom_validate_config as validator  # noqa: E402


FAIL = 0
WARN = 0
HINTS: list[str] = []


def err(msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"FAIL: {msg}", file=sys.stderr)


def warn(msg: str) -> None:
    global WARN
    WARN += 1
    print(f"WARN: {msg}")


def ok(msg: str) -> None:
    print(f"OK:   {msg}")


def hint(msg: str) -> None:
    HINTS.append(msg)


def lsmod_has(name: str) -> bool:
    try:
        out = subprocess.check_output(["lsmod"], text=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return name in out.split()


def check_tools() -> None:
    for name in ("setserial", "python3", "ip", "modprobe"):
        if Path(f"/sbin/{name}").exists() or shutil_which(name):
            ok(f"{name} available")
        else:
            warn(f"{name} missing")


def shutil_which(name: str) -> bool:
    import shutil

    return shutil.which(name) is not None


def check_modules_for_ini(ini_path: Path) -> None:
    cp = configparser.ConfigParser()
    cp.read(ini_path, encoding="utf-8")
    cat_path = Path(cp["stack"].get("catalog", "/etc/baycom/modems.ini"))
    for alt in (cat_path, ini_path.parent / "modems.ini", ini_path.parent.parent / "modems.ini"):
        if alt.is_file():
            cat_path = alt
            break
    cat = configparser.ConfigParser()
    if cat_path.is_file():
        cat.read(cat_path, encoding="utf-8")

    need_ser = need_par = need_kiss = False
    for mid in cp["profile"].get("modems", "").split(","):
        mid = mid.strip()
        if not mid:
            continue
        sec = f"modem.{mid}"
        if sec not in cp:
            continue
        m = cp[sec]
        cat_id = m.get("catalog", "baycom-ser12").strip()
        driver = m.get("driver", cat.get(f"modem.{cat_id}", "driver", fallback="baycom_ser_fdx"))
        if driver == "baycom_ser_fdx":
            need_ser = True
        elif driver == "baycom_par":
            need_par = True
        elif driver == "kiss_serial":
            need_kiss = True

    for mod in ("ax25",):
        if modprobe_n(mod):
            ok(f"kernel module {mod} available")
        else:
            err(f"kernel module {mod} missing — enable CONFIG_AX25")

    if need_ser:
        if modprobe_n("baycom_ser_fdx"):
            ok("kernel module baycom_ser_fdx available")
        else:
            err("baycom_ser_fdx missing — enable CONFIG_BAYCOM_SER_FDX")
    if need_par:
        if modprobe_n("baycom_par"):
            ok("kernel module baycom_par available")
        else:
            err("baycom_par missing — enable CONFIG_BAYCOM_PAR")
        if modprobe_n("parport_pc") or modprobe_n("parport"):
            ok("parport subsystem available")
        else:
            warn("parport module missing — LPT modems need parport_pc")

    if need_kiss:
        ok("kiss-serial profile — no baycom kernel module required")


def resolve_modprobe() -> str | None:
    for path in ("/sbin/modprobe", "/usr/sbin/modprobe"):
        if Path(path).exists():
            return path
    return shutil_which("modprobe")


def modprobe_n(mod: str) -> bool:
    if lsmod_has(mod):
        return True
    modprobe = resolve_modprobe()
    if not modprobe:
        return False
    try:
        subprocess.run([modprobe, "-n", mod], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_stack_state() -> None:
    ser = lsmod_has("baycom_ser_fdx")
    par = lsmod_has("baycom_par")
    if ser:
        ok("baycom_ser_fdx loaded")
    else:
        warn("baycom_ser_fdx not loaded")
    if par:
        ok("baycom_par loaded")
    elif not ser:
        hint("Start stack: sudo baycom-pr-ctl preflight && sudo baycom-pr-ctl start")


def check_kiss_links(ini_path: Path) -> None:
    loader = Path(__file__).resolve().parent / "baycom_ini_load.py"
    try:
        out = subprocess.check_output([sys.executable, str(loader), str(ini_path)], text=True)
    except subprocess.CalledProcessError:
        warn("could not load INI for kiss link check")
        return
    env: dict[str, str] = {}
    for line in out.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            env[k] = v.strip("'\"")
    count = int(env.get("BP_MODEM_COUNT", "0"))
    for i in range(count):
        kiss = env.get(f"BP_M{i}_KISS", "")
        label = env.get(f"BP_M{i}_LABEL", f"m{i}")
        if not kiss:
            continue
        p = Path(kiss)
        if p.is_symlink():
            target = p.resolve()
            if target.exists():
                ok(f"{label}: KISS {kiss} -> {target}")
            else:
                warn(f"{label}: KISS target missing {target}")
                hint("Run: sudo baycom-pr-ctl start")
        elif p.exists():
            ok(f"{label}: KISS path {kiss}")
        else:
            warn(f"{label}: KISS link missing {kiss}")


def check_axports(ini_path: Path, offline: bool) -> None:
    ax = Path(__file__).resolve().parent / "baycom_axports.py"
    if not ax.is_file():
        warn("baycom_axports.py missing")
        return
    if offline:
        rc = subprocess.call([sys.executable, str(ax), str(ini_path), "show"])
        if rc == 0:
            ok("axports generation from INI OK (--offline)")
        else:
            err("axports generation failed")
            hint("Set ax25_port and callsign per kernel modem in INI")
        return
    rc = subprocess.call([sys.executable, str(ax), str(ini_path), "check"])
    if rc == 0:
        ok("axports matches INI")
    else:
        err("axports check failed")
        hint("Run: sudo baycom-pr-ctl axports apply")


def main() -> int:
    global FAIL, WARN
    parser = argparse.ArgumentParser(description="BayCom stack doctor — config + hardware + runtime")
    parser.add_argument("ini", nargs="?", default="/etc/baycom/baycom-pr.ini")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="skip hardware preflight and runtime checks (repo QA / no UART)",
    )
    args = parser.parse_args()
    ini_path = Path(args.ini)
    if not ini_path.is_file():
        alt = Path(__file__).resolve().parent.parent / "config/baycom-pr.ini"
        if alt.is_file():
            ini_path = alt
            warn(f"using repo template {ini_path}")
        else:
            err(f"INI not found: {args.ini}")
            return 1

    print(f"=== BayCom doctor: {ini_path} ===\n")

    print("-- Dependencies --")
    if args.offline:
        for name in ("python3", "ip"):
            if shutil_which(name):
                ok(f"{name} available")
        ok("dependency check relaxed (--offline)")
    else:
        check_tools()
        check_modules_for_ini(ini_path)

    print("\n-- Configuration --")
    if validator.validate_site(ini_path) == 0:
        ok("INI validation passed")
    else:
        err("INI validation failed")
        hint("Run: baycom-pr-ctl probe --apply " + str(ini_path))

    print("\n-- Preflight (hardware safety) --")
    rc = 0
    if args.offline:
        ok("preflight skipped (--offline)")
    else:
        rc = subprocess.call(
            [sys.executable, str(Path(__file__).parent / "baycom_preflight.py"), str(ini_path)]
        )
        if rc != 0:
            err("preflight failed — do not start until fixed")
            hint("Run: sudo baycom-pr-ctl recover")
            hint("Run: baycom-pr-ctl probe")
            hint("Run: baycom-pr-ctl setup")
        else:
            ok("preflight passed")

    print("\n-- AX.25 ports --")
    check_axports(ini_path, args.offline)

    print("\n-- Runtime --")
    if args.offline:
        ok("runtime checks skipped (--offline)")
    else:
        check_stack_state()
        check_kiss_links(ini_path)

    if FAIL == 0 and WARN == 0 and rc == 0:
        ok("system looks ready")
    elif FAIL == 0 and rc == 0:
        ok("ready with warnings — review above")

    if HINTS:
        print("\n-- Suggested next steps --")
        for h in HINTS:
            print(f"  → {h}")

    print(f"\n== Doctor: {FAIL} error(s), {WARN} warning(s) ==")
    return 1 if FAIL or rc else 0


if __name__ == "__main__":
    sys.exit(main())
