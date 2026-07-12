#!/usr/bin/env python3
"""
tnc2c-autotest - safe, exhaustive Landolt TNC2C serial discovery.

Tests baud/parity combinations, modem lines, host vs echo vs garbage,
firmware banner, and (optionally) KISS without RF frames.

Does NOT send KISS UI frames or key PTT unless --tx is passed.

Usage:
  ./tnc2c-autotest.sh
  ./tnc2c-autotest.sh /dev/ttyS4
  ./tnc2c-autotest.sh --quick          # likely bauds only (~45s)
  ./tnc2c-autotest.sh --write-env      # update tnc2c-serial.env if confident
  ./tnc2c-autotest.sh --json out.json
  ./tnc2c-autotest.sh --host-check    # after power reset: 19200 8N1 only (~6s)
  ./tnc2c-autotest.sh --host-check --write-env
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import subprocess
import sys
import time
import termios
import fcntl
from dataclasses import asdict, dataclass, field
from typing import Optional

BAUD_MAP: dict[int, int] = {
    300: termios.B300,
    600: termios.B600,
    1200: termios.B1200,
    2400: termios.B2400,
    4800: termios.B4800,
    9600: termios.B9600,
    19200: termios.B19200,
}

BAUDS_FULL = (300, 600, 1200, 2400, 4800, 9600, 19200)
BAUDS_QUICK = (19200, 2400, 4800, 9600)
HOST_CHECK_LINES = ("8N1",)

LINE_FORMATS = (
    ("8N1", 8, "none", 1),
    ("7E1", 7, "even", 1),
    ("8E1", 8, "even", 1),
)

LINE_PREFERENCE = {"8N1": 3, "7E1": 2, "8E1": 1}

FIRMWARE_MARKERS = (
    b"TheFirmware",
    b"NORD",
    b"Version 2.7",
    b"Checksum",
    b"Copyright",
    b"DAMA",
    b"SMACK",
)

HOST_MARKERS = (
    b"cmd:",
    b"CMD:",
    b"help",
    b"HELP",
    b"MYCALL",
    b"KISS was",
    b"KISS is",
    b"KISS now",
    b"Invalid",
    b"Unknown",
)


@dataclass
class ProfileResult:
    name: str
    baud: int
    line: str
    rts: bool = False
    cts: bool = False
    dsr: bool = False
    dcd: bool = False
    passive_bytes: int = 0
    boot_bytes: int = 0
    info_reply: bytes = b""
    help_reply: bytes = b""
    kiss_reply: bytes = b""
    combined_reply: bytes = b""
    printable_ratio: float = 0.0
    host_score: int = 0
    echo_only: bool = False
    garbage: bool = False
    has_cmd: bool = False
    has_firmware: bool = False
    notes: list[str] = field(default_factory=list)

    def classify(self) -> str:
        if (
            self.has_firmware
            or self.has_cmd
            or has_firmware_banner(self.info_reply)
        ):
            return "HOST"
        if self.garbage:
            return "GARBAGE"
        if self.echo_only or (
            is_echo(b"INFO\r", self.info_reply) and is_echo(b"HELP\r", self.help_reply)
        ):
            return "ECHO"
        if self.combined_reply:
            return "PARTIAL"
        return "SILENT"


def has_firmware_banner(data: bytes) -> bool:
    if not data:
        return False
    lower = data.lower()
    return any(m.lower() in lower for m in FIRMWARE_MARKERS)


def order_bauds(bauds: tuple[int, ...]) -> tuple[int, ...]:
    """Test 19200 first so wrong bauds don't disturb a working host session."""
    rest = tuple(b for b in bauds if b != 19200)
    return (19200, *rest) if 19200 in bauds else bauds


def line_format(line: str) -> tuple[int, str, int]:
    for name, data_bits, parity, stop_bits in LINE_FORMATS:
        if name == line:
            return data_bits, parity, stop_bits
    raise ValueError(f"unknown line format {line}")


def timings_for(baud: int, gentle: bool) -> tuple[float, float, float]:
    """Returns listen_s, cmd_wait, info_read."""
    if gentle or baud == 19200:
        return (2.0 if gentle else 1.5, 0.9 if gentle else 0.7, 3.0 if gentle else 3.0)
    return (1.2, 0.55, 1.6)


def finalize_profile(
    res: ProfileResult,
    info_cmd: bytes,
    info: bytes,
    help_cmd: bytes,
    help: bytes,
    kiss_on: bytes,
    combined: bytes,
) -> None:
    res.info_reply = info
    res.help_reply = help
    res.kiss_reply = kiss_on
    res.combined_reply = combined
    res.printable_ratio = printable_ratio(combined)

    s1, e1, c1, f1 = score_replies(info_cmd, info)
    s2, e2, c2, f2 = score_replies(help_cmd, help)
    s3, _, c3, f3 = score_replies(b"kiss on\r", kiss_on)
    res.host_score = max(s1, s2, s3)
    res.has_cmd = c1 or c2 or c3
    res.has_firmware = (
        f1 or f2 or f3
        or has_firmware_banner(info)
        or has_firmware_banner(help)
    )
    if res.has_firmware:
        res.host_score = max(res.host_score, 55)
        res.echo_only = False
    elif is_echo(info_cmd, info) and (not help or is_echo(help_cmd, help)):
        res.echo_only = True
    else:
        res.echo_only = (e1 and e2) and res.host_score < 15
    res.garbage = (
        bool(combined)
        and res.printable_ratio < 0.55
        and not res.has_firmware
        and res.host_score < 20
    )
    if res.passive_bytes and res.has_firmware:
        res.notes.append("boot_banner")
    if kiss_on and not is_echo(b"kiss on\r", kiss_on):
        res.notes.append("kiss_ack")


def rank_key(res: ProfileResult) -> tuple:
    """Higher is better. Prefer real host, then 8N1/7E1 over 8E1."""
    return (
        int(res.has_firmware),
        int(res.has_cmd),
        int(not res.echo_only),
        res.host_score,
        res.printable_ratio,
        LINE_PREFERENCE.get(res.line, 0),
        len(res.combined_reply),
    )


def load_env(path: str) -> dict[str, str]:
    env: dict[str, str] = {}
    if not os.path.isfile(path):
        return env
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def printable_ratio(data: bytes) -> float:
    if not data:
        return 0.0
    good = sum(1 for b in data if b in (9, 10, 13) or 32 <= b < 127)
    return good / len(data)


def open_serial(
    dev: str,
    baud: int,
    data_bits: int,
    parity: str,
    stop_bits: int,
    rts: bool = True,
    dtr: bool = True,
) -> int:
    if baud not in BAUD_MAP:
        raise ValueError(f"unsupported baud {baud}")
    fd = os.open(dev, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    t = termios.tcgetattr(fd)
    t[0] = t[1] = 0
    cflag = termios.CLOCAL | termios.CREAD
    if data_bits == 7:
        cflag |= termios.CS7
    else:
        cflag |= termios.CS8
    if parity == "even":
        cflag |= termios.PARENB
    elif parity == "odd":
        cflag |= termios.PARENB | termios.PARODD
    t[2] = cflag
    speed = BAUD_MAP[baud]
    t[3] = t[4] = t[5] = speed
    t[6][termios.VMIN] = 0
    t[6][termios.VTIME] = 5
    termios.tcsetattr(fd, termios.TCSANOW, t)
    termios.tcflush(fd, termios.TCIOFLUSH)
    flags = struct.unpack("I", fcntl.ioctl(fd, 0x5415, struct.pack("I", 0)))[0]
    if rts:
        flags |= 0x004
    else:
        flags &= ~0x004
    if dtr:
        flags |= 0x002
    else:
        flags &= ~0x002
    fcntl.ioctl(fd, 0x5416, struct.pack("I", flags))
    return fd


def modem_lines(fd: int) -> tuple[bool, bool, bool, bool]:
    flags = struct.unpack("I", fcntl.ioctl(fd, 0x5415, struct.pack("I", 0)))[0]
    return (
        bool(flags & 0x004),
        bool(flags & 0x008),
        bool(flags & 0x100),
        bool(flags & 0x080),
    )


def read_for(fd: int, seconds: float) -> bytes:
    end = time.time() + seconds
    chunks: list[bytes] = []
    while time.time() < end:
        try:
            b = os.read(fd, 4096)
            if b:
                chunks.append(b)
        except BlockingIOError:
            time.sleep(0.02)
    return b"".join(chunks)


def write_flush(fd: int, data: bytes) -> None:
    os.write(fd, data)
    termios.tcdrain(fd)


def is_echo(cmd: bytes, reply: bytes) -> bool:
    if not reply:
        return False
    c = cmd.strip(b"\r\n")
    r = reply.strip()
    return r in (c, c + b"\r", c + b"\n", c + b"\r\n")


def score_replies(cmd: bytes, *chunks: bytes) -> tuple[int, bool, bool, bool]:
    reply = b"".join(chunks)
    if not reply:
        return 0, False, False, False

    score = 0
    lower = reply.lower()
    has_cmd = b"cmd:" in lower
    has_fw = any(m.lower() in lower for m in FIRMWARE_MARKERS)

    if has_cmd:
        score += 60
    if has_fw:
        score += 50
    for m in HOST_MARKERS:
        if m.lower() in lower:
            score += 8
    if len(reply) > len(cmd) + 8 and not is_echo(cmd, reply):
        score += 10
    if b"\n" in reply and len(reply) > 30:
        score += 5

    echo = is_echo(cmd, reply) and score < 20
    garbage = printable_ratio(reply) < 0.55 and len(reply) >= 4
    return score, echo, has_cmd, has_fw


def profile_name(baud: int, line: str) -> str:
    return f"{baud}-{line}"


def test_profile(
    dev: str,
    baud: int,
    line: str,
    data_bits: int,
    parity: str,
    stop_bits: int,
    gentle: bool = False,
) -> ProfileResult:
    listen_s, cmd_wait, info_read = timings_for(baud, gentle)
    res = ProfileResult(name=profile_name(baud, line), baud=baud, line=line)
    fd = open_serial(dev, baud, data_bits, parity, stop_bits)
    res.rts, res.cts, res.dsr, res.dcd = modem_lines(fd)

    passive = read_for(fd, listen_s)
    res.passive_bytes = len(passive)

    if not gentle:
        write_flush(fd, b"\x03\x1a")
        time.sleep(0.15)
        read_for(fd, 0.2)

    write_flush(fd, b"\r\r")
    time.sleep(cmd_wait)
    wake = read_for(fd, listen_s)

    write_flush(fd, b"kiss off\r")
    time.sleep(cmd_wait)
    kiss_off = read_for(fd, listen_s)

    info_cmd = b"INFO\r"
    write_flush(fd, info_cmd)
    time.sleep(cmd_wait)
    info = read_for(fd, info_read)

    help_cmd = b"HELP\r"
    write_flush(fd, help_cmd)
    time.sleep(cmd_wait)
    help = read_for(fd, listen_s + 0.3)

    write_flush(fd, b"kiss on\r")
    time.sleep(cmd_wait)
    kiss_on = read_for(fd, listen_s)

    write_flush(fd, b"kiss off\r")
    time.sleep(0.2)
    read_for(fd, 0.2)

    finalize_profile(
        res, info_cmd, info, help_cmd, help, kiss_on,
        passive + wake + kiss_off + info + help + kiss_on,
    )
    os.close(fd)
    return res


def test_host_check(
    dev: str,
    baud: int,
    line: str,
    dtr_cycle: bool = False,
    no_kiss: bool = False,
) -> ProfileResult:
    """Gentle single-profile check - DTR high, optional KISS-reset, kiss off, INFO."""
    data_bits, parity, stop_bits = line_format(line)
    res = ProfileResult(name=profile_name(baud, line), baud=baud, line=line)

    prelude = b""
    if dtr_cycle:
        boot = boot_listen(dev, baud, line, data_bits, parity, stop_bits)
        res.boot_bytes = len(boot)
        prelude = boot
        if has_firmware_banner(boot):
            res.has_firmware = True
            res.notes.append("dtr_boot_banner")

    fd = open_serial(dev, baud, data_bits, parity, stop_bits)
    res.rts, res.cts, res.dsr, res.dcd = modem_lines(fd)

    passive = read_for(fd, 1.0)
    res.passive_bytes = len(passive)
    prelude += passive
    if has_firmware_banner(passive):
        res.has_firmware = True
        res.notes.append("passive_boot_banner")

    if not no_kiss:
        write_flush(fd, b"\xc0\xff\xc0")
        time.sleep(0.8)
        prelude += read_for(fd, 0.8)
        res.notes.append("kiss_reset")

    write_flush(fd, b"kiss off\r")
    time.sleep(0.4)
    kiss_off = read_for(fd, 0.8)

    info_cmd = b"INFO\r"
    write_flush(fd, info_cmd)
    time.sleep(0.3)
    info = read_for(fd, 3.5)

    finalize_profile(res, info_cmd, info, b"HELP\r", b"", b"", prelude + kiss_off + info)
    os.close(fd)
    return res


def boot_listen(dev: str, baud: int, line: str, data_bits: int, parity: str, stop_bits: int) -> bytes:
    fd = open_serial(dev, baud, data_bits, parity, stop_bits)
    flags = struct.unpack("I", fcntl.ioctl(fd, 0x5415, struct.pack("I", 0)))[0]
    flags &= ~0x002
    fcntl.ioctl(fd, 0x5416, struct.pack("I", flags))
    time.sleep(0.8)
    flags |= 0x002 | 0x004
    fcntl.ioctl(fd, 0x5416, struct.pack("I", flags))
    data = read_for(fd, 4.0)
    os.close(fd)
    return data


def deep_test(dev: str, res: ProfileResult) -> ProfileResult:
    line = res.line
    data_bits, parity, stop_bits = line_format(line)
    gentle = res.baud == 19200

    fd = open_serial(dev, res.baud, data_bits, parity, stop_bits)
    res.rts, res.cts, res.dsr, res.dcd = modem_lines(fd)

    write_flush(fd, b"kiss off\r")
    time.sleep(0.6 if gentle else 0.4)
    read_for(fd, 0.3)

    for _ in range(4):
        write_flush(fd, b"\r")
        time.sleep(0.35)
    enters = read_for(fd, 1.5)
    if b"cmd:" in enters.lower():
        res.has_cmd = True
        res.host_score += 20
        res.notes.append("cmd_after_enter")

    write_flush(fd, b"MYCALL TEST-0\r")
    time.sleep(0.6)
    mycall = read_for(fd, 1.0)
    if mycall and not is_echo(b"MYCALL TEST-0\r", mycall):
        lower = mycall.lower()
        if b"cmd:" in lower or has_firmware_banner(mycall):
            res.host_score += 15
            res.notes.append("mycall_ack")

    if not res.has_firmware:
        boot = boot_listen(dev, res.baud, line, data_bits, parity, stop_bits)
        res.boot_bytes = len(boot)
        if has_firmware_banner(boot):
            res.has_firmware = True
            res.host_score = max(res.host_score, 55)
            res.echo_only = False
            res.notes.append("dtr_boot_banner")

    os.close(fd)
    return res


def port_holders(dev: str) -> list[str]:
    holders: list[str] = []
    try:
        out = subprocess.run(
            ["fuser", "-v", dev],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if out.returncode == 0 and out.stderr:
            for line in out.stderr.splitlines():
                line = line.strip()
                if line and not line.startswith("USER"):
                    holders.append(line)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return holders


def preflight(dev: str) -> list[str]:
    issues: list[str] = []
    if os.system("pgrep -x hybbx >/dev/null 2>&1") == 0:
        issues.append("hybbx is running - stop it first")
    if os.system("pgrep minicom >/dev/null 2>&1") == 0:
        issues.append("minicom is running - exit it first (pkill minicom)")
    if not os.path.exists(dev):
        issues.append(f"{dev} does not exist")
    elif not os.access(dev, os.R_OK | os.W_OK):
        issues.append(f"no access to {dev} (dialout group?)")
    holders = port_holders(dev)
    if holders:
        issues.append(f"port in use: {', '.join(holders[:3])}")
    return issues


def quartz_hint(baud: int) -> str:
    hints = []
    term_98304 = {9600: "TERM Pos.1", 4800: "TERM Pos.2", 2400: "TERM Pos.3", 1200: "TERM Pos.4"}
    term_49152 = {4800: "TERM Pos.1", 2400: "TERM Pos.2", 1200: "TERM Pos.3", 600: "TERM Pos.4"}
    if baud in term_98304:
        hints.append(f"with 9.8304 MHz crystal: {term_98304[baud]}")
    if baud in term_49152:
        hints.append(f"with 4.9152 MHz crystal: {term_49152[baud]}")
    if baud == 19200:
        hints.append("19200 is in the manual only with RADIO bridge (2.4576 MHz Pos.5), not TERM")
        hints.append("-> possible mod, extended firmware, or different crystal")
    return "; ".join(hints) if hints else "-"


def suggest_env(best: ProfileResult) -> dict[str, str]:
    line = best.line.lower()
    return {
        "TNC2C_DEV": "",  # filled by caller
        "TNC2C_BAUD": str(best.baud),
        "TNC2C_LINE": line,
        "TNC2C_RADIO_BAUD": "2400",
        "TNC2C_MODEM": "tcm3105",
        "HYBBX_SERIAL_LINE": line,
    }


def write_env_file(path: str, dev: str, best: ProfileResult) -> None:
    vals = suggest_env(best)
    vals["TNC2C_DEV"] = dev
    lines = [
        f"# Auto-generated by tnc2c-autotest {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"# Best profile: {best.name} ({best.classify()}, score={best.host_score})",
    ]
    for k, v in vals.items():
        lines.append(f"{k}={v}")
    lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# --- optional TX (from health check) ---

def kiss_escape(data: bytes) -> bytes:
    out = bytearray()
    for b in data:
        if b == 0xC0:
            out.extend((0xDB, 0xDC))
        elif b == 0xDB:
            out.extend((0xDB, 0xDD))
        else:
            out.append(b)
    return bytes(out)


def ax25_addr(call: str, ssid: int, last: bool) -> bytes:
    call = call.upper().ljust(6)[:6]
    raw = bytes((ord(c) << 1) for c in call)
    ssid_b = ((ssid & 0x0F) << 1) | (0x01 if last else 0x00)
    return raw + bytes([ssid_b])


def ax25_crc(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
    return crc ^ 0xFFFF


def ax25_ui(src: str, dst: str, info: bytes) -> bytes:
    body = ax25_addr(dst, 0, False) + ax25_addr(src, 0, True) + b"\x03\xF0" + info
    crc = ax25_crc(body)
    return body + bytes((crc & 0xFF, crc >> 8))


def run_tx_test(dev: str, best: ProfileResult) -> dict:
    fmt = next(f for f in LINE_FORMATS if f[0] == best.line)
    _, data_bits, parity, stop_bits = fmt
    fd = open_serial(dev, best.baud, data_bits, parity, stop_bits)
    write_flush(fd, b"kiss off\r")
    time.sleep(0.4)
    read_for(fd, 0.3)
    write_flush(fd, b"kiss on\r")
    time.sleep(0.5)
    read_for(fd, 0.3)
    payload = ax25_ui("TEST-0", "CQ", b"AUTOTEST")
    pkt = b"\xC0" + bytes([0]) + kiss_escape(payload) + b"\xC0"
    write_flush(fd, pkt)
    time.sleep(3.0)
    rx = read_for(fd, 1.0)
    write_flush(fd, b"kiss off\r")
    os.close(fd)
    return {
        "sent": len(pkt),
        "rx_len": len(rx),
        "echoed": pkt in rx or payload in rx,
    }


def preview(data: bytes, limit: int = 72) -> str:
    if not data:
        return "(empty)"
    s = data[:limit].decode("ascii", errors="replace")
    s = s.replace("\r", "\\r").replace("\n", "\\n")
    if len(data) > limit:
        s += "..."
    return s


def print_header(title: str) -> None:
    print(f"\n{'=' * 64}")
    print(title)
    print("=" * 64)


def print_result_summary(
    best: ProfileResult,
    dev: str,
    ranked: list[ProfileResult],
    root: str,
    args: argparse.Namespace,
    suggested: dict[str, str],
    tx_result: Optional[dict],
    t0: float,
) -> int:
    host_profiles = [r for r in ranked if r.classify() == "HOST"]
    echo_profiles = [r for r in ranked if r.classify() == "ECHO"]
    garbage_profiles = [r for r in ranked if r.classify() == "GARBAGE"]

    print_header("Result")
    print(f"  Best profile:   {best.name}")
    print(f"  Class:          {best.classify()}")
    print(f"  Host score:     {best.host_score}")
    print(f"  Modem:          RTS={int(best.rts)} CTS={int(best.cts)} DSR={int(best.dsr)}")
    print(f"  INFO:           {preview(best.info_reply, 120)}")
    if best.has_firmware or has_firmware_banner(best.info_reply):
        print("  Firmware banner: YES")
    if best.has_cmd:
        print("  cmd: prompt:     YES")
    print(f"  Crystal/bridge: {quartz_hint(best.baud)}")

    if host_profiles:
        print(f"\n  HOST profiles ({len(host_profiles)}): {', '.join(r.name for r in host_profiles[:5])}")
    if echo_profiles and not host_profiles:
        print(f"\n  ECHO only ({len(echo_profiles)}) - TNC mirrors commands, does not process them.")
        print("  -> Power-reset the TNC, then: ./tnc2c-autotest.sh --host-check --write-env")
    if garbage_profiles:
        top_g = sorted(garbage_profiles, key=lambda r: r.printable_ratio, reverse=True)[:3]
        print(f"  GARBAGE profiles: {', '.join(r.name for r in top_g)} (wrong baud/parity)")

    print("\n  Recommended settings:")
    print(f"    minicom -D {dev} -b {best.baud}   (# {best.line})")
    for k in ("TNC2C_BAUD", "TNC2C_LINE", "HYBBX_SERIAL_LINE"):
        print(f"    {k}={suggested[k]}")

    if args.write_env and best.classify() == "HOST":
        env_path = os.path.join(root, "tnc2c-serial.env")
        write_env_file(env_path, dev, best)
        print(f"\n  Written: {env_path}")
    elif args.write_env:
        print("\n  --write-env skipped (no reliable HOST profile)")

    print_header("KISS-TX")
    if not args.tx:
        print("  Skipped (safe). Optional: --tx (PTT may key!)")
    else:
        print("  WARNING: sends AX.25 UI frame - check PTT LED!")
        tx_result = run_tx_test(dev, best)
        print(f"  Sent {tx_result['sent']} B, RX {tx_result['rx_len']} B, Echo={tx_result['echoed']}")

    elapsed = time.time() - t0
    status = "OK" if best.classify() == "HOST" else (
        "DEGRADED" if best.classify() in ("ECHO", "PARTIAL") else "FAIL"
    )

    print_header("SUMMARY")
    print(f"  Status:   {status}")
    print(f"  Device:   {dev}")
    print(f"  Profile:  {best.name} ({best.classify()})")
    print(f"  Duration: {elapsed:.0f}s")

    if args.json:
        report = {
            "device": dev,
            "status": status,
            "elapsed_s": round(elapsed, 1),
            "best": asdict(best),
            "ranking": [asdict(r) for r in ranked[:12]],
            "suggested_env": suggested,
            "tx": tx_result,
        }

        def fix(obj):
            if isinstance(obj, dict):
                return {k: fix(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [fix(v) for v in obj]
            if isinstance(obj, bytes):
                return obj.decode("ascii", errors="replace")
            return obj

        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(fix(report), f, indent=2, ensure_ascii=False)
        print(f"  JSON:     {args.json}")

    return 0 if status == "OK" else (1 if status == "DEGRADED" else 2)


def run_host_check(
    dev: str,
    root: str,
    env: dict[str, str],
    args: argparse.Namespace,
) -> int:
    t0 = time.time()
    print_header("TNC2C HOST-CHECK (DTR high - no DTR drop, no baud sweep)")
    print(f"Device:  {dev}")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    if args.dtr_cycle:
        print("Note: --dtr-cycle active (DTR drop - may trigger echo mode)")

    print_header("1) Preflight")
    issues = preflight(dev)
    if issues:
        for i in issues:
            print(f"  FAIL: {i}")
        print("\nAbort - clear port/background services and retry.")
        return 2
    print("  OK: port free, hybbx/minicom inactive, access OK")

    kiss_step = "kiss off -> INFO" if args.no_kiss else "KISS-reset -> kiss off -> INFO"
    print_header(f"2) Host-Check 19200-8N1 (passive -> {kiss_step})")
    results: list[ProfileResult] = []
    for line in HOST_CHECK_LINES:
        name = profile_name(19200, line)
        if not args.quiet:
            print(f"  {name:12} ...", end="", flush=True)
        try:
            r = test_host_check(
                dev, 19200, line, dtr_cycle=args.dtr_cycle, no_kiss=args.no_kiss
            )
            results.append(r)
            if not args.quiet:
                print(
                    f" {r.classify():7} score={r.host_score:3} fw={int(r.has_firmware)} "
                    f"INFO={preview(r.info_reply, 50)!r}"
                )
        except OSError as e:
            if not args.quiet:
                print(f" ERROR: {e}")

    if not results:
        print("  No profiles tested.")
        return 2

    ranked = sorted(results, key=rank_key, reverse=True)
    best = ranked[0]
    suggested = suggest_env(best)
    suggested["TNC2C_DEV"] = dev
    return print_result_summary(best, dev, ranked, root, args, suggested, None, t0)


def main() -> int:
    parser = argparse.ArgumentParser(description="TNC2C safe exhaustive autotest")
    parser.add_argument("device", nargs="?", default=None)
    parser.add_argument(
        "--host-check",
        action="store_true",
        help="gentle 19200-8N1 only - after power reset (~10s)",
    )
    parser.add_argument(
        "--dtr-cycle",
        action="store_true",
        help="brief DTR drop (legacy; may trigger echo mode - not for host-check)",
    )
    parser.add_argument(
        "--no-kiss",
        action="store_true",
        help="host-check: skip KISS-reset frame",
    )
    parser.add_argument("--quick", action="store_true", help="19200 first, then 2400/4800/9600")
    parser.add_argument("--write-env", action="store_true", help="write tnc2c-serial.env if HOST found")
    parser.add_argument("--json", metavar="FILE", help="write JSON report")
    parser.add_argument("--tx", action="store_true", help="KISS TX test - keys PTT!")
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    env = load_env(os.path.join(root, "tnc2c-serial.env"))
    dev = args.device or env.get("TNC2C_DEV", "/dev/ttyS4")

    if args.host_check:
        return run_host_check(dev, root, env, args)

    bauds = order_bauds(BAUDS_QUICK if args.quick else BAUDS_FULL)
    total = len(bauds) * len(LINE_FORMATS)

    t0 = time.time()
    print_header("TNC2C AUTOTEST (safe - no PTT unless --tx)")
    print(f"Device:  {dev}")
    print(f"Mode:    {'quick' if args.quick else 'full'} ({total} profiles, 19200 first)")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    print_header("1) Preflight")
    issues = preflight(dev)
    if issues:
        for i in issues:
            print(f"  FAIL: {i}")
        print("\nAbort - clear port/background services and retry.")
        return 2
    print("  OK: port free, hybbx/minicom inactive, access OK")

    print_header("2) Host precheck 19200-8N1")
    precheck = test_host_check(dev, 19200, "8N1", dtr_cycle=args.dtr_cycle)
    print(
        f"  {precheck.name:12} {precheck.classify():7} fw={int(precheck.has_firmware)} "
        f"INFO={preview(precheck.info_reply, 60)!r}"
    )

    print_header("3) Profile sweep (19200 first, no Ctrl+C at 19200)")
    results: list[ProfileResult] = [precheck]
    seen = {precheck.name}
    n = 0
    for baud in bauds:
        for line, data_bits, parity, stop_bits in LINE_FORMATS:
            name = profile_name(baud, line)
            if name in seen:
                continue
            n += 1
            if not args.quiet:
                print(f"  [{n:2}/{total - 1}] {name:12} ...", end="", flush=True)
            try:
                gentle = baud == 19200
                r = test_profile(dev, baud, line, data_bits, parity, stop_bits, gentle=gentle)
                results.append(r)
                seen.add(name)
                if not args.quiet:
                    print(
                        f" {r.classify():7} score={r.host_score:3} "
                        f"CTS={int(r.cts)} pr={r.printable_ratio:.0%} "
                        f"INFO={preview(r.info_reply, 40)!r}"
                    )
            except OSError as e:
                if not args.quiet:
                    print(f" ERROR: {e}")

    ranked = sorted(results, key=rank_key, reverse=True)
    best = ranked[0] if ranked else None

    print_header("4) Ranking (Top 8)")
    for r in ranked[:8]:
        print(
            f"  {r.name:12} {r.classify():7} score={r.host_score:3} "
            f"cmd={int(r.has_cmd)} fw={int(r.has_firmware)} echo={int(r.echo_only)} "
            f"CTS={int(r.cts)}"
        )

    print_header("5) Deep test (Top 3)")
    deep_targets = [r for r in ranked[:3] if r.host_score > 0 or r.combined_reply]
    if not deep_targets and ranked:
        deep_targets = ranked[:1]
    for r in deep_targets:
        if r.name == precheck.name and precheck.classify() == "HOST":
            continue
        print(f"  -> {r.name} ...", flush=True)
        deep_test(dev, r)

    ranked = sorted(results, key=rank_key, reverse=True)
    best = ranked[0]

    if best and best.classify() in ("ECHO", "PARTIAL") and env.get("TNC2C_BAUD"):
        saved_line = env.get("TNC2C_LINE", "8n1").upper()
        if "7" in saved_line and "E" in saved_line:
            saved_line = "7E1"
        elif saved_line.startswith("8") and "E" in saved_line:
            saved_line = "8E1"
        else:
            saved_line = "8N1"
        saved_name = profile_name(int(env["TNC2C_BAUD"]), saved_line)
        saved = next((r for r in results if r.name == saved_name), None)
        if saved and saved.classify() != "HOST":
            print(f"  (Note: saved profile {saved_name} - use --host-check after power reset)")

    if best is None:
        print("  No response on any profile.")
        return 2

    suggested = suggest_env(best)
    suggested["TNC2C_DEV"] = dev
    return print_result_summary(best, dev, ranked, root, args, suggested, None, t0)


if __name__ == "__main__":
    sys.exit(main())
