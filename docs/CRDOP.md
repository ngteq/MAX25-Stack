# CRDOP — MAX25-SoftModem

> **Static rule:** **CRDOP** is the stack acronym for **MAX25-SoftModem** — the in-house sound-card AX.25 modem (`stacks/crdop/`, device id `soft-crdop`). Citizens Band and amateur radio are **use cases**, not an acronym expansion. This file is authoritative for CRDOP naming in MAX25-Stack.

**Status:** MAX25-Stack **v1.0.0** standard component · **License:** GNU GPL v3  
**Location:** `$SRC/stacks/crdop/` · **Dev track:** `CUR999` in `stacks/crdop/VERSION` (internal DSP scaffold id; not a separate product release)

CRDOP is the **sound-card-based software modem** subproject of [MainAX25-Stack (MAX25-Stack)](../README.md). Product name: **MAX25-SoftModem**. Plugin/device id: `soft-crdop`.

Research vault (modulation, FEC, hardware): `$VAULT/projects/max25-stack/` — see [docs/PATHS.md](PATHS.md).

---

## 1. Subproject within MAX25-Stack

| Item | Value |
|------|--------|
| **Product name** | **MAX25-SoftModem** |
| **Stack acronym** | **CRDOP** |
| **Version file** | `CUR999` (`$SRC/stacks/crdop/VERSION`) — dev track only |
| **Stack release** | **MAX25-Stack v1.0.0** (`VERSION` at repo root) |
| **Tree** | `$SRC/stacks/crdop/` |
| **Registry** | `plugins/devices/soft-crdop/`, `plugins/hardware/soft-modems/` |
| **Daemon hook** | `max25d` → `CrdopTcpBackend` (`device_backends.py`) |
| **Build** | **ON by default** — `MAX25_BUILD_CRDOP=ON`; disable with `-DMAX25_BUILD_CRDOP=OFF` |
| **HyBBX** | External consumer via `share/hybbx/crdop-host.ini.example` |

CRDOP is an **in-house GNU GPLv3 subproject** developed, tested, and documented inside MAX25-Stack, with its own headers, INI, launcher, and roadmap.

```
$SRC/
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

**Modulation priorities** (P0 Bell 202 → P1 G3RUH → P2 HF 300, FEC strategy, RF paths): [stacks/crdop/ROADMAP.md](../stacks/crdop/ROADMAP.md).

**Duplex:** half-duplex and full-duplex, per radio and audio hardware capability.

CRDOP behaves like a **hardware modem** from the operator's view: sound IN/OUT + transceiver, integrated via `max25d` like serial or kernel modem paths.

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

- Source in `$SRC/stacks/crdop/` is licensed under **GPL-3.0-or-later** (see [LICENSE](../stacks/crdop/LICENSE) and repository root [LICENSE](../LICENSE)).
- Derivative hardware documentation that ships with the repo follows the same free-software intent.
- **ARDOP-plugin** is an optional MAX25-Stack plugin — enable with `ardop_compat=true` on `soft-crdop`. Registry: [plugins/external/ardop/README.md](../plugins/external/ardop/README.md).

Contributors grant rights consistent with GPLv3 copyleft.

---

## 6. What CRDOP is not

| Item | Policy |
|------|--------|
| ARDOP modem binary in MAX25 install | **Not included** — use **ARDOP-plugin** mode with operator ARDOP host |
| ARDOP vendor tree in release tarball | **Not included** |
| PulseAudio / PipeWire production path | **Forbidden** |
| Kernel AX.25 replacement | CRDOP is a **modem**, not `libax25` |
| HyBBX session logic | External — attach after stack is up |
| Speeds > 19200 baud | Out of scope (current phase) |
| Acronym expansion “CB/AR Digital Open Protocol” | **Deprecated** — use **MAX25-SoftModem** |

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
cd $SRC
./scripts/build.sh
# Acoustic bench (no RF):
python3 stacks/crdop/tools/max25-signal-sniffer.py --loopback
# max25d with audio-dummy:
#   [devices] audio-dummy = audio:loopback
./scripts/max25-ctl start --hardware acoustic-bench --device audio-dummy
max25-terminal -U $RUN_MAX25/modem.sock
```

### Acoustic bench tools

| Tool | Purpose |
|------|---------|
| `max25-signal-sniffer` | Sniff/evaluate Bell 202 AFSK (ALSA, WAV, or `--loopback`) |
| `audio-dummyd` | M25 host TCP dummy for `audio:host` mode |
| Device `audio-dummy` | max25d backend — loopback / ALSA sniff / host |

---

## 9. Documentation index

**Compact entry:** [stacks/crdop/docs/INDEX.md](../stacks/crdop/docs/INDEX.md)

| Audience | Start here |
|----------|------------|
| Implementation specs | [HOST-PROTOCOL-SPEC.md](../stacks/crdop/docs/HOST-PROTOCOL-SPEC.md), [FEC-SPEC.md](../stacks/crdop/docs/FEC-SPEC.md), [ACOUSTIC-TEST-PROTOCOL.md](../stacks/crdop/docs/ACOUSTIC-TEST-PROTOCOL.md) |
| MAX25 operator | [MAX25-OPERATOR-RUNBOOK.md](MAX25-OPERATOR-RUNBOOK.md) · [HARDWARE-ACCEPTANCE.md](HARDWARE-ACCEPTANCE.md) |
| Developer | [stacks/crdop/docs/DEVELOPER.md](../stacks/crdop/docs/DEVELOPER.md) |
| Hardware builder | [stacks/crdop/docs/HARDWARE-INTERFACE.md](../stacks/crdop/docs/HARDWARE-INTERFACE.md) |
| Path conventions | [PATHS.md](PATHS.md) |
| License / distribution | [stacks/crdop/docs/LICENSE-USAGE.md](../stacks/crdop/docs/LICENSE-USAGE.md) |

---

*This file is a static project rule. Changes require explicit maintainer review.*
