"""
TheFirmware / TNC-2 class — terminal recovery without power cycle.

Shared by tnc2c-host-reset, tnc2c-boot-wait, kiss_bridge (max25d).

Recovery ladder (cumulative, stop on first banner):
  0. DTR+RTS high + settle (caller / max25d open)
  1. Passive listen
  2. KISS return 0xC0 0xFF 0xC0  +  ESC+@K
  3. JHOST 0 (300× NUL + framed command)
  4. Buffer flush ^Q^X
  5. kiss off + INFO (+ combined kiss off\\rINFO\\r)
  6. 3× Ctrl-C + RESTART (+ @RESTART) + INFO
  7. Repeat RESTART round with longer wait
  8. ESC E 0 (echo off) + INFO

Power-cycle only when cold-boot happened without DTR (Landolt TNC2C).
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


def matched_markers(data: bytes) -> list[str]:
    return [m.decode("ascii", errors="replace") for m in FIRMWARE_MARKERS if m.lower() in data.lower()]


def escape_bytes(data: bytes, max_len: int = 96) -> str:
    out: list[str] = []
    for byte in data[:max_len]:
        if 32 <= byte < 127:
            out.append(chr(byte))
        elif byte == 0x0D:
            out.append("\\r")
        elif byte == 0x0A:
            out.append("\\n")
        else:
            out.append(f"\\x{byte:02x}")
    if len(data) > max_len:
        out.append("…")
    return "".join(out)


def format_rx_brief(data: bytes) -> str:
    if not data:
        return "0 B silent"
    markers = matched_markers(data)
    marker_txt = ",".join(markers) if markers else "none"
    return f"{len(data)} B, markers={marker_txt}, text={escape_bytes(data)!r}"


def format_rx_diag(data: bytes) -> str:
    """One-line firmware/RX summary for operator logs."""
    if not data:
        return "silent (0 bytes) — check power, baud, CTS/DTR wiring"
    markers = matched_markers(data)
    hex_snip = data[:48].hex(" ")
    if len(data) > 48:
        hex_snip += " …"
    parts = [
        f"{len(data)} bytes",
        f"markers={markers or 'none'}",
        f"text={escape_bytes(data, 120)!r}",
        f"hex={hex_snip}",
    ]
    return "; ".join(parts)


def classify_recovery_failure(received: bytes) -> str:
    if not received:
        return (
            "silent — TNC sent nothing (power, baud/line, DE-9 wiring, or boot without DTR)"
        )
    if has_banner(received):
        return "banner seen in RX but INFO probe failed — check double-echo or host mode"
    lower = received.lower()
    echo_hits = sum(
        1
        for token in (
            b"kiss off",
            b"info\r",
            b"info\n",
            b"restart\r",
            b"@restart\r",
            b"jhost 0",
        )
        if token in lower
    )
    if echo_hits >= 2 or (
        b"kiss off" in lower and (b"info" in lower or b"info\r" in lower)
    ):
        return (
            "echo-only — terminal echoes commands, no TheFirmware/cmd: banner "
            "(Landolt: DTR must be high at power-on; try boot-wait + power cycle)"
        )
    if any(b < 0x20 and b not in (0x0D, 0x0A, 0x09) for b in received[:64]):
        return (
            f"binary/non-text ({len(received)} B) — likely KISS/stream mode, not host cmd:"
        )
    return f"non-banner text ({len(received)} B) — firmware state unclear, capture full RX"


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


def probe_combined(
    write_flush: Callable[[bytes], None],
    read_for: Callable[[float], bytes],
) -> tuple[bool, bytes, bool]:
    """Single write kiss off + INFO (gettoweb / forum pattern)."""
    write_flush(b"kiss off\rINFO\r")
    time.sleep(0.8)
    reply = read_for(5.0)
    only_echo = is_echo_only(b"kiss off\rINFO\r", reply) or (
        is_echo_only(b"kiss off\r", reply[:20]) and is_echo_only(b"INFO\r", reply[-20:])
    )
    return has_banner(reply), reply, only_echo


def send_jhost0(write_flush: Callable[[bytes], None]) -> None:
    """Leave WA8DED host mode → terminal (gettoweb.de / WA8DED guide)."""
    write_flush(b"\x00" * 300)
    time.sleep(0.15)
    write_flush(b"\x00\x01\x06JHOST 0\r")
    time.sleep(0.8)


def send_kiss_return(write_flush: Callable[[bytes], None]) -> None:
    write_flush(b"\xc0\xff\xc0")
    time.sleep(1.0)


def send_esc_at_k(write_flush: Callable[[bytes], None]) -> None:
    """Alternate KISS exit (TheFirmware / Symek)."""
    write_flush(b"\x1b@K")
    time.sleep(0.8)


def send_echo_off(write_flush: Callable[[bytes], None]) -> None:
    """TheFirmware ESC E 0 — disable terminal echo (TAPR double-echo)."""
    write_flush(b"\x1bE0\r")
    time.sleep(0.3)


def send_restart_escape(write_flush: Callable[[bytes], None]) -> None:
    """Exit stuck KISS / sync terminal (packet-radio.net PK-88 pattern)."""
    for _ in range(3):
        write_flush(b"\x03")
        time.sleep(0.08)
    time.sleep(0.3)
    write_flush(b"RESTART\r")
    time.sleep(2.0)


def send_at_restart(write_flush: Callable[[bytes], None]) -> None:
    """TheFirmware @-prefix restart (some TF builds in transparent mode)."""
    write_flush(b"@RESTART\r")
    time.sleep(2.0)


def send_buffer_flush(write_flush: Callable[[bytes], None]) -> None:
    """WA8DED host guide: ^Q^X before commands if junk in buffer."""
    write_flush(b"\x11\x18")  # DC1 + CAN
    time.sleep(0.2)


def _try_probe(
    write_flush: Callable[[bytes], None],
    read_for: Callable[[float], bytes],
    out: LogFn,
    label: str,
) -> tuple[bool, bytes]:
    ok, probe, only_echo = probe_info(write_flush, read_for)
    if ok:
        out(f"recovery: OK after {label}")
        return True, probe
    out(
        f"recovery: probe after {label} — {format_rx_brief(probe)}, "
        f"echo_only={only_echo}, banner={has_banner(probe)}"
    )
    if not only_echo and probe:
        out(f"recovery: partial reply after {label}")
    return False, probe


def recover_terminal(
    write_flush: Callable[[bytes], None],
    read_for: Callable[[float], bytes],
    *,
    skip_kiss_frame: bool = False,
    log: LogFn | None = None,
) -> tuple[bool, bytes]:
    """Run full software recovery ladder. Returns (host_ok, all_rx_bytes)."""
    out = log or (lambda _msg: None)
    received = b""

    chunk = read_for(1.5)
    received += chunk
    out(f"recovery: passive listen — {format_rx_brief(chunk)}")

    if not skip_kiss_frame:
        send_kiss_return(write_flush)
        chunk = read_for(1.0)
        received += chunk
        out(f"recovery: KISS return frame — {format_rx_brief(chunk)}")
        send_esc_at_k(write_flush)
        chunk = read_for(0.8)
        received += chunk
        out(f"recovery: ESC+@K — {format_rx_brief(chunk)}")

    send_jhost0(write_flush)
    chunk = read_for(1.0)
    received += chunk
    out(f"recovery: JHOST 0 — {format_rx_brief(chunk)}")

    send_buffer_flush(write_flush)
    chunk = read_for(0.3)
    received += chunk
    out("recovery: buffer flush")

    ok, probe = _try_probe(write_flush, read_for, out, "kiss off + INFO")
    received += probe
    if ok:
        return True, received

    ok, probe, _ = probe_combined(write_flush, read_for)
    received += probe
    if ok:
        out("recovery: OK after combined kiss off + INFO")
        return True, received

    send_restart_escape(write_flush)
    received += read_for(2.5)
    out("recovery: 3× Ctrl-C + RESTART")
    ok, probe = _try_probe(write_flush, read_for, out, "RESTART")
    received += probe
    if ok:
        return True, received

    send_at_restart(write_flush)
    received += read_for(2.0)
    out("recovery: @RESTART")
    ok, probe = _try_probe(write_flush, read_for, out, "@RESTART")
    received += probe
    if ok:
        return True, received

    send_echo_off(write_flush)
    received += read_for(0.3)
    ok, probe = _try_probe(write_flush, read_for, out, "ESC E 0")
    received += probe
    if ok:
        return True, received

    send_restart_escape(write_flush)
    received += read_for(3.0)
    out("recovery: second RESTART round")
    ok, probe = _try_probe(write_flush, read_for, out, "second RESTART")
    received += probe
    if ok:
        return True, received

    send_buffer_flush(write_flush)
    received += read_for(0.5)
    ok, probe = _try_probe(write_flush, read_for, out, "final buffer flush")
    received += probe
    if ok:
        return True, received

    out(
        "recovery: FAILED — echo only or silent "
        "(retry with DTR high; cold-boot without DTR may need one boot-wait)"
    )
    out(f"recovery: firmware assessment — {classify_recovery_failure(received)}")
    out(f"recovery: RX capture — {format_rx_diag(received)}")
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
