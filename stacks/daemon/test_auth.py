#!/usr/bin/env python3
"""TCP auth smoke test for max25d M25/1."""
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DAEMON = ROOT / "stacks/daemon/max25d"
BASE_INI = ROOT / "share/max25/max25d.ini.example"


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
    password = "preview-secret"

    with tempfile.NamedTemporaryFile("w", suffix=".ini", delete=False) as tmp:
        tmp.write(BASE_INI.read_text())
        tmp.write(f"\n[network]\ntcp_password = {password}\n")
        ini_path = Path(tmp.name)

    proc = subprocess.Popen(
        [sys.executable, str(DAEMON), "--no-stack", "-c", str(ini_path), "--tcp-port", str(port)],
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
        assert reader.read() == "AUTH required"

        sock.sendall(b"AUTH wrong\n")
        assert reader.read() == "ERR auth failed"
        sock.close()

        sock = socket.create_connection(("127.0.0.1", port), timeout=3)
        reader = LineReader(sock)
        assert reader.read() == "AUTH required"
        sock.sendall(f"AUTH {password}\n".encode())
        assert reader.read() == "OK"
        status = reader.read()
        assert status.startswith("STATUS ")

        sock.sendall(b"PING\n")
        assert reader.read() == "OK"

        print("OK: max25d TCP auth smoke")
        return 0
    finally:
        try:
            sock.close()
        except OSError:
            pass
        proc.terminate()
        proc.wait(timeout=5)
        ini_path.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
