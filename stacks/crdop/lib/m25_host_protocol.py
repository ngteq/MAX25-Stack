"""
MAX25 native host protocol for SoftModem / audio-dummy (design freeze).

Payload on data channel = AX.25 UI body **without** HDLC/FCS (same as KISS DATA).
Control channel = line-oriented ASCII commands (M25-family, not ARDOP FEC/ARQ).
"""
from __future__ import annotations

import socket
import threading
from typing import Callable, Optional

# KISS-compatible data semantics; control is text lines ending in \\n
DEFAULT_CTRL_PORT = 8515
DEFAULT_DATA_PORT = 8516

CmdFn = Callable[[str], str]
DataRxFn = Callable[[bytes], None]


class M25SoftModemHost:
    """Minimal TCP host for bench / audio-dummy (ctrl + data ports)."""

    def __init__(
        self,
        ctrl_port: int = DEFAULT_CTRL_PORT,
        data_port: int = DEFAULT_DATA_PORT,
        on_data_tx: Optional[Callable[[bytes], str]] = None,
    ) -> None:
        self.ctrl_port = ctrl_port
        self.data_port = data_port
        self._on_data_tx = on_data_tx or (lambda _b: "OK")
        self._stop = threading.Event()
        self._ctrl_srv: Optional[socket.socket] = None
        self._data_srv: Optional[socket.socket] = None
        self._threads: list[threading.Thread] = []
        self._mycall = "NOCALL-0"
        self._listen = True

    def start(self) -> None:
        self._ctrl_srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._ctrl_srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._ctrl_srv.bind(("127.0.0.1", self.ctrl_port))
        self._ctrl_srv.listen(4)
        self._data_srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._data_srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._data_srv.bind(("127.0.0.1", self.data_port))
        self._data_srv.listen(4)
        self._stop.clear()
        for target, name in ((self._accept_ctrl, "ctrl"), (self._accept_data, "data")):
            t = threading.Thread(target=target, name=f"m25-host-{name}", daemon=True)
            t.start()
            self._threads.append(t)

    def stop(self) -> None:
        self._stop.set()
        for srv in (self._ctrl_srv, self._data_srv):
            if srv is not None:
                try:
                    srv.close()
                except OSError:
                    pass
        self._ctrl_srv = None
        self._data_srv = None

    def _accept_ctrl(self) -> None:
        assert self._ctrl_srv is not None
        while not self._stop.is_set():
            try:
                self._ctrl_srv.settimeout(0.5)
                conn, _ = self._ctrl_srv.accept()
            except (OSError, socket.timeout):
                continue
            threading.Thread(
                target=self._ctrl_session,
                args=(conn,),
                daemon=True,
            ).start()

    def _ctrl_session(self, conn: socket.socket) -> None:
        buf = b""
        try:
            conn.settimeout(0.5)
            while not self._stop.is_set():
                try:
                    chunk = conn.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    raw, buf = buf.split(b"\n", 1)
                    line = raw.decode("ascii", errors="replace").strip()
                    if not line:
                        continue
                    reply = self._handle_cmd(line)
                    conn.sendall((reply + "\n").encode("ascii"))
        finally:
            conn.close()

    def _handle_cmd(self, line: str) -> str:
        parts = line.split()
        cmd = parts[0].upper() if parts else ""
        if cmd == "INITIALIZE":
            return "OK"
        if cmd == "PROTOCOLMODE" and len(parts) > 1 and parts[1].upper() == "KISS":
            return "OK"
        if cmd == "MYCALL" and len(parts) > 1:
            self._mycall = parts[1].upper()
            return "OK"
        if cmd == "LISTEN":
            self._listen = len(parts) < 2 or parts[1].upper() in ("TRUE", "1", "ON", "YES")
            return "OK"
        if cmd == "PING":
            return "OK"
        if cmd == "STATUS":
            return f"STATUS ready mycall={self._mycall}"
        return "ERR unknown command"

    def _accept_data(self) -> None:
        assert self._data_srv is not None
        while not self._stop.is_set():
            try:
                self._data_srv.settimeout(0.5)
                conn, _ = self._data_srv.accept()
            except (OSError, socket.timeout):
                continue
            threading.Thread(
                target=self._data_session,
                args=(conn,),
                daemon=True,
            ).start()

    def _data_session(self, conn: socket.socket) -> None:
        try:
            payload = conn.recv(4096)
            if payload:
                reply = self._on_data_tx(payload)
                conn.sendall(reply.encode("ascii", errors="replace"))
        finally:
            conn.close()
