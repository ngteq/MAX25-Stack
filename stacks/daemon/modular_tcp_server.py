"""
Modular TCP/IP Servers Service — central Main + Secondary routing for MAX25.

Public name in docs: "modular TCP/IP Servers Service".
Main instance accepts M25/1 clients and forwards sessions to Secondary max25d peers.
"""
from __future__ import annotations

import configparser
import selectors
import socket
import threading
from dataclasses import dataclass, field
from typing import Callable, Optional


LogFn = Callable[[str], None]


@dataclass
class SecondaryEndpoint:
    name: str
    host: str
    port: int


@dataclass
class ModularTcpConfig:
    enabled: bool = False
    role: str = "standalone"  # standalone | main | secondary
    service_name: str = "modular-tcp-server"
    instance_id: str = ""
    secondaries: list[SecondaryEndpoint] = field(default_factory=list)
    connect_timeout: float = 5.0
    buffer_size: int = 65536


def load_modular_tcp(cp: configparser.ConfigParser) -> ModularTcpConfig:
    cfg = ModularTcpConfig()
    if not cp.has_section("modular_tcp"):
        return cfg
    sec = cp["modular_tcp"]
    cfg.enabled = sec.get("enabled", "no").strip().lower() in ("1", "yes", "true", "on")
    cfg.role = sec.get("role", cfg.role).strip().lower() or cfg.role
    cfg.service_name = sec.get("service_name", cfg.service_name).strip() or cfg.service_name
    cfg.instance_id = sec.get("instance_id", cfg.instance_id).strip()
    if cp.has_option("modular_tcp", "connect_timeout"):
        cfg.connect_timeout = float(cp.get("modular_tcp", "connect_timeout"))
    if cp.has_section("modular_tcp.secondaries"):
        for key in cp.options("modular_tcp.secondaries"):
            raw = cp.get("modular_tcp.secondaries", key).strip()
            if not raw:
                continue
            host, _, port_s = raw.partition(":")
            port = int(port_s or "7326")
            cfg.secondaries.append(SecondaryEndpoint(name=key.strip(), host=host.strip(), port=port))
    if cfg.enabled and cfg.role == "main" and not cfg.secondaries:
        # Legacy comma list: secondaries = host:port,host:port
        raw = sec.get("secondaries", "").strip()
        if raw:
            for idx, item in enumerate(x.strip() for x in raw.split(",") if x.strip()):
                host, _, port_s = item.partition(":")
                cfg.secondaries.append(
                    SecondaryEndpoint(
                        name=f"secondary-{idx + 1}",
                        host=host.strip(),
                        port=int(port_s or "7326"),
                    )
                )
    return cfg


class ModularTcpMainService:
    """Bidirectional relay: operator client <-> Secondary max25d M25/1."""

    def __init__(
        self,
        cfg: ModularTcpConfig,
        listen_host: str,
        listen_port: int,
        log: LogFn,
    ) -> None:
        self.cfg = cfg
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.log = log
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._rr_index = 0
        self._lock = threading.Lock()

    def _pick_secondary(self) -> Optional[SecondaryEndpoint]:
        with self._lock:
            if not self.cfg.secondaries:
                return None
            ep = self.cfg.secondaries[self._rr_index % len(self.cfg.secondaries)]
            self._rr_index += 1
            return ep

    def _relay(self, client: socket.socket, upstream: socket.socket) -> None:
        sel = selectors.DefaultSelector()
        sel.register(client, selectors.EVENT_READ)
        sel.register(upstream, selectors.EVENT_READ)
        try:
            while not self._stop.is_set():
                for key, _ in sel.select(timeout=0.5):
                    sock = key.fileobj
                    assert isinstance(sock, socket.socket)
                    try:
                        data = sock.recv(self.cfg.buffer_size)
                    except OSError:
                        return
                    if not data:
                        return
                    target = upstream if sock is client else client
                    try:
                        target.sendall(data)
                    except OSError:
                        return
        finally:
            sel.close()

    def _handle_client(self, client: socket.socket, addr: tuple[str, int]) -> None:
        ep = self._pick_secondary()
        if ep is None:
            self.log(f"modular_tcp: no secondaries configured — drop {addr}")
            client.close()
            return
        upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream.settimeout(self.cfg.connect_timeout)
        try:
            upstream.connect((ep.host, ep.port))
        except OSError as exc:
            self.log(f"modular_tcp: upstream {ep.name} {ep.host}:{ep.port} failed ({exc})")
            client.close()
            return
        upstream.settimeout(None)
        self.log(f"modular_tcp: {addr} -> {ep.name} {ep.host}:{ep.port}")
        try:
            self._relay(client, upstream)
        finally:
            for s in (client, upstream):
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                s.close()

    def _serve(self) -> None:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self.listen_host, self.listen_port))
        srv.listen(64)
        srv.settimeout(1.0)
        self.log(
            f"modular_tcp: Main service '{self.cfg.service_name}' "
            f"listen {self.listen_host}:{self.listen_port} "
            f"secondaries={len(self.cfg.secondaries)}"
        )
        try:
            while not self._stop.is_set():
                try:
                    client, addr = srv.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                threading.Thread(
                    target=self._handle_client,
                    args=(client, addr),
                    daemon=True,
                ).start()
        finally:
            srv.close()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._serve, name="modular-tcp-main", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None
