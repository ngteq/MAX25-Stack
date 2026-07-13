"""
AFSK demodulator — Bell 202 mark/space discrimination per symbol period.

Uses per-symbol Goertzel energy at 1200 Hz and 2200 Hz (Dire Wolf class approach).
"""
from __future__ import annotations

import math
import struct
from array import array

from bell202_line_code import TONE_MARK, TONE_SPACE, decode_tones_to_bits

_TWO_PI = 2.0 * math.pi


def _goertzel_power(samples: array, freq: float, sample_rate: int) -> float:
    n = len(samples)
    if n < 8:
        return 0.0
    k = int(0.5 + (n * freq) / sample_rate)
    w = _TWO_PI * k / n
    coeff = 2.0 * math.cos(w)
    s0 = s1 = s2 = 0.0
    for x in samples:
        s0 = x + coeff * s1 - s2
        s2 = s1
        s1 = s0
    return s1 * s1 + s2 * s2 - coeff * s1 * s2


class AfskDemodulator:
    def __init__(self, sample_rate: int = 48000, baud: int = 1200) -> None:
        self.sample_rate = sample_rate
        self.baud = baud
        self.samples_per_symbol = sample_rate // baud

    def demodulate_pcm(self, pcm: bytes) -> list[int]:
        """Return mark/space tone sequence from mono S16_LE PCM."""
        count = len(pcm) // 2
        if count < self.samples_per_symbol:
            return []
        samples = array("h")
        samples.frombytes(pcm[: count * 2])
        tones: list[int] = []
        pos = 0
        while pos + self.samples_per_symbol <= len(samples):
            window = samples[pos : pos + self.samples_per_symbol]
            pos += self.samples_per_symbol
            p_mark = _goertzel_power(window, 1200.0, self.sample_rate)
            p_space = _goertzel_power(window, 2200.0, self.sample_rate)
            tones.append(TONE_MARK if p_mark >= p_space else TONE_SPACE)
        return tones

    def demodulate_to_bits(self, pcm: bytes, start_tone: int = TONE_SPACE) -> bytes:
        return decode_tones_to_bits(self.demodulate_pcm(pcm), start_tone=start_tone)
