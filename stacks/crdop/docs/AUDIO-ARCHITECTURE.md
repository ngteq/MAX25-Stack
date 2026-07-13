# CRDOP audio architecture — kernel ALSA only

**CRDOP** = **CB/AR Digital Open Protocol** (CB = Citizens Band, AR = Amateur Radio).

MAX25-SoftModem (CRDOP) talks to the radio **through the sound hardware directly**. There is **no PulseAudio**, **no PipeWire default route**, and **no desktop sound server** in the path.

## Stack layers

```
┌─────────────┐   M25/1 TCP    ┌──────────────┐   host TCP   ┌─────────────┐
│  max25d     │ ◄────────────► │ CRDOP modem  │ ◄──────────► │ max25-      │
│  (stack)    │                │ (DSP/AX.25)  │              │ terminal    │
└─────────────┘                └──────┬───────┘              └─────────────┘
                                      │
                              MAX25 sound-proxy
                              (buffer, timing, duplex)
                                      │
                                      ▼
                              libasound (userspace)
                                      │
                                      ▼
                              Linux kernel ALSA
                              (/dev/snd/*, drivers)
                                      │
                                      ▼
                              Sound hardware (USB/PCI codec)
                                      │
                                      ▼
                              Radio interface (line / acoustic)
```

| Layer | Role | Allowed |
|-------|------|---------|
| **max25d** | Device lifecycle, `CrdopTcpBackend`, no audio I/O | — |
| **CRDOP modem** | AFSK encode/decode, AX.25 framing, duplex policy | — |
| **MAX25 sound-proxy** | **Only** audio shim between modem and ALSA — period size, xrun recovery, hw params, PTT timing hooks | MAX25-owned |
| **ALSA userspace** | `snd_pcm_*` on **`hw:` / `plughw:`** devices | Direct libasound |
| **Kernel ALSA** | Driver, DMA, card registry | Required |
| **PulseAudio / PipeWire** | — | **Forbidden** in production path |

The sound-proxy is **not** a second network hop — it is the in-process (or co-process) module that owns ALSA opens and keeps modem timing off the desktop audio stack.

## Why no PulseAudio

PulseAudio and PipeWire insert mixing, resampling, and variable latency between applications and the kernel. CRDOP must:

- Reproduce **exact mark/space frequencies** on playback
- Sample capture with **stable phase** for demodulation
- Meet **tighter deadlines** as baud rises toward 19200

A userspace mixer breaks those guarantees. Operators must bind **card and device explicitly** (`hw:Card,Device` or tested `plughw:`).

## Operator setup

1. Identify hardware: `arecord -l` and `aplay -l` (kernel cards, not `pulse` pseudo-devices).
2. Set INI `[audio] capture` and `playback` to **hardware ALSA names**.
3. Ensure no session steals the device (`pasuspender` / stop PulseAudio on dedicated hosts).
4. Verify loopback before on-air traffic.

Example INI:

```ini
[audio]
backend = alsa-kernel
no_pulse = yes
capture = hw:1,0
playback = hw:1,0
```

Dedicated packet-radio hosts: prefer **single-purpose Linux** without a desktop sound daemon, or `PULSE_SERVER=` / `PIPEWIRE_RUNTIME_DIR=` unset for the `crdop` service unit.

## Development (Eigenentwicklung)

Native CRDOP will implement the sound-proxy in-tree (`include/crdop/sound_proxy.h`). Legacy optional vendor builds used `ALSASound.c` with the same rule: **open ALSA devices directly**.

## See also

- [SOFTMODEM.md](SOFTMODEM.md) — product scope, baud, duplex
- [CONFIG.md](CONFIG.md) — INI keys
- [BUILD.md](BUILD.md) — `libasound2-dev` dependency
