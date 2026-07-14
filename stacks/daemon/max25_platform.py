"""MAX25 host platform — Linux full stack, FreeBSD server + CRDOP/OSS."""
from __future__ import annotations

import os
import sys


def system_name() -> str:
    return sys.platform


def is_linux() -> bool:
    return sys.platform == "linux"


def is_freebsd() -> bool:
    return sys.platform.startswith("freebsd")


def is_bsd() -> bool:
    return sys.platform.startswith(("freebsd", "openbsd", "netbsd", "darwin"))


def max25d_supported() -> bool:
    """Daemon may run (full stack on Linux, server+CRDOP on FreeBSD)."""
    return is_linux() or is_freebsd()


def default_unix_socket() -> str:
    if is_linux():
        return "/run/max25/modem.sock"
    if is_freebsd():
        return "/var/run/max25/modem.sock"
    return "/tmp/max25/modem.sock"


def default_bans_file() -> str:
    if is_linux():
        return "/var/lib/max25/bans.txt"
    return "/var/db/max25/bans.txt"


def supported_device_ids() -> frozenset[str]:
    if is_linux():
        return frozenset(
            {
                "tnc2c",
                "pktnc2",
                "baycom-ser12",
                "baycom-par96",
                "baycom-kiss",
                "baycom-a",
                "baycom-b",
                "soft-crdop",
                "audio-dummy",
            }
        )
    if is_freebsd():
        return frozenset({"soft-crdop", "audio-dummy"})
    return frozenset({"soft-crdop"})


def crdop_audio_backend() -> str:
    """Host audio API for CRDOP sound-proxy."""
    env = os.environ.get("MAX25_AUDIO_BACKEND", "").strip().lower()
    if env in ("alsa", "oss"):
        return env
    if is_linux():
        return "alsa"
    if is_freebsd():
        return "oss"
    return "alsa"


def platform_label() -> str:
    if is_linux():
        return "Linux/KLinux"
    if is_freebsd():
        return "FreeBSD"
    return sys.platform
