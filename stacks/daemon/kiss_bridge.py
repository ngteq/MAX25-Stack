"""
KISS serial bridge for max25d — AX.25 UI over TNC2C / PK-TNC2.

PTT: TNC firmware keys on KISS DATA (requires MYCALL); kernel BayCom (baycom_ser_fdx)
keys RTS in the driver when the KISS bridge accepts a DATA frame — no max25d PTT command.
"""
from __future__ import annotations

import fcntl
import os
import struct
import termios
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from ax25_codec import (  # noqa: E402
    ax25_build_ui,
    ax25_crc,
    ax25_crc_valid,
    ax25_parse_ui,
    format_callsign,
    parse_callsign,
    validate_callsign,
)

FEND = 0xC0
FESC = 0xDB
TFEND = 0xDC
TFESC = 0xDD

KISS_CMD_DATA = 0x00
MAX_FRAME = 1024
MAX_PAYLOAD = 256


@dataclass
class SerialProfile:
    device: str = "/dev/ttyS4"
    baud: int = 19200
    line: str = "8n1"
    dtr_rts: bool = True
    kiss_entry: str = "kiss_on"  # kiss_on | auto


class KissDecoder:
    def __init__(self) -> None:
        self._buf = bytearray()
        self._in_frame = False
        self._escape = False

    def feed(self, data: bytes) -> list[tuple[int, bytes]]:
        frames: list[tuple[int, bytes]] = []
        for byte in data:
            if byte == FEND:
                if self._in_frame and self._buf:
                    parsed = self._deliver()
                    if parsed is not None:
                        frames.append(parsed)
                self._in_frame = True
                self._escape = False
                self._buf.clear()
                continue
            if not self._in_frame:
                continue
            if self._escape:
                if byte == TFEND:
                    byte = FEND
                elif byte == TFESC:
                    byte = FESC
                self._escape = False
            elif byte == FESC:
                self._escape = True
                continue
            if len(self._buf) >= MAX_FRAME:
                self._buf.clear()
                self._in_frame = False
                continue
            self._buf.append(byte)
        return frames

    def _deliver(self) -> Optional[tuple[int, bytes]]:
        if len(self._buf) < 1:
            return None
        cmd_byte = self._buf[0]
        if (cmd_byte & 0x0F) != KISS_CMD_DATA:
            return None
        port = (cmd_byte >> 4) & 0x0F
        payload = bytes(self._buf[1:])
        return port, payload


def kiss_escape(data: bytes) -> bytes:
    out = bytearray()
    for b in data:
        if b == FEND:
            out.extend((FESC, TFEND))
        elif b == FESC:
            out.extend((FESC, TFESC))
        else:
            out.append(b)
    return bytes(out)


def kiss_encode(port: int, cmd: int, payload: bytes) -> bytes:
    cmd_byte = ((port & 0x0F) << 4) | (cmd & 0x0F)
    return b"\xC0" + kiss_escape(bytes([cmd_byte]) + payload) + b"\xC0"


def kiss_data_frame(port: int, ax25_frame: bytes) -> bytes:
    """Build KISS DATA; strip FCS when CRC validates (ax25ipd / KISS convention)."""
    if ax25_crc_valid(ax25_frame):
        ax25_frame = ax25_frame[:-2]
    return kiss_encode(port, KISS_CMD_DATA, ax25_frame)


def format_rx_line(src: str, dst: str, payload: bytes, ax25_ui: bool) -> str:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        text = payload.decode("utf-8", errors="replace")
    if ax25_ui:
        return f"[AX25 UI {src}>{dst}] {text}"
    return text


def load_env_file(path: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path or not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                out[key.strip()] = val.strip()
    return out


def _load_serial_env(device_id: str, root: str, prefix: Optional[str] = None) -> dict[str, str]:
    from paths import serial_env_candidates

    tree = Path(root)
    pref = Path(prefix) if prefix else None
    for path in serial_env_candidates(device_id, tree, pref):
        env = load_env_file(str(path))
        if env:
            return env
    return {}


def serial_profile_for_device(
    device_id: str,
    root: str,
    ini: dict[str, str],
    prefix: Optional[str] = None,
) -> SerialProfile:
    prof = SerialProfile()
    if ini.get("device"):
        prof.device = ini["device"]
    if ini.get("baud"):
        prof.baud = int(ini["baud"])
    if ini.get("line"):
        prof.line = ini["line"].lower()
    if ini.get("dtr_rts"):
        prof.dtr_rts = ini["dtr_rts"].lower() in ("1", "yes", "true", "on")
    if ini.get("kiss_entry"):
        prof.kiss_entry = ini["kiss_entry"].lower()

    env = _load_serial_env(device_id, root, prefix)

    if device_id == "tnc2c":
        prof.device = ini.get("device") or env.get("TNC2C_DEV", prof.device)
        prof.baud = int(ini.get("baud") or env.get("TNC2C_BAUD", prof.baud))
        prof.line = (ini.get("line") or env.get("TNC2C_LINE", prof.line)).lower()
        if "dtr_rts" not in ini:
            prof.dtr_rts = True
        if "kiss_entry" not in ini:
            prof.kiss_entry = "kiss_on"
    elif device_id == "pktnc2":
        prof.device = ini.get("device") or env.get("PKTNC2_DEV") or env.get("TNC_DEV", prof.device)
        prof.baud = int(ini.get("baud") or env.get("PKTNC2_BAUD") or env.get("TNC_BAUD", "9600"))
        prof.line = (ini.get("line") or env.get("PKTNC2_LINE") or env.get("TNC_LINE", "8n1")).lower()
        if "dtr_rts" not in ini:
            prof.dtr_rts = False
        if "kiss_entry" not in ini:
            prof.kiss_entry = "auto"
    return prof


def _parse_line(line: str) -> tuple[int, int]:
    line = line.lower()
    if line == "7e1":
        return termios.CS7, termios.PARENB
    return termios.CS8, 0


def _parse_baud(baud: int) -> int:
    table = {
        1200: termios.B1200,
        2400: termios.B2400,
        4800: termios.B4800,
        9600: termios.B9600,
        19200: termios.B19200,
    }
    if baud not in table:
        raise ValueError(f"unsupported baud: {baud}")
    return table[baud]


class KissBridge:
    """Thread-safe KISS bridge on a serial TNC port."""

    def __init__(
        self,
        profile: SerialProfile,
        on_rx: Callable[[str], None],
        log: Optional[Callable[[str], None]] = None,
        *,
        tree_root: str = "",
        install_prefix: Optional[str] = None,
    ) -> None:
        self.profile = profile
        self._on_rx = on_rx
        self._log = log or (lambda _m: None)
        self._tree_root = tree_root
        self._install_prefix = install_prefix
        self._fd: Optional[int] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._kiss_active = False
        self._mycall = ""
        self.status = "closed"
        self._decoder = KissDecoder()

    def open(self) -> bool:
        dev = self.profile.device
        if not os.access(dev, os.R_OK | os.W_OK):
            self.status = "error-no-device"
            self._log(f"serial: no access to {dev}")
            return False
        try:
            speed = _parse_baud(self.profile.baud)
            databits, parity = _parse_line(self.profile.line)
        except ValueError as exc:
            self.status = "error-config"
            self._log(f"serial: {exc}")
            return False
        try:
            fd = os.open(dev, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
            t = termios.tcgetattr(fd)
            t[0] = t[1] = 0
            t[2] = termios.CLOCAL | termios.CREAD | databits | parity
            t[3] = t[4] = t[5] = speed
            t[6][termios.VMIN] = 0
            t[6][termios.VTIME] = 5
            termios.tcsetattr(fd, termios.TCSANOW, t)
            termios.tcflush(fd, termios.TCIOFLUSH)
            flags = struct.unpack("I", fcntl.ioctl(fd, 0x5415, struct.pack("I", 0)))[0]
            if self.profile.dtr_rts:
                flags |= 0x004 | 0x002
            fcntl.ioctl(fd, 0x5416, struct.pack("I", flags))
        except OSError as exc:
            self.status = "error-open"
            self._log(f"serial open failed: {exc}")
            return False
        self._fd = fd
        self._log(f"serial open {dev} {self.profile.baud} {self.profile.line.upper()}")
        if self.profile.dtr_rts:
            time.sleep(2.0)
            self._log("serial: DTR settle (2s)")
        self.status = "open"
        return True

    def close(self) -> None:
        self._stop_rx_thread()
        with self._lock:
            if self._fd is not None:
                if self._kiss_active:
                    self._write_unlocked(b"kiss off\r")
                try:
                    os.close(self._fd)
                except OSError:
                    pass
                self._fd = None
            self._kiss_active = False
        self.status = "closed"
        self._decoder = KissDecoder()

    def _stop_rx_thread(self) -> None:
        """Stop KISS RX thread so recovery owns the serial FD exclusively."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._stop.clear()

    def _start_rx_thread(self) -> None:
        """Start KISS RX after terminal recovery and KISS entry succeed."""
        if self._fd is None or self._thread is not None or not self._kiss_active:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._rx_loop, name="kiss-rx", daemon=True)
        self._thread.start()

    def attach_session(self, mycall: str) -> bool:
        if self._fd is None:
            return False
        self._mycall = mycall.upper()
        self._stop_rx_thread()
        with self._lock:
            ok = self._stabilize_unlocked(self._mycall, force_ladder=False)
        if ok:
            self._start_rx_thread()
        return ok

    def stabilize_session(self, mycall: str, *, force: bool = False) -> bool:
        """Probe terminal/KISS health and repair without closing the port (keeps DTR)."""
        if self._fd is None:
            self.status = "error-open"
            return False
        self._mycall = mycall.upper()
        self._stop_rx_thread()
        with self._lock:
            ok = self._stabilize_unlocked(self._mycall, force_ladder=force)
        if ok:
            self._start_rx_thread()
        return ok

    def _load_recovery_mod(self):
        import importlib.util

        from paths import tnc_serial_recovery_path

        path = None
        if self._tree_root:
            prefix = Path(self._install_prefix) if self._install_prefix else None
            path = tnc_serial_recovery_path(Path(self._tree_root), prefix)
        if path is None:
            path = Path(__file__).resolve().parents[1] / "tncs" / "tnc_serial_recovery.py"
        if not path.is_file():
            return None
        spec = importlib.util.spec_from_file_location("tnc_serial_recovery", path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _recovery_io(self) -> tuple[Callable[[bytes], None], Callable[[float], bytes]]:
        def wf(data: bytes) -> None:
            self._write_unlocked(data)

        def rf(seconds: float) -> bytes:
            return self._drain_unlocked(seconds)

        return wf, rf

    def _leave_kiss_unlocked(self) -> None:
        if not self._kiss_active:
            return
        self._write_unlocked(b"kiss off\r")
        time.sleep(0.3)
        self._drain_unlocked(0.2)
        self._kiss_active = False

    def _enter_kiss_session_unlocked(self) -> bool:
        if not self._set_mycall_unlocked(self._mycall):
            self._log("serial: MYCALL may have failed")
        if not self._enter_kiss_unlocked():
            self.status = "error-kiss"
            self._kiss_active = False
            return False
        self._kiss_active = True
        self.status = "ready"
        return True

    def _stabilize_unlocked(self, mycall: str, *, force_ladder: bool) -> bool:
        """Host probe, optional recovery ladder, MYCALL + KISS — port stays open."""
        self._mycall = mycall.upper()
        try:
            mod = self._load_recovery_mod()
            wf, rf = self._recovery_io()
            self._leave_kiss_unlocked()

            if mod is None:
                self._log("serial: tnc_serial_recovery.py not found")
                self.status = "error-config"
                self._kiss_active = False
                return False

            ok, probe_data, only_echo = mod.probe_info(wf, rf, pause=0.25)
            if not ok or only_echo or force_ladder:
                self._log(
                    f"serial: initial probe — {mod.format_rx_brief(probe_data)}, "
                    f"echo_only={only_echo}, banner={mod.has_banner(probe_data)}"
                )
            if ok and not only_echo and not force_ladder:
                return self._enter_kiss_session_unlocked()
            if only_echo or not ok or force_ladder:
                label = "auto-repair" if force_ladder else "recovery ladder"
                self._log(f"serial: {label}")
                ok, _ = mod.recover_terminal(wf, rf, log=self._log)
                if not ok:
                    self.status = "error-host"
                    self._kiss_active = False
                    return False
                return self._enter_kiss_session_unlocked()
            self.status = "error-host"
            self._kiss_active = False
            return False
        except OSError as exc:
            self.status = "error-io"
            self._kiss_active = False
            self._log(f"serial: stabilize I/O error ({exc})")
            return False

    def _recover_terminal_unlocked(self) -> bool:
        """Legacy hook — full ladder when probe fails."""
        try:
            mod = self._load_recovery_mod()
            if mod is None:
                return True
            wf, rf = self._recovery_io()
            ok, _, only_echo = mod.probe_info(wf, rf)
            if ok and not only_echo:
                self._log("serial: terminal mode OK")
                return True
            self._log("serial: software recovery ladder")
            ok, _ = mod.recover_terminal(wf, rf, log=self._log)
            if ok:
                self._log("serial: recovery OK")
            return ok
        except Exception as exc:
            self._log(f"serial: recovery skipped ({exc})")
            return True

    def detach_session(self) -> None:
        self._stop_rx_thread()
        with self._lock:
            if self._fd is not None and self._kiss_active:
                self._write_unlocked(b"kiss off\r")
                time.sleep(0.2)
            self._kiss_active = False
        if self._fd is not None:
            self.status = "open"

    def transmit(self, src: str, dst: str, text: str, ax25_ui: bool) -> tuple[bool, str]:
        if self._fd is None or not self._kiss_active:
            return False, "serial not ready"
        if len(text.encode("utf-8")) > MAX_PAYLOAD:
            return False, "payload too long"
        try:
            validate_callsign(src)
            validate_callsign(dst)
        except ValueError as exc:
            return False, str(exc)
        info = text.encode("utf-8")
        try:
            frame = ax25_build_ui(src, dst, info)
        except ValueError as exc:
            return False, str(exc)
        pkt = kiss_data_frame(0, frame)
        with self._lock:
            try:
                self._write_unlocked(pkt)
                termios.tcdrain(self._fd)
            except OSError as exc:
                self.status = "error-tx"
                return False, f"tx failed: {exc}"
        display = format_rx_line(src, dst, info, ax25_ui)
        return True, display

    def _write_unlocked(self, data: bytes) -> None:
        if self._fd is None:
            return
        os.write(self._fd, data)

    def _drain_unlocked(self, seconds: float) -> bytes:
        if self._fd is None:
            return b""
        end = time.time() + seconds
        chunks: list[bytes] = []
        while time.time() < end:
            try:
                chunk = os.read(self._fd, 4096)
                if chunk:
                    chunks.append(chunk)
            except BlockingIOError:
                time.sleep(0.02)
        return b"".join(chunks)

    def _set_mycall_unlocked(self, call: str) -> bool:
        mod = self._load_recovery_mod()
        if mod is not None and hasattr(mod, "tf_mycall_frame"):
            cmd = mod.tf_mycall_frame(call)
        else:
            cmd = f"\x1bI {call.upper()}\r".encode("ascii", errors="replace")
        self._write_unlocked(cmd)
        time.sleep(0.4)
        reply = self._drain_unlocked(0.6)
        return b"?" not in reply[:32]

    def _enter_kiss_unlocked(self) -> bool:
        entry = self.profile.kiss_entry
        if entry == "tapr":
            self._write_unlocked(b"kiss on\r")
            time.sleep(0.5)
            self._drain_unlocked(0.3)
            return True
        self._write_unlocked(b"\x1b@K")
        time.sleep(0.5)
        self._drain_unlocked(0.3)
        return True

    def _rx_loop(self) -> None:
        while not self._stop.is_set():
            fd = self._fd
            if fd is None:
                break
            try:
                chunk = os.read(fd, 4096)
            except BlockingIOError:
                time.sleep(0.05)
                continue
            except OSError:
                self._log("serial: rx I/O error — watch will repair")
                self.status = "error-io"
                break
            if not chunk:
                time.sleep(0.05)
                continue
            for _port, payload in self._decoder.feed(chunk):
                if not payload:
                    continue
                parsed = ax25_parse_ui(payload)
                if parsed is None:
                    continue
                src, dst, info = parsed
                line = format_rx_line(src, dst, info, ax25_ui=True)
                self._on_rx(line)
