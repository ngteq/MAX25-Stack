"""
TheFirmware TF 2.7 — terminal recovery without power cycle.

Native command set (NORD><LINK source / ALAS — see 0-RESEARCHES vault).
TAPR strings (kiss off, INFO, RESTART) are not primary; kept as last-resort legacy.

Recovery ladder (stop on first banner):
  0. DTR+RTS high + settle (caller)
  1. Passive listen
  2. KISS return 0xC0 0xFF 0xC0  (tfkiss.mac cmd 0xFF → firmware reset + banner)
  3. Buffer flush ^Q^X + JHOST 0
  4. ESC V  (version / terminal probe)
  5. ESC QRES  (cold boot from EPROM — no mains power cycle)
  6. ESC E 0 + ESC V
  7. Legacy TAPR kiss off + INFO (optional last resort)
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

TF_ESC_V = b"\x1bV\r"
TF_ESC_QRES = b"\x1bQRES\r"
TF_ESC_AT_K = b"\x1b@K"
TF_ESC_E0 = b"\x1bE0\r"

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
        return "banner seen in RX but terminal probe failed — check host mode or double-echo"
    lower = received.lower()
    if b"\x1bv" in lower or b"* " in received:
        if not has_banner(received):
            return (
                "TF terminal alive (ESC V prompt) but no firmware banner — try ESC QRES with DTR high"
            )
    echo_hits = sum(
        1
        for token in (
            b"kiss off",
            b"info\r",
            b"info\n",
            b"restart\r",
            b"jhost 0",
        )
        if token in lower
    )
    if echo_hits >= 2 or (
        b"kiss off" in lower and (b"info" in lower or b"info\r" in lower)
    ):
        return (
            "echo-only — TAPR-style or transparent echo, no TheFirmware banner "
            "(Landolt: DTR high at power-on; try boot-wait or ESC QRES)"
        )
    if any(b < 0x20 and b not in (0x0D, 0x0A, 0x09) for b in received[:64]):
        return (
            f"binary/non-text ({len(received)} B) — likely KISS/stream mode, not terminal"
        )
    return f"non-banner text ({len(received)} B) — firmware state unclear, capture full RX"


def has_banner(data: bytes) -> bool:
    lower = data.lower()
    return any(m.lower() in lower for m in FIRMWARE_MARKERS)


def is_echo_only(cmd: bytes, reply: bytes) -> bool:
    c = cmd.strip(b"\r\n")
    r = reply.strip()
    return r in (c, c + b"\r", c + b"\n", c + b"\r\n")


def probe_tf_terminal(
    write_flush: Callable[[bytes], None],
    read_for: Callable[[float], bytes],
    pause: float = 0.4,
) -> tuple[bool, bytes, bool]:
    """ESC V — native TheFirmware version / terminal probe."""
    write_flush(TF_ESC_V)
    time.sleep(pause)
    reply = read_for(4.0)
    only_echo = is_echo_only(TF_ESC_V, reply)
    return has_banner(reply), reply, only_echo


def probe_info(
    write_flush: Callable[[bytes], None],
    read_for: Callable[[float], bytes],
    pause: float = 0.4,
) -> tuple[bool, bytes, bool]:
    """Alias: native TF probe (was TAPR kiss off + INFO)."""
    return probe_tf_terminal(write_flush, read_for, pause=pause)


def probe_combined(
    write_flush: Callable[[bytes], None],
    read_for: Callable[[float], bytes],
) -> tuple[bool, bytes, bool]:
    """Legacy TAPR kiss off + INFO — last resort only."""
    write_flush(b"kiss off\rINFO\r")
    time.sleep(0.8)
    reply = read_for(5.0)
    only_echo = is_echo_only(b"kiss off\rINFO\r", reply) or (
        is_echo_only(b"kiss off\r", reply[:20]) and is_echo_only(b"INFO\r", reply[-20:])
    )
    return has_banner(reply), reply, only_echo


def send_jhost0(write_flush: Callable[[bytes], None]) -> None:
    """Leave WA8DED host mode → terminal (gettoweb / WA8DED guide)."""
    send_buffer_flush(write_flush)
    write_flush(b"\x00" * 300)
    time.sleep(0.15)
    write_flush(b"\x00\x01\x06JHOST 0\r")
    time.sleep(0.8)


def send_kiss_return(write_flush: Callable[[bytes], None]) -> None:
    write_flush(b"\xc0\xff\xc0")
    time.sleep(1.0)


def send_esc_at_k(write_flush: Callable[[bytes], None]) -> None:
    """Enter KISS from terminal (tfb.c @K) — not an exit path."""
    write_flush(TF_ESC_AT_K)
    time.sleep(0.8)


def send_echo_off(write_flush: Callable[[bytes], None]) -> None:
    """TheFirmware ESC E 0 — disable terminal echo."""
    write_flush(TF_ESC_E0)
    time.sleep(0.3)


def send_qres(write_flush: Callable[[bytes], None]) -> None:
    """Software cold boot from EPROM (tfd.c Qcmd) — DTR must stay high."""
    write_flush(TF_ESC_QRES)
    time.sleep(2.5)


def send_buffer_flush(write_flush: Callable[[bytes], None]) -> None:
    """WA8DED host guide: ^Q^X before commands if junk in buffer."""
    write_flush(b"\x11\x18")
    time.sleep(0.2)


def tf_mycall_frame(call: str) -> bytes:
    """ESC I — set own callsign (tfb.c Icmd)."""
    return f"\x1bI {call.upper()}\r".encode("ascii", errors="replace")


def _try_probe(
    write_flush: Callable[[bytes], None],
    read_for: Callable[[float], bytes],
    out: LogFn,
    label: str,
) -> tuple[bool, bytes]:
    ok, probe, only_echo = probe_tf_terminal(write_flush, read_for)
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
    if has_banner(chunk):
        out("recovery: OK — banner on passive listen")
        return True, received

    if not skip_kiss_frame:
        send_kiss_return(write_flush)
        chunk = read_for(2.5)
        received += chunk
        out(f"recovery: KISS return frame — {format_rx_brief(chunk)}")
        if has_banner(chunk):
            out("recovery: OK after KISS return (firmware reset)")
            return True, received

    send_jhost0(write_flush)
    chunk = read_for(1.0)
    received += chunk
    out(f"recovery: JHOST 0 — {format_rx_brief(chunk)}")
    if has_banner(chunk):
        out("recovery: OK after JHOST 0")
        return True, received

    ok, probe = _try_probe(write_flush, read_for, out, "ESC V")
    received += probe
    if ok:
        return True, received

    send_qres(write_flush)
    chunk = read_for(3.0)
    received += chunk
    out(f"recovery: ESC QRES — {format_rx_brief(chunk)}")
    if has_banner(chunk):
        out("recovery: OK after ESC QRES")
        return True, received

    ok, probe = _try_probe(write_flush, read_for, out, "post-QRES ESC V")
    received += probe
    if ok:
        return True, received

    send_echo_off(write_flush)
    received += read_for(0.3)
    ok, probe = _try_probe(write_flush, read_for, out, "ESC E 0")
    received += probe
    if ok:
        return True, received

    send_qres(write_flush)
    received += read_for(3.0)
    out("recovery: second ESC QRES")
    ok, probe = _try_probe(write_flush, read_for, out, "second QRES")
    received += probe
    if ok:
        return True, received

    ok, probe, _ = probe_combined(write_flush, read_for)
    received += probe
    if ok:
        out("recovery: OK after legacy TAPR kiss off + INFO")
        return True, received
    if probe:
        out(f"recovery: legacy TAPR probe — {format_rx_brief(probe)}")

    out(
        "recovery: FAILED — echo only or silent "
        "(retry with DTR high; cold-boot without DTR may need boot-wait + power cycle)"
    )
    out(f"recovery: firmware assessment — {classify_recovery_failure(received)}")
    out(f"recovery: RX capture — {format_rx_diag(received)}")
    return False, received


def enter_kiss(
    write_flush: Callable[[bytes], None],
    read_for: Callable[[float], bytes],
    entry: str = "kiss_on",
) -> None:
    """Enter KISS after terminal recovery (native TF: ESC @K)."""
    if entry == "tapr":
        write_flush(b"kiss on\r")
        time.sleep(0.5)
        read_for(0.5)
        return
    if entry == "auto":
        write_flush(TF_ESC_AT_K)
        time.sleep(0.5)
        reply = read_for(0.5)
        if reply.strip() in (b"kiss on", b"kiss on\r", b"kiss on\n"):
            write_flush(TF_ESC_AT_K)
            time.sleep(0.5)
            read_for(0.5)
        return
    write_flush(TF_ESC_AT_K)
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
