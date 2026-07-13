#!/usr/bin/env python3
"""Audio dummy daemon — M25 host TCP + acoustic DSP bench for max25d."""
from __future__ import annotations

import argparse
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / "stacks" / "crdop" / "lib"
sys.path.insert(0, str(LIB))

from acoustic_engine import AcousticEngine  # noqa: E402
from m25_host_protocol import DEFAULT_CTRL_PORT, DEFAULT_DATA_PORT, M25SoftModemHost  # noqa: E402
from sound_proxy import SoundConfig  # noqa: E402

_DAEMON = ROOT / "stacks" / "daemon"
sys.path.insert(0, str(_DAEMON))
from ax25_codec import ax25_build_ui  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="MAX25 audio-dummy device daemon")
    ap.add_argument("--ctrl-port", type=int, default=DEFAULT_CTRL_PORT)
    ap.add_argument("--data-port", type=int, default=DEFAULT_DATA_PORT)
    ap.add_argument("-D", "--capture", default="")
    ap.add_argument("-P", "--playback", default="")
    ap.add_argument("-r", "--rate", type=int, default=48000)
    args = ap.parse_args()

    sound = SoundConfig(
        capture=args.capture or "default",
        playback=args.playback or args.capture or "default",
        sample_rate=args.rate,
    )
    eng = AcousticEngine(sample_rate=args.rate, sound=sound)
    rx_lock = threading.Lock()
    last_rx: list[str] = []

    def on_tx(payload: bytes) -> str:
        if len(payload) < 16:
            return "ERR short payload"
        pcm = eng.mod.modulate_bits(payload)
        eng.sound.playback = sound.playback
        from sound_proxy import SoundProxy

        SoundProxy(sound).play_pcm(pcm)
        return "OK"

    host = M25SoftModemHost(args.ctrl_port, args.data_port, on_data_tx=on_tx)
    host.start()
    print(
        f"audio-dummyd ctrl=:{args.ctrl_port} data=:{args.data_port} rate={args.rate}",
        flush=True,
    )
    try:
        while True:
            threading.Event().wait(3600.0)
    except KeyboardInterrupt:
        host.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
