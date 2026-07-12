#!/usr/bin/env python3
"""Offline smoke test for max25d M25/1 protocol."""
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DAEMON = ROOT / "stacks/daemon/max25d"
INI = ROOT / "share/max25/max25d.ini.example"


class LineReader:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.buf = b""

    def read(self, timeout: float = 5.0) -> str:
        self.sock.settimeout(timeout)
        while b"\n" not in self.buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise RuntimeError("connection closed")
            self.buf += chunk
        line, self.buf = self.buf.split(b"\n", 1)
        return line.decode("utf-8")


def free_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def main() -> int:
    port = free_port()
    proc = subprocess.Popen(
        [sys.executable, str(DAEMON), "--no-stack", "-c", str(INI), "--tcp-port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(0.6)
    try:
        sock = socket.create_connection(("127.0.0.1", port), timeout=3)
    except OSError as exc:
        proc.terminate()
        proc.wait(timeout=3)
        print(f"FAIL: connect: {exc}", file=sys.stderr)
        return 1

    reader = LineReader(sock)
    try:
        assert reader.read() == "OK"
        status = reader.read()
        assert status.startswith("STATUS ")

        sock.sendall(b"SET CALLERID DG1ABC\n")
        assert reader.read() == "OK"

        sock.sendall(b"CONNECT\n")
        assert reader.read() == "EVENT connected"
        assert reader.read() == "OK"

        sock.sendall(b"SEND 73\n")
        rx = reader.read()
        assert rx.startswith("RX ")
        assert reader.read() == "OK"

        sock.sendall(b"GET STATUS\n")
        st = reader.read()
        assert "callerid=DG1ABC" in st
        assert reader.read() == "OK"

        print("OK: max25d protocol smoke")
        return 0
    finally:
        sock.close()
        proc.terminate()
        proc.wait(timeout=5)


if __name__ == "__main__":
    sys.exit(main())
