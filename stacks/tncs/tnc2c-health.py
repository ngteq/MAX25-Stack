#!/usr/bin/env python3
"""
tnc2c-health - full Landolt TNC2C health check (serial, host, KISS, optional TX).

Does NOT replace visual LED checks (Power/PTT/CD/Connected/Status).

Usage:
  ./tnc2c-health.sh
  ./tnc2c-health.sh /dev/ttyS4
  ./tnc2c-health.sh --tx          # include KISS TX attempt (keys PTT!)
  ./tnc2c-health.sh --tx --quiet
"""

from __future__ import annotations

import argparse
import fcntl
import os
import struct
import sys
import time
import termios
from dataclasses import dataclass, field
from typing import Optional

BAUD_MAP = {
    300: termios.B300,
    600: termios.B600,
    1200: termios.B1200,
    2400: termios.B2400,
    4800: termios.B4800,
    9600: termios.B9600,
    19200: termios.B19200,
}

PROFILES = [
    ("19200-8N1", 19200, False),
    ("19200-7E1", 19200, True),
    ("9600-7E1", 9600, True),
    ("9600-8N1", 9600, False),
    ("2400-7E1", 2400, True),
    ("4800-7E1", 4800, True),
]

HOST_MARKERS = (
    b"cmd:",
    b"CMD:",
    b"TNC",
    b"***",
    b"help",
    b"HELP",
    b"version",
    b"Version",
    b"MYCALL",
    b"KISS was",
    b"KISS is",
)

ECHO_ONLY_MARKERS = (
    b"kiss off",
    b"kiss on",
    b"INFO",
    b"HELP",
    b"RESTART",
)


@dataclass
class ProfileResult:
    name: str
    rts: bool
    cts: bool
    dsr: bool
    info_reply: bytes = b""
    host_score: int = 0
    echo_only: bool = False
    has_cmd_prompt: bool = False
    kiss_ack: bool = False
    kiss_echo_only: bool = False
    notes: list[str] = field(default_factory=list)


def load_env(path: str) -> dict[str, str]:
    env: dict[str, str] = {}
    if not os.path.isfile(path):
        return env
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def open_serial(dev: str, baud: int, seven_e1: bool) -> int:
    fd = os.open(dev, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    if baud not in BAUD_MAP:
        raise ValueError(f"unsupported baud {baud}")
    t = termios.tcgetattr(fd)
    t[0] = t[1] = 0
    t[2] = termios.CLOCAL | termios.CREAD | (termios.CS7 if seven_e1 else termios.CS8)
    if seven_e1:
        t[2] |= termios.PARENB
    speed = BAUD_MAP[baud]
    t[3] = t[4] = t[5] = speed
    t[6][termios.VMIN] = 0
    t[6][termios.VTIME] = 5
    termios.tcsetattr(fd, termios.TCSANOW, t)
    termios.tcflush(fd, termios.TCIOFLUSH)
    flags = struct.unpack("I", fcntl.ioctl(fd, 0x5415, struct.pack("I", 0)))[0]
    flags |= 0x004 | 0x002  # RTS DTR
    fcntl.ioctl(fd, 0x5416, struct.pack("I", flags))
    return fd


def modem_lines(fd: int) -> tuple[bool, bool, bool]:
    flags = struct.unpack("I", fcntl.ioctl(fd, 0x5415, struct.pack("I", 0)))[0]
    return bool(flags & 0x004), bool(flags & 0x008), bool(flags & 0x100)


def read_for(fd: int, seconds: float) -> bytes:
    end = time.time() + seconds
    chunks: list[bytes] = []
    while time.time() < end:
        try:
            b = os.read(fd, 4096)
            if b:
                chunks.append(b)
        except BlockingIOError:
            time.sleep(0.03)
    return b"".join(chunks)


def write_flush(fd: int, data: bytes) -> None:
    os.write(fd, data)
    termios.tcdrain(fd)


def score_host_reply(cmd: bytes, reply: bytes) -> tuple[int, bool, bool]:
    if not reply:
        return 0, False, False

    stripped_cmd = cmd.strip(b"\r\n")
    echo_only = reply.strip() == stripped_cmd or reply.strip() in (
        stripped_cmd,
        stripped_cmd + b"\r",
        stripped_cmd + b"\n",
        stripped_cmd + b"\r\n",
    )

    score = 0
    if b"cmd:" in reply.lower() or b"cmd>" in reply.lower():
        score += 50
    for m in HOST_MARKERS:
        if m.lower() in reply.lower():
            score += 10
    if len(reply) > len(cmd) + 4 and not echo_only:
        score += 5
    if b"\n" in reply and len(reply) > 20:
        score += 5

    has_cmd = b"cmd:" in reply.lower()
    return score, echo_only, has_cmd


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
    body = ax25_addr(dst, 0, False) + ax25_addr(src, 0, True)
    body += b"\x03\xF0" + info
    crc = ax25_crc(body)
    return body + bytes((crc & 0xFF, crc >> 8))


def kiss_frame(port: int, payload: bytes) -> bytes:
    return b"\xC0" + bytes([port & 0x0F]) + kiss_escape(payload) + b"\xC0"


def test_profile(dev: str, name: str, baud: int, seven_e1: bool) -> ProfileResult:
    res = ProfileResult(name=name, rts=False, cts=False, dsr=False)
    fd = open_serial(dev, baud, seven_e1)
    res.rts, res.cts, res.dsr = modem_lines(fd)

    # break out of possible modes
    write_flush(fd, b"\x03\x1a")  # Ctrl+C, Ctrl+Z
    time.sleep(0.2)
    read_for(fd, 0.3)

    write_flush(fd, b"kiss off\r")
    time.sleep(0.4)
    read_for(fd, 0.4)

    write_flush(fd, b"\r")
    time.sleep(0.2)
    read_for(fd, 0.3)

    cmd = b"INFO\r"
    write_flush(fd, cmd)
    time.sleep(0.6)
    info = read_for(fd, 1.0)
    res.info_reply = info
    score, echo, has_cmd = score_host_reply(cmd, info)
    res.host_score = score
    res.echo_only = echo and score < 15
    res.has_cmd_prompt = has_cmd

    write_flush(fd, b"HELP\r")
    time.sleep(0.5)
    help_r = read_for(fd, 0.8)
    hs, echo2, hc = score_host_reply(b"HELP\r", help_r)
    res.host_score = max(res.host_score, hs)
    if hc:
        res.has_cmd_prompt = True
    if echo2 and hs < 10:
        res.echo_only = res.echo_only or True

    write_flush(fd, b"kiss on\r")
    time.sleep(0.5)
    kiss_r = read_for(fd, 0.6)
    if b"kiss" in kiss_r.lower() and len(kiss_r) < 32:
        res.kiss_echo_only = True
    if b"on" in kiss_r.lower() and len(kiss_r) > 8 and not res.kiss_echo_only:
        res.kiss_ack = True

    passive = read_for(fd, 1.0)
    if passive:
        res.notes.append(f"passive_after_kiss={len(passive)}B")

    write_flush(fd, b"kiss off\r")
    time.sleep(0.2)
    os.close(fd)
    return res


def run_tx_test(dev: str, profile_name: str, baud: int, seven_e1: bool) -> dict:
    fd = open_serial(dev, baud, seven_e1)
    write_flush(fd, b"kiss off\r")
    time.sleep(0.4)
    read_for(fd, 0.3)
    write_flush(fd, b"kiss on\r")
    time.sleep(0.5)
    read_for(fd, 0.3)

    payload = ax25_ui("TEST-0", "CQ", b"HEALTH")
    pkt = kiss_frame(0, payload)
    write_flush(fd, pkt)
    time.sleep(3.0)
    rx = read_for(fd, 1.0)
    write_flush(fd, b"kiss off\r")
    os.close(fd)

    echoed = pkt in rx or payload in rx
    return {
        "sent": len(pkt),
        "rx_len": len(rx),
        "frame_echoed_back": echoed,
        "rx_sample": rx[:96],
    }


def print_header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(title)
    print("=" * 60)


def main() -> int:
    parser = argparse.ArgumentParser(description="TNC2C full health check")
    parser.add_argument("device", nargs="?", default=None)
    parser.add_argument("--tx", action="store_true", help="attempt KISS TX (keys PTT)")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    env = load_env(os.path.join(root, "tnc2c-serial.env"))
    dev = args.device or env.get("TNC2C_DEV", "/dev/ttyS4")

    print_header("TNC2C HEALTH CHECK")
    print(f"Device: {dev}")
    print(f"Time:   {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # --- preflight ---
    print_header("1) Preflight")
    if os.system("pgrep -x hybbx >/dev/null 2>&1") == 0:
        print("FAIL: hybbx is running - stop it first")
        return 2
    print("OK: hybbx not active")

    if not os.access(dev, os.R_OK | os.W_OK):
        print(f"FAIL: no access to {dev} (dialout group?)")
        return 2
    print(f"OK: access to {dev}")

    # --- profile sweep ---
    print_header("2) Serial profiles (host detection)")
    results: list[ProfileResult] = []
    for name, baud, seven in PROFILES:
        try:
            r = test_profile(dev, name, baud, seven)
            results.append(r)
            info_preview = r.info_reply[:40].replace(b"\r", b"\\r").replace(b"\n", b"\\n")
            print(
                f"  {name:12} RTS={int(r.rts)} CTS={int(r.cts)} DSR={int(r.dsr)} "
                f"score={r.host_score:2} cmd={int(r.has_cmd_prompt)} "
                f"echo_only={int(r.echo_only)} INFO={info_preview!r}"
            )
        except OSError as e:
            print(f"  {name:12} ERROR: {e}")

    best = max(results, key=lambda x: x.host_score, default=None)
    if best is None:
        print("FAIL: no profiles tested")
        return 2

    # pick working line: prefer env, else best score, else 19200-8N1 clean echo
    preferred = env.get("TNC2C_LINE", "8n1").lower()
    work_name = best.name
    work_baud = 19200
    work_7e1 = preferred.startswith("7e")
    for name, baud, seven in PROFILES:
        if name == best.name:
            work_baud, work_7e1 = baud, seven
            break
    if best.host_score < 15:
        for r in results:
            if r.name == "19200-8N1" and r.info_reply.strip() in (
                b"INFO\r\n",
                b"INFO\r",
                b"INFO",
            ):
                work_name = r.name
                work_baud, work_7e1 = 19200, False
                break

    print(f"\nBest profile (host score): {best.name} (score={best.host_score})")
    print(f"Working profile for tests: {work_name}")

    # --- diagnosis ---
    print_header("3) Serial / host mode diagnosis")
    any_cmd = any(r.has_cmd_prompt for r in results)
    mostly_echo = all(r.echo_only or r.host_score < 15 for r in results)

    if any_cmd:
        print("OK: real host mode (cmd: prompt) detected")
    elif mostly_echo:
        print("WARN: command echo only - no cmd: prompt, no INFO listing")
        print("      -> TNC probably does NOT process commands")
        print("      -> KISS/PTT via software probably ineffective")
        print("      -> LEDs do not change (matches this picture)")
    else:
        print("PARTIAL: replies present but no clear host dialog")

    if all(not r.cts for r in results):
        print("WARN: CTS=0 on all profiles - handshake problem")
        print("      -> bridge DB25 pins 4 and 5 in cable if needed (manual)")

    # --- RF / LED manual ---
    print_header("4) TNC LEDs (no radio / with radio)")
    print("No radio (audio off): Pin4 open -> LED3 (CD) often ON continuously (normal)")
    print("With radio: LED3 should be ON with noise, OFF with squelch closed")
    print("LED 1 Power | LED 2 PTT | LED 3 CD | LED 4 Connected | LED 5 Status")

    # --- optional TX ---
    print_header("5) KISS send test")
    if not args.tx:
        print("Skipped (without --tx). To test: ./tnc2c-health.sh --tx")
    else:
        print("WARNING: sends KISS frame - PTT may key!")
        tx = run_tx_test(dev, work_name, work_baud, work_7e1)
        print(f"  Profile: {work_name}")
        print(f"  Sent: {tx['sent']} bytes KISS")
        print(f"  RX: {tx['rx_len']} bytes")
        print(f"  Frame echoed back directly: {tx['frame_echoed_back']}")
        if tx["frame_echoed_back"]:
            print("  WARN: frame returns unchanged -> possible serial loopback,")
            print("        not sent over radio")
        print("  -> CHECK NOW: LED2 (PTT) and S-meter on radio")

    # --- hardware checklist ---
    print_header("6) Hardware checklist (if not transmitting)")
    print("  [ ] PTT  radio red      -> TNC DIN Pin 3")
    print("  [ ] GND  radio black    -> TNC DIN Pin 2")
    print("  [ ] TX   radio white    -> TNC DIN Pin 1")
    print("  [ ] RX   3.5mm tip      -> TNC DIN Pin 4 (left center)")
    print("  [ ] VOX  on AE6110      -> OFF")
    print("  [ ] Mike gain on TNC    -> increase slowly (pot on modem)")
    print("  [ ] RADIO bridge TNC    -> 2400 baud (Pos. 2)")
    print("  [ ] TERM bridge TNC     -> 19200")

    # --- software checklist ---
    print_header("7) Software / next steps")
    if mostly_echo and not any_cmd:
        print("  1. TNC may be stuck in KISS/transparent - power-cycle TNC briefly")
        print("  2. minicom -D {} -b {} (test {})".format(
            dev, work_baud, "7E1" if work_7e1 else "8N1"))
        print("  3. After reset: 'kiss off' + Enter, then 'INFO' - expect cmd:")
        print("  4. Only when cmd: appears -> ./tnc2c-health.sh --tx")
        print("  5. Start HyBBX only after that (serial_line from tnc2c-serial.env)")
    else:
        print(f"  Serial OK with {work_name}")
        print("  ./tnc2c-send-test.sh for single send test")
        print("  HyBBX: baud=19200 serial_line=8n1 (this device)")

    print_header("SUMMARY")
    status = "DEGRADED" if mostly_echo and not any_cmd else "OK"
    print(f"Overall: {status}")
    print(f"Device: {dev}")
    print(f"Best host profile: {best.name} (score={best.host_score})")
    print(f"CTS on best: {int(best.cts)}  echo_only: {int(best.echo_only)}  cmd: {int(best.has_cmd_prompt)}")

    return 1 if status == "DEGRADED" else 0


if __name__ == "__main__":
    sys.exit(main())
