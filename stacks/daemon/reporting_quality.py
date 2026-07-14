"""RX data-quality window for max25d STATUS error=/voice= reporting."""
from __future__ import annotations

import re
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque, Optional

_AX25_UI_LINE_RE = re.compile(
    r"^\[(?:CRDOP )?AX25 UI ([^>]+)>([^\]]+)\]\s?(.*)$",
    re.DOTALL,
)
_AX25_UI_PARTIAL_RE = re.compile(r"\[AX25 UI ", re.IGNORECASE)
_VOICE_NOISE_LINE_RE = re.compile(
    r"^\[(?:CRDOP RX|AUDIO RX|VOICE)[^\]]*\]",
    re.IGNORECASE,
)


class RxOutcome(str, Enum):
    GOOD = "good"
    BAD = "bad"
    IGNORE = "ignore"


def classify_rx_line(line: str, callid: str) -> RxOutcome:
    """
    Classify an RX display line for data-quality tracking.

    - GOOD: complete AX.25 UI frame whose destination matches configured CALLID.
    - BAD: incomplete AX.25 UI or wrong CALLID (incomplete data counts as error).
    - IGNORE: voice/noise/interference — excluded from data pass statistics.
    """
    text = line.strip()
    if not text:
        return RxOutcome.IGNORE

    match = _AX25_UI_LINE_RE.match(text)
    if match:
        dest = match.group(2).strip().upper()
        expected = callid.strip().upper()
        if not expected or dest != expected:
            return RxOutcome.BAD
        return RxOutcome.GOOD

    if _AX25_UI_PARTIAL_RE.search(text):
        return RxOutcome.BAD

    if _VOICE_NOISE_LINE_RE.match(text):
        return RxOutcome.IGNORE

    return RxOutcome.IGNORE


@dataclass
class _PassWindow:
    good: int = 0
    bad: int = 0
    ignored: bool = False
    started_at: float = 0.0


@dataclass
class DataQualityTracker:
    """
    Rolling pass window: each pass lasts up to pass_window_sec (default 20s).
    passes_required consecutive passes (default 3) form one evaluation cycle
    (3 × max 20s = up to 60s). Voice/noise does not fill a pass slot.
    """

    passes_required: int = 3
    min_good_percent: int = 50
    pass_window_sec: int = 20
    passes: Deque[str] = field(default_factory=deque)
    voice_activity: bool = False
    current: _PassWindow = field(default_factory=_PassWindow)

    def __post_init__(self) -> None:
        if self.passes_required < 1:
            self.passes_required = 1
        if self.min_good_percent < 1:
            self.min_good_percent = 1
        elif self.min_good_percent > 100:
            self.min_good_percent = 100
        if self.pass_window_sec < 1:
            self.pass_window_sec = 1
        elif self.pass_window_sec > 300:
            self.pass_window_sec = 300
        self.passes = deque(maxlen=self.passes_required)

    def _now(self, now: Optional[float]) -> float:
        return time.time() if now is None else now

    def _ensure_window(self, now: float) -> None:
        if self.current.started_at == 0.0:
            self.current.started_at = now

    def _pass_outcome_from_counts(self, good: int, bad: int) -> str:
        if bad > 0:
            return "bad"
        if good > 0:
            return "good"
        return "bad"

    def _finalize_current_pass(self) -> None:
        good = self.current.good
        bad = self.current.bad
        if good == 0 and bad == 0:
            if self.current.ignored:
                return
            self.passes.append("bad")
            return
        self.passes.append(self._pass_outcome_from_counts(good, bad))

    def _roll_window(self, now: float) -> None:
        self._finalize_current_pass()
        self.current = _PassWindow(started_at=now)

    def tick(self, now: Optional[float] = None) -> None:
        """Expire the active pass when pass_window_sec elapsed."""
        ts = self._now(now)
        if self.current.started_at == 0.0:
            return
        if ts - self.current.started_at < self.pass_window_sec:
            return
        self._roll_window(ts)

    def record(self, outcome: RxOutcome, now: Optional[float] = None) -> None:
        ts = self._now(now)
        self.tick(ts)
        self._ensure_window(ts)

        if outcome == RxOutcome.IGNORE:
            self.voice_activity = True
            self.current.ignored = True
            return
        if outcome == RxOutcome.GOOD:
            self.current.good += 1
        elif outcome == RxOutcome.BAD:
            self.current.bad += 1

    def record_bad(self, now: Optional[float] = None) -> None:
        self.record(RxOutcome.BAD, now)

    def good_ratio_percent(self) -> Optional[int]:
        if len(self.passes) < self.passes_required:
            return None
        good = sum(1 for item in self.passes if item == "good")
        total = len(self.passes)
        if total == 0:
            return None
        return (100 * good) // total

    def data_error_valid(self, *, reporting_enabled: bool) -> bool:
        if not reporting_enabled:
            return False
        ratio = self.good_ratio_percent()
        if ratio is None:
            return False
        return ratio >= self.min_good_percent

    def voice_signal_valid(self, *, reporting_enabled: bool, link_healthy: bool) -> bool:
        """
        Voice/noise/disturbance path: when link is healthy and voice activity was
        seen (non-data RX), treat as 100% valid even if the content was noise only.
        """
        if not reporting_enabled:
            return False
        if not link_healthy:
            return False
        if self.voice_activity:
            return True
        return True

    def max_cycle_seconds(self) -> int:
        return self.passes_required * self.pass_window_sec
