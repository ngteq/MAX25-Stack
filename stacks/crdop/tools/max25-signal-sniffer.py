#!/usr/bin/env python3
"""MAX25 signal sniffer — analyze Bell 202 AFSK on ALSA capture or PCM file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIB = ROOT / "stacks" / "crdop" / "lib"
sys.path.insert(0, str(LIB))

from acoustic_engine import AcousticEngine  # noqa: E402
from sound_proxy import SoundConfig, SoundProxy  # noqa: E402


def read_wav_pcm(path: Path) -> bytes:
    import wave

    with wave.open(str(path), "rb") as wf:
        if wf.getsampwidth() != 2 or wf.getnchannels() != 1:
            raise SystemExit("WAV must be mono S16_LE")
        return wf.readframes(wf.getnframes())


def main() -> int:
    ap = argparse.ArgumentParser(description="MAX25 acoustic signal sniffer (Bell 202 1200 bd)")
    ap.add_argument("-D", "--device", default="", help="ALSA capture device (hw: or plughw:)")
    ap.add_argument("-r", "--rate", type=int, default=48000)
    ap.add_argument("-f", "--file", type=Path, help="Read mono S16 WAV instead of ALSA")
    ap.add_argument("-t", "--seconds", type=float, default=2.0, help="ALSA capture duration")
    ap.add_argument("--loopback", action="store_true", help="Internal DSP loopback (no audio hw)")
    ap.add_argument("--mark", action="store_true", help="Play mark calibration tone (1200 Hz)")
    ap.add_argument("--space", action="store_true", help="Play space calibration tone (2200 Hz)")
    args = ap.parse_args()

    cfg = SoundConfig(capture=args.device or "default", sample_rate=args.rate)
    eng = AcousticEngine(sample_rate=args.rate, sound=cfg)

    if args.loopback:
        rep = eng.loopback_self_test()
        print(f"loopback samples={rep.samples} symbols={rep.symbols} transitions={rep.transitions}")
        print(f"mark={rep.mark_ratio:.2%} space={rep.space_ratio:.2%}")
        for line in rep.decode_lines:
            print(line)
        return 0 if rep.decode_lines else 1

    if args.mark:
        eng.play_mark_calibration(args.seconds)
        print(f"played mark tone {args.seconds}s")
        return 0
    if args.space:
        eng.play_space_calibration(args.seconds)
        print(f"played space tone {args.seconds}s")
        return 0

    if args.file:
        pcm = read_wav_pcm(args.file)
    else:
        if not args.device:
            print("error: -D hw:... or --file or --loopback required", file=sys.stderr)
            return 2
        proxy = SoundProxy(cfg)
        proxy.start_capture()
        nbytes = int(args.rate * args.seconds) * 2
        pcm = proxy.read_capture(nbytes)
        proxy.close()

    rep = eng.analyze_pcm(pcm)
    print(f"sniff samples={rep.samples} symbols={rep.symbols} transitions={rep.transitions}")
    print(f"mark={rep.mark_ratio:.2%} space={rep.space_ratio:.2%} frames={len(rep.frames)}")
    for line in rep.decode_lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
