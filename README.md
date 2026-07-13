# MainAX25-Stack (MAX25-Stack)

**Main AX.25 Stack** — standalone Packet Radio / AX.25 hardware lifecycle. HyBBX attaches as an external consumer (`packet_radio`, `baycom`, `crdop`). MAX25 owns modem/TNC prep, KISS bridge, and M25/1 operator IPC.

**Product:** MAX25-Stack-v1.0.0 · **Version:** `1.0.0` (see `VERSION`) · Full doc map: [docs/README.md](docs/README.md)

## Architecture

```
Operator                    Linux host (max25d)
┌─────────────────┐        ┌──────────────────────────────┐
│ max25-terminal  │ M25/1  │ max25d · KISS bridge         │
│ F10 · CALLERID  │ ─────► │ TNCs · BayCom · CRDOP        │
└─────────────────┘ :7325  └──────────────▲───────────────┘
                                           │ serial / kernel / audio+TCP
                              HyBBX Secondary (external)
                              packet_radio · baycom · crdop
```

| Layer | Location | Role |
|-------|----------|------|
| Operator client | `stacks/terminal/` | Text + F10 menu — **only** official client |
| Daemon | `stacks/daemon/` | Linux-only supervisor, M25/1, multi-device KISS, AX.25 source ban list |
| Merged stacks | `stacks/tncs/`, `baycom-pr/`, `crdop/` | Device-specific tools and lifecycle |
| Plugins | `plugins/` | Operating mode → hardware → device registry |
| HyBBX attach | `share/hybbx/` | INI examples — HyBBX repo is external |

## MAX25-SoftModem (CRDOP — CB/AR Digital Open Protocol) — standard component

**CRDOP** (**CB/AR Digital Open Protocol**; CB = Citizens Band, AR = Amateur Radio) is our in-house **MAX25-SoftModem** — built and installed **by default** with every MAX25-Stack build. Disable only when you do not need a sound-card modem:

```bash
cmake -B build -DMAX25_BUILD_CRDOP=OFF
```

| Topic | Policy |
|-------|--------|
| Status | **Development and test phase** — in-house development, openly documented |
| Speed | **1200 baud** primary, extensions up to **19200 baud** |
| Above 19200 baud | **Not implemented** in the current phase |
| Duplex | **Half-duplex** and **full-duplex** |
| AX.25 / Packet Radio | **Fully compatible on the acoustic layer** — same AFSK tone classes as TNCs and BayCom modems |
| Use like hardware | Sound card **IN/OUT** + radio — kernel **ALSA direct**, MAX25 **sound-proxy**, **no PulseAudio** |
| Sound card | **Required** — kernel ALSA; accurate tones; stricter at higher baud |
| ARDOP wire-compat | **Optional only** — third-party hosts; never vendored in MAX25 releases |

```
Radio ↔ hw IN/OUT ↔ kernel ALSA ↔ MAX25 sound-proxy ↔ CRDOP ↔ max25d ↔ M25/1 / HyBBX
         (no PulseAudio — libasound direct)
```

Docs: [docs/CRDOP.md](docs/CRDOP.md) · [stacks/crdop/docs/SOFTMODEM.md](stacks/crdop/docs/SOFTMODEM.md) · [stacks/crdop/docs/AUDIO-ARCHITECTURE.md](stacks/crdop/docs/AUDIO-ARCHITECTURE.md)

## Quick start

```bash
./scripts/build.sh
./scripts/discover-plugins.sh --json
./scripts/release-check.sh
```

Build output: `build/bin/` (`max25-terminal`, `tnc2c-probe`, `baycom_test`, CRDOP scaffold/launcher, …).

### Linux host (max25d + terminal)

```bash
./scripts/install-max25.sh --deps
sudo cp share/max25/max25d.ini.host.example /etc/max25/max25d.ini
sudo max25d -c /etc/max25/max25d.ini
max25-terminal -U /run/max25/modem.sock --ax25-ui
```

Guide: [docs/LINUX-HOST-SETUP.md](docs/LINUX-HOST-SETUP.md).

### Active devices (v1)

| Device | Standalone | HyBBX plugin |
|--------|------------|--------------|
| **TNC2C** (`tnc2c`) | `max25-ctl start --hardware tncs --device tnc2c` | `packet_radio` |
| **BayCom SER12** (`baycom-ser12`) | `max25-ctl start --hardware modems --device baycom-ser12` | `baycom` |
| **MAX25-SoftModem** (`soft-crdop`) | `max25-ctl start --hardware soft-modems --device soft-crdop` | `crdop` |

Default operating mode: `standalone`. BayCom: **single PC-COM default**; dual modem opt-in ([BAYCOM.md](docs/BAYCOM.md)). Deferred: `pktnc2`, `baycom-par96`, `baycom-kiss`.

## Platform

| Component | Platforms |
|-----------|-----------|
| **`max25d`** | **Linux only** — BayCom kernel, TNC boot-wait, CRDOP, multi-device KISS |
| **`max25-terminal`** | Linux, *BSD, macOS, Windows, AmigaOS (reduced) — remote TCP to Linux `max25d` |

Details: [docs/PLATFORMS.md](docs/PLATFORMS.md).

## Documentation

| Audience | Doc |
|----------|-----|
| **Index** | [docs/README.md](docs/README.md) |
| Host setup | [LINUX-HOST-SETUP.md](docs/LINUX-HOST-SETUP.md) |
| Terminal operator | [MAX25-TERMINAL.md](docs/MAX25-TERMINAL.md) |
| Client / M25/1 | [MAX25-CLIENT.md](docs/MAX25-CLIENT.md) |
| Packet radio facts | [PACKET-RADIO.md](docs/PACKET-RADIO.md) |
| BayCom / PC-COM | [BAYCOM.md](docs/BAYCOM.md) |
| SoftModem (CRDOP) | [stacks/crdop/docs/SOFTMODEM.md](stacks/crdop/docs/SOFTMODEM.md) |
| HyBBX attach | [HYBBX.md](docs/HYBBX.md) |
| Architecture | [ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Development | [DEVELOPMENT.md](docs/DEVELOPMENT.md) |
| v1 scope | [V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md) |

Agents: [AGENTS.md](AGENTS.md) · Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
