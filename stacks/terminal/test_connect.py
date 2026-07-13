#!/usr/bin/env python3
"""TCP connect smoke test for max25-terminal --probe."""
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DAEMON = ROOT / "stacks/daemon/max25d"
INI = ROOT / "share/max25/max25d.ini.example"


def terminal_binary() -> Path:
    import os

    env = os.environ.get("MAX25_TERMINAL")
    if env:
        return Path(env)
    for candidate in (
        ROOT / "build/bin/max25-terminal",
        ROOT / "stacks/terminal/max25-terminal",
    ):
        if candidate.is_file():
            return candidate
    return ROOT / "build/bin/max25-terminal"


def free_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def main() -> int:
    terminal = terminal_binary()
    if not terminal.is_file():
        print(
            f"FAIL: max25-terminal missing — run cmake --build build --target max25-terminal "
            f"(looked for {terminal})",
            file=sys.stderr,
        )
        return 1

    port = free_port()
    proc = subprocess.Popen(
        [str(DAEMON), "--no-stack", "-c", str(INI), "--tcp-port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.6)
    try:
        out = subprocess.check_output(
            [str(terminal), "-T", "-H", "127.0.0.1", "-p", str(port), "--probe"],
            text=True,
            timeout=10,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        proc.terminate()
        proc.wait(timeout=5)
        print(f"FAIL: terminal probe: {exc}", file=sys.stderr)
        return 1
    finally:
        proc.terminate()
        proc.wait(timeout=5)

    if "STATUS hardware=" not in out or "callerid=" not in out:
        print(f"FAIL: unexpected probe output: {out!r}", file=sys.stderr)
        return 1

    print("OK: max25-terminal TCP probe")
    return 0


if __name__ == "__main__":
    sys.exit(main())
