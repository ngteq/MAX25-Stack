"""
MAX25 sound-proxy — host audio capture/playback.

Linux/KLinux: ALSA (arecord/aplay).
FreeBSD: OSS via sound_proxy_oss (sox or /dev/dsp).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Protocol, runtime_checkable


@dataclass
class SoundConfig:
    capture: str = "default"
    playback: str = "default"
    sample_rate: int = 48000
    channels: int = 1
    period_frames: int = 256
    forbid_pulse: bool = True
    backend: str = ""  # alsa | oss — empty = auto from platform


@runtime_checkable
class SoundProxyProto(Protocol):
    def start_capture(self) -> None: ...
    def read_capture(self, nbytes: int) -> bytes: ...
    def play_pcm(self, pcm: bytes) -> None: ...
    def sniff_loop(
        self,
        chunk_symbols: int,
        on_pcm: Callable[[bytes], None],
        stop: Optional[threading.Event] = None,
    ) -> None: ...
    def close(self) -> None: ...


def _detect_backend(cfg: SoundConfig) -> str:
    explicit = (cfg.backend or os.environ.get("MAX25_AUDIO_BACKEND", "")).strip().lower()
    if explicit in ("alsa", "oss"):
        return explicit
    if sys.platform.startswith("freebsd"):
        return "oss"
    return "alsa"


def create_sound_proxy(cfg: SoundConfig) -> SoundProxyProto:
    backend = _detect_backend(cfg)
    if backend == "oss":
        from sound_proxy_oss import OssSoundConfig, OssSoundProxy

        cap = cfg.capture if cfg.capture not in ("", "default") else "/dev/dsp"
        pb = cfg.playback if cfg.playback not in ("", "default") else cap
        return OssSoundProxy(
            OssSoundConfig(
                capture=cap,
                playback=pb,
                sample_rate=cfg.sample_rate,
                channels=cfg.channels,
            )
        )
    return AlsaSoundProxy(cfg)


class AlsaSoundProxy:
    def __init__(self, cfg: SoundConfig) -> None:
        self.cfg = cfg
        self._rec_proc: Optional[subprocess.Popen[bytes]] = None
        self._play_proc: Optional[subprocess.Popen[bytes]] = None
        self._stop = threading.Event()

    def _alsa_env(self) -> dict[str, str]:
        env = os.environ.copy()
        if self.cfg.forbid_pulse:
            env.pop("PULSE_SERVER", None)
            env.pop("PIPEWIRE_RUNTIME_DIR", None)
            env["PULSE_SERVER"] = ""
        return env

    @staticmethod
    def _check_device(name: str) -> None:
        low = name.lower()
        if low in ("default", "pulse", "pipewire") or "pulse" in low or "pipewire" in low:
            raise ValueError(
                f"audio device {name!r} not allowed — use hw: or plughw: (kernel ALSA)"
            )

    def start_capture(self) -> None:
        if not shutil.which("arecord"):
            raise RuntimeError("arecord not found — install alsa-utils")
        self._check_device(self.cfg.capture)
        cmd = [
            "arecord",
            "-q",
            "-D",
            self.cfg.capture,
            "-f",
            "S16_LE",
            "-r",
            str(self.cfg.sample_rate),
            "-c",
            str(self.cfg.channels),
            "-t",
            "raw",
        ]
        self._rec_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=self._alsa_env(),
        )

    def read_capture(self, nbytes: int) -> bytes:
        if self._rec_proc is None or self._rec_proc.stdout is None:
            return b""
        return self._rec_proc.stdout.read(nbytes) or b""

    def play_pcm(self, pcm: bytes) -> None:
        if not pcm:
            return
        if not shutil.which("aplay"):
            raise RuntimeError("aplay not found — install alsa-utils")
        self._check_device(self.cfg.playback)
        cmd = [
            "aplay",
            "-q",
            "-D",
            self.cfg.playback,
            "-f",
            "S16_LE",
            "-r",
            str(self.cfg.sample_rate),
            "-c",
            str(self.cfg.channels),
            "-t",
            "raw",
        ]
        subprocess.run(
            cmd,
            input=pcm,
            check=False,
            env=self._alsa_env(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def sniff_loop(
        self,
        chunk_symbols: int,
        on_pcm: Callable[[bytes], None],
        stop: Optional[threading.Event] = None,
    ) -> None:
        stop_ev = stop or self._stop
        frame_bytes = (self.cfg.sample_rate // 1200) * 2 * chunk_symbols
        self.start_capture()
        try:
            while not stop_ev.is_set():
                chunk = self.read_capture(frame_bytes)
                if not chunk:
                    break
                on_pcm(chunk)
        finally:
            self.close()

    def close(self) -> None:
        self._stop.set()
        for proc in (self._rec_proc, self._play_proc):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    proc.kill()
        self._rec_proc = None
        self._play_proc = None


# Backward-compatible alias
SoundProxy = AlsaSoundProxy
