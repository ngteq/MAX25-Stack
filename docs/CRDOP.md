# CRDOP — CB/AR Digital Open Protocol (MAX25-SoftModem)

> **Static rule:** **CRDOP** = **CB/AR Digital Open Protocol** (CB = Citizens Band, AR = Amateur Radio). This expansion is authoritative everywhere CRDOP is defined in MAX25-Stack.

**Status:** Static project rule · **License:** GNU GPL v3 · **Location:** `stacks/crdop/` (MAX25-Stack subproject)  
**Product version:** **CRDOP-CUR999** (`CUR999` in `stacks/crdop/VERSION`) — pre-release until **v0.5**

CRDOP is the **sound-card-based software modem** subproject of [MainAX25-Stack (MAX25-Stack)](../README.md). Product name: **MAX25-SoftModem**. Plugin/device id: `soft-crdop`.

This document is the **authoritative project rule** for CRDOP. All design, documentation, and implementation must align with it.

---

## 1. Subproject within MAX25-Stack

| Item | Value |
|------|--------|
| **Product label** | **CRDOP-CUR999** |
| **Version file** | `CUR999` (`stacks/crdop/VERSION`) |
| **Release target** | **v0.5** (first numbered release; not yet shipped) |
| **Tree** | `stacks/crdop/` |
| **Registry** | `plugins/devices/soft-crdop/`, `plugins/hardware/soft-modems/` |
| **Daemon hook** | `max25d` → `CrdopTcpBackend` (`device_backends.py`) |
| **Build** | **ON by default** — `MAX25_BUILD_CRDOP=ON`; disable with `-DMAX25_BUILD_CRDOP=OFF` |
| **HyBBX** | External consumer via `share/hybbx/crdop-host.ini.example` |

CRDOP is **not** a third-party drop-in. It is an **in-house GNU GPLv3 subproject** developed, tested, and documented inside MAX25-Stack, with its own headers, INI, launcher, and roadmap.

```
MAX25-Stack/
├── docs/CRDOP.md              ← this file (project rule)
├── stacks/crdop/              ← subproject root
│   ├── include/crdop/         ← native API (sound-proxy, modem)
│   ├── share/                 ← INI examples
│   ├── scripts/crdopc         ← launcher
│   └── docs/                  ← technical deep-dives
└── plugins/.../soft-crdop/    ← plugin contract
```

---

## 2. Sound-card-based development (mandatory)

CRDOP is developed **only** on the **sound-card path**:

- **Capture + playback** through a **good sound interface** (USB/PCI codec, isolated line I/O).
- **Kernel ALSA only** — direct `hw:` / `plughw:` via libasound.
- **MAX25 sound-proxy** — sole shim between modem DSP and ALSA (see [stacks/crdop/docs/AUDIO-ARCHITECTURE.md](../stacks/crdop/docs/AUDIO-ARCHITECTURE.md)).
- **No PulseAudio**, **no PipeWire default route**, **no desktop sound server** in the production path.

A suitable sound card is **required**, not optional: the modem must reproduce mark/space frequencies accurately; requirements **increase with baud rate**.

---

## 3. Compatibility goal — AX.25 / KISS / TNCs / modems

CRDOP targets **full compatibility** in the software-modem domain with established packet-radio stacks:

| Domain | Compatibility target |
|--------|------------------------|
| **AX.25** | UI frames, addressing, FCS — aligned with `stacks/daemon/ax25_codec.py` and on-air AFSK |
| **KISS** | Framing semantics where host paths use KISS (conceptual parity with serial TNC bridges) |
| **Hardware TNCs** | Acoustic and line-level interchange with 1200 AFSK packet modems |
| **Kernel modems** | Same tone discipline and timing class on the RF/audio layer |
| **max25d** | First-class device backend — same operator workflow as serial/KISS devices |

**Primary speed:** 1200 baud. **Design range:** up to **19200 baud**. **Above 19200 baud:** not implemented in the current phase.

**Modulation priorities** (P0 Bell 202 → P1 G3RUH → P2 HF 300, FEC strategy, RF paths, **full research vault coverage**): [stacks/crdop/ROADMAP.md](../stacks/crdop/ROADMAP.md).

**Duplex:** half-duplex and full-duplex, per radio and audio hardware capability.

CRDOP behaves like a **hardware modem** from the operator’s view: sound IN/OUT + transceiver, integrated via `max25d` like serial or kernel modem paths.

---

## 4. Dual mission — hardware solutions & software solutions

### 4.1 Hardware solutions (primary)

CRDOP documentation and APIs **primarily serve builders** who create **hardware around the modem**:

- Level-matched radio interfaces (mic/speaker ↔ line)
- Galvanic isolation (transformers, opto)
- PTT interfaces (GPIO, serial, VOX)
- Acoustic couplers for bench validation
- Reference BOMs, schematics, and acceptance tests

Open, reproducible hardware is a **first-class deliverable**, not an afterthought.

### 4.2 Software solutions (pure computer)

CRDOP also supports **pure software deployment** on general-purpose computers:

- Dedicated Linux host + sound card + radio
- Development, test, and field operation without custom PCBs
- `max25-terminal` + `max25d` + CRDOP launcher workflow
- Documented INI, ALSA device selection, and loopback validation

Both tracks share the **same GPLv3 codebase** and **same on-air compatibility goals**.

---

## 5. License — GNU GPL v3

CRDOP is a **GNU GPLv3** project:

- Source in `stacks/crdop/` is licensed under **GPL-3.0-or-later** (see [LICENSE](../stacks/crdop/LICENSE) and repository root [LICENSE](../LICENSE)).
- Derivative hardware documentation that ships with the repo follows the same free-software intent.
- **ARDOP vendor code** (ardopcf, etc.) is **never** bundled in MAX25 releases.
- **ARDOP binaries** are **never** installed in MAX25 releases.
- Optional third-party ARDOP attach via `ardop_compat=true` on `soft-crdop` only.

Contributors grant rights consistent with GPLv3 copyleft.

---

## 6. What CRDOP is not

| Item | Policy |
|------|--------|
| ARDOP fork / vendored ardopcf | **Never** in release tarballs or install tree |
| ARDOP binaries (crdopc vendor) | **Never** shipped — external operator install only |
| PulseAudio / PipeWire production path | **Forbidden** |
| Kernel AX.25 replacement | CRDOP is a **modem**, not `libax25` |
| HyBBX session logic | External — attach after stack is up |
| Speeds > 19200 baud | Out of scope (current phase) |

---

## 7. Development phase (current)

| Milestone | State |
|-----------|--------|
| Project rule & docs | **Active** (this file) |
| `max25d` backend + offline tests | Done |
| INI, launcher, HyBBX examples | Done |
| MAX25 sound-proxy API (`include/crdop/sound_proxy.h`) | Scaffold |
| Native modem DSP (1200 baud AFSK) | In progress |
| Hardware interface guide | In progress — [stacks/crdop/docs/HARDWARE-INTERFACE.md](../stacks/crdop/docs/HARDWARE-INTERFACE.md) |
| Acoustic validation vs 1200 AFSK reference paths | Test phase |

See [stacks/crdop/ROADMAP.md](../stacks/crdop/ROADMAP.md).

---

## 8. Operator quick reference

```bash
./scripts/build.sh
# Acoustic bench (no RF):
python3 stacks/crdop/tools/max25-signal-sniffer.py --loopback
# max25d with audio-dummy:
#   [devices] audio-dummy = audio:loopback
./scripts/max25-ctl start --hardware acoustic-bench --device audio-dummy
max25-terminal -U /run/max25/modem.sock
```

### Acoustic bench tools

| Tool | Purpose |
|------|---------|
| `max25-signal-sniffer` | Sniff/evaluate Bell 202 AFSK (ALSA, WAV, or `--loopback`) |
| `audio-dummyd` | M25 host TCP dummy for `audio:host` mode |
| Device `audio-dummy` | max25d backend — loopback / ALSA sniff / host |

---

## 10. Documentation index

**Compact entry:** [stacks/crdop/docs/INDEX.md](../stacks/crdop/docs/INDEX.md) — full table of CRDOP docs for developers, operators, and hardware builders.

| Audience | Start here |
|----------|------------|
| MAX25 operator | [stacks/crdop/docs/MAX25-USAGE.md](../stacks/crdop/docs/MAX25-USAGE.md) |
| Developer | [stacks/crdop/docs/DEVELOPER.md](../stacks/crdop/docs/DEVELOPER.md) |
| Hardware builder | [stacks/crdop/docs/HARDWARE-INTERFACE.md](../stacks/crdop/docs/HARDWARE-INTERFACE.md) |
| License / distribution | [stacks/crdop/docs/LICENSE-USAGE.md](../stacks/crdop/docs/LICENSE-USAGE.md) |

## 11. Related documents

| Document | Topic |
|----------|--------|
| [stacks/crdop/README.md](../stacks/crdop/README.md) | Subproject entry |
| [stacks/crdop/docs/INDEX.md](../stacks/crdop/docs/INDEX.md) | Documentation index |
| [stacks/crdop/docs/SOFTMODEM.md](../stacks/crdop/docs/SOFTMODEM.md) | Product definition |
| [stacks/crdop/docs/AUDIO-ARCHITECTURE.md](../stacks/crdop/docs/AUDIO-ARCHITECTURE.md) | Kernel ALSA, sound-proxy |
| [stacks/crdop/docs/CONFIG.md](../stacks/crdop/docs/CONFIG.md) | INI keys |
| [stacks/crdop/docs/PROTOCOL.md](../stacks/crdop/docs/PROTOCOL.md) | Host TCP interface |
| [stacks/crdop/ROADMAP.md](../stacks/crdop/ROADMAP.md) | P0/P1/P2 phases, RF paths, FEC |
| [PACKET-RADIO.md](PACKET-RADIO.md) | AX.25 / KISS context in MAX25 |
| [V1.0.0-SCOPE.md](V1.0.0-SCOPE.md) | Release scope |

---

*This file is a static project rule. Changes require explicit maintainer review.*
