# MainAX25-Stack (MAX25-Stack)

**Main AX.25 Stack** — unified Packet Radio / AX.25 standalone stack, fully **HyBBX-compatible**. HyBBX attaches as a plugin consumer; MainAX25 (MAX25) owns modem/TNC lifecycle, KISS, and AX.25 link preparation.

Merged from:

| Source | Location | Role |
|--------|----------|------|
| **TNCs-Stack** | `stacks/tncs/` | Serial TNC tools (TNC2C, PK-TNC2) |
| **baycom_pr-Stack** | `stacks/baycom-pr/` | BayCom kernel modems (SER12, PAR96, KISS) |
| **CRDOP** | `stacks/crdop/` | Sound-card ARDOP soft modem (`soft-crdop`) |

## Quick start

```bash
make all
./scripts/discover-plugins.sh
./scripts/max25-ctl help
```

### Example Linux edge setup

Use the example INI and install steps for a typical edge node (`max25d` + USB TNC/modem):

```bash
./scripts/install-max25.sh --deps
sudo cp share/max25/max25d.ini.edge.example /etc/max25/max25d.ini
sudo max25d -c /etc/max25/max25d.ini
max25-terminal -U /run/max25/modem.sock
```

Setup guide: [docs/LINUX-EDGE-SETUP.md](docs/LINUX-EDGE-SETUP.md).

### TNC2C

```bash
./scripts/max25-ctl start --hardware tncs --device tnc2c
./scripts/max25-ctl test
# HyBBX Secondary: share/hybbx/tnc2c-edge.ini.example
```

### BayCom SER12

```bash
make -C stacks/baycom-pr all
sudo make -C stacks/baycom-pr install
./scripts/max25-ctl start --hardware modems --device baycom-ser12
```

### CRDOP soft modem (soft-crdop)

```bash
make -C stacks/crdop all
./scripts/max25-ctl start --hardware soft-modems --device soft-crdop
# HyBBX Secondary with share/hybbx/crdop-edge.ini.example
```

## Platform

**Daemon (`max25d`): Linux only** — full stack including **BayCom**, TNCs, CRDOP. IPC port **7325** (M25/1).

**Terminal (`max25-terminal` / `max25-client`):** the **only** official operator client — text + F10 menu; connects to Linux `max25d` (TCP or unix socket). Develop & bind: [docs/MAX25-CLIENT.md](docs/MAX25-CLIENT.md) · Operator: [docs/MAX25-TERMINAL.md](docs/MAX25-TERMINAL.md) · Platforms: [docs/PLATFORMS.md](docs/PLATFORMS.md).

```bash
# Linux host — daemon (hardware owner)
./stacks/daemon/max25d -c share/max25/max25d.ini.example

# Any platform — operator UI
./stacks/terminal/max25-terminal --host <linux-host> --port 7325
```

## Plugin architecture

```
plugins/
├── betriebsform/     Operating mode (Standalone, Service, HyBBX Edge)
├── hardware/         Hardware group (TNCs, Modems, Soft Modems)
└── devices/          Device-specific (tnc2c, pktnc2, baycom-ser12, soft-crdop, …)
```

Registry: `plugins/manifest.yaml` · Discovery: `./scripts/discover-plugins.sh`

## HyBBX

| MainAX25 hardware | HyBBX plugin | Docs |
|----------------|--------------|------|
| TNCs | `packet_radio` | [docs/HYBBX.md](docs/HYBBX.md) |
| Modems | `baycom` | `stacks/baycom-pr/docs/PLUGIN.md` |
| Soft modems | `crdop` | [docs/HYBBX.md](docs/HYBBX.md#crdop) |

INI examples: `share/hybbx/`

## v1.0.0 roadmap

**Current version:** `1.0.0-rc1` (see `VERSION`)

MainAX25 ships **standalone-first**: one operator brings up TNC or modem without HyBBX; HyBBX attaches later via INI examples in `share/hybbx/`.

| v1.0.0 active | Standalone entry | HyBBX plugin |
|---------------|------------------|--------------|
| **TNC2C** (`tnc2c`) | `max25-ctl start --hardware tncs --device tnc2c` | `packet_radio` |
| **BayCom SER12** (`baycom-ser12`) | `baycom-pr-ctl start` | `baycom` |
| **CRDOP** (`soft-crdop`) | `max25-ctl start --hardware soft-modems` | `crdop` |

**Default operating mode:** `standalone` · **Deferred:** `pktnc2`, `baycom-par96`, `baycom-kiss`, minicom fork, *BSD port.

```bash
make release-check    # v1.0.0 offline gates
```

Full scope, acceptance tests, and release checklist: [docs/V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md).

## Documentation

| Doc | Content |
|-----|---------|
| [docs/V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md) | v1.0.0 MVP scope, workflows, acceptance |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Stack layers, plugin hierarchy |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Development rules, testing |
| [docs/HYBBX.md](docs/HYBBX.md) | HyBBX integration contract |
| [docs/PLATFORMS.md](docs/PLATFORMS.md) | Linux daemon; cross-platform terminal |
| [docs/LINUX-EDGE-SETUP.md](docs/LINUX-EDGE-SETUP.md) | Example edge install & `max25d.ini` |
| [docs/MAX25-TERMINAL.md](docs/MAX25-TERMINAL.md) | Operator UI (F10 menu, CALLERID/CALLID) |
| [docs/PACKET-RADIO.md](docs/PACKET-RADIO.md) | **AX.25, KISS, TNC, BayCom facts** |
| [docs/MAX25-CLIENT.md](docs/MAX25-CLIENT.md) | Client development & M25/1 binding |
| [docs/MERGE-REPORT.md](docs/MERGE-REPORT.md) | Merge archive (one-time) |

## Contributing

[CONTRIBUTING.md](CONTRIBUTING.md) · Agents: [AGENTS.md](AGENTS.md)
