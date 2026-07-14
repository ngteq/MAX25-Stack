"""
MAX25 sound-proxy — FreeBSD/OSS capture and playback.

Uses `sox` with OSS devices when available; falls back to raw /dev/dsp read/write.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import threading
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class OssSoundConfig:
    capture: str = "/dev/dsp"
    playback: str = "/dev/dsp"
    sample_rate: int = 48000
    channels: int = 1


class OssSoundProxy:
    def __init__(self, cfg: OssSoundConfig) -> None:
        self.cfg = cfg
        self._rec_proc: Optional[subprocess.Popen[bytes]] = None
        self._dsp_fd: Optional[int] = None
        self._stop = threading.Event()
        self._use_sox = shutil.which("sox") is not None

    def _sox_capture_cmd(self) -> list[str]:
        dev = self.cfg.capture
        return [
            "sox",
            "-q",
            "-t",
            "oss",
            dev,
            "-r",
            str(self.cfg.sample_rate),
            "-c",
            str(self.cfg.channels),
            "-b",
            "16",
            "-e",
            "signed-integer",
            "-t",
            "raw",
            "-",
        ]

    def _sox_play_cmd(self) -> list[str]:
        dev = self.cfg.playback
        return [
            "sox",
            "-q",
            "-t",
            "raw",
            "-r",
            str(self.cfg.sample_rate),
            "-c",
            str(self.cfg.channels),
            "-b",
            "16",
            "-e",
            "signed-integer",
            "-",
            "-t",
            "oss",
            dev,
        ]

    def start_capture(self) -> None:
        if self._use_sox:
            self._rec_proc = subprocess.Popen(
                self._sox_capture_cmd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            return
        flags = os.O_RDONLY
        try:
            self._dsp_fd = os.open(self.cfg.capture, flags)
        except OSError as exc:
            raise RuntimeError(f"OSS open {self.cfg.capture}: {exc}") from exc

    def read_capture(self, nbytes: int) -> bytes:
        if self._rec_proc is not None and self._rec_proc.stdout is not None:
            return self._rec_proc.stdout.read(nbytes) or b""
        if self._dsp_fd is not None:
            try:
                return os.read(self._dsp_fd, nbytes) or b""
            except OSError:
                return b""
        return b""

    def play_pcm(self, pcm: bytes) -> None:
        if not pcm:
            return
        if self._use_sox:
            subprocess.run(
                self._sox_play_cmd(),
                input=pcm,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return
        try:
            fd = os.open(self.cfg.playback, os.O_WRONLY)
        except OSError:
            return
        try:
            os.write(fd, pcm)
        finally:
            os.close(fd)

    def sniff_loop(
        self,
        chunk_symbols: int,
        on_pcm: Callable[[bytes], None],
        stop: Optional[threading.Event] = None,
    ) -> None:
        stop_ev = stop or self._stop
        frame_bytes = max(256, (self.cfg.sample_rate // 1200) * 2 * chunk_symbols)
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
        if self._rec_proc is not None and self._rec_proc.poll() is None:
            self._rec_proc.terminate()
            try:
                self._rec_proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                self._rec_proc.kill()
        self._rec_proc = None
        if self._dsp_fd is not None:
            try:
                os.close(self._dsp_fd)
            except OSError:
                pass
            self._dsp_fd = None
