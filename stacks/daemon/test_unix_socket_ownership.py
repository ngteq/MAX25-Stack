#!/usr/bin/env python3
"""Unix socket path ownership — do not orphan a live max25d listen FD."""
from __future__ import annotations

import os
import socket
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from max25d import unlink_unix_if_ours, unix_path_id, unix_path_is_live  # noqa: E402


def test_unix_path_live_and_owned_unlink() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path_a = os.path.join(tmp, "a.sock")
        path_b = os.path.join(tmp, "b.sock")
        assert unix_path_is_live(path_a) is False

        srv_a = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv_a.bind(path_a)
        srv_a.listen(1)
        id_a = unix_path_id(path_a)
        assert id_a is not None
        assert unix_path_is_live(path_a) is True

        srv_b = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv_b.bind(path_b)
        srv_b.listen(1)
        id_b = unix_path_id(path_b)
        assert id_b is not None and id_b != id_a

        # Foreign exit must not unlink the peer's rebound path.
        unlink_unix_if_ours(path_b, id_a)
        assert os.path.exists(path_b)

        # Owner exit unlinks only matching inode.
        unlink_unix_if_ours(path_a, id_a)
        assert not os.path.exists(path_a)

        # Stale bind_id after peer rebound: no unlink.
        os.unlink(path_b)
        srv_b.close()
        srv_b2 = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv_b2.bind(path_b)
        srv_b2.listen(1)
        unlink_unix_if_ours(path_b, id_b)  # old id
        assert os.path.exists(path_b)

        srv_a.close()
        srv_b2.close()
        unlink_unix_if_ours(path_b, unix_path_id(path_b))
        assert not os.path.exists(path_b)

    print("PASS: unix socket ownership")


if __name__ == "__main__":
    test_unix_path_live_and_owned_unlink()
