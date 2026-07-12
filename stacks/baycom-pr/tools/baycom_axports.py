#!/usr/bin/env python3
# BayCom PR-Stack — Copyright (C) 2026 BayCom PR-Stack contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate and verify /etc/baycom/axports/axports from baycom-pr.ini."""

from __future__ import annotations

import argparse
import configparser
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

MARKER_BEGIN = "# --- baycom-pr-stack managed ---"
MARKER_END = "# --- end baycom-pr-stack managed ---"

DEFAULT_AXPORTS_DIR = Path("/etc/baycom/axports")
DEFAULT_AXPORTS_FILE = DEFAULT_AXPORTS_DIR / "axports"
DEFAULT_AX25_LINK = Path("/etc/ax25/axports")

KERNEL_BACKENDS = frozenset({"kernel-ser12", "kernel-par96"})


@dataclass
class AxportRow:
    port: str
    callsign: str
    speed: int
    paclen: int
    window: int
    description: str
    iface: str
    label: str


def resolve_catalog_path(ini_path: Path, stack: configparser.SectionProxy) -> Path:
    catalog_path = Path(stack.get("catalog", "/etc/baycom/modems.ini"))
    if catalog_path.is_file():
        return catalog_path
    for alt in (ini_path.parent / "modems.ini", ini_path.parent.parent / "modems.ini"):
        if alt.is_file():
            return alt
    return catalog_path


def resolve_backend(driver: str, backend: str, cat_backend: str) -> str:
    if backend.strip():
        return backend.strip()
    if cat_backend.strip():
        return cat_backend.strip()
    if driver == "kiss_serial":
        return "kiss-serial"
    if driver == "baycom_par":
        return "kernel-par96"
    return "kernel-ser12"


def default_iface(cat: configparser.SectionProxy, idx: int, backend: str, explicit: str) -> str:
    if explicit.strip():
        return explicit.strip()
    prefix = cat.get("iface_prefix", "").strip()
    if prefix:
        return f"{prefix}{idx}"
    if backend == "kernel-par96":
        return f"bcp{idx}"
    return f"bcsf{idx}"


def load_rows(ini_path: Path) -> tuple[list[AxportRow], list[str]]:
    cp = configparser.ConfigParser()
    cp.read(ini_path, encoding="utf-8")
    if "stack" not in cp or "profile" not in cp:
        raise ValueError("INI missing [stack] or [profile]")

    cat = configparser.ConfigParser()
    cat_path = resolve_catalog_path(ini_path, cp["stack"])
    if cat_path.is_file():
        cat.read(cat_path, encoding="utf-8")

    modem_ids = [x.strip() for x in cp["profile"].get("modems", "").split(",") if x.strip()]
    if not modem_ids:
        raise ValueError("profile.modems is empty")

    rows: list[AxportRow] = []
    warnings: list[str] = []

    for idx, mid in enumerate(modem_ids):
        sec = f"modem.{mid}"
        if sec not in cp:
            raise ValueError(f"[{sec}] missing")
        m = cp[sec]
        cat_id = m.get("catalog", "baycom-ser12").strip()
        cat_sec = f"modem.{cat_id}"
        c = cat[cat_sec] if cat_sec in cat else {}

        driver = m.get("driver", c.get("driver", "baycom_ser_fdx"))
        backend = resolve_backend(driver, m.get("backend", ""), c.get("backend", ""))
        label = m.get("label", mid)
        iface = default_iface(c, idx, backend, m.get("iface", ""))

        if backend not in KERNEL_BACKENDS:
            warnings.append(
                f"{label}: backend {backend} — no kernel axports row (use KISS clients)"
            )
            continue

        port = m.get("ax25_port", "").strip()
        callsign = m.get("callsign", "").strip()
        if not port:
            warnings.append(f"{label}: ax25_port missing — skipped")
            continue
        if not callsign:
            warnings.append(f"{label}: callsign missing — skipped")
            continue

        try:
            speed = int(m.get("baud", c.get("baud", "1200")))
        except ValueError:
            speed = 1200

        rows.append(
            AxportRow(
                port=port,
                callsign=callsign,
                speed=speed,
                paclen=255,
                window=2,
                description=f"{label} / {iface}",
                iface=iface,
                label=label,
            )
        )

    return rows, warnings


def format_row(row: AxportRow) -> str:
    return f"{row.port:<9} {row.callsign:<10} {row.speed:<6} {row.paclen:<6} {row.window:<7} {row.description}"


def format_managed_block(rows: list[AxportRow]) -> list[str]:
    lines = [
        MARKER_BEGIN,
        "#   name    callsign   speed  paclen  window  description",
    ]
    lines.extend(format_row(r) for r in rows)
    lines.append(MARKER_END)
    return lines


def merge_content(existing: str | None, managed_lines: list[str]) -> str:
    header = [
        "# BayCom PR-Stack — AX.25 ports",
        "# Generated from baycom-pr.ini — user lines outside the managed block are kept",
        "",
    ]
    body: list[str] = []
    if existing:
        in_managed = False
        for line in existing.splitlines():
            if line.strip() == MARKER_BEGIN:
                in_managed = True
                continue
            if line.strip() == MARKER_END:
                in_managed = False
                continue
            if not in_managed and not line.startswith("# BayCom PR-Stack — AX.25 ports"):
                body.append(line)
        while body and not body[-1].strip():
            body.pop()

    out = header + body
    if out and out[-1].strip():
        out.append("")
    out.extend(managed_lines)
    out.append("")
    return "\n".join(out)


def ensure_ax25_symlink(axports_file: Path, ax25_link: Path, dry_run: bool) -> None:
    ax25_dir = ax25_link.parent
    if dry_run:
        return
    ax25_dir.mkdir(parents=True, exist_ok=True)
    if ax25_link.is_symlink():
        target = ax25_link.resolve()
        if target == axports_file.resolve():
            return
        ax25_link.unlink()
    elif ax25_link.exists():
        raise FileExistsError(f"{ax25_link} exists and is not a symlink — remove manually")
    axports_file.parent.mkdir(parents=True, exist_ok=True)
    ax25_link.symlink_to(axports_file)


def apply_ini(
    ini_path: Path,
    axports_file: Path = DEFAULT_AXPORTS_FILE,
    ax25_link: Path = DEFAULT_AX25_LINK,
    dry_run: bool = False,
    backup: bool = True,
) -> int:
    rows, warnings = load_rows(ini_path)
    for w in warnings:
        print(f"WARN: {w}")
    if not rows:
        print("WARN: no kernel axports rows — skipped (kiss-only or missing ax25_port/callsign)")
        return 0

    existing = axports_file.read_text(encoding="utf-8") if axports_file.is_file() else None
    content = merge_content(existing, format_managed_block(rows))

    if dry_run:
        print(content, end="")
        return 0

    axports_file.parent.mkdir(parents=True, exist_ok=True)
    if backup and axports_file.is_file():
        shutil.copy2(axports_file, f"{axports_file}.bak")

    axports_file.write_text(content, encoding="utf-8")
    ensure_ax25_symlink(axports_file, ax25_link, dry_run=False)

    for row in rows:
        print(f"OK:   {row.port} {row.callsign} {row.speed} ({row.label})")
    print(f"OK:   wrote {axports_file}")
    if ax25_link.is_symlink():
        print(f"OK:   {ax25_link} -> {axports_file}")
    return 0


def show_ini(ini_path: Path) -> int:
    rows, warnings = load_rows(ini_path)
    for w in warnings:
        print(f"WARN: {w}")
    if not rows:
        print("WARN: no kernel axports rows")
        return 0
    print("\n".join(format_managed_block(rows)))
    return 0


def check_ini(
    ini_path: Path,
    axports_file: Path = DEFAULT_AXPORTS_FILE,
    ax25_link: Path = DEFAULT_AX25_LINK,
) -> int:
    rows, warnings = load_rows(ini_path)
    fail = 0
    for w in warnings:
        print(f"WARN: {w}")
    if not rows:
        print("OK:   no kernel axports rows to check")
        return 0

    if not axports_file.is_file():
        print(f"FAIL: {axports_file} missing — run: baycom-pr-ctl axports apply", file=sys.stderr)
        fail += 1
    else:
        text = axports_file.read_text(encoding="utf-8")
        for row in rows:
            pat = re.compile(
                rf"^[ \t]*{re.escape(row.port)}[ \t]+{re.escape(row.callsign)}[ \t]+{row.speed}\b",
                re.M,
            )
            if pat.search(text):
                print(f"OK:   axports contains {row.port} {row.callsign}")
            else:
                print(
                    f"FAIL: axports missing or mismatch for {row.port} / {row.callsign}",
                    file=sys.stderr,
                )
                fail += 1

    if ax25_link.is_symlink():
        if ax25_link.resolve() == axports_file.resolve():
            print(f"OK:   {ax25_link} symlink")
        else:
            print(f"FAIL: {ax25_link} points elsewhere", file=sys.stderr)
            fail += 1
    elif axports_file.is_file():
        print(f"WARN: {ax25_link} not linked — run: baycom-pr-ctl axports apply")
        fail += 1

    return 1 if fail else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="BayCom PR-Stack axports helper")
    parser.add_argument("ini", type=Path, nargs="?", default=Path("/etc/baycom/baycom-pr.ini"))
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_apply = sub.add_parser("apply", help="write axports from INI")
    p_apply.add_argument("--dry-run", action="store_true")
    p_apply.add_argument("--no-backup", action="store_true")
    p_apply.add_argument("--axports-file", type=Path, default=DEFAULT_AXPORTS_FILE)
    p_apply.add_argument("--ax25-link", type=Path, default=DEFAULT_AX25_LINK)

    sub.add_parser("show", help="print managed block")
    p_check = sub.add_parser("check", help="verify axports vs INI")
    p_check.add_argument("--axports-file", type=Path, default=DEFAULT_AXPORTS_FILE)
    p_check.add_argument("--ax25-link", type=Path, default=DEFAULT_AX25_LINK)

    args = parser.parse_args()
    ini = args.ini
    if not ini.is_file():
        print(f"error: {ini} not found", file=sys.stderr)
        return 1

    try:
        if args.cmd == "apply":
            return apply_ini(
                ini,
                axports_file=args.axports_file,
                ax25_link=args.ax25_link,
                dry_run=args.dry_run,
                backup=not args.no_backup,
            )
        if args.cmd == "show":
            return show_ini(ini)
        if args.cmd == "check":
            return check_ini(ini, axports_file=args.axports_file, ax25_link=args.ax25_link)
    except (ValueError, FileExistsError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 2


if __name__ == "__main__":
    sys.exit(main())
