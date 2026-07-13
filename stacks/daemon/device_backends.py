"""
Device backends for max25d — heterogeneous RF paths (TNC, BayCom, CRDOP).

Each enabled [devices] id gets one backend instance. Backends without hardware
validation log a startup warning but still wire real stack paths (not silent no-ops).
"""
from __future__ import annotations

import os
import select
import socket
import struct
import termios
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional

from kiss_bridge import (
    MAX_PAYLOAD,
    KissDecoder,
    SerialProfile,
    ax25_build_ui,
    ax25_parse_ui,
    format_rx_line,
    kiss_data_frame,
    serial_profile_for_device,
)
from kiss_bridge import KissBridge  # noqa: E402 — re-exported wrapper target

LogFn = Callable[[str], None]
RxFn = Callable[[str], None]

# manifest.yaml device ids → default hardware + backend kind
DEVICE_REGISTRY: dict[str, dict[str, str | bool]] = {
    "tnc2c": {"hardware": "tncs", "backend": "kiss-serial", "tested": True},
    "pktnc2": {"hardware": "tncs", "backend": "kiss-serial", "tested": False},
    "baycom-ser12": {"hardware": "modems", "backend": "baycom-kiss", "tested": True},
    "baycom-par96": {"hardware": "modems", "backend": "baycom-kiss", "tested": False},
    "baycom-kiss": {"hardware": "modems", "backend": "kiss-raw-serial", "tested": False},
    "soft-crdop": {"hardware": "soft-modems", "backend": "crdop-tcp", "tested": True},
    "audio-dummy": {"hardware": "acoustic-bench", "backend": "audio-dummy", "tested": True},
}


def registry_hardware(device_id: str, fallback: str = "tncs") -> str:
    entry = DEVICE_REGISTRY.get(device_id, {})
    return str(entry.get("hardware", fallback))


def registry_backend(device_id: str) -> str:
    entry = DEVICE_REGISTRY.get(device_id, {})
    return str(entry.get("backend", "kiss-serial"))


def registry_tested(device_id: str) -> bool:
    entry = DEVICE_REGISTRY.get(device_id, {})
    return bool(entry.get("tested", False))


def baycom_ctl_device_id(dev_cfg: DeviceBackendConfig) -> str:
    """Plugin id for max25-ctl / baycom-pr-ctl when starting kernel BayCom."""
    entry = DEVICE_REGISTRY.get(dev_cfg.device_id, {})
    if entry.get("backend") == "baycom-kiss":
        return dev_cfg.device_id
    return "baycom-ser12"


@dataclass
class DeviceBackendConfig:
    device_id: str
    hardware: str = ""
    backend_type: str = ""
    device_spec: str = ""
    enabled: bool = True
    # Serial (TNC / baycom-kiss USB)
    serial_device: str = ""
    serial_baud: int = 0
    serial_line: str = ""
    serial_dtr_rts: str = ""
    serial_kiss_entry: str = ""
    # BayCom kernel KISS PTY
    kiss_link: str = ""
    baycom_modem: str = "a"
    baycom_ini: str = ""
    # CRDOP TCP
    crdop_host: str = "127.0.0.1"
    crdop_port: int = 8515
    crdop_profile: str = "default"
    crdop_fecmode: str = "4FSK.500.100S"
    crdop_listen: bool = True
    crdop_ardop_compat: bool = False
    # Acoustic bench / audio-dummy
    audio_mode: str = "loopback"  # loopback | alsa | host
    audio_capture: str = ""
    audio_playback: str = ""
    audio_sample_rate: int = 48000
    audio_host_port: int = 8520


class DeviceBackend(ABC):
    """Common RX/TX/PTT surface for max25d."""

    device_id: str
    status: str = "closed"
    backend_type: str = ""

    @abstractmethod
    def open(self) -> bool:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def attach_session(self, mycall: str) -> bool:
        ...

    @abstractmethod
    def detach_session(self) -> None:
        ...

    @abstractmethod
    def transmit(self, src: str, dst: str, text: str, ax25_ui: bool) -> tuple[bool, str]:
        ...


class KissSerialBackend(DeviceBackend):
    """TNC2C / PK-TNC2 — command-mode serial entry into KISS."""

    backend_type = "kiss-serial"

    def __init__(
        self,
        cfg: DeviceBackendConfig,
        root: str,
        on_rx: RxFn,
        log: Optional[LogFn] = None,
        prefix: Optional[str] = None,
    ) -> None:
        self.device_id = cfg.device_id
        self._cfg = cfg
        self._root = root
        self._prefix = prefix
        self._on_rx = on_rx
        self._log = log or (lambda _m: None)
        self._bridge: Optional[KissBridge] = None
        self.status = "closed"

    def _ini_overrides(self) -> dict[str, str]:
        out: dict[str, str] = {}
        if self._cfg.serial_device:
            out["device"] = self._cfg.serial_device
        if self._cfg.serial_baud:
            out["baud"] = str(self._cfg.serial_baud)
        if self._cfg.serial_line:
            out["line"] = self._cfg.serial_line
        if self._cfg.serial_dtr_rts:
            out["dtr_rts"] = self._cfg.serial_dtr_rts
        if self._cfg.serial_kiss_entry:
            out["kiss_entry"] = self._cfg.serial_kiss_entry
        return out

    def open(self) -> bool:
        profile = serial_profile_for_device(
            self.device_id,
            self._root,
            self._ini_overrides(),
            prefix=self._prefix,
        )
        bridge = KissBridge(
            profile,
            self._on_rx,
            self._log,
            tree_root=self._root,
            install_prefix=self._prefix,
        )
        if not bridge.open():
            self._bridge = bridge
            self.status = bridge.status
            return False
        self._bridge = bridge
        self.status = bridge.status
        return True

    def close(self) -> None:
        if self._bridge is not None:
            self._bridge.close()
            self.status = self._bridge.status
            self._bridge = None
        else:
            self.status = "closed"

    def stabilize_session(self, mycall: str, *, force: bool = False) -> bool:
        if self._bridge is None:
            return False
        ok = self._bridge.stabilize_session(mycall, force=force)
        self.status = self._bridge.status
        return ok

    def attach_session(self, mycall: str) -> bool:
        if self._bridge is None:
            return False
        ok = self._bridge.attach_session(mycall)
        self.status = self._bridge.status
        return ok

    def detach_session(self) -> None:
        if self._bridge is None:
            return
        self._bridge.detach_session()
        self.status = self._bridge.status

    def transmit(self, src: str, dst: str, text: str, ax25_ui: bool) -> tuple[bool, str]:
        if self._bridge is None:
            return False, "serial not ready"
        ok, display = self._bridge.transmit(src, dst, text, ax25_ui)
        self.status = self._bridge.status
        return ok, display


class KissRawBackend(DeviceBackend):
    """Raw KISS on serial or BayCom KISS PTY (no command-mode entry)."""

    backend_type = "kiss-raw"

    def __init__(
        self,
        cfg: DeviceBackendConfig,
        path: str,
        profile: SerialProfile,
        on_rx: RxFn,
        log: Optional[LogFn] = None,
        *,
        is_pty: bool = False,
    ) -> None:
        self.device_id = cfg.device_id
        self._path = path
        self._profile = profile
        self._on_rx = on_rx
        self._log = log or (lambda _m: None)
        self._is_pty = is_pty
        self._fd: Optional[int] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._mycall = ""
        self._kiss_active = False
        self._decoder = KissDecoder()
        self.status = "closed"

    def open(self) -> bool:
        path = self._path
        if not path:
            self.status = "error-no-path"
            self._log(f"{self.device_id}: no KISS path configured")
            return False
        if not os.path.exists(path):
            self.status = "error-no-device"
            self._log(f"{self.device_id}: path missing: {path}")
            return False
        try:
            fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
            if not self._is_pty:
                self._configure_serial(fd)
            termios.tcflush(fd, termios.TCIOFLUSH)
        except OSError as exc:
            self.status = "error-open"
            self._log(f"{self.device_id}: open failed: {exc}")
            return False
        self._fd = fd
        self.status = "open"
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._rx_loop,
            name=f"kiss-raw-{self.device_id}",
            daemon=True,
        )
        self._thread.start()
        self._log(f"{self.device_id}: raw KISS open {path}")
        return True

    def _configure_serial(self, fd: int) -> None:
        from kiss_bridge import _parse_baud, _parse_line

        speed = _parse_baud(self._profile.baud)
        databits, parity = _parse_line(self._profile.line)
        t = termios.tcgetattr(fd)
        t[0] = t[1] = 0
        t[2] = termios.CLOCAL | termios.CREAD | databits | parity
        t[3] = t[4] = t[5] = speed
        t[6][termios.VMIN] = 0
        t[6][termios.VTIME] = 5
        termios.tcsetattr(fd, termios.TCSANOW, t)
        flags = struct.unpack("I", __import__("fcntl").ioctl(fd, 0x5415, struct.pack("I", 0)))[0]
        if self._profile.dtr_rts:
            flags |= 0x004 | 0x002
        __import__("fcntl").ioctl(fd, 0x5416, struct.pack("I", flags))

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        with self._lock:
            if self._fd is not None:
                try:
                    os.close(self._fd)
                except OSError:
                    pass
                self._fd = None
            self._kiss_active = False
        self.status = "closed"
        self._decoder = KissDecoder()

    def attach_session(self, mycall: str) -> bool:
        if self._fd is None:
            return False
        self._mycall = mycall.upper()
        self._kiss_active = True
        self.status = "ready"
        return True

    def detach_session(self) -> None:
        self._kiss_active = False
        if self._fd is not None:
            self.status = "open"

    def transmit(self, src: str, dst: str, text: str, ax25_ui: bool) -> tuple[bool, str]:
        if self._fd is None or not self._kiss_active:
            return False, "KISS not ready"
        if len(text.encode("utf-8")) > MAX_PAYLOAD:
            return False, "payload too long"
        info = text.encode("utf-8")
        frame = ax25_build_ui(src, dst, info)
        pkt = kiss_data_frame(0, frame)
        with self._lock:
            try:
                os.write(self._fd, pkt)
                termios.tcdrain(self._fd)
            except OSError as exc:
                self.status = "error-tx"
                return False, f"tx failed: {exc}"
        display = format_rx_line(src, dst, info, ax25_ui)
        return True, display

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


class BayComKissBackend(KissRawBackend):
    """BayCom kernel modem (SER12 / PAR96) via baycom-pr KISS PTY."""

    backend_type = "baycom-kiss"

    def __init__(
        self,
        cfg: DeviceBackendConfig,
        on_rx: RxFn,
        log: Optional[LogFn] = None,
    ) -> None:
        modem = cfg.baycom_modem or "a"
        kiss = cfg.kiss_link or f"/var/run/baycom-pr/kiss-{modem}"
        if modem == "a" and not cfg.kiss_link:
            default = "/var/run/baycom-pr/kiss"
            if os.path.exists(default) or not os.path.exists(kiss):
                kiss = default
        profile = SerialProfile(baud=9600, line="8n1", dtr_rts=False)
        super().__init__(cfg, kiss, profile, on_rx, log, is_pty=True)


class KissRawSerialBackend(KissRawBackend):
    """USB/async BayCom KISS serial (kiss-serial backend)."""

    backend_type = "kiss-raw-serial"

    def __init__(
        self,
        cfg: DeviceBackendConfig,
        root: str,
        on_rx: RxFn,
        log: Optional[LogFn] = None,
    ) -> None:
        prof = SerialProfile(baud=9600, line="8n1", dtr_rts=False)
        if cfg.serial_device:
            prof.device = cfg.serial_device
        if cfg.serial_baud:
            prof.baud = cfg.serial_baud
        if cfg.serial_line:
            prof.line = cfg.serial_line
        env_path = os.path.join(root, "stacks", "baycom-pr", "config", "baycom-pr.ini")
        if os.path.isfile(env_path) and not cfg.serial_device:
            pass
        path = cfg.serial_device or prof.device
        super().__init__(cfg, path, prof, on_rx, log, is_pty=False)


class CrdopTcpBackend(DeviceBackend):
    """MAX25-SoftModem (CRDOP) via TCP host interface (:8515 / :8516).

    Default: native M25/KISS host protocol (MAX25-SoftModem).
    Optional: third-party ARDOP wire-compat when crdop_ardop_compat=true.
    """

    backend_type = "crdop-tcp"

    def __init__(
        self,
        cfg: DeviceBackendConfig,
        on_rx: RxFn,
        log: Optional[LogFn] = None,
    ) -> None:
        self.device_id = cfg.device_id
        self._cfg = cfg
        self._on_rx = on_rx
        self._log = log or (lambda _m: None)
        self._ctrl: Optional[socket.socket] = None
        self._data: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.RLock()
        self._mycall = ""
        self._connected = False
        self.status = "closed"

    def _line_term(self) -> str:
        return "\r" if self._cfg.crdop_ardop_compat else "\n"

    def open(self) -> bool:
        host = self._cfg.crdop_host
        port = self._cfg.crdop_port
        try:
            ctrl = socket.create_connection((host, port), timeout=5.0)
            ctrl.settimeout(0.5)
            data = socket.create_connection((host, port + 1), timeout=5.0)
            data.settimeout(0.5)
        except OSError as exc:
            self.status = "error-connect"
            self._log(f"{self.device_id}: CRDOP TCP connect failed ({host}:{port}): {exc}")
            return False
        self._ctrl = ctrl
        self._data = data
        self.status = "open"
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._rx_loop,
            name=f"crdop-rx-{self.device_id}",
            daemon=True,
        )
        self._thread.start()
        self._log(f"{self.device_id}: CRDOP TCP open {host}:{port}")
        return True

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        for sock in (self._ctrl, self._data):
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
        self._ctrl = None
        self._data = None
        self._connected = False
        self.status = "closed"

    def _cmd(self, text: str) -> str:
        if self._ctrl is None:
            return ""
        term = self._line_term()
        payload = (text.rstrip(term) + term).encode("ascii", errors="replace")
        with self._lock:
            self._ctrl.sendall(payload)
            return self._read_line_unlocked()

    def _read_line_unlocked(self) -> str:
        if self._ctrl is None:
            return ""
        term = self._line_term()
        term_b = term.encode("ascii")
        buf = b""
        deadline = time.time() + 3.0
        while time.time() < deadline:
            try:
                chunk = self._ctrl.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
            while term_b in buf:
                raw, buf = buf.split(term_b, 1)
                line = raw.decode("ascii", errors="replace").strip()
                if line:
                    return line
        return ""

    def attach_session(self, mycall: str) -> bool:
        if self._ctrl is None:
            return False
        self._mycall = mycall.upper()
        if self._cfg.crdop_ardop_compat:
            cmds = [
                "INITIALIZE",
                "PROTOCOLMODE FEC",
                f"MYCALL {self._mycall}",
                f"FECMODE {self._cfg.crdop_fecmode}",
                "FECREPEATS 1",
            ]
        else:
            cmds = [
                "INITIALIZE",
                "PROTOCOLMODE KISS",
                f"MYCALL {self._mycall}",
            ]
        if self._cfg.crdop_listen:
            cmds.append("LISTEN TRUE")
        for cmd in cmds:
            reply = self._cmd(cmd)
            self._log(f"{self.device_id}: {cmd} → {reply or '(no reply)'}")
        self._connected = True
        self.status = "ready"
        return True

    def detach_session(self) -> None:
        if self._ctrl is not None and self._connected:
            self._cmd("ABORT")
        self._connected = False
        if self._ctrl is not None:
            self.status = "open"

    def transmit(self, src: str, dst: str, text: str, ax25_ui: bool) -> tuple[bool, str]:
        if self._ctrl is None or self._data is None or not self._connected:
            return False, "CRDOP not ready"
        payload = text.encode("utf-8")
        if len(payload) > MAX_PAYLOAD:
            return False, "payload too long"
        with self._lock:
            try:
                if self._cfg.crdop_ardop_compat:
                    self._data.sendall(payload)
                    self._cmd("PURGEBUFFER")
                    reply = self._cmd("FECSEND TRUE")
                    self._log(f"{self.device_id}: FECSEND → {reply}")
                else:
                    body = ax25_build_ui(src, dst, payload)
                    if len(body) >= 2:
                        body = body[:-2]
                    self._data.sendall(body)
            except OSError as exc:
                self.status = "error-tx"
                return False, f"tx failed: {exc}"
        if ax25_ui:
            display = f"[CRDOP AX25 UI {src}>{dst}] {text}"
        else:
            display = text
        return True, display

    def _rx_loop(self) -> None:
        while not self._stop.is_set():
            ctrl = self._ctrl
            if ctrl is None:
                break
            try:
                ready, _, _ = select.select([ctrl], [], [], 0.5)
                if not ready:
                    continue
                chunk = ctrl.recv(4096)
            except (OSError, socket.timeout):
                continue
            if not chunk:
                time.sleep(0.05)
                continue
            term = self._line_term()
            for line in chunk.decode("ascii", errors="replace").split(term):
                line = line.strip()
                if not line:
                    continue
                if self._cfg.crdop_ardop_compat:
                    if line.startswith("STATUS ") and "frame received OK" in line:
                        self._on_rx(f"[ARDOP RX {self.device_id}] {line[7:]}")
                    elif line.startswith("FEC") and "data" in line.lower():
                        self._on_rx(f"[ARDOP RX {self.device_id}] {line}")
                elif line.startswith("STATUS"):
                    self._on_rx(f"[CRDOP RX {self.device_id}] {line}")


class AudioDummyBackend(DeviceBackend):
    """Acoustic bench dummy — loopback, ALSA sniff, or M25 host TCP (no ARDOP FEC)."""

    backend_type = "audio-dummy"

    def __init__(
        self,
        cfg: DeviceBackendConfig,
        on_rx: RxFn,
        log: Optional[LogFn] = None,
    ) -> None:
        self.device_id = cfg.device_id
        self._cfg = cfg
        self._on_rx = on_rx
        self._log = log or (lambda _m: None)
        self._ctrl: Optional[socket.socket] = None
        self._data: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.RLock()
        self._mycall = ""
        self._connected = False
        self._engine = None
        self.status = "closed"

    def _import_engine(self):
        import sys
        from pathlib import Path

        lib = Path(__file__).resolve().parents[1] / "crdop" / "lib"
        if str(lib) not in sys.path:
            sys.path.insert(0, str(lib))
        from acoustic_engine import AcousticEngine  # noqa: WPS433
        from sound_proxy import SoundConfig  # noqa: WPS433

        sound = SoundConfig(
            capture=self._cfg.audio_capture or "default",
            playback=self._cfg.audio_playback or self._cfg.audio_capture or "default",
            sample_rate=self._cfg.audio_sample_rate,
        )
        return AcousticEngine(sample_rate=self._cfg.audio_sample_rate, sound=sound)

    def open(self) -> bool:
        mode = (self._cfg.audio_mode or "loopback").lower()
        if mode == "host":
            host = "127.0.0.1"
            port = self._cfg.audio_host_port
            try:
                ctrl = socket.create_connection((host, port), timeout=3.0)
                ctrl.settimeout(0.5)
                data = socket.create_connection((host, port + 1), timeout=3.0)
                data.settimeout(0.5)
            except OSError as exc:
                self.status = "error-connect"
                self._log(f"{self.device_id}: audio-dummy host connect failed: {exc}")
                return False
            self._ctrl = ctrl
            self._data = data
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._host_rx_loop,
                name=f"audio-dummy-{self.device_id}",
                daemon=True,
            )
            self._thread.start()
            self.status = "open"
            self._log(f"{self.device_id}: audio-dummy host {host}:{port}")
            return True

        try:
            self._engine = self._import_engine()
        except Exception as exc:
            self.status = "error-engine"
            self._log(f"{self.device_id}: audio engine load failed: {exc}")
            return False

        if mode == "alsa" and self._cfg.audio_capture:
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._alsa_sniff_loop,
                name=f"audio-sniff-{self.device_id}",
                daemon=True,
            )
            self._thread.start()
        self.status = "open"
        self._log(f"{self.device_id}: audio-dummy mode={mode}")
        return True

    def close(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        for sock in (self._ctrl, self._data):
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
        self._ctrl = None
        self._data = None
        self._connected = False
        self.status = "closed"

    def _host_cmd(self, text: str) -> str:
        if self._ctrl is None:
            return ""
        payload = (text.rstrip("\n") + "\n").encode("ascii", errors="replace")
        with self._lock:
            self._ctrl.sendall(payload)
            buf = b""
            deadline = time.time() + 2.0
            while time.time() < deadline:
                try:
                    chunk = self._ctrl.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                buf += chunk
                if b"\n" in buf:
                    line, _ = buf.split(b"\n", 1)
                    return line.decode("ascii", errors="replace").strip()
        return ""

    def attach_session(self, mycall: str) -> bool:
        self._mycall = mycall.upper()
        if self._ctrl is not None:
            for cmd in (
                "INITIALIZE",
                "PROTOCOLMODE KISS",
                f"MYCALL {self._mycall}",
                "LISTEN TRUE",
            ):
                reply = self._host_cmd(cmd)
                self._log(f"{self.device_id}: {cmd} → {reply or '(no reply)'}")
        self._connected = True
        self.status = "ready"
        return True

    def detach_session(self) -> None:
        self._connected = False
        if self._ctrl is not None:
            self.status = "open"
        else:
            self.status = "closed"

    def transmit(self, src: str, dst: str, text: str, ax25_ui: bool) -> tuple[bool, str]:
        if not self._connected:
            return False, "audio-dummy not ready"
        payload = text.encode("utf-8")
        if len(payload) > MAX_PAYLOAD:
            return False, "payload too long"

        if self._engine is not None:
            pcm = self._engine.encode_ax25_ui(src, dst, text)
            rep = self._engine.analyze_pcm(pcm)
            for line in rep.decode_lines:
                self._on_rx(f"[AUDIO RX {self.device_id}] {line}")
            display = f"[AX25 UI {src}>{dst}] {text}" if ax25_ui else text
            return True, display

        if self._data is None:
            return False, "no data channel"
        import sys
        from pathlib import Path

        lib = Path(__file__).resolve().parents[1] / "crdop" / "lib"
        if str(lib) not in sys.path:
            sys.path.insert(0, str(lib))
        from ax25_codec import ax25_build_ui  # noqa: WPS433

        body = ax25_build_ui(src, dst, payload)
        if len(body) >= 2:
            body = body[:-2]
        try:
            with self._lock:
                self._data.sendall(body)
        except OSError as exc:
            return False, f"tx failed: {exc}"
        display = f"[AX25 UI {src}>{dst}] {text}" if ax25_ui else text
        return True, display

    def _alsa_sniff_loop(self) -> None:
        import sys
        from pathlib import Path

        lib = Path(__file__).resolve().parents[1] / "crdop" / "lib"
        if str(lib) not in sys.path:
            sys.path.insert(0, str(lib))
        from sound_proxy import SoundProxy  # noqa: WPS433

        if self._engine is None:
            return
        proxy = SoundProxy(self._engine.sound)

        def on_pcm(chunk: bytes) -> None:
            rep = self._engine.analyze_pcm(chunk)
            for line in rep.decode_lines:
                self._on_rx(f"[SNIFF {self.device_id}] {line}")

        try:
            proxy.sniff_loop(chunk_symbols=40, on_pcm=on_pcm, stop=self._stop)
        except Exception as exc:
            self._log(f"{self.device_id}: sniff error: {exc}")

    def _host_rx_loop(self) -> None:
        while not self._stop.is_set():
            if self._ctrl is None:
                break
            try:
                ready, _, _ = select.select([self._ctrl], [], [], 0.5)
                if not ready:
                    continue
                chunk = self._ctrl.recv(4096)
            except (OSError, socket.timeout):
                continue
            if not chunk:
                time.sleep(0.05)
                continue
            for line in chunk.decode("ascii", errors="replace").split("\n"):
                line = line.strip()
                if line.startswith("STATUS"):
                    self._on_rx(f"[AUDIO RX {self.device_id}] {line}")


def parse_device_spec(device_id: str, spec: str, cp, cfg_defaults: dict) -> DeviceBackendConfig:
    """Build backend config from [devices] value and optional [device.<id>]."""
    dev = DeviceBackendConfig(device_id=device_id)
    dev.hardware = registry_hardware(device_id, cfg_defaults.get("hardware", "tncs"))
    dev.backend_type = registry_backend(device_id)

    section = f"device.{device_id}"
    sec_opts: dict[str, str] = {}
    if cp.has_section(section):
        sec_opts = {k: cp.get(section, k) for k in cp.options(section)}

    if sec_opts.get("hardware"):
        dev.hardware = sec_opts["hardware"]
    if sec_opts.get("backend"):
        dev.backend_type = sec_opts["backend"]

    spec = (spec or "").strip()
    dev.device_spec = spec

    if spec.startswith("baycom:"):
        dev.backend_type = "baycom-kiss"
        dev.baycom_modem = spec.split(":", 1)[1].strip() or "a"
        dev.hardware = "modems"
    elif spec.startswith("crdop:"):
        dev.backend_type = "crdop-tcp"
        dev.crdop_profile = spec.split(":", 1)[1].strip() or "default"
        dev.hardware = "soft-modems"
    elif spec.startswith("audio:"):
        dev.backend_type = "audio-dummy"
        dev.audio_mode = spec.split(":", 1)[1].strip() or "loopback"
        dev.hardware = "acoustic-bench"
    elif spec.startswith("/") or spec.startswith("dev:"):
        if dev.backend_type in ("baycom-kiss",):
            dev.kiss_link = spec
        else:
            dev.serial_device = spec.removeprefix("dev:")
            if dev.backend_type == "crdop-tcp":
                dev.backend_type = "kiss-serial"
    elif spec:
        dev.serial_device = spec

    if sec_opts.get("kiss_link"):
        dev.kiss_link = sec_opts["kiss_link"]
    if sec_opts.get("modem"):
        dev.baycom_modem = sec_opts["modem"]
    if sec_opts.get("baycom_ini"):
        dev.baycom_ini = sec_opts["baycom_ini"]
    if sec_opts.get("host"):
        dev.crdop_host = sec_opts["host"]
    if sec_opts.get("port"):
        dev.crdop_port = int(sec_opts["port"])
    if sec_opts.get("fecmode"):
        dev.crdop_fecmode = sec_opts["fecmode"]
    if sec_opts.get("listen"):
        dev.crdop_listen = sec_opts["listen"].lower() in ("1", "yes", "true", "on")
    if sec_opts.get("ardop_compat"):
        dev.crdop_ardop_compat = sec_opts["ardop_compat"].lower() in ("1", "yes", "true", "on")
    if sec_opts.get("mode"):
        dev.audio_mode = sec_opts["mode"]
    if sec_opts.get("capture"):
        dev.audio_capture = sec_opts["capture"]
    if sec_opts.get("playback"):
        dev.audio_playback = sec_opts["playback"]
    if sec_opts.get("sample_rate"):
        dev.audio_sample_rate = int(sec_opts["sample_rate"])
    if sec_opts.get("host_port"):
        dev.audio_host_port = int(sec_opts["host_port"])

    serial_sec = f"serial.{device_id}"
    if cp.has_section(serial_sec):
        if cp.has_option(serial_sec, "device"):
            dev.serial_device = cp.get(serial_sec, "device")
        if cp.has_option(serial_sec, "baud"):
            dev.serial_baud = cp.getint(serial_sec, "baud")
        if cp.has_option(serial_sec, "line"):
            dev.serial_line = cp.get(serial_sec, "line")
        if cp.has_option(serial_sec, "dtr_rts"):
            dev.serial_dtr_rts = cp.get(serial_sec, "dtr_rts")
        if cp.has_option(serial_sec, "kiss_entry"):
            dev.serial_kiss_entry = cp.get(serial_sec, "kiss_entry")

    return dev


def create_backend(
    dev_cfg: DeviceBackendConfig,
    root: str,
    on_rx: RxFn,
    log: Optional[LogFn] = None,
    prefix: Optional[str] = None,
) -> DeviceBackend:
    kind = dev_cfg.backend_type or registry_backend(dev_cfg.device_id)
    if kind == "kiss-serial":
        return KissSerialBackend(dev_cfg, root, on_rx, log, prefix=prefix)
    if kind == "baycom-kiss":
        return BayComKissBackend(dev_cfg, on_rx, log)
    if kind == "kiss-raw-serial":
        return KissRawSerialBackend(dev_cfg, root, on_rx, log)
    if kind == "crdop-tcp":
        return CrdopTcpBackend(dev_cfg, on_rx, log)
    if kind == "audio-dummy":
        return AudioDummyBackend(dev_cfg, on_rx, log)
    return KissSerialBackend(dev_cfg, root, on_rx, log, prefix=prefix)


def backend_needs_stack(kind: str) -> bool:
    return kind in ("kiss-serial", "baycom-kiss", "kiss-raw-serial", "crdop-tcp", "audio-dummy")


def backend_serial_label(backend: Optional[DeviceBackend]) -> str:
    if backend is None:
        return "n/a"
    return backend.status
