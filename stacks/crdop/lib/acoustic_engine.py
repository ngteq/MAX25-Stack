"""
Acoustic bench engine — modulate/demodulate/sniff without RF.

Used by audio-dummy device and max25-signal-sniffer.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_LIB = Path(__file__).resolve().parent
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from afsk_demodulator import AfskDemodulator  # noqa: E402
from afsk_modulator import AfskModulator  # noqa: E402
from bell202_line_code import TONE_MARK, TONE_SPACE  # noqa: E402
from hdlc_codec import build_hdlc_frame, parse_hdlc_stream  # noqa: E402
from sound_proxy import SoundConfig, create_sound_proxy  # noqa: E402

_ROOT = Path(__file__).resolve().parents[3]
_DAEMON = _ROOT / "stacks" / "daemon"
if str(_DAEMON) not in sys.path:
    sys.path.insert(0, str(_DAEMON))
from ax25_codec import ax25_build_ui, ax25_parse_ui  # noqa: E402


@dataclass
class SniffReport:
    samples: int = 0
    symbols: int = 0
    mark_ratio: float = 0.0
    space_ratio: float = 0.0
    transitions: int = 0
    frames: list[bytes] = field(default_factory=list)
    decode_lines: list[str] = field(default_factory=list)


class AcousticEngine:
    def __init__(
        self,
        sample_rate: int = 48000,
        baud: int = 1200,
        sound: Optional[SoundConfig] = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.baud = baud
        self.mod = AfskModulator(sample_rate, baud)
        self.demod = AfskDemodulator(sample_rate, baud)
        self.sound = sound or SoundConfig(sample_rate=sample_rate)

    def encode_ax25_ui(self, src: str, dst: str, text: str) -> bytes:
        body = ax25_build_ui(src, dst, text.encode("utf-8"))
        # strip FCS for KISS-style host body, then build on-air HDLC
        if len(body) >= 2:
            body = body[:-2]
        hdlc = build_hdlc_frame(body)
        return self.mod.modulate_bits(hdlc)

    def analyze_pcm(self, pcm: bytes) -> SniffReport:
        rep = SniffReport(samples=len(pcm) // 2)
        tones = self.demod.demodulate_pcm(pcm)
        rep.symbols = len(tones)
        if not tones:
            return rep
        marks = sum(1 for t in tones if t == TONE_MARK)
        rep.mark_ratio = marks / len(tones)
        rep.space_ratio = 1.0 - rep.mark_ratio
        rep.transitions = sum(1 for i in range(1, len(tones)) if tones[i] != tones[i - 1])
        raw_bits = self.demod.demodulate_to_bits(pcm)
        for frame in parse_hdlc_stream(raw_bits):
            rep.frames.append(frame)
            parsed = ax25_parse_ui(frame)
            if parsed:
                src, dst, info = parsed
                rep.decode_lines.append(f"[AX25 UI {src}>{dst}] {info.decode('utf-8', errors='replace')}")
        return rep

    def loopback_self_test(self, src: str = "TST-0", dst: str = "QST") -> SniffReport:
        pcm = self.encode_ax25_ui(src, dst, "LOOP")
        return self.analyze_pcm(pcm)

    def play_mark_calibration(self, seconds: float = 1.0) -> None:
        create_sound_proxy(self.sound).play_pcm(self.mod.steady_tone(TONE_MARK, seconds))

    def play_space_calibration(self, seconds: float = 1.0) -> None:
        create_sound_proxy(self.sound).play_pcm(self.mod.steady_tone(TONE_SPACE, seconds))
