#!/usr/bin/env python3
"""CI-safe smoke: max25-ws-proxy forwards M25/1 PING (no UART / no stack)."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import os
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
ROOT = Path(__file__).resolve().parents[3]
PROXY = ROOT / "stacks/web/proxy/max25-ws-proxy.py"
DAEMON = ROOT / "stacks/daemon/max25d"


def ws_accept(sec_key: str) -> str:
    digest = hashlib.sha1((sec_key + WS_GUID).encode()).digest()
    return base64.b64encode(digest).decode()


def free_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def wait_for_unix(path: str, proc: subprocess.Popen[str], timeout: float = 8.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        if Path(path).exists():
            try:
                probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                probe.settimeout(0.25)
                probe.connect(path)
                probe.close()
                return True
            except OSError:
                pass
        time.sleep(0.05)
    return False


def wait_for_port(port: int, proc: subprocess.Popen[str], timeout: float = 8.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        try:
            probe = socket.create_connection(("127.0.0.1", port), timeout=0.25)
            probe.close()
            return True
        except OSError:
            time.sleep(0.05)
    return False


def drain_stderr(proc: subprocess.Popen[str]) -> str:
    if not proc.stderr:
        return ""
    try:
        return proc.stderr.read() or ""
    except OSError:
        return ""


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


def stop(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=2)


def main() -> int:
    if not DAEMON.is_file():
        print(f"max25_web_smoke: missing daemon launcher {DAEMON}", file=sys.stderr)
        return 1
    if not PROXY.is_file():
        print(f"max25_web_smoke: missing proxy {PROXY}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="max25-web-smoke-") as tmp:
        sock = str(Path(tmp) / "modem.sock")
        tcp_port = free_port()
        proxy_port = free_port()
        ini = Path(tmp) / "max25d.ini"
        proxy_ini = Path(tmp) / "web-proxy.ini"
        # /dev/null: CI must not open a real UART (ttyS0 is flaky / absent).
        ini.write_text(
            "[daemon]\nmode=standalone\nhardware=tncs\ndevice=tnc2c\n"
            "[network]\ntcp_host=127.0.0.1\n"
            f"tcp_port={tcp_port}\nunix_socket={sock}\ntcp_password=\n"
            "[devices]\ntnc2c=/dev/null\n",
            encoding="utf-8",
        )
        proxy_ini.write_text(
            f"[proxy]\nbind=127.0.0.1\nport={proxy_port}\npath=/max25\n"
            f"[upstream]\nhost=127.0.0.1\nport={tcp_port}\ntcp_password=\n",
            encoding="utf-8",
        )

        daemon = subprocess.Popen(
            [
                str(DAEMON),
                "--no-stack",
                "--no-serial",
                "-c",
                str(ini),
                "--tcp-port",
                str(tcp_port),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        proxy: subprocess.Popen[str] | None = None
        try:
            if not wait_for_unix(sock, daemon):
                err = drain_stderr(daemon)
                print(
                    f"max25_web_smoke: max25d unix sock not ready: {err.strip()}",
                    file=sys.stderr,
                )
                return 1
            if not wait_for_port(tcp_port, daemon):
                err = drain_stderr(daemon)
                print(
                    f"max25_web_smoke: max25d TCP not listening: {err.strip()}",
                    file=sys.stderr,
                )
                return 1

            proxy = subprocess.Popen(
                [sys.executable, str(PROXY), "-c", str(proxy_ini)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            if not wait_for_port(proxy_port, proxy):
                err = drain_stderr(proxy)
                print(
                    f"max25_web_smoke: proxy not listening: {err.strip()}",
                    file=sys.stderr,
                )
                return 1

            deadline = time.time() + 8
            last_exc: Exception | None = None
            while time.time() < deadline:
                if daemon.poll() is not None or proxy.poll() is not None:
                    break
                try:
                    out = asyncio.run(
                        ws_exchange("127.0.0.1", proxy_port, "/max25", "PING\n")
                    )
                    if "OK" in out or "PONG" in out or "STATUS" in out:
                        print("max25_web_smoke: ok")
                        return 0
                    last_exc = RuntimeError(f"unexpected reply: {out!r}")
                except (
                    ConnectionRefusedError,
                    OSError,
                    RuntimeError,
                    asyncio.IncompleteReadError,
                ) as exc:
                    last_exc = exc
                    time.sleep(0.15)

            d_err = drain_stderr(daemon)
            p_err = drain_stderr(proxy) if proxy else ""
            detail = f"last={last_exc!r}" if last_exc else "no M25/1 response"
            print(f"max25_web_smoke: failed — {detail}", file=sys.stderr)
            if d_err.strip():
                print(f"max25d stderr:\n{d_err.rstrip()}", file=sys.stderr)
            if p_err.strip():
                print(f"proxy stderr:\n{p_err.rstrip()}", file=sys.stderr)
            return 1
        finally:
            if proxy is not None:
                stop(proxy)
            stop(daemon)


if __name__ == "__main__":
    sys.exit(main())
