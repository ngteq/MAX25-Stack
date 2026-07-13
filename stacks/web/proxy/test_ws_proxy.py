#!/usr/bin/env python3
"""Smoke test: max25-ws-proxy forwards M25/1 PING to a running max25d."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import os
import signal
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
ROOT = Path(__file__).resolve().parents[3]
PROXY = ROOT / "stacks/web/proxy/max25-ws-proxy.py"
DAEMON = ROOT / "stacks/daemon/max25d.py"


def ws_accept(sec_key: str) -> str:
    digest = hashlib.sha1((sec_key + WS_GUID).encode()).digest()
    return base64.b64encode(digest).decode()


async def ws_exchange(host: str, port: int, path: str, send: str) -> str:
    reader, writer = await asyncio.open_connection(host, port)
    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    )
    writer.write(req.encode())
    await writer.drain()
    status = await reader.readline()
    if b"101" not in status:
        raise RuntimeError(f"upgrade failed: {status!r}")
    while True:
        line = await reader.readline()
        if line in (b"\r\n", b"\n", b""):
            break

    payload = send.encode()
    header = bytes([0x81, len(payload)])
    writer.write(header + payload)
    await writer.drain()

    hdr = await reader.readexactly(2)
    length = hdr[1] & 0x7F
    if length == 126:
        length = struct.unpack("!H", await reader.readexactly(2))[0]
    data = await reader.readexactly(length)
    writer.close()
    await writer.wait_closed()
    return data.decode()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="max25-web-smoke-") as tmp:
        sock = str(Path(tmp) / "modem.sock")
        tcp_port = 17325
        proxy_port = 17326
        ini = Path(tmp) / "max25d.ini"
        proxy_ini = Path(tmp) / "web-proxy.ini"
        ini.write_text(
            f"[daemon]\nmode=standalone\nhardware=tncs\ndevice=tnc2c\n"
            f"[network]\ntcp_host=127.0.0.1\ntcp_port={tcp_port}\n"
            f"unix_socket={sock}\ntcp_password=\n"
            f"[devices]\ntnc2c=/dev/ttyS0\n",
            encoding="utf-8",
        )
        proxy_ini.write_text(
            f"[proxy]\nbind=127.0.0.1\nport={proxy_port}\npath=/max25\n"
            f"[upstream]\nhost=127.0.0.1\nport={tcp_port}\ntcp_password=\n",
            encoding="utf-8",
        )

        daemon = subprocess.Popen(
            [sys.executable, str(DAEMON), "-c", str(ini)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        proxy = subprocess.Popen(
            [sys.executable, str(PROXY), "-c", str(proxy_ini)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.time() + 10
            while time.time() < deadline:
                try:
                    out = asyncio.run(
                        ws_exchange("127.0.0.1", proxy_port, "/max25", "PING\n")
                    )
                    if "OK" in out or "PONG" in out or "STATUS" in out:
                        print("max25_web_smoke: ok")
                        return 0
                except (ConnectionRefusedError, OSError, RuntimeError):
                    time.sleep(0.2)
            print("max25_web_smoke: failed — no M25/1 response", file=sys.stderr)
            return 1
        finally:
            for proc in (proxy, daemon):
                proc.send_signal(signal.SIGTERM)
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()


if __name__ == "__main__":
    sys.exit(main())
