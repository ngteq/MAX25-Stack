# MAX25-SoftModem — product definition

> **Authoritative rule:** [docs/CRDOP.md](../../../docs/CRDOP.md) · **Doc index:** [INDEX.md](INDEX.md)

## Name and role

- **Product:** MAX25-SoftModem (stack acronym **CRDOP**; plugin id `soft-crdop`)
- **Stack version:** MAX25-Stack **v1.0.0** · **Dev track:** `CUR999` in `$SRC/stacks/crdop/VERSION`
- **Stack:** MainAX25-Stack — **standard** component (built/installed unless `MAX25_BUILD_CRDOP=OFF`)
- **Nature:** Pure MAX25 in-house development — in **development and test phase**, openly documented

## Use like a hardware modem

CRDOP uses the host **sound card IN and OUT** plus a **suitable radio** (or acoustic coupling to existing RF hardware). In `max25d` it registers like any other device backend — operators use the same M25/1 flow (`SET DEVICE`, `CONNECT`, `SEND`).

```
┌──────────┐   line or acoustic    ┌─────────────┐   TCP    ┌─────────┐
│  Radio   │ ◄──────────────────► │ CRDOP/ALSA  │ ◄──────► │ max25d  │
└──────────┘                      └─────────────┘          └─────────┘
                                        │
                                  1200–19200 baud
                                  half or full duplex
```

### Acoustic AX.25 compatibility

On the **acoustic / RF layer**, CRDOP targets **AX.25 Packet Radio** interoperability at the PHY level:

- **1200 baud Bell 202 AFSK** (1200/2200 Hz) — standard VHF/UHF and CB packet class
- **Half- and full-duplex** per radio and audio capability
- **Acoustic or line-level** coupling — valid test and field configuration

CRDOP is an **alternative modem** when the sound card is the RF interface. It does not replace an existing UART/KISS path when that path is already in use.

Interface specification for builders: [HARDWARE-INTERFACE.md](HARDWARE-INTERFACE.md). MAX25-Stack usage: [MAX25-USAGE.md](MAX25-USAGE.md).

## Protocol stack

| Layer | Policy |
|-------|--------|
| On-air / acoustic | AX.25-compatible AFSK tones (1200 baud primary) |
| Host to max25d | MAX25-native TCP control + data (see [PROTOCOL.md](PROTOCOL.md)) |

We study legacy stacks; we implement our own modem and document it for **reproducible hardware builds**.

## Sound path — kernel ALSA only

CRDOP does **not** use PulseAudio, PipeWire-as-default, or any desktop sound server.

| Layer | Function |
|-------|----------|
| **MAX25 sound-proxy** | Sole shim between modem DSP and ALSA — buffers, timing, duplex, xrun recovery |
| **libasound** | Direct `hw:` / `plughw:` opens |
| **Kernel ALSA** | Driver + `/dev/snd/*` |
| **Hardware** | Sound card → radio interface |

Configure explicit devices in `crdop.ini` `[audio]` (`capture`, `playback`). See [AUDIO-ARCHITECTURE.md](AUDIO-ARCHITECTURE.md).

## Baud scope

| Priority | Range | Status |
|----------|-------|--------|
| **P0** | **1200 baud** Bell 202 AFSK | Primary — CB + VHF on-air |
| **P1** | **9600–19200** G3RUH direct FSK | Planned after 1200 stable (VHF backbone) |
| **P2** | **300** HF AFSK | Optional |
| — | **>19200 baud** | **Not implemented** — do not configure or expect |

Full modulation matrix, RF paths, band context, delivery milestones: **[ROADMAP.md](../ROADMAP.md)**.

Higher baud rates demand **proportionally better** audio hardware (sample rate, jitter, SNR, isolation). G3RUH requires a **direct FSK radio path** — not the CB FM mic/speaker route.

## Duplex

| Mode | Status |
|------|--------|
| **Half-duplex** | Standard CB / packet-radio (PTT or VOX-style timing) |
| **Full-duplex** | Supported when radio and audio hardware allow simultaneous TX/RX paths |

Configure in `crdop.ini`: `[modem] duplex = half|full`.

## Sound card — required (not optional)

CRDOP must:

1. **Generate** precise mark/space frequencies on **playback**.
2. **Decode** those tones reliably on **capture**.

Requirements **scale with baud**:

| Baud class | Audio expectation |
|------------|-------------------|
| 1200 | Stable full-duplex or half-duplex USB codec or PCI interface; galvanic isolation to radio |
| 9600–19200 | Low-jitter interface, adequate bandwidth, verified loopback before on-air |

**Unsuitable:** onboard laptop mic/speaker shortcuts, anonymous USB “sound sticks”, Bluetooth bridges, unisolated consumer line inputs.

Document your ALSA device in INI (`[audio] capture` / `playback`) and verify with loopback or sidetone before traffic.

## Open hardware

Documentation targets builders who want to **manufacture radio ↔ sound-card interfaces**:

- Level matching (radio mic/speaker ↔ line level)
- Galvanic isolation (transformers / opto)
- PTT integration (GPIO, serial — VOX not recommended for packet)
- Acoustic coupler fixtures for bench validation

Generic interface specification: [HARDWARE-INTERFACE.md](HARDWARE-INTERFACE.md). Delivery milestones: [ROADMAP.md](../ROADMAP.md).

## Build / release (MAX25-Stack-v1.0.0)

**CRDOP dev track:** `CUR999` in `$SRC/stacks/crdop/VERSION` (ships with MAX25-Stack v1.0.0).

| Item | Shipped |
|------|---------|
| CRDOP scaffold (INI, launcher, install) | **Yes** — default CMake |
| `max25d` `crdop-tcp` backend | **Yes** — offline-tested |
| Native `crdopc` DSP binary | **In development** — in-house modem DSP |
| ARDOP / ardopcf vendor tree | **Never** in release tarball |

## HyBBX

When CRDOP is active, HyBBX Secondary attaches via `share/hybbx/crdop-host.ini.example`. HyBBX remains an external project.

## Testing phase

Current work: loopback audio, acoustic bench validation, field on-air trials, acceptable sound-card criteria. Report results via project issues — RF acceptance remains manual until automated gates exist. Developer tests: [DEVELOPER.md](DEVELOPER.md).
