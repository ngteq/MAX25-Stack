# MainAX25-Stack (MAX25-Stack) Architecture

**Main AX.25 Stack** — Packet Radio / AX.25 standalone stack with HyBBX-compatible plugin boundaries.

## Layer model

```
┌─────────────────────────────────────────────────────────┐
│  MAX25 Terminal (max25-client) — all platforms (planned) │
│  F10 menu · CALLERID/CALLID · --ax25-ui                  │
├─────────────────────────────────────────────────────────┤
│  max25d (Linux only) — config, plugins, device owner    │
│  evolves from max25-ctl · BayCom · TNC · CRDOP          │
├─────────────────────────────────────────────────────────┤
│  HyBBX (external) — sessions, HBX, BBS, users          │
│  Plugins: packet_radio | baycom | crdop                 │
├─────────────────────────────────────────────────────────┤
│  MainAX25 operating mode — standalone | service | hybbx-edge │
├─────────────────────────────────────────────────────────┤
│  MainAX25 Hardware — tncs | modems | soft-modems             │
├─────────────────────────────────────────────────────────┤
│  MainAX25 Device — tnc2c | pktnc2 | baycom-ser12 | soft-crdop | … │
├─────────────────────────────────────────────────────────┤
│  Protocol — KISS | hostmode | kernel hdlcdrv | AX.25 | ARDOP │
├─────────────────────────────────────────────────────────┤
│  Physical — serial UART | USB | LPT | RF (Linux daemon)   │
└─────────────────────────────────────────────────────────┘
```

**Split:** daemon and hardware on **Linux**; **terminal** on any platform, talking to `max25d` over M25/1. Packet-radio facts: [PACKET-RADIO.md](PACKET-RADIO.md). See [PLATFORMS.md](PLATFORMS.md), [MAX25-CLIENT.md](MAX25-CLIENT.md), [MAX25-TERMINAL.md](MAX25-TERMINAL.md).

## Directory layout

```
MainAX25-Stack (MAX25-Stack)/
├── plugins/           Plugin registry + operating mode / hardware / device metadata
├── stacks/
│   ├── tncs/          Merged TNCs-Stack (serial TNC operator tools)
│   ├── baycom-pr/     Merged baycom_pr-Stack (kernel modem lifecycle)
│   └── crdop/         Merged CRDOP (sound-card ARDOP soft modem)
├── stacks/daemon/     max25d (Linux supervisor, M25/1 IPC)
├── stacks/terminal/   max25-terminal / max25-client
├── scripts/           max25-ctl, discover-plugins, build-all
├── share/hybbx/       HyBBX INI snippets per device/mode
└── docs/              Architecture, platforms, MAX25 Terminal spec
```

**Implemented:** `stacks/daemon/max25d` — Linux supervisor; `stacks/terminal/` — **sole official client** (`max25-terminal` / `max25-client`), text + F10 menu. Binding: [MAX25-CLIENT.md](MAX25-CLIENT.md).

## Plugin types

| Type | ID prefix | Responsibility |
|------|-----------|----------------|
| **Operating mode** | `betriebsform/*` | How many radios, 24/7 vs operator, HyBBX edge role |
| **Hardware** | `hardware/*` | Stack path, build targets, HyBBX plugin name |
| **Device** | `devices/*` | Concrete profile — serial params, INI, scripts |

**Soft modems** (`hardware/soft-modems`) are sound-card programs without kernel drivers — e.g. `soft-crdop` (CRDOP/ARDOP). They complement AX.25 hardware stacks; see [PLATFORMS.md](PLATFORMS.md) for platform limits.

## Discovery & automation

1. `plugins/manifest.yaml` — canonical plugin list
2. `plugins/**/plugin.yaml` — per-plugin metadata (HyBBX mapping, scripts, INI)
3. `scripts/discover-plugins.sh` — list/filter plugins (no Python deps)
4. `scripts/max25-ctl` — unified start/stop/build entry
5. `./scripts/build.sh` — builds merged stacks (tncs, baycom-pr, crdop)

## Platform

**`max25d` — Linux only** (BayCom, kernel AX.25, full stack). **`max25-terminal`** on Linux, *BSD, macOS, Windows (AmigaOS reduced later). See [PLATFORMS.md](PLATFORMS.md).

Future: generate `devices/*/plugin.yaml` from `stacks/baycom-pr/config/modems.ini` catalog.

## HyBBX attachment

MainAX25 (MAX25) is the **modem/TNC owner**. HyBBX:

1. Waits for stack ready (boot-wait OK, or `baycom-pr-ctl status`)
2. Opens serial or KISS per `share/hybbx/*.ini.example`
3. Bridges AX.25 to Main over HBX

See [HYBBX.md](HYBBX.md).

## Merged stack responsibilities

### `stacks/tncs` (TNCs-Stack)

- Boot-wait / DTR sequencing for TNC2C
- Health, integration test, probe/find C tools
- Operator docs for Unit A (active) and Unit B (planned)
- Does **not** embed HyBBX — provides INI snippets only

### `stacks/baycom-pr` (baycom_pr-Stack)

- Kernel module load, KISS PTY bridge, AX.25 port sync
- `baycom-pr-ctl` lifecycle (probe, setup, doctor, start, recover)
- Service dual-modem template for 24/7 HyBBX
- **Linux only** — runs inside `max25d`; BayCom stays first-class on Linux

### `stacks/crdop` (CRDOP)

- Sound-card ARDOP modem (`crdopc`) — CB-first profiles
- Device plugin `soft-crdop`; HyBBX `crdop` transport over TCP
- Builds on Linux and *BSD (ALSA); not AX.25/KISS

## Operating mode matrix

| Mode | Radios | Typical MainAX25 path | HyBBX role |
|------|--------|-------------------|------------|
| Standalone | 1 | Either stack | Optional local Main |
| Service | 1–2 | baycom-pr dual or tncs dual INI | Secondary 24/7 |
| HyBBX Edge | 1 per section | Device plugin scripts | Secondary RF edge |
