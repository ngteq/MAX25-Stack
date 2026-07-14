#!/usr/bin/env python3
"""Data-quality window — CALLID match, timed passes, configurable min % good."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reporting_quality import (  # noqa: E402
    DataQualityTracker,
    RxOutcome,
    classify_rx_line,
)

T0 = 1_000_000.0
WIN = 20


def test_classify_good_callid() -> None:
    assert classify_rx_line("[AX25 UI DG1ABC>QST] 73", "QST") == RxOutcome.GOOD


def test_classify_bad_callid() -> None:
    assert classify_rx_line("[AX25 UI DG1ABC>CB-0] 73", "QST") == RxOutcome.BAD


def test_classify_incomplete_ax25() -> None:
    assert classify_rx_line("[AX25 UI DG1ABC>QST", "QST") == RxOutcome.BAD


def test_classify_voice_noise_ignored() -> None:
    assert classify_rx_line("[CRDOP RX soft-crdop] hiss", "QST") == RxOutcome.IGNORE


def test_classify_crdop_ax25_good() -> None:
    line = "[CRDOP AX25 UI CB-0>QST] ping"
    assert classify_rx_line(line, "QST") == RxOutcome.GOOD


def _close_pass(q: DataQualityTracker, index: int, start: float = T0) -> None:
    q.tick(start + (index + 1) * WIN + 1)


def test_pass_window_max_twenty_seconds() -> None:
    q = DataQualityTracker(passes_required=3, min_good_percent=50, pass_window_sec=20)
    q.record(RxOutcome.GOOD, T0 + 1)
    q.tick(T0 + 19)
    assert len(q.passes) == 0
    _close_pass(q, 0)
    assert list(q.passes) == ["good"]


def test_three_passes_fifty_percent() -> None:
    q = DataQualityTracker(passes_required=3, min_good_percent=50, pass_window_sec=20)
    q.record(RxOutcome.GOOD, T0 + 1)
    _close_pass(q, 0)
    q.record(RxOutcome.BAD, T0 + 20 + 1)
    _close_pass(q, 1)
    assert q.data_error_valid(reporting_enabled=True) is False
    q.record(RxOutcome.GOOD, T0 + 40 + 1)
    _close_pass(q, 2)
    assert q.data_error_valid(reporting_enabled=True) is True


def test_three_passes_below_fifty_percent() -> None:
    q = DataQualityTracker(passes_required=3, min_good_percent=50, pass_window_sec=20)
    q.record(RxOutcome.BAD, T0 + 1)
    _close_pass(q, 0)
    q.record(RxOutcome.BAD, T0 + 21)
    _close_pass(q, 1)
    q.record(RxOutcome.GOOD, T0 + 41)
    _close_pass(q, 2)
    assert q.data_error_valid(reporting_enabled=True) is False


def test_ignore_does_not_consume_pass() -> None:
    q = DataQualityTracker(passes_required=3, min_good_percent=50, pass_window_sec=20)
    q.record(RxOutcome.IGNORE, T0 + 1)
    _close_pass(q, 0)
    assert len(q.passes) == 0
    q.record(RxOutcome.GOOD, T0 + 21)
    _close_pass(q, 1)
    q.record(RxOutcome.GOOD, T0 + 41)
    _close_pass(q, 2)
    q.record(RxOutcome.GOOD, T0 + 61)
    _close_pass(q, 3)
    assert q.data_error_valid(reporting_enabled=True) is True
    assert q.voice_activity is True


def test_silent_window_counts_as_bad() -> None:
    q = DataQualityTracker(passes_required=1, min_good_percent=50, pass_window_sec=20)
    q.current.started_at = T0
    _close_pass(q, 0)
    assert list(q.passes) == ["bad"]


def test_max_cycle_seconds() -> None:
    q = DataQualityTracker(passes_required=3, pass_window_sec=20)
    assert q.max_cycle_seconds() == 60


def test_voice_valid_on_activity() -> None:
    q = DataQualityTracker()
    q.record(RxOutcome.IGNORE, T0 + 1)
    assert q.voice_signal_valid(reporting_enabled=True, link_healthy=True) is True


if __name__ == "__main__":
    test_classify_good_callid()
    test_classify_bad_callid()
    test_classify_incomplete_ax25()
    test_classify_voice_noise_ignored()
    test_classify_crdop_ax25_good()
    test_pass_window_max_twenty_seconds()
    test_three_passes_fifty_percent()
    test_three_passes_below_fifty_percent()
    test_ignore_does_not_consume_pass()
    test_silent_window_counts_as_bad()
    test_max_cycle_seconds()
    test_voice_valid_on_activity()
    print("test_reporting_quality: ok")
