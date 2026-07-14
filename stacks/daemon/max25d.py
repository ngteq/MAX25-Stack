#!/usr/bin/env python3
"""
max25d — MainAX25-Stack daemon.

Linux/KLinux: full hardware stack. FreeBSD: server + CRDOP/OSS (modular TCP/IP service).
"""
from __future__ import annotations

import argparse
import configparser
import os
import re
import select
import signal
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Set

sys.path.insert(0, str(Path(__file__).resolve().parent))
from device_backends import (  # noqa: E402
    DeviceBackend,
    DeviceBackendConfig,
    backend_serial_label,
    baycom_ctl_device_id,
    create_backend,
    parse_device_spec,
    registry_tested,
)
from banlist import BanList, DEFAULT_BANS_FILE, extract_ax25_source  # noqa: E402
from daemon_log import LOGGER, emit_startup_banner, emit_startup_complete  # noqa: E402
from kiss_bridge import KissBridge  # noqa: E402 — tests patch this symbol
from paths import ctl_path, resolve_baycom_ini, resolve_layout  # noqa: E402
from max25_platform import (  # noqa: E402
    default_unix_socket,
    max25d_supported,
    platform_label,
    supported_device_ids,
)
from modular_tcp_server import ModularTcpMainService, ModularTcpConfig, load_modular_tcp  # noqa: E402

_EXE = Path(__file__).resolve()
TREE, PREFIX = resolve_layout(_EXE)
ROOT = TREE  # dev checkout root or MAX25_ROOT / install prefix

DEFAULT_TCP_PORT = 7325
DEFAULT_UNIX = default_unix_socket()
CALLSIGN_RE = re.compile(r"^[A-Z0-9]{1,6}(-(1[0-5]|[0-9]))?$")
RESERVED_DEVICE_KEYS = frozenset({"default", "enabled"})


def _device_is_baycom(dev: DeviceBackendConfig) -> bool:
    if dev.device_id.startswith("baycom"):
        return True
    spec = (dev.device_spec or "").strip()
    if spec.startswith("baycom:"):
        return True
    return dev.backend_type == "baycom-kiss" and dev.hardware == "modems"


def _device_is_pccom(dev: DeviceBackendConfig) -> bool:
    if "pccom" in dev.device_id.lower():
        return True
    ini = (dev.baycom_ini or "").lower()
    return "pccom" in ini


def _device_allowed_by_features(dev: DeviceBackendConfig, cfg: DaemonConfig) -> bool:
    if _device_is_baycom(dev) and not cfg.feature_baycom:
        LOGGER.warn(
            f"device {dev.device_id}: BayCom disabled — set [features] baycom=yes",
            area="config",
        )
        return False
    if _device_is_pccom(dev) and not cfg.feature_pccom:
        LOGGER.warn(
            f"device {dev.device_id}: PC-COM disabled — set [features] pccom=yes",
            area="config",
        )
        return False
    return True


@dataclass
class DaemonConfig:
    mode: str = "standalone"
    hardware: str = "tncs"
    device: str = "tnc2c"
    default_device: str = ""
    devices: list[DeviceBackendConfig] = field(default_factory=list)
    tcp_host: str = "0.0.0.0"
    tcp_port: int = DEFAULT_TCP_PORT
    unix_socket: str = DEFAULT_UNIX
    tcp_password: str = ""
    callerid: str = "CB-0"
    callid: str = "QST"
    ax25_ui: bool = True
    auto_start: bool = True
    serial_enabled: bool = True
    serial_watch: bool = True
    serial_watch_interval: int = 60
    serial_repair_cooldown: int = 20
    serial_watch_startup_grace: int = 45
    stack_recover_only: bool = True
    stack_retry_interval: int = 120
    serial_bootwait_escalate: bool = True
    serial_bootwait_escalate_after: int = 3
    serial_bootwait_escalate_cooldown: int = 300
    bans_file: str = str(DEFAULT_BANS_FILE)
    config_path: str = ""
    feature_baycom: bool = False
    feature_pccom: bool = False
    # Legacy single-device [serial] overrides (used when [devices] absent).
    serial_device: str = ""
    serial_baud: int = 0
    serial_line: str = ""
    serial_dtr_rts: str = ""
    serial_kiss_entry: str = ""
    modular_tcp: ModularTcpConfig = field(default_factory=ModularTcpConfig)


@dataclass
class DeviceRuntime:
    cfg: DeviceBackendConfig
    backend: Optional[DeviceBackend] = None
    stack_proc: Optional[subprocess.Popen] = None
    stack_status: str = "stopped"
    link_status: str = "n/a"
    last_watch: float = 0.0
    last_repair: float = 0.0
    last_stack_retry: float = 0.0
    prep_done: bool = False
    inline_repair_failures: int = 0
    last_bootwait_escalate: float = 0.0


@dataclass
class DaemonState:
    cfg: DaemonConfig
    connected: bool = False
    monitor_only: bool = False
    selected_device: str = ""
    devices: dict[str, DeviceRuntime] = field(default_factory=dict)
    clients: Set[socket.socket] = field(default_factory=set)
    bans: BanList = field(default_factory=BanList)
    lock: threading.Lock = field(default_factory=threading.Lock)
    started_at: float = 0.0


def log(msg: str) -> None:
    """Legacy log hook — structured stderr (human + machine readable)."""
    LOGGER.emit_unstructured(msg)


def valid_callsign(value: str) -> bool:
    return bool(value and CALLSIGN_RE.match(value.upper()))


def _truthy(value: str) -> bool:
    return value.lower() in ("1", "yes", "true", "on")


def _serial_overrides_from_section(cp: configparser.ConfigParser, section: str) -> dict[str, str]:
    if not cp.has_section(section):
        return {}
    out: dict[str, str] = {}
    for key in ("device", "baud", "line", "dtr_rts", "kiss_entry"):
        if cp.has_option(section, key):
            out[key] = cp.get(section, key)
    return out


def _apply_serial_overrides(dev: DeviceBackendConfig, overrides: dict[str, str]) -> None:
    if overrides.get("device"):
        dev.serial_device = overrides["device"]
    if overrides.get("baud"):
        dev.serial_baud = int(overrides["baud"])
    if overrides.get("line"):
        dev.serial_line = overrides["line"]
    if overrides.get("dtr_rts"):
        dev.serial_dtr_rts = overrides["dtr_rts"]
    if overrides.get("kiss_entry"):
        dev.serial_kiss_entry = overrides["kiss_entry"]


def parse_devices(cp: configparser.ConfigParser, cfg: DaemonConfig) -> list[DeviceBackendConfig]:
    """Build device list from [devices] or legacy [daemon] device= + [serial]."""
    defaults = {"hardware": cfg.hardware}
    if cp.has_section("devices"):
        default_id = cp.get("devices", "default", fallback="").strip()
        enabled_raw = cp.get("devices", "enabled", fallback="").strip()
        enabled_set: Optional[set[str]] = None
        if enabled_raw:
            enabled_set = {x.strip() for x in enabled_raw.split(",") if x.strip()}

        entries: list[DeviceBackendConfig] = []
        for key in cp.options("devices"):
            if key.lower() in RESERVED_DEVICE_KEYS:
                continue
            device_id = key.strip()
            spec = cp.get("devices", key, fallback="").strip()
            dev = parse_device_spec(device_id, spec, cp, defaults)
            if enabled_set is not None:
                dev.enabled = device_id in enabled_set
            entries.append(dev)

        if not entries:
            LOGGER.warn(
                "[devices] section empty — falling back to legacy single device",
                area="config",
            )
        else:
            if default_id:
                cfg.default_device = default_id
            elif cfg.device:
                cfg.default_device = cfg.device
            else:
                cfg.default_device = entries[0].device_id
            return entries

    # Legacy single device
    device_id = cfg.device or "tnc2c"
    dev = parse_device_spec(device_id, "", cp, defaults)
    legacy = _serial_overrides_from_section(cp, "serial")
    if cfg.serial_device:
        legacy.setdefault("device", cfg.serial_device)
    if cfg.serial_baud:
        legacy.setdefault("baud", str(cfg.serial_baud))
    if cfg.serial_line:
        legacy.setdefault("line", cfg.serial_line)
    if cfg.serial_dtr_rts:
        legacy.setdefault("dtr_rts", cfg.serial_dtr_rts)
    if cfg.serial_kiss_entry:
        legacy.setdefault("kiss_entry", cfg.serial_kiss_entry)
    _apply_serial_overrides(dev, legacy)
    cfg.default_device = device_id
    return [dev]


def load_config(path: Optional[Path]) -> DaemonConfig:
    cfg = DaemonConfig()
    if path is None:
        for candidate in (
            Path(os.environ.get("MAX25D_INI", "")),
            Path("/etc/max25/max25d.ini"),
            ROOT / "share/max25/max25d.ini.example",
        ):
            if candidate and candidate.is_file():
                path = candidate
                break
    if path is None or not path.is_file():
        LOGGER.warn(f"using built-in defaults (no ini at {path})", area="config")
        cfg.devices = [parse_device_spec(cfg.device, "", configparser.ConfigParser(), {"hardware": cfg.hardware})]
        cfg.default_device = cfg.device
        cfg.config_path = ""
        return cfg

    cfg.config_path = str(path)

    cp = configparser.ConfigParser(strict=False)
    cp.read(path)
    if cp.has_section("daemon"):
        cfg.mode = cp.get("daemon", "mode", fallback=cfg.mode)
        cfg.hardware = cp.get("daemon", "hardware", fallback=cfg.hardware)
        cfg.device = cp.get("daemon", "device", fallback=cfg.device)
    if cp.has_section("network"):
        cfg.tcp_host = cp.get("network", "tcp_host", fallback=cfg.tcp_host)
        cfg.tcp_port = cp.getint("network", "tcp_port", fallback=cfg.tcp_port)
        cfg.unix_socket = cp.get("network", "unix_socket", fallback=cfg.unix_socket)
        cfg.tcp_password = cp.get("network", "tcp_password", fallback=cfg.tcp_password)
    if cp.has_section("modem"):
        cfg.callerid = cp.get("modem", "callerid", fallback=cfg.callerid).upper()
        cfg.callid = cp.get("modem", "callid", fallback=cfg.callid).upper()
        cfg.ax25_ui = _truthy(cp.get("modem", "ax25_ui", fallback="yes"))
        cfg.bans_file = cp.get("modem", "bans_file", fallback=cfg.bans_file)
    if cp.has_section("stack"):
        cfg.auto_start = _truthy(cp.get("stack", "auto_start", fallback="yes"))
        if cp.has_option("stack", "serial_watch"):
            cfg.serial_watch = _truthy(cp.get("stack", "serial_watch"))
        cfg.serial_watch_interval = cp.getint(
            "stack", "serial_watch_interval", fallback=cfg.serial_watch_interval
        )
        cfg.serial_repair_cooldown = cp.getint(
            "stack", "serial_repair_cooldown", fallback=cfg.serial_repair_cooldown
        )
        cfg.serial_watch_startup_grace = cp.getint(
            "stack", "serial_watch_startup_grace", fallback=cfg.serial_watch_startup_grace
        )
        if cp.has_option("stack", "stack_recover_only"):
            cfg.stack_recover_only = _truthy(cp.get("stack", "stack_recover_only"))
        cfg.stack_retry_interval = cp.getint(
            "stack", "stack_retry_interval", fallback=cfg.stack_retry_interval
        )
        if cp.has_option("stack", "serial_bootwait_escalate"):
            cfg.serial_bootwait_escalate = _truthy(cp.get("stack", "serial_bootwait_escalate"))
        cfg.serial_bootwait_escalate_after = cp.getint(
            "stack", "serial_bootwait_escalate_after", fallback=cfg.serial_bootwait_escalate_after
        )
        cfg.serial_bootwait_escalate_cooldown = cp.getint(
            "stack",
            "serial_bootwait_escalate_cooldown",
            fallback=cfg.serial_bootwait_escalate_cooldown,
        )
    if cp.has_section("serial"):
        cfg.serial_device = cp.get("serial", "device", fallback="")
        cfg.serial_baud = cp.getint("serial", "baud", fallback=0)
        cfg.serial_line = cp.get("serial", "line", fallback="")
        cfg.serial_dtr_rts = cp.get("serial", "dtr_rts", fallback="")
        cfg.serial_kiss_entry = cp.get("serial", "kiss_entry", fallback="")

    if cp.has_section("features"):
        cfg.feature_baycom = _truthy(cp.get("features", "baycom", fallback="no"))
        cfg.feature_pccom = _truthy(cp.get("features", "pccom", fallback="no"))

    cfg.devices = parse_devices(cp, cfg)
    cfg.devices = [d for d in cfg.devices if _device_allowed_by_features(d, cfg)]
    allowed = supported_device_ids()
    if allowed:
        filtered: list[DeviceBackendConfig] = []
        for dev in cfg.devices:
            if dev.device_id in allowed:
                filtered.append(dev)
            else:
                LOGGER.warn(
                    f"device {dev.device_id} not supported on {platform_label()} — skipped",
                    area="config",
                )
        cfg.devices = filtered
    cfg.modular_tcp = load_modular_tcp(cp)
    if not cfg.default_device and cfg.devices:
        cfg.default_device = cfg.devices[0].device_id
    cfg.device = cfg.default_device
    return cfg


def init_device_runtimes(state: DaemonState) -> None:
    state.devices.clear()
    for dev_cfg in state.cfg.devices:
        if not dev_cfg.enabled:
            continue
        state.devices[dev_cfg.device_id] = DeviceRuntime(cfg=dev_cfg)
        if not registry_tested(dev_cfg.device_id):
            LOGGER.warn(
                f"backend={dev_cfg.backend_type or 'auto'} — not hardware-validated in CI",
                area="devices",
                device=dev_cfg.device_id,
            )
    if state.cfg.default_device in state.devices:
        state.selected_device = state.cfg.default_device
    elif state.devices:
        state.selected_device = next(iter(state.devices))
    else:
        state.selected_device = state.cfg.default_device


def enabled_device_ids(state: DaemonState) -> list[str]:
    return list(state.devices.keys())


def device_hardware(state: DaemonState, dev_id: str) -> str:
    rt = state.devices.get(dev_id)
    if rt is None:
        return state.cfg.hardware
    return rt.cfg.hardware or state.cfg.hardware


def device_backend_kind(state: DaemonState, dev_id: str) -> str:
    rt = state.devices.get(dev_id)
    if rt is None:
        return "kiss-serial"
    return rt.cfg.backend_type or "kiss-serial"


def on_backend_rx(state: DaemonState, dev_id: str, line: str) -> None:
    src = extract_ax25_source(line)
    if src and state.bans.is_banned(src):
        return
    log(f"rx {dev_id}: {line}")
    broadcast(state, f"RX device={dev_id} {line}")


BACKEND_POLL_OPEN_STATUSES = frozenset(
    {
        "closed",
        "error-open",
        "error-connect",
        "error-no-device",
        "error-no-path",
    }
)

SERIAL_REPAIR_STATUSES = frozenset(
    {
        "error-host",
        "error-kiss",
        "error-tx",
        "error-io",
        "error-config",
    }
)

BACKEND_RETRY_STATUSES = BACKEND_POLL_OPEN_STATUSES | SERIAL_REPAIR_STATUSES


def uses_inline_tnc_prep(state: DaemonState, dev_id: str) -> bool:
    """kiss-serial owned by max25d — no boot-wait subprocess (avoids port conflict)."""
    if not state.cfg.stack_recover_only:
        return False
    return device_backend_kind(state, dev_id) == "kiss-serial"


def prep_inline_serial_device(state: DaemonState, dev_id: str) -> None:
    """Open serial and run initial recovery while holding DTR (no subprocess)."""
    rt = state.devices[dev_id]
    rt.stack_status = "ready"
    LOGGER.info("inline prep — max25d owns serial recovery", area="stack", device=dev_id)
    if not backend_enabled(state, dev_id):
        return
    if not open_backend(state, dev_id):
        LOGGER.error(f"serial prep open failed status={rt.link_status}", area="serial", device=dev_id)
        return
    backend = rt.backend
    stabilize = getattr(backend, "stabilize_session", None)
    if stabilize is None:
        return
    ok = stabilize(state.cfg.callerid, force=False)
    rt.prep_done = True
    rt.link_status = backend.status
    if ok:
        LOGGER.ok("serial prep complete — terminal + KISS ready", area="serial", device=dev_id)
    elif (
        backend.status == "error-host"
        and state.cfg.serial_bootwait_escalate
        and rt.stack_proc is None
    ):
        LOGGER.warn(
            "inline ladder exhausted (error-host) — escalating to boot-wait + power-cycle hint",
            area="serial",
            device=dev_id,
        )
        rt.last_bootwait_escalate = time.time()
        escalate_to_bootwait_stack(state, dev_id)
    else:
        LOGGER.warn(
            f"prep deferred status={backend.status} — serial watch will retry",
            area="serial",
            device=dev_id,
        )


def escalate_to_bootwait_stack(state: DaemonState, dev_id: str) -> None:
    """Release inline serial and run boot-wait subprocess (DTR + power-cycle rescue)."""
    rt = state.devices[dev_id]
    close_backend(state, dev_id)
    rt.prep_done = False
    ctl = ctl_path(ROOT, PREFIX, _EXE)
    if not ctl.is_file():
        rt.stack_status = "error-no-ctl"
        log(f"serial watch: boot-wait escalate failed — no ctl ({dev_id})")
        return
    hw = device_hardware(state, dev_id)
    args = [
        str(ctl),
        "start",
        "--mode",
        state.cfg.mode,
        "--hardware",
        hw,
        "--device",
        dev_id,
    ]
    env = os.environ.copy()
    env["MAX25_MODE"] = state.cfg.mode
    env.pop("MAX25_TNC_PREP", None)
    workdir = str(ROOT if (ROOT / "plugins").is_dir() else (PREFIX or ROOT))
    try:
        proc = subprocess.Popen(
            args,
            cwd=workdir,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        log(f"serial watch: boot-wait escalate failed ({dev_id}): {exc}")
        rt.stack_status = "error"
        return
    rt.stack_proc = proc
    rt.stack_status = "running"
    log(
        f"serial watch: escalating to boot-wait ({dev_id}) pid={proc.pid} "
        "— power OFF TNC 10s then ON while script runs (DTR held high)"
    )
    broadcast(state, f"EVENT device={dev_id} serial=boot-wait-escalate")


def backend_needs_open(backend: Optional[DeviceBackend]) -> bool:
    if backend is None:
        return True
    return backend.status in BACKEND_POLL_OPEN_STATUSES


def open_backend(state: DaemonState, dev_id: str) -> bool:
    rt = state.devices.get(dev_id)
    if rt is None or not backend_enabled(state, dev_id):
        if rt is not None:
            rt.link_status = "n/a"
        return False
    if rt.backend is not None and rt.backend.status not in BACKEND_RETRY_STATUSES:
        return rt.backend.status in ("open", "ready")
    if (
        rt.backend is not None
        and rt.backend.status in SERIAL_REPAIR_STATUSES
        and rt.prep_done
    ):
        return rt.backend.status in ("open", "ready", "error-host", "error-kiss")
    if rt.backend is not None and rt.backend.status != "closed":
        rt.backend.close()
        rt.backend = None
    backend = create_backend(
        rt.cfg,
        str(ROOT),
        lambda line, d=dev_id: on_backend_rx(state, d, line),
        log,
        prefix=str(PREFIX) if PREFIX else None,
    )
    if not backend.open():
        rt.backend = backend
        rt.link_status = backend.status
        return False
    rt.backend = backend
    rt.link_status = backend.status
    return True


def close_backend(state: DaemonState, dev_id: str) -> None:
    rt = state.devices.get(dev_id)
    if rt is None or rt.backend is None:
        return
    rt.backend.close()
    rt.link_status = rt.backend.status
    rt.backend = None


def attach_backend_session(state: DaemonState, dev_id: str) -> bool:
    if not backend_enabled(state, dev_id):
        return True
    rt = state.devices[dev_id]
    if backend_needs_open(rt.backend):
        if not open_backend(state, dev_id):
            return False
    assert rt.backend is not None
    ok = rt.backend.attach_session(state.cfg.callerid)
    rt.link_status = rt.backend.status
    return ok


def detach_backend_session(state: DaemonState, dev_id: str) -> None:
    rt = state.devices.get(dev_id)
    if rt is None or rt.backend is None:
        return
    rt.backend.detach_session()
    rt.link_status = rt.backend.status


def attach_all_sessions(state: DaemonState) -> bool:
    ok = True
    for dev_id in enabled_device_ids(state):
        if backend_enabled(state, dev_id):
            if not attach_backend_session(state, dev_id):
                ok = False
    return ok


def detach_all_sessions(state: DaemonState) -> None:
    for dev_id in enabled_device_ids(state):
        detach_backend_session(state, dev_id)


def backend_enabled(state: DaemonState, dev_id: str) -> bool:
    if not state.cfg.serial_enabled:
        return False
    rt = state.devices.get(dev_id)
    if rt is None:
        return False
    kind = rt.cfg.backend_type
    return kind in ("kiss-serial", "baycom-kiss", "kiss-raw-serial", "crdop-tcp")


def aggregate_stack_status(state: DaemonState) -> str:
    if not state.devices:
        return "stopped"
    statuses = {rt.stack_status for rt in state.devices.values()}
    if "running" in statuses:
        return "running"
    if any(s.startswith("error") for s in statuses):
        return "error"
    if statuses == {"ready"} or statuses == {"stopped"}:
        return next(iter(statuses))
    if "ready" in statuses:
        return "ready"
    return "running" if "running" in statuses else "stopped"


def aggregate_link_status(state: DaemonState) -> str:
    if not state.devices:
        return "n/a"
    if len(state.devices) == 1:
        rt = next(iter(state.devices.values()))
        return backend_serial_label(rt.backend) if rt.backend is not None else rt.link_status
    parts: list[str] = []
    for dev_id in sorted(state.devices):
        rt = state.devices[dev_id]
        st = backend_serial_label(rt.backend) if rt.backend is not None else rt.link_status
        parts.append(f"{dev_id}={st}")
    return ",".join(parts)


def status_line(state: DaemonState) -> str:
    c = state.cfg
    dev_list = ",".join(enabled_device_ids(state))
    selected = state.selected_device or c.default_device or c.device
    return (
        f"STATUS hardware={c.hardware} device={selected} devices={dev_list} "
        f"mode={c.mode} callerid={c.callerid} callid={c.callid} "
        f"ax25_ui={'on' if c.ax25_ui else 'off'} "
        f"connected={'yes' if state.connected else 'no'} "
        f"stack={aggregate_stack_status(state)} serial={aggregate_link_status(state)}"
    )


def broadcast(state: DaemonState, line: str, skip: Optional[socket.socket] = None) -> None:
    payload = (line + "\n").encode("utf-8")
    dead: list[socket.socket] = []
    with state.lock:
        for sock in state.clients:
            if sock is skip:
                continue
            try:
                sock.sendall(payload)
            except OSError:
                dead.append(sock)
        for sock in dead:
            state.clients.discard(sock)


def send_line(sock: socket.socket, line: str) -> None:
    sock.sendall((line + "\n").encode("utf-8"))


def start_device_stack(state: DaemonState, dev_id: str) -> None:
    if uses_inline_tnc_prep(state, dev_id):
        prep_inline_serial_device(state, dev_id)
        return
    rt = state.devices[dev_id]
    ctl = ctl_path(ROOT, PREFIX, _EXE)
    if not ctl.is_file():
        rt.stack_status = "error-no-ctl"
        return
    hw = device_hardware(state, dev_id)
    dev_cfg = rt.cfg
    ctl_device = dev_id
    if (dev_cfg.backend_type or "") == "baycom-kiss":
        ctl_device = baycom_ctl_device_id(dev_cfg)
    args = [
        str(ctl),
        "start",
        "--mode",
        state.cfg.mode,
        "--hardware",
        hw,
        "--device",
        ctl_device,
    ]
    kind = dev_cfg.backend_type or ""
    if kind == "baycom-kiss":
        explicit = dev_cfg.baycom_ini or ""
        resolved = resolve_baycom_ini(dev_id, ROOT, PREFIX, explicit)
        if resolved:
            args.extend(["--baycom-ini", str(resolved)])
    env = os.environ.copy()
    env["MAX25_MODE"] = state.cfg.mode
    if hw == "tncs" and state.cfg.stack_recover_only:
        env["MAX25_TNC_PREP"] = "recover"
    workdir = str(ROOT if (ROOT / "plugins").is_dir() else (PREFIX or ROOT))
    try:
        proc = subprocess.Popen(
            args,
            cwd=workdir,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        log(f"stack start failed ({dev_id}): {exc}")
        rt.stack_status = "error"
        return
    rt.stack_proc = proc
    rt.stack_status = "running"
    log(f"stack started pid={proc.pid} ({hw}/{dev_id})")


def start_stacks(state: DaemonState) -> None:
    """Start per-device stacks; one baycom-pr-ctl per shared baycom_ini."""
    started_baycom_ini: dict[str, str] = {}
    for dev_id in enabled_device_ids(state):
        rt = state.devices[dev_id]
        kind = rt.cfg.backend_type or ""
        if uses_inline_tnc_prep(state, dev_id):
            prep_inline_serial_device(state, dev_id)
            continue
        if kind == "baycom-kiss":
            explicit = rt.cfg.baycom_ini or ""
            resolved = resolve_baycom_ini(dev_id, ROOT, PREFIX, explicit)
            ini_key = str(resolved) if resolved else ""
            if ini_key and ini_key in started_baycom_ini:
                primary = started_baycom_ini[ini_key]
                primary_rt = state.devices[primary]
                rt.stack_proc = primary_rt.stack_proc
                rt.stack_status = primary_rt.stack_status
                log(f"stack shared with {primary} ({dev_id}, ini={ini_key})")
                continue
        start_device_stack(state, dev_id)
        if kind == "baycom-kiss":
            explicit = rt.cfg.baycom_ini or ""
            resolved = resolve_baycom_ini(dev_id, ROOT, PREFIX, explicit)
            if resolved:
                started_baycom_ini[str(resolved)] = dev_id


def stop_device_stack(state: DaemonState, dev_id: str) -> None:
    close_backend(state, dev_id)
    rt = state.devices[dev_id]
    proc = rt.stack_proc
    if proc is not None and proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except OSError:
            proc.terminate()
    rt.stack_proc = None
    rt.stack_status = "stopped"
    hw = device_hardware(state, dev_id)
    ctl = ctl_path(ROOT, PREFIX, _EXE)
    if ctl.is_file():
        workdir = str(ROOT if (ROOT / "plugins").is_dir() else (PREFIX or ROOT))
        stop_args = [str(ctl), "stop", "--hardware", hw, "--device", dev_id]
        kind = rt.cfg.backend_type or ""
        if kind == "baycom-kiss":
            explicit = rt.cfg.baycom_ini or ""
            resolved = resolve_baycom_ini(dev_id, ROOT, PREFIX, explicit)
            if resolved:
                stop_args.extend(["--baycom-ini", str(resolved)])
        subprocess.run(
            stop_args,
            cwd=workdir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def stop_stacks(state: DaemonState) -> None:
    for dev_id in list(state.devices):
        stop_device_stack(state, dev_id)
    log("all stacks stopped")


def poll_device_stack(state: DaemonState, dev_id: str) -> None:
    rt = state.devices[dev_id]
    proc = rt.stack_proc
    if proc is None:
        return
    rc = proc.poll()
    if rc is None:
        return
    rt.stack_proc = None
    if rc == 0:
        rt.stack_status = "ready"
        log(f"stack boot-wait finished ({dev_id}) rc={rc}")
        if backend_enabled(state, dev_id):
            open_backend(state, dev_id)
            backend = rt.backend
            stabilize = getattr(backend, "stabilize_session", None) if backend else None
            if stabilize is not None:
                ok = stabilize(state.cfg.callerid, force=False)
                rt.prep_done = True
                rt.link_status = backend.status
                rt.inline_repair_failures = 0
                if ok:
                    log(f"serial post boot-wait OK ({dev_id})")
                    if state.connected:
                        attach_backend_session(state, dev_id)
                else:
                    log(
                        f"serial post boot-wait deferred ({dev_id}) "
                        f"status={backend.status}"
                    )
    else:
        rt.stack_status = f"error-rc{rc}"
        log(f"stack boot-wait failed ({dev_id}) rc={rc}")


def poll_stacks(state: DaemonState) -> None:
    for dev_id in enabled_device_ids(state):
        poll_device_stack(state, dev_id)
    retry_pending_backends(state)


def retry_pending_backends(state: DaemonState) -> None:
    """Re-attach KISS PTY/serial when stack is up but the link was not ready yet."""
    for dev_id in enabled_device_ids(state):
        if not backend_enabled(state, dev_id):
            continue
        rt = state.devices[dev_id]
        if rt.stack_status not in ("ready", "stopped"):
            continue
        if not backend_needs_open(rt.backend):
            continue
        open_backend(state, dev_id)


def poll_serial_stability(state: DaemonState) -> None:
    """Periodic TNC health probe + software recovery (no power cycle)."""
    cfg = state.cfg
    if not cfg.serial_watch:
        return
    now = time.time()
    if state.started_at and now - state.started_at < cfg.serial_watch_startup_grace:
        return
    for dev_id in enabled_device_ids(state):
        if device_backend_kind(state, dev_id) != "kiss-serial":
            continue
        rt = state.devices[dev_id]
        if rt.stack_proc is not None and rt.stack_proc.poll() is None:
            continue
        if (
            not uses_inline_tnc_prep(state, dev_id)
            and cfg.stack_recover_only
            and rt.stack_status.startswith("error")
            and rt.stack_proc is None
            and now - rt.last_stack_retry >= cfg.stack_retry_interval
        ):
            rt.last_stack_retry = now
            log(f"serial watch: stack retry recover-only ({dev_id})")
            start_device_stack(state, dev_id)
            continue
        if not backend_enabled(state, dev_id):
            continue
        backend = rt.backend
        force = backend is not None and backend.status in SERIAL_REPAIR_STATUSES
        due = now - rt.last_watch >= cfg.serial_watch_interval
        if not force and not due:
            continue
        if backend is None:
            if backend_needs_open(None):
                open_backend(state, dev_id)
                backend = rt.backend
            if backend is None:
                continue
        if now - rt.last_repair < cfg.serial_repair_cooldown and not force:
            continue
        if backend.status == "ready" and not force:
            if due:
                rt.last_watch = now
            continue
        stabilize = getattr(backend, "stabilize_session", None)
        if stabilize is None:
            continue
        rt.last_watch = now
        rt.last_repair = now
        ok = stabilize(state.cfg.callerid, force=force)
        rt.link_status = backend.status
        if ok:
            rt.inline_repair_failures = 0
            if force:
                log(f"serial watch: repaired ({dev_id})")
                broadcast(state, f"EVENT device={dev_id} serial=ready")
        else:
            log(f"serial watch: repair failed ({dev_id}) status={backend.status}")
            if (
                uses_inline_tnc_prep(state, dev_id)
                and backend.status == "error-host"
                and cfg.serial_bootwait_escalate
            ):
                rt.inline_repair_failures += 1
                if (
                    rt.inline_repair_failures >= cfg.serial_bootwait_escalate_after
                    and now - rt.last_bootwait_escalate >= cfg.serial_bootwait_escalate_cooldown
                ):
                    rt.last_bootwait_escalate = now
                    rt.inline_repair_failures = 0
                    escalate_to_bootwait_stack(state, dev_id)
                elif rt.inline_repair_failures >= cfg.serial_bootwait_escalate_after:
                    log(
                        f"serial watch: boot-wait escalate cooldown ({dev_id}) "
                        f"— manual: stacks/tncs/{dev_id}-boot-wait.sh"
                    )
            if backend.status in ("error-io", "error-open", "error-no-device"):
                close_backend(state, dev_id)
                if open_backend(state, dev_id) and state.connected:
                    attach_backend_session(state, dev_id)


def format_tx(state: DaemonState, text: str) -> str:
    if state.cfg.ax25_ui:
        return f"[AX25 UI {state.cfg.callerid}>{state.cfg.callid}] {text}"
    return text


def resolve_selected_device(state: DaemonState) -> Optional[str]:
    dev_id = state.selected_device
    if dev_id in state.devices:
        return dev_id
    ids = enabled_device_ids(state)
    return ids[0] if ids else None


def device_line(state: DaemonState, dev_id: str) -> str:
    rt = state.devices[dev_id]
    link = backend_serial_label(rt.backend) if rt.backend is not None else rt.link_status
    hw = device_hardware(state, dev_id)
    backend = rt.cfg.backend_type or "auto"
    enabled = "yes" if rt.cfg.enabled else "no"
    return (
        f"DEVICE id={dev_id} hardware={hw} backend={backend} serial={link} "
        f"stack={rt.stack_status} enabled={enabled}"
    )


def handle_command(state: DaemonState, sock: socket.socket, line: str) -> None:
    line = line.strip("\r\n")
    if not line:
        return
    upper = line.upper()

    if upper == "PING":
        send_line(sock, "OK")
        return

    if upper == "GET STATUS":
        send_line(sock, status_line(state))
        send_line(sock, "OK")
        return

    if upper == "GET DEVICES":
        for dev_id in sorted(state.devices):
            send_line(sock, device_line(state, dev_id))
        send_line(sock, "OK")
        return

    if upper.startswith("SET DEVICE ") or upper.startswith("SELECT DEVICE "):
        prefix = "SET DEVICE " if upper.startswith("SET DEVICE ") else "SELECT DEVICE "
        dev_id = line[len(prefix) :].strip()
        if dev_id not in state.devices:
            send_line(sock, f"ERR unknown device: {dev_id}")
            return
        state.selected_device = dev_id
        state.cfg.device = dev_id
        send_line(sock, "OK")
        return

    if upper.startswith("SET CALLERID "):
        value = line[13:].strip().upper()
        if not valid_callsign(value):
            send_line(sock, "ERR invalid CALLERID")
            return
        state.cfg.callerid = value
        send_line(sock, "OK")
        return

    if upper.startswith("SET CALLID "):
        value = line[11:].strip().upper()
        if not valid_callsign(value):
            send_line(sock, "ERR invalid CALLID")
            return
        state.cfg.callid = value
        send_line(sock, "OK")
        return

    if upper.startswith("SET AX25_UI "):
        flag = line[12:].strip().lower()
        if flag in ("on", "yes", "1", "true"):
            state.cfg.ax25_ui = True
        elif flag in ("off", "no", "0", "false"):
            state.cfg.ax25_ui = False
        else:
            send_line(sock, "ERR ax25_ui on|off")
            return
        send_line(sock, "OK")
        return

    if upper == "CONNECT":
        if not attach_all_sessions(state):
            send_line(sock, "ERR link not ready")
            return
        state.connected = True
        send_line(sock, "EVENT connected")
        send_line(sock, "OK")
        return

    if upper == "DISCONNECT":
        detach_all_sessions(state)
        state.connected = False
        send_line(sock, "EVENT disconnected")
        send_line(sock, "OK")
        return

    if upper.startswith("MONITOR "):
        flag = line[8:].strip().lower()
        state.monitor_only = flag in ("on", "yes", "1", "true")
        send_line(sock, "OK")
        return

    if upper.startswith("BAN "):
        value = line[4:].strip().upper()
        if not valid_callsign(value):
            send_line(sock, "ERR invalid callsign")
            return
        try:
            state.bans.add(value)
        except OSError as exc:
            send_line(sock, f"ERR ban save failed: {exc}")
            return
        send_line(sock, "OK")
        return

    if upper.startswith("UNBAN "):
        value = line[6:].strip().upper()
        if not valid_callsign(value):
            send_line(sock, "ERR invalid callsign")
            return
        try:
            if not state.bans.remove(value):
                send_line(sock, "ERR not banned")
                return
        except OSError as exc:
            send_line(sock, f"ERR ban save failed: {exc}")
            return
        send_line(sock, "OK")
        return

    if upper == "BANS":
        for entry in state.bans.list():
            send_line(sock, f"BAN {entry}")
        send_line(sock, "OK")
        return

    if upper.startswith("SEND "):
        if state.monitor_only:
            send_line(sock, "ERR monitor-only")
            return
        if not state.connected:
            send_line(sock, "ERR not connected")
            return
        dev_id = resolve_selected_device(state)
        if dev_id is None:
            send_line(sock, "ERR no device configured")
            return
        payload = line[5:]
        framed = format_tx(state, payload)
        rt = state.devices[dev_id]
        if backend_enabled(state, dev_id):
            if rt.backend is None or rt.backend.status != "ready":
                send_line(sock, "ERR link not ready")
                return
            ok, display = rt.backend.transmit(
                state.cfg.callerid,
                state.cfg.callid,
                payload,
                state.cfg.ax25_ui,
            )
            if not ok and hasattr(rt.backend, "stabilize_session"):
                log(f"serial watch: tx retry after repair ({dev_id})")
                if rt.backend.stabilize_session(state.cfg.callerid, force=True):
                    rt.link_status = rt.backend.status
                    ok, display = rt.backend.transmit(
                        state.cfg.callerid,
                        state.cfg.callid,
                        payload,
                        state.cfg.ax25_ui,
                    )
            if not ok:
                send_line(sock, f"ERR {display}")
                return
            framed = f"device={dev_id} {display}"
        log(f"tx {dev_id}: {framed}")
        send_line(sock, f"RX {framed}")
        broadcast(state, f"RX {framed}", skip=sock)
        send_line(sock, "OK")
        return

    send_line(sock, f"ERR unknown command: {line.split()[0]}")


def tcp_auth_ok(sock: socket.socket, expected: str, timeout: float = 30.0) -> bool:
    if not expected:
        return True
    send_line(sock, "AUTH required")
    sock.settimeout(timeout)
    buf = b""
    try:
        while True:
            try:
                chunk = sock.recv(4096)
            except socket.timeout:
                return False
            if not chunk:
                return False
            buf += chunk
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                try:
                    line = raw.decode("utf-8").strip("\r")
                except UnicodeDecodeError:
                    return False
                if not line:
                    continue
                if line.upper().startswith("AUTH "):
                    supplied = line[5:]
                    return supplied == expected
                return False
    finally:
        sock.settimeout(300.0)


def client_thread(state: DaemonState, sock: socket.socket, from_tcp: bool) -> None:
    sock.settimeout(300.0)
    buf = b""
    try:
        if from_tcp and state.cfg.tcp_password:
            if not tcp_auth_ok(sock, state.cfg.tcp_password):
                send_line(sock, "ERR auth failed")
                return
        send_line(sock, "OK")
        send_line(sock, status_line(state))
        while True:
            try:
                chunk = sock.recv(4096)
            except socket.timeout:
                continue
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                try:
                    line = raw.decode("utf-8")
                except UnicodeDecodeError:
                    send_line(sock, "ERR invalid utf-8")
                    continue
                handle_command(state, sock, line)
    except OSError:
        pass
    finally:
        with state.lock:
            state.clients.discard(sock)
        try:
            sock.close()
        except OSError:
            pass


def serve(state: DaemonState, listeners: list[tuple[socket.socket, bool]]) -> None:
    running = True

    def on_signal(_signum, _frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    if state.cfg.auto_start:
        start_stacks(state)

    state.started_at = time.time()

    device_lines: list[tuple[str, str, str]] = []
    for dev_id in enabled_device_ids(state):
        rt = state.devices[dev_id]
        link = backend_serial_label(rt.backend) if rt.backend is not None else rt.link_status
        device_lines.append((dev_id, rt.stack_status, link))

    emit_startup_complete(
        device_lines=device_lines,
        tcp_host=state.cfg.tcp_host,
        tcp_port=state.cfg.tcp_port,
        unix_socket=state.cfg.unix_socket,
    )

    while running:
        poll_stacks(state)
        poll_serial_stability(state)
        socks = [lsock for lsock, _ in listeners]
        rlist, _, _ = select.select(socks, [], [], 1.0)
        for lsock, from_tcp in listeners:
            if lsock not in rlist:
                continue
            try:
                client, _addr = lsock.accept()
            except OSError:
                continue
            client.setblocking(True)
            with state.lock:
                state.clients.add(client)
            threading.Thread(
                target=client_thread,
                args=(state, client, from_tcp),
                daemon=True,
            ).start()

    stop_stacks(state)
    for lsock, _ in listeners:
        lsock.close()
    if state.cfg.unix_socket:
        try:
            os.unlink(state.cfg.unix_socket)
        except FileNotFoundError:
            pass


def make_listeners(cfg: DaemonConfig) -> list[tuple[socket.socket, bool]]:
    listeners: list[tuple[socket.socket, bool]] = []

    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp.bind((cfg.tcp_host, cfg.tcp_port))
    tcp.listen(32)
    tcp.setblocking(False)
    listeners.append((tcp, True))

    if cfg.unix_socket:
        sock_path = Path(cfg.unix_socket)
        try:
            sock_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            fallback = Path("/tmp/max25/modem.sock")
            log(f"unix {cfg.unix_socket} unavailable, using {fallback}")
            cfg.unix_socket = str(fallback)
            sock_path = fallback
            try:
                sock_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError:
                log("unix socket disabled (no writable path)")
                cfg.unix_socket = ""
                return listeners
        try:
            os.unlink(cfg.unix_socket)
        except FileNotFoundError:
            pass
        except OSError:
            pass
        unix = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            unix.bind(cfg.unix_socket)
        except OSError as exc:
            log(f"unix socket {cfg.unix_socket} skipped ({exc})")
            unix.close()
        else:
            try:
                os.chmod(cfg.unix_socket, 0o660)
            except OSError:
                pass
            unix.listen(32)
            unix.setblocking(False)
            listeners.append((unix, False))

    return listeners


def main(argv: Optional[list[str]] = None) -> int:
    if not max25d_supported():
        log(f"max25d is not supported on {sys.platform}")
        return 1

    parser = argparse.ArgumentParser(description=f"MAX25 daemon ({platform_label()})")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=None,
        help="Path to max25d.ini",
    )
    parser.add_argument(
        "--no-stack",
        action="store_true",
        help="Do not auto-start hardware stack",
    )
    parser.add_argument(
        "--tcp-port",
        type=int,
        default=None,
        help="Override TCP listen port",
    )
    parser.add_argument(
        "--no-serial",
        action="store_true",
        help="Disable KISS serial bridge (loopback SEND only)",
    )
    parser.add_argument(
        "--session",
        choices=("tmux", "screen"),
        metavar="BACKEND",
        help="Re-exec via max25d-session (detach in tmux/screen); use max25d-session attach",
    )
    args = parser.parse_args(argv)

    if args.session:
        session_sh = ROOT / "scripts" / "max25d-session.sh"
        if not session_sh.is_file():
            session_sh = Path(PREFIX) / "bin" / "max25d-session" if PREFIX else session_sh
        if not session_sh.is_file():
            LOGGER.error(
                "max25d-session not found — install scripts/max25d-session.sh or use tmux/screen manually",
                area="session",
            )
            return 1
        cmd = [str(session_sh), "start", f"--{args.session}"]
        if args.config:
            cmd.extend(["-c", str(args.config)])
        os.execv(cmd[0], cmd)

    cfg = load_config(args.config)
    if args.no_stack:
        cfg.auto_start = False
    if args.tcp_port is not None:
        cfg.tcp_port = args.tcp_port
    if args.no_serial:
        cfg.serial_enabled = False

    if cfg.modular_tcp.enabled and cfg.modular_tcp.role == "main":
        svc = ModularTcpMainService(cfg.modular_tcp, cfg.tcp_host, cfg.tcp_port, log)
        svc.start()
        log(
            f"modular TCP/IP Servers Service — Main '{cfg.modular_tcp.service_name}' "
            f"({len(cfg.modular_tcp.secondaries)} secondaries)"
        )
        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            pass
        finally:
            svc.stop()
        return 0

    state = DaemonState(cfg=cfg, bans=BanList(cfg.bans_file))
    init_device_runtimes(state)
    emit_startup_banner(
        config_path=cfg.config_path or None,
        cfg=cfg,
        devices=cfg.devices,
        tested_fn=registry_tested,
    )
    listeners = make_listeners(cfg)
    try:
        serve(state, listeners)
    except KeyboardInterrupt:
        stop_stacks(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
