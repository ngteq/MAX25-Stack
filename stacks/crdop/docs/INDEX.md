# CRDOP documentation index

**CRDOP** = **CB/AR Digital Open Protocol** (CB = Citizens Band, AR = Amateur Radio). Product: **MAX25-SoftModem** (`stacks/crdop/`). Version: **CRDOP-CUR999** until **v0.5**.

**Project rule (authoritative):** [docs/CRDOP.md](../../../docs/CRDOP.md)  
**AI agent map:** [AGENTS.md](../../../AGENTS.md) (repo root)

---

## Start here

| Audience | Doc | One-line purpose |
|----------|-----|------------------|
| Everyone | [SOFTMODEM.md](SOFTMODEM.md) | What CRDOP is — baud scope, duplex, ALSA path |
| MAX25 operator | [MAX25-USAGE.md](MAX25-USAGE.md) | Build, `max25d`, plugins, terminal, HyBBX attach |
| Developer | [DEVELOPER.md](DEVELOPER.md) | Source tree, modules, tests, extending the modem |
| Hardware builder | [HARDWARE-INTERFACE.md](HARDWARE-INTERFACE.md) | Generic radio/audio interface specification |
| Legal / distribution | [LICENSE-USAGE.md](LICENSE-USAGE.md) | GPLv3 — private and commercial use rights |

---

## Technical reference

| Doc | One-line purpose |
|-----|------------------|
| [AUDIO-ARCHITECTURE.md](AUDIO-ARCHITECTURE.md) | Kernel ALSA only — sound-proxy, no PulseAudio |
| [PROTOCOL.md](PROTOCOL.md) | M25-family host TCP (:8515 ctrl, :8516 data) |
| [CONFIG.md](CONFIG.md) | `crdop.ini` keys and launcher behaviour |
| [BUILD.md](BUILD.md) | Standalone CMake build and cross-compile |
| [EXAMPLES.md](EXAMPLES.md) | INI profiles, launcher, `max25d` snippets |
| [CHANGELOG.md](CHANGELOG.md) | Release notes |

---

## Planning

| Doc | One-line purpose |
|-----|------------------|
| [ROADMAP.md](../ROADMAP.md) | P0/P1/P2 modulation, RF paths, FEC, phased milestones — **full research vault synthesis** (`0-RESEARCHES/reference/modems-packet-radio/`) |

---

## Plugin registry

| Id | Type | Role |
|----|------|------|
| `soft-crdop` | device | Production sound-card modem (`soft-modems` hardware) |
| `audio-dummy` | device | Acoustic bench — loopback / ALSA / host (`acoustic-bench`) |
| `soft-modems` | hardware | CRDOP device family |
| `acoustic-bench` | hardware | Dev/test bench — no RF required |

---

## Install tree (MAX25-Stack build)

| Path | Contents |
|------|----------|
| `bin/crdop` | Launcher (`scripts/crdopc`) |
| `bin/audio-dummyd` | M25 host + acoustic engine |
| `bin/max25-signal-sniffer` | Bell 202 analysis tool |
| `share/crdop/` | INI examples, `lib/*.py`, `VERSION` |
| `share/hybbx/crdop-host.ini.example` | HyBBX Secondary attach |

---

*Compact index — depth in linked docs. Research vault paths listed in [ROADMAP.md](../ROADMAP.md#reference-index).*
