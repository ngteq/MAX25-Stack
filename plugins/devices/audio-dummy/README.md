# Device: audio-dummy (acoustic bench)

**Status:** `active` — development/test device for on-host acoustic signal evaluation.

## Purpose

Main **dummy device** for Bell 202 AFSK without RF:

- **loopback** — full DSP encode/decode in process (CI default)
- **alsa** — capture from sound card, sniff/decode live
- **host** — TCP to `audio-dummyd` (M25 KISS host protocol, ports 8520/8521)

## Tools

```bash
# Internal loopback (no hardware):
stacks/crdop/tools/max25-signal-sniffer --loopback

# ALSA capture sniff:
stacks/crdop/tools/max25-signal-sniffer -D plughw:1,0 -t 3

# Calibration tones (mark 1200 Hz / space 2200 Hz):
stacks/crdop/tools/max25-signal-sniffer -D plughw:1,0 --mark -t 1
stacks/crdop/tools/max25-signal-sniffer -D plughw:1,0 --space -t 1
```

## max25d

```ini
[devices]
audio-dummy = audio:loopback

[device.audio-dummy]
mode = loopback   ; loopback | alsa | host
; capture = plughw:1,0
; playback = plughw:1,0
; sample_rate = 48000
; host_port = 8520
```

Docs: [docs/CRDOP.md](../../../docs/CRDOP.md)
