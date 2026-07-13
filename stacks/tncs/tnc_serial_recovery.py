"""
TheFirmware / TNC-2 class — terminal recovery without power cycle.

Shared by tnc2c-host-reset, tnc2c-boot-wait, kiss_bridge (max25d).

Recovery ladder (cumulative, stop on first banner):
  1. Passive read
  2. KISS return frame 0xC0 0xFF 0xC0  (gettoweb / TAPR)
  3. JHOST 0 escape — 300× NUL + framed command  (gettoweb / WA8DED)
  4. kiss off + INFO probe
  5. 3× Ctrl-C + RESTART + INFO  (packet-radio.net / TF)
  6. ^Q^X + kiss off + INFO  (buffer flush)

Power-cycle is only needed when DTR was low at cold boot (Landolt TNC2C).
"""

from __future__ import annotations

import time
from typing import Callable

FIRMWARE_MARKERS = (
    b"TheFirmware",
    b"NORD",
    b"Version 2.7",
    b"Checksum",
    b"Copyright",
    b"DAMA",
    b"SMACK",
    b"cmd:",
    b"CMD:",
)

LogFn = Callable[[str], None]


def has_banner(data: bytes) -> bool:
    lower = data.lower()
    return any(m.lower() in lower for m in FIRMWARE_MARKERS)


def is_echo_only(cmd: bytes, reply: bytes) -> bool:
    c = cmd.strip(b"\r\n")
    r = reply.strip()
    return r in (c, c + b"\r", c + b"\n", c + b"\r\n")


def probe_info(
    write_flush: Callable[[bytes], None],
    read_for: Callable[[float], bytes],
    pause: float = 0.4,
) -> tuple[bool, bytes, bool]:
    """kiss off + INFO. Returns (banner_ok, combined, only_echo)."""
    write_flush(b"kiss off\r")
    time.sleep(0.6)
    prelude = read_for(1.0)
    write_flush(b"INFO\r")
    time.sleep(pause)
    info = read_for(5.0)
    combined = prelude + info
    only_echo = is_echo_only(b"kiss off\r", prelude) and is_echo_only(
        b"INFO\r", info
    )
    return has_banner(combined), combined, only_echo


def send_jhost0(write_flush: Callable[[bytes], None]) -> None:
    """Leave WA8DED host mode → terminal (gettoweb.de / WA8DED guide)."""
    write_flush(b"\x00" * 300)
    time.sleep(0.15)
    write_flush(b"\x00\x01\x06JHOST 0\r")
    time.sleep(0.8)


def send_kiss_return(write_flush: Callable[[bytes], None]) -> None:
    write_flush(b"\xc0\xff\xc0")
    time.sleep(1.0)


def send_restart_escape(write_flush: Callable[[bytes], None]) -> None:
    """Exit stuck KISS / sync terminal (packet-radio.net PK-88 pattern)."""
    for _ in range(3):
        write_flush(b"\x03")
        time.sleep(0.08)
    time.sleep(0.3)
    write_flush(b"RESTART\r")
    time.sleep(1.5)


def send_buffer_flush(write_flush: Callable[[bytes], None]) -> None:
    """WA8DED host guide: ^Q^X before commands if junk in buffer."""
    write_flush(b"\x11\x18")  # DC1 + CAN
    time.sleep(0.2)


def recover_terminal(
    write_flush: Callable[[bytes], None],
    read_for: Callable[[float], bytes],
    *,
    skip_kiss_frame: bool = False,
    log: LogFn | None = None,
) -> tuple[bool, bytes]:
    """
    Run full software recovery ladder. Returns (host_ok, all_rx_bytes).
  """
    out = log or (lambda _msg: None)
    received = b""

    received += read_for(1.5)
    out("recovery: passive listen")

    if not skip_kiss_frame:
        send_kiss_return(write_flush)
        received += read_for(1.0)
        out("recovery: KISS return frame")

    send_jhost0(write_flush)
    received += read_for(1.0)
    out("recovery: JHOST 0")

    ok, probe, only_echo = probe_info(write_flush, read_for)
    received += probe
    if ok:
        out("recovery: OK after kiss off + INFO")
        return True, received
    if not only_echo and probe:
        out("recovery: partial reply (no banner yet)")

    if only_echo or not ok:
        send_restart_escape(write_flush)
        received += read_for(2.0)
        out("recovery: 3× Ctrl-C + RESTART")
        ok, probe, only_echo = probe_info(write_flush, read_for)
        received += probe
        if ok:
            out("recovery: OK after RESTART")
            return True, received

    if only_echo:
        send_buffer_flush(write_flush)
        received += read_for(0.5)
        ok, probe, only_echo = probe_info(write_flush, read_for)
        received += probe
        if ok:
            out("recovery: OK after buffer flush")
            return True, received

    out("recovery: FAILED — echo only or silent (power-cycle + DTR at boot may be required)")
    return False, received


def enter_kiss(
    write_flush: Callable[[bytes], None],
    read_for: Callable[[float], bytes],
    entry: str = "kiss_on",
) -> None:
    """Enter KISS after terminal recovery."""
    if entry == "auto":
        write_flush(b"kiss on\r")
        time.sleep(0.5)
        reply = read_for(0.5)
        if reply.strip() in (b"kiss on", b"kiss on\r", b"kiss on\n"):
            write_flush(b"\x1b@K")
            time.sleep(0.5)
            read_for(0.5)
    else:
        write_flush(b"kiss on\r")
        time.sleep(0.5)
        read_for(0.3)


def recover_and_enter_kiss(
    write_flush: Callable[[bytes], None],
    read_for: Callable[[float], bytes],
    *,
    kiss_entry: str = "kiss_on",
    skip_kiss_frame: bool = False,
    log: LogFn | None = None,
) -> bool:
    ok, _ = recover_terminal(
        write_flush, read_for, skip_kiss_frame=skip_kiss_frame, log=log
    )
    if not ok:
        return False
    enter_kiss(write_flush, read_for, kiss_entry)
    return True
