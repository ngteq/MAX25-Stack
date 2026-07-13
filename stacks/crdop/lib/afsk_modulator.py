"""
Continuous-phase AFSK modulator — Bell 202 mark 1200 Hz / space 2200 Hz.
"""
from __future__ import annotations

import math
import struct
from array import array

from bell202_line_code import MARK_HZ, SPACE_HZ, TONE_MARK, encode_bits_to_tones

_TWO_PI = 2.0 * math.pi


class AfskModulator:
  def __init__(self, sample_rate: int = 48000, baud: int = 1200) -> None:
      self.sample_rate = sample_rate
      self.baud = baud
      self._phase = 0.0

  def _tone_freq(self, tone: int) -> float:
      return MARK_HZ if tone == TONE_MARK else SPACE_HZ

  def modulate_bits(self, bits: bytes, start_tone: int = 0) -> bytes:
      """Return mono S16_LE PCM for the given bit stream."""
      tones = encode_bits_to_tones(bits, start_tone=start_tone)
      samples_per_symbol = self.sample_rate // self.baud
      out: array[int] = array("h")
      for tone in tones:
          freq = self._tone_freq(tone)
          step = _TWO_PI * freq / self.sample_rate
          for _ in range(samples_per_symbol):
              sample = int(0.7 * 32767.0 * math.sin(self._phase))
              out.append(sample)
              self._phase += step
              if self._phase >= _TWO_PI:
                  self._phase -= _TWO_PI
      return struct.pack(f"<{len(out)}h", *out)

  def steady_tone(self, tone: int, duration_s: float) -> bytes:
      """Calibration tone (Dire Wolf -x style mark/space hold)."""
      n = int(self.sample_rate * duration_s)
      freq = self._tone_freq(tone)
      step = _TWO_PI * freq / self.sample_rate
      out: array[int] = array("h")
      for _ in range(n):
          out.append(int(0.7 * 32767.0 * math.sin(self._phase)))
          self._phase += step
          if self._phase >= _TWO_PI:
              self._phase -= _TWO_PI
      return struct.pack(f"<{len(out)}h", *out)
