"""
Structured stderr logging for max25d — human- and machine-readable lines.

Format:
  max25d [LEVEL] [area] message
  max25d [LEVEL] [area] [device] message

Levels: INFO, OK, WARN, ERROR, EVENT, RECOVERY
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Callable, Optional

PREFIX = "max25d"
DEVICE_TOKENS = ("tnc2c", "pktnc2", "max25e0", "max25e0:bc0", "max25e0:bc1", "baycom-kiss", "soft-crdop")


@dataclass(frozen=True)
class DeviceSummary:
    device_id: str
    backend: str
    hardware: str
    serial: str
    enabled: bool
    tested: bool


class DaemonLogger:
    """Thread-safe enough for max25d (GIL); all lines go to stderr."""

    def __init__(self, emit: Optional[Callable[[str], None]] = None) -> None:
        self._emit = emit or self._default_emit

    @staticmethod
    def _default_emit(line: str) -> None:
        print(line, file=sys.stderr, flush=True)

    def _line(
        self,
        level: str,
        msg: str,
        *,
        area: str = "",
        device: str = "",
    ) -> None:
        parts = [PREFIX, f"[{level}]"]
        if area:
            parts.append(f"[{area}]")
        if device:
            parts.append(f"[{device}]")
        parts.append(msg)
        self._emit(" ".join(parts))

    def info(self, msg: str, *, area: str = "", device: str = "") -> None:
        self._line("INFO", msg, area=area, device=device)

    def ok(self, msg: str, *, area: str = "", device: str = "") -> None:
        self._line("OK", msg, area=area, device=device)

    def warn(self, msg: str, *, area: str = "", device: str = "") -> None:
        self._line("WARN", msg, area=area, device=device)

    def error(self, msg: str, *, area: str = "", device: str = "") -> None:
        self._line("ERROR", msg, area=area, device=device)

    def event(self, msg: str, *, area: str = "", device: str = "") -> None:
        self._line("EVENT", msg, area=area, device=device)

    def recovery(self, msg: str, *, device: str = "") -> None:
        self._line("RECOVERY", msg, area="serial", device=device)

    def _parse_device_prefix(self, text: str) -> tuple[str, str]:
        head, sep, tail = text.partition(":")
        if sep and head in DEVICE_TOKENS:
            return head, tail.strip()
        device = ""
        for token in DEVICE_TOKENS:
            if f"({token})" in text or f" {token})" in text:
                device = token
                break
        return device, text

    def emit_unstructured(self, msg: str) -> None:
        """Map legacy free-form strings to structured levels."""
        device, text = self._parse_device_prefix(msg.strip())
        lower = text.lower()
        if lower.startswith("warning:"):
            self.warn(text[8:].strip(), device=device)
        elif lower.startswith("recovery:"):
            self.recovery(text[9:].strip(), device=device)
        elif " prep ok" in lower or lower.startswith("ok:"):
            self.ok(text, device=device)
        elif any(x in lower for x in ("failed", "error", "fail:")):
            self.error(text, device=device)
        elif lower.startswith("serial watch:"):
            self.info(text, area="watch", device=device)
        elif lower.startswith("serial "):
            self.info(text, area="serial", device=device)
        elif lower.startswith("stack "):
            self.info(text, area="stack", device=device)
        elif lower.startswith("rx ") or lower.startswith("tx "):
            self.event(text, device=device)
        else:
            self.info(text, device=device)

    def banner(self, title: str) -> None:
        self._emit(f"{PREFIX} === {title} ===")

    def section(self, name: str) -> None:
        self._emit(f"{PREFIX} [{name}]")

    def kv(self, key: str, value: str, *, indent: int = 0) -> None:
        pad = "  " * indent
        self._emit(f"{PREFIX} {pad}{key}={value}")


LOGGER = DaemonLogger()


def device_serial_label(dev) -> str:
    """Human-readable serial/KISS path for startup summary."""
    spec = (dev.device_spec or dev.serial_device or "").strip()
    if dev.backend_type == "kiss-serial":
        baud = dev.serial_baud or "?"
        line = (dev.serial_line or "?").upper()
        dtr = dev.serial_dtr_rts or "default"
        kiss = dev.serial_kiss_entry or "default"
        path = spec or dev.serial_device or "?"
        return f"{path} {baud} {line} dtr={dtr} kiss_entry={kiss}"
    if dev.backend_type == "baycom-kiss":
        return f"baycom:{dev.baycom_modem or 'a'} kiss={dev.kiss_link or '?'}"
    if dev.backend_type == "crdop-tcp":
        host = dev.crdop_host or "127.0.0.1"
        port = dev.crdop_port or "?"
        return f"crdop-tcp {host}:{port}"
    if spec:
        return spec
    return dev.backend_type or "auto"


def emit_startup_banner(
    *,
    config_path: Optional[str],
    cfg,
    devices: list,
    tested_fn: Callable[[str], bool],
) -> None:
    LOGGER.banner("MAX25d starting")
    LOGGER.section("config")
    if config_path:
        LOGGER.kv("ini", config_path, indent=1)
    else:
        LOGGER.kv("ini", "(built-in defaults)", indent=1)
    LOGGER.kv("mode", cfg.mode, indent=1)
    LOGGER.kv("default_device", cfg.default_device or cfg.device, indent=1)
    LOGGER.kv("devices", str(len(devices)), indent=1)

    LOGGER.section("network")
    LOGGER.kv("tcp", f"{cfg.tcp_host}:{cfg.tcp_port}", indent=1)
    LOGGER.kv("unix", cfg.unix_socket or "(disabled)", indent=1)
    if cfg.tcp_password:
        LOGGER.kv("tcp_auth", "enabled", indent=1)
    else:
        LOGGER.warn("TCP has no password — set tcp_password before exposing LAN", area="security")

    LOGGER.section("modem")
    LOGGER.kv("callerid", cfg.callerid, indent=1)
    LOGGER.kv("callid", cfg.callid, indent=1)
    LOGGER.kv("ax25_ui", "yes" if cfg.ax25_ui else "no", indent=1)
    if cfg.bans_file:
        LOGGER.kv("bans_file", cfg.bans_file, indent=1)

    LOGGER.section("stack")
    LOGGER.kv("auto_start", "yes" if cfg.auto_start else "no", indent=1)
    LOGGER.kv("serial_enabled", "yes" if cfg.serial_enabled else "no", indent=1)
    LOGGER.kv("stack_recover_only", "yes" if cfg.stack_recover_only else "no", indent=1)
    LOGGER.kv("serial_watch", "yes" if cfg.serial_watch else "no", indent=1)
    if cfg.serial_watch:
        LOGGER.kv("serial_watch_interval", f"{cfg.serial_watch_interval}s", indent=1)
        LOGGER.kv("serial_watch_startup_grace", f"{cfg.serial_watch_startup_grace}s", indent=1)
    LOGGER.kv("serial_bootwait_escalate", "yes" if cfg.serial_bootwait_escalate else "no", indent=1)

    LOGGER.section("session")
    LOGGER.kv(
        "detach",
        "max25d --session tmux  |  max25d-session start/attach/stop",
        indent=1,
    )

    LOGGER.section("devices")
    for dev in devices:
        if not dev.enabled:
            LOGGER.kv(
                dev.device_id,
                f"disabled backend={dev.backend_type or 'auto'}",
                indent=1,
            )
            continue
        serial = device_serial_label(dev)
        hw = dev.hardware or cfg.hardware
        tested = tested_fn(dev.device_id)
        note = "" if tested else " — not hardware-validated in CI"
        LOGGER.kv(
            dev.device_id,
            f"{hw} {serial}{note}",
            indent=1,
        )
        if not tested and dev.backend_type == "kiss-serial":
            LOGGER.warn(
                "RF path not CI-validated — verify on hardware before production",
                area="devices",
                device=dev.device_id,
            )


def emit_startup_complete(
    *,
    device_lines: list[tuple[str, str, str]],
    tcp_host: str,
    tcp_port: int,
    unix_socket: str,
) -> None:
    LOGGER.banner("MAX25d ready")
    LOGGER.section("listen")
    LOGGER.kv("tcp", f"{tcp_host}:{tcp_port}", indent=1)
    LOGGER.kv("unix", unix_socket or "(disabled)", indent=1)
    if device_lines:
        LOGGER.section("device_status")
        for dev_id, stack_st, link_st in device_lines:
            LOGGER.kv(dev_id, f"stack={stack_st} link={link_st}", indent=1)
    LOGGER.info(
        "attach: max25-terminal -U /run/max25/modem.sock  |  "
        "detach session: max25d-session attach",
        area="operator",
    )
