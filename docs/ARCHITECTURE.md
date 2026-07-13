# Architecture

**Main AX.25 Stack (MAX25)** — Packet Radio / AX.25 standalone stack with HyBBX-compatible plugin boundaries.

## Layer model

```
┌─────────────────────────────────────────────────────────┐
│  max25-terminal / max25-client — all platforms (v1)     │
│  F10 menu · CALLERID/CALLID · --ax25-ui                 │
├─────────────────────────────────────────────────────────┤
│  max25d (Linux only) — config, plugins, KISS bridge     │
│  M25/1 IPC · multi-device · BayCom · TNC · CRDOP        │
├─────────────────────────────────────────────────────────┤
│  HyBBX (external) — sessions, HBX, BBS                  │
│  Plugins: packet_radio | baycom | crdop                 │
├─────────────────────────────────────────────────────────┤
│  Operating mode — standalone | service | hybbx-host     │
├─────────────────────────────────────────────────────────┤
│  Hardware — tncs | modems | soft-modems                   │
├─────────────────────────────────────────────────────────┤
│  Device — tnc2c | baycom-ser12 | soft-crdop | …         │
├─────────────────────────────────────────────────────────┤
│  Protocol — KISS | kernel hdlcdrv | AX.25 UI | CRDOP M25 host │
└─────────────────────────────────────────────────────────┘
```

**Split:** daemon and hardware on **Linux**; terminal on any platform via M25/1. Packet-radio facts: [PACKET-RADIO.md](PACKET-RADIO.md).

## Directory layout

```
MAX25-Stack/
├── plugins/           Registry — operating mode / hardware / device
├── stacks/
│   ├── tncs/          Serial TNC tools (TNC2C, PK-TNC2 planned)
│   ├── baycom-pr/     Kernel BayCom lifecycle
│   ├── crdop/         MAX25-SoftModem (CRDOP — CB/AR Digital Open Protocol) — sound-card AX.25 modem
│   ├── daemon/        max25d + kiss_bridge.py
│   └── terminal/      max25-terminal / max25-client
├── scripts/           build.sh, max25-ctl, discover-plugins, release-check
├── share/max25/       max25d.ini examples, systemd unit
├── share/hybbx/       HyBBX INI snippets per device
└── docs/              [README.md](README.md) — doc index
```

## Plugin hierarchy

| Type | Path | Responsibility |
|------|------|----------------|
| **Operating mode** | `betriebsform/*` | Standalone, service, HyBBX host role |
| **Hardware** | `hardware/*` | Stack path, HyBBX plugin name |
| **Device** | `devices/*` | Serial params, INI, scripts |

Registry: `plugins/manifest.yaml`. Discovery CLI (`discover-plugins.sh`) lists **hardware** and **device** only — not operating modes.

## max25d (Linux daemon)

| Responsibility | Detail |
|----------------|--------|
| M25/1 IPC | TCP `:7325`, Unix `/run/max25/modem.sock` |
| Multi-device | `[devices]` in `max25d.ini` — one backend per id (`kiss-serial`, `baycom-kiss`, `crdop-tcp`, …) |
| KISS bridge | `kiss_bridge.py` — serial KISS for TNC paths |
| Stack lifecycle | boot-wait, BayCom kernel, `crdopc` start |
| TCP auth | Plain-text `AUTH` when `tcp_password` set |

Config: `share/max25/max25d.ini.example`. Daemon README: [stacks/daemon/README.md](../stacks/daemon/README.md).

## Merged stack roles

| Stack | Owns | Does not own |
|-------|------|--------------|
| `stacks/tncs` | TNC2C boot-wait, probe, health | HyBBX sessions |
| `stacks/baycom-pr` | Kernel module, KISS PTY, AX.25 port sync | HyBBX HBX |
| `stacks/crdop` | MAX25-SoftModem (CRDOP) — sound IN/OUT, acoustic AX.25, max25d TCP | KISS serial to TNC |

Link stack READMEs — do not duplicate operator detail here.

## HyBBX attachment

MAX25 is the **modem/TNC owner**. HyBBX:

1. Waits for stack ready (boot-wait OK, or `baycom-pr-ctl status`)
2. Opens serial, KISS PTY, or CRDOP TCP per `share/hybbx/*.ini.example`
3. Bridges to Main over HBX

Contract: [HYBBX.md](HYBBX.md).

## Operating mode matrix

| Mode | Radios | Typical path | HyBBX role |
|------|--------|--------------|------------|
| `standalone` | 1 | Any active device | Optional local Main |
| `service` | 1–2 | Dual INI templates | Secondary 24/7 |
| `hybbx-host` | 1 per section | Device plugin scripts | Secondary RF host |

## See also

- [README.md](README.md) — doc index
- [PLATFORMS.md](PLATFORMS.md) — Linux daemon, cross-platform terminal
- [MAX25-CLIENT.md](MAX25-CLIENT.md) — M25/1 binding
- [LINUX-HOST-SETUP.md](LINUX-HOST-SETUP.md) — example host install
