#!/usr/bin/env python3
"""
max25-ws-proxy — WebSocket forward-proxy to max25d M25/1 TCP (loopback only).

Accepts RFC6455 text frames and forwards bytes to max25d without protocol
translation. Optional upstream AUTH uses [upstream] tcp_password from config.

Intended behind a TLS reverse proxy; see stacks/web/share/reverse-proxy/.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import configparser
import hashlib
import logging
import os
import signal
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
LOG = logging.getLogger("max25-ws-proxy")


@dataclass
class ProxyConfig:
    bind: str = "127.0.0.1"
    port: int = 7326
    path: str = "/max25"
    upstream_host: str = "127.0.0.1"
    upstream_port: int = 7325
    tcp_password: str = ""
    max_connections: int = 10


def load_config(path: Optional[str]) -> ProxyConfig:
    cfg = ProxyConfig()
    if not path:
        return cfg

    ini = configparser.ConfigParser()
    ini.read(path)
    if ini.has_section("proxy"):
        sec = ini["proxy"]
        cfg.bind = sec.get("bind", cfg.bind)
        cfg.port = sec.getint("port", fallback=cfg.port)
        cfg.path = sec.get("path", cfg.path)
        cfg.max_connections = sec.getint("max_connections", fallback=cfg.max_connections)
    if ini.has_section("upstream"):
        sec = ini["upstream"]
        cfg.upstream_host = sec.get("host", cfg.upstream_host)
        cfg.upstream_port = sec.getint("port", fallback=cfg.upstream_port)
        cfg.tcp_password = sec.get("tcp_password", cfg.tcp_password)
    return cfg


def resolve_config_path(explicit: Optional[str]) -> Optional[str]:
    if explicit:
        return explicit
    env = os.environ.get("MAX25_WEB_PROXY_INI")
    if env:
        return env
    for candidate in (
        "/etc/max25/web-proxy.ini",
    ):
        if Path(candidate).is_file():
            return candidate
    return None


async def read_http_request(reader: asyncio.StreamReader) -> tuple[str, dict[str, str]]:
    request_line = (await reader.readline()).decode("ascii", errors="replace").strip()
    if not request_line:
        raise ConnectionError("empty request")
    headers: dict[str, str] = {}
    while True:
        line = (await reader.readline()).decode("ascii", errors="replace").strip()
        if line == "":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return request_line, headers


def ws_accept_key(sec_key: str) -> str:
    digest = hashlib.sha1((sec_key + WS_GUID).encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


async def ws_handshake(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    expected_path: str,
) -> None:
    request_line, headers = await read_http_request(reader)
    parts = request_line.split()
    if len(parts) < 2:
        raise ConnectionError("bad request line")
    path = parts[1].split("?", 1)[0]
    if path != expected_path:
        raise ConnectionError(f"path mismatch: {path!r}")

    upgrade = headers.get("upgrade", "").lower()
    connection = headers.get("connection", "").lower()
    sec_key = headers.get("sec-websocket-key", "")
    if upgrade != "websocket" or "upgrade" not in connection or not sec_key:
        raise ConnectionError("not a websocket upgrade")

    accept = ws_accept_key(sec_key)
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n"
        "\r\n"
    )
    writer.write(response.encode("ascii"))
    await writer.drain()


async def ws_read_frame(reader: asyncio.StreamReader) -> tuple[int, bytes]:
    header = await reader.readexactly(2)
    b1, b2 = header[0], header[1]
    opcode = b1 & 0x0F
    masked = bool(b2 & 0x80)
    length = b2 & 0x7F
    if length == 126:
        length = struct.unpack("!H", await reader.readexactly(2))[0]
    elif length == 127:
        length = struct.unpack("!Q", await reader.readexactly(8))[0]
    mask = await reader.readexactly(4) if masked else b""
    payload = await reader.readexactly(length) if length else b""
    if masked:
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return opcode, payload


async def ws_write_text(writer: asyncio.StreamWriter, text: bytes) -> None:
    length = len(text)
    header = bytearray([0x81])  # FIN + text frame
    if length < 126:
        header.append(length)
    elif length < 65536:
        header.append(126)
        header.extend(struct.pack("!H", length))
    else:
        header.append(127)
        header.extend(struct.pack("!Q", length))
    writer.write(bytes(header) + text)
    await writer.drain()


async def ws_write_pong(writer: asyncio.StreamWriter, payload: bytes) -> None:
    length = len(payload)
    header = bytearray([0x8A])  # FIN + pong
    if length < 126:
        header.append(length)
    else:
        header.append(126)
        header.extend(struct.pack("!H", length))
    writer.write(bytes(header) + payload)
    await writer.drain()


async def read_line(reader: asyncio.StreamReader) -> Optional[str]:
    line = await reader.readline()
    if not line:
        return None
    text = line.decode("utf-8", errors="replace")
    if text.endswith("\n"):
        text = text[:-1]
    if text.endswith("\r"):
        text = text[:-1]
    return text


async def upstream_handshake(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    tcp_password: str,
) -> list[str]:
    """Complete max25d connect handshake; return lines to forward to the client."""
    first = await read_line(reader)
    if first is None:
        raise ConnectionError("upstream closed during handshake")

    forwarded: list[str] = []
    if first == "AUTH required":
        if not tcp_password:
            forwarded.append(first)
            return forwarded
        writer.write(f"AUTH {tcp_password}\n".encode("utf-8"))
        await writer.drain()
        reply = await read_line(reader)
        if reply != "OK":
            raise ConnectionError(f"upstream auth failed: {reply!r}")
        forwarded.append("OK")
        status = await read_line(reader)
        if status is None:
            raise ConnectionError("upstream closed after auth")
        forwarded.append(status)
        return forwarded

    if first != "OK":
        raise ConnectionError(f"unexpected upstream greeting: {first!r}")
    forwarded.append(first)
    status = await read_line(reader)
    if status is None:
        raise ConnectionError("upstream closed after OK")
    forwarded.append(status)
    return forwarded


async def pipe_tcp_to_ws(
    tcp_reader: asyncio.StreamReader,
    ws_writer: asyncio.StreamWriter,
) -> None:
    while True:
        chunk = await tcp_reader.read(4096)
        if not chunk:
            break
        await ws_write_text(ws_writer, chunk)


async def pipe_ws_to_tcp(
    ws_reader: asyncio.StreamReader,
    ws_writer: asyncio.StreamWriter,
    tcp_writer: asyncio.StreamWriter,
) -> None:
    while True:
        opcode, payload = await ws_read_frame(ws_reader)
        if opcode == 0x8:
            break
        if opcode == 0x9:
            await ws_write_pong(ws_writer, payload)
            continue
        if opcode == 0xA:
            continue
        if opcode != 0x1:
            LOG.warning("ignoring non-text websocket frame opcode=%s", opcode)
            continue
        tcp_writer.write(payload)
        await tcp_writer.drain()


class ConnectionLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.active = 0

    def try_acquire(self) -> bool:
        if self.active >= self.limit:
            return False
        self.active += 1
        return True

    def release(self) -> None:
        if self.active > 0:
            self.active -= 1


async def handle_client(
    ws_reader: asyncio.StreamReader,
    ws_writer: asyncio.StreamWriter,
    cfg: ProxyConfig,
    limiter: ConnectionLimiter,
) -> None:
    peer = ws_writer.get_extra_info("peername")
    if not limiter.try_acquire():
        LOG.warning("connection limit reached; rejecting %s", peer)
        ws_writer.close()
        await ws_writer.wait_closed()
        return

    try:
        await ws_handshake(ws_reader, ws_writer, cfg.path)
    except Exception as exc:
        LOG.warning("handshake failed from %s: %s", peer, exc)
        limiter.release()
        ws_writer.close()
        await ws_writer.wait_closed()
        return

    LOG.info("websocket accepted from %s", peer)
    tcp_reader: Optional[asyncio.StreamReader] = None
    tcp_writer: Optional[asyncio.StreamWriter] = None
    try:
        tcp_reader, tcp_writer = await asyncio.open_connection(
            cfg.upstream_host, cfg.upstream_port
        )
        lines = await upstream_handshake(tcp_reader, tcp_writer, cfg.tcp_password)
        for line in lines:
            await ws_write_text(ws_writer, (line + "\n").encode("utf-8"))

        tcp_task = asyncio.create_task(pipe_tcp_to_ws(tcp_reader, ws_writer))
        ws_task = asyncio.create_task(pipe_ws_to_tcp(ws_reader, ws_writer, tcp_writer))
        done, pending = await asyncio.wait(
            {tcp_task, ws_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
    except Exception as exc:
        LOG.warning("session ended for %s: %s", peer, exc)
        try:
            await ws_write_text(ws_writer, f"\n[proxy error: {exc}]\n".encode("utf-8"))
        except Exception:
            pass
    finally:
        if tcp_writer is not None:
            tcp_writer.close()
            try:
                await tcp_writer.wait_closed()
            except Exception:
                pass
        ws_writer.close()
        try:
            await ws_writer.wait_closed()
        except Exception:
            pass
        limiter.release()
        LOG.info("websocket closed for %s", peer)


async def run_server(cfg: ProxyConfig) -> None:
    limiter = ConnectionLimiter(cfg.max_connections)
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, cfg, limiter),
        host=cfg.bind,
        port=cfg.port,
    )
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
    LOG.info(
        "listening on %s path=%s -> %s:%s",
        addrs,
        cfg.path,
        cfg.upstream_host,
        cfg.upstream_port,
    )
    async with server:
        await server.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(description="MAX25 WebSocket forward-proxy to max25d TCP")
    parser.add_argument("-c", "--config", help="web-proxy.ini path")
    parser.add_argument("--bind", help="override [proxy] bind")
    parser.add_argument("--port", type=int, help="override [proxy] port")
    parser.add_argument("--path", help="override [proxy] path")
    parser.add_argument("--upstream-host", help="override [upstream] host")
    parser.add_argument("--upstream-port", type=int, help="override [upstream] port")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    config_path = resolve_config_path(args.config)
    cfg = load_config(config_path)
    if args.bind:
        cfg.bind = args.bind
    if args.port:
        cfg.port = args.port
    if args.path:
        cfg.path = args.path
    if args.upstream_host:
        cfg.upstream_host = args.upstream_host
    if args.upstream_port:
        cfg.upstream_port = args.upstream_port

    if config_path:
        LOG.info("config: %s", config_path)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, loop.stop)

    try:
        loop.run_until_complete(run_server(cfg))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
