# MainAX25-Stack (MAX25-Stack) Architecture

**Main AX.25 Stack** — Packet Radio / AX.25 standalone stack with HyBBX-compatible plugin boundaries.

## Layer model

```
┌─────────────────────────────────────────────────────────┐
│  HyBBX (external) — sessions, HBX, BBS, users          │
│  Plugins: packet_radio | baycom                         │
├─────────────────────────────────────────────────────────┤
│  MainAX25 Betriebsform — standalone | service | hybbx-edge │
├─────────────────────────────────────────────────────────┤
│  MainAX25 Hardware — tncs | modems                         │
├─────────────────────────────────────────────────────────┤
│  MainAX25 Device — tnc2c | pktnc2 | baycom-ser12 | …       │
├─────────────────────────────────────────────────────────┤
│  Protocol — KISS | hostmode | kernel hdlcdrv | AX.25    │
├─────────────────────────────────────────────────────────┤
│  Physical — serial UART | USB | LPT | RF                │
└─────────────────────────────────────────────────────────┘
```

## Directory layout

```
MainAX25-Stack (MAX25-Stack)/
├── plugins/           Plugin registry + Betriebsform/Hardware/Device metadata
├── stacks/
│   ├── tncs/          Merged TNCs-Stack (serial TNC operator tools)
│   └── baycom-pr/     Merged baycom_pr-Stack (kernel modem lifecycle)
├── scripts/           max25-ctl, discover-plugins, build-all
├── share/hybbx/       HyBBX INI snippets per device/mode
└── docs/              Architecture, HyBBX contract, merge report
```

## Plugin types

| Type | ID prefix | Responsibility |
|------|-----------|----------------|
| **Betriebsform** | `betriebsform/*` | How many radios, 24/7 vs operator, HyBBX edge role |
| **Hardware** | `hardware/*` | Stack path, build targets, HyBBX plugin name |
| **Device** | `devices/*` | Concrete profile — serial params, INI, scripts |

## Discovery & automation

1. `plugins/manifest.yaml` — canonical plugin list
2. `plugins/**/plugin.yaml` — per-plugin metadata (HyBBX mapping, scripts, INI)
3. `scripts/discover-plugins.sh` — list/filter plugins (no Python deps)
4. `scripts/max25-ctl` — unified start/stop/build entry
5. `make all` — builds both merged stacks

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

## Betriebsform matrix

| Mode | Radios | Typical MainAX25 path | HyBBX role |
|------|--------|-------------------|------------|
| Standalone | 1 | Either stack | Optional local Main |
| Service | 1–2 | baycom-pr dual or tncs dual INI | Secondary 24/7 |
| HyBBX Edge | 1 per section | Device plugin scripts | Secondary RF edge |
